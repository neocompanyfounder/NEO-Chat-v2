"""Webhook endpoint for Evolution API message reception (T040-T041, T072)."""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from typing import Dict, Any, Optional, List
import asyncio
import re
from collections import defaultdict
from src.models.webhook_events import WebhookEvent
from src.agents.crew_manager import CrewManager
from src.db.repositories.user_repository import UserRepository
from src.db.supabase_client import supabase_client
from src.utils.phone_utils import normalize_phone_number
from src.utils.logger import get_logger
from src.utils.config import get_settings

logger = get_logger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])

# FIFO queue per user (phone number)
user_message_queues: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
user_queue_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

# URL detection pattern (T072)
URL_PATTERN = re.compile(
    r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)',
    re.IGNORECASE
)


def extract_urls(text: str) -> List[str]:
    """Extract URLs from text message (T072).
    
    Args:
        text: Message text
        
    Returns:
        List of URLs found
    """
    if not text:
        return []
    
    urls = URL_PATTERN.findall(text)
    return [url.strip() for url in urls if url.strip()]


async def get_crew_manager() -> CrewManager:
    """Dependency to get crew manager instance.
    
    Returns:
        Configured CrewManager
    """
    # This will be properly initialized with dependency injection
    # For now, returning None - will be set up in main.py
    from src.api.main import app
    return app.state.crew_manager


async def process_user_queue(phone_number: str, crew_manager: CrewManager):
    """Process messages from user's FIFO queue.
    
    Args:
        phone_number: User's phone number
        crew_manager: CrewManager instance for processing
    """
    queue = user_message_queues[phone_number]
    lock = user_queue_locks[phone_number]
    
    async with lock:
        while not queue.empty():
            try:
                message_data = await queue.get()
                
                logger.info(
                    "Processing queued message",
                    extra={
                        "phone_number": phone_number,
                        "queue_size": queue.qsize()
                    }
                )
                
                # Check message type
                if message_data.get("media_info"):
                    media_info = message_data["media_info"]
                    
                    # Check if this is a voice message (T080)
                    if media_info.get("is_voice"):
                        # Process voice message
                        await crew_manager.process_voice_message(
                            user_id=message_data["user_id"],
                            phone_number=phone_number,
                            media_info=media_info
                        )
                    else:
                        # Process file upload (T058)
                        await crew_manager.process_file_upload(
                            user_id=message_data["user_id"],
                            phone_number=phone_number,
                            media_info=media_info,
                            caption=message_data.get("message", "")
                        )
                else:
                    # Check if message contains URLs (T072)
                    message_text = message_data["message"]
                    urls = extract_urls(message_text)
                    
                    if urls:
                        # Process web crawl for first URL found
                        url = urls[0]
                        logger.info(
                            "URL detected in message",
                            extra={
                                "user_id": message_data["user_id"],
                                "url": url,
                                "total_urls": len(urls)
                            }
                        )
                        
                        await crew_manager.process_web_crawl(
                            user_id=message_data["user_id"],
                            phone_number=phone_number,
                            url=url
                        )
                    else:
                        # Process regular text message
                        await crew_manager.process_simple_message(
                            user_id=message_data["user_id"],
                            phone_number=phone_number,
                            message=message_text
                        )
                
                queue.task_done()
                
            except Exception as e:
                logger.error(
                    "Queue message processing failed",
                    extra={
                        "error": str(e),
                        "phone_number": phone_number
                    }
                )


@router.post("/evolution")
async def evolution_webhook(
    event: Dict[str, Any],
    background_tasks: BackgroundTasks,
    crew_manager: CrewManager = Depends(get_crew_manager)
):
    """Receive webhook events from Evolution API.
    
    Implements FIFO message queue per user (FR-002b).
    
    Args:
        event: Webhook event data
        background_tasks: FastAPI background tasks
        crew_manager: Crew manager for message processing
        
    Returns:
        Acknowledgment response
    """
    logger.info(
        "Webhook event received",
        extra={
            "event_type": event.get("event"),
            "instance": event.get("instance")
        }
    )
    logger.debug(
        "Webhook payload",
        extra={
            "payload": event
        }
    )
    
    try:
        # Parse event type
        event_type = (
            event.get("event")
            or event.get("type")
            or event.get("action")
        )

        # Fallback for message-upsert style events without explicit type field
        if not event_type:
            data_section = event.get("data") or {}
            if data_section.get("message"):
                event_type = "messages.upsert"
            elif "messages" in event:
                # Some Evolution builds wrap message payloads directly under `messages`
                event_type = "messages.upsert"
        
        if event_type == "messages.upsert":
            # Extract message data
            data = event.get("data", {})
            message_data = data.get("message", {})
            
            # Get sender info
            sender_info = data.get("key", {})
            remote_jid = sender_info.get("remoteJid", "")
            
            # Extract phone number and normalize to E.164
            phone_number = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid
            normalized_phone = normalize_phone_number(phone_number)
            
            # Check if message is from user (not from bot)
            from_me = sender_info.get("fromMe", False)
            if from_me:
                logger.info(
                    "Ignoring message from bot",
                    extra={"phone_number": normalized_phone}
                )
                return {"status": "ignored", "reason": "message_from_bot"}
            
            # Extract message content
            message_type = message_data.get("messageType", "")
            message_text = ""
            media_info = None
            
            if message_type == "conversation":
                message_text = message_data.get("conversation", "")
            elif message_type == "extendedTextMessage":
                message_text = message_data.get("extendedTextMessage", {}).get("text", "")
            elif message_type in ["imageMessage", "documentMessage"]:
                # File upload detected (T058)
                media_info = {
                    "type": message_type,
                    "data": message_data.get(message_type, {})
                }
                # Caption as message text if present
                message_text = media_info["data"].get("caption", "")
                logger.info(
                    "File upload detected",
                    extra={
                        "message_type": message_type,
                        "phone_number": normalized_phone,
                        "has_caption": bool(message_text)
                    }
                )
            elif message_type == "audioMessage":
                # Voice message detected (T080)
                media_info = {
                    "type": message_type,
                    "data": message_data.get(message_type, {}),
                    "is_voice": True  # Flag to distinguish from audio files
                }
                logger.info(
                    "Voice message detected",
                    extra={
                        "message_type": message_type,
                        "phone_number": normalized_phone,
                        "duration": media_info["data"].get("seconds", 0)
                    }
                )
            else:
                logger.info(
                    "Unsupported message type",
                    extra={
                        "message_type": message_type,
                        "phone_number": normalized_phone
                    }
                )
                return {"status": "ignored", "reason": f"unsupported_type_{message_type}"}
            
            # Allow empty text for media messages
            if not message_text and not media_info:
                logger.warning(
                    "Empty message received",
                    extra={"phone_number": normalized_phone}
                )
                return {"status": "ignored", "reason": "empty_message"}
            
            # Get or create user
            user_repo = UserRepository(supabase_client)
            user = await user_repo.get_or_create(normalized_phone)
            
            logger.info(
                "Message queued for processing",
                extra={
                    "user_id": user["id"],
                    "phone_number": normalized_phone,
                    "message_length": len(message_text)
                }
            )
            
            # Add message to user's FIFO queue
            queue = user_message_queues[normalized_phone]
            await queue.put({
                "user_id": user["id"],
                "message": message_text,
                "media_info": media_info,  # T058: Include media info for file uploads
                "timestamp": data.get("messageTimestamp")
            })
            
            # Process queue in background
            background_tasks.add_task(
                process_user_queue,
                normalized_phone,
                crew_manager
            )
            
            return {
                "status": "queued",
                "user_id": user["id"],
                "phone_number": normalized_phone,
                "queue_size": queue.qsize()
            }
        
        else:
            logger.warning(
                "Unhandled event type",
                extra={
                    "event_type": event_type,
                    "payload": event
                }
            )
            return {"status": "ignored", "reason": f"unhandled_event_{event_type}"}
    
    except Exception as e:
        logger.error(
            "Webhook processing failed",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "event": event
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Webhook processing error: {str(e)}"
        )


@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "endpoint": "webhook",
        "active_queues": len(user_message_queues)
    }
