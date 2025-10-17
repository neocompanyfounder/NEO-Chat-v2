"""WhatsApp service for Evolution API integration (T032, T085-T086)."""

import httpx
from typing import Optional, Dict, Any, List
from src.utils.config import Settings
from src.utils.logger import get_logger
from src.utils.retry import with_retry

logger = get_logger(__name__)


class WhatsAppService:
    """Service for sending and receiving WhatsApp messages via Evolution API."""

    def __init__(self, settings: Settings):
        """Initialize WhatsApp service with Evolution API configuration.
        
        Args:
            settings: Application settings containing Evolution API credentials
        """
        self.settings = settings
        self.base_url = settings.EVOLUTION_API_URL
        self.api_key = settings.EVOLUTION_API_KEY
        self.instance_name = settings.EVOLUTION_INSTANCE_NAME
        self.timeout = settings.EVOLUTION_TIMEOUT
        
        self.headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }

    @with_retry(max_retries=5, base_delay=1.0)
    async def send_text_message(
        self, 
        phone_number: str, 
        message: str
    ) -> Dict[str, Any]:
        """Send a text message via Evolution API.
        
        Args:
            phone_number: Recipient phone number in E.164 format
            message: Text message content
            
        Returns:
            API response with message ID and status
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"{self.base_url}/message/sendText/{self.instance_name}"
        
        payload = {
            "number": phone_number,
            "text": message
        }
        
        logger.info(
            "Sending WhatsApp text message",
            extra={
                "phone_number": phone_number,
                "message_length": len(message)
            }
        )
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(
                "WhatsApp message sent successfully",
                extra={
                    "phone_number": phone_number,
                    "message_id": result.get("key", {}).get("id")
                }
            )
            
            return result

    @with_retry(max_retries=5, base_delay=1.0)
    async def send_list_message(
        self,
        phone_number: str,
        title: str,
        description: str,
        button_text: str,
        sections: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Send a List Message with up to 10 options.
        
        Args:
            phone_number: Recipient phone number in E.164 format
            title: List title (max 60 chars)
            description: List description (max 1024 chars)
            button_text: Button text (max 20 chars)
            sections: List of sections with rows (options)
            
        Returns:
            API response with message ID and status
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"{self.base_url}/message/sendList/{self.instance_name}"
        
        payload = {
            "number": phone_number,
            "title": title[:60],
            "description": description[:1024],
            "buttonText": button_text[:20],
            "sections": sections
        }
        
        logger.info(
            "Sending WhatsApp List Message",
            extra={
                "phone_number": phone_number,
                "title": title
            }
        )
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            return response.json()

    @with_retry(max_retries=5, base_delay=1.0)
    async def send_buttons(
        self,
        phone_number: str,
        message: str,
        buttons: list[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Send Reply Buttons (up to 3 buttons).
        
        Args:
            phone_number: Recipient phone number in E.164 format
            message: Message text
            buttons: List of buttons with id and displayText (max 3)
            
        Returns:
            API response with message ID and status
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"{self.base_url}/message/sendButtons/{self.instance_name}"
        
        # Limit to 3 buttons and truncate text to 20 chars
        limited_buttons = [
            {
                "id": btn["id"],
                "displayText": btn["displayText"][:20]
            }
            for btn in buttons[:3]
        ]
        
        payload = {
            "number": phone_number,
            "text": message,
            "buttons": limited_buttons
        }
        
        logger.info(
            "Sending WhatsApp Reply Buttons",
            extra={
                "phone_number": phone_number,
                "button_count": len(limited_buttons)
            }
        )
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            return response.json()

    async def download_media(
        self,
        media_url: str,
        media_type: str
    ) -> bytes:
        """Download media file from WhatsApp servers.
        
        Args:
            media_url: URL to media file
            media_type: Type of media (image, audio, document)
            
        Returns:
            Media file content as bytes
            
        Raises:
            httpx.HTTPError: If download fails
        """
        logger.info(
            "Downloading WhatsApp media",
            extra={
                "media_url": media_url,
                "media_type": media_type
            }
        )
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(media_url)
            response.raise_for_status()
            
            content = response.content
            logger.info(
                "Media downloaded successfully",
                extra={
                    "media_type": media_type,
                    "size_bytes": len(content)
                }
            )
            
            return content
    
    @with_retry(max_retries=3, base_delay=1.0)
    async def send_list_message(
        self,
        phone_number: str,
        title: str,
        description: str,
        button_text: str,
        sections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Send a List Message with up to 10 options (T085).
        
        Args:
            phone_number: Recipient phone number in E.164 format
            title: Message title
            description: Message description
            button_text: Text for the button that opens the list
            sections: List of sections, each containing rows with id, title, description
            
        Returns:
            API response with message ID
            
        Example:
            sections = [{
                "title": "Main Menu",
                "rows": [
                    {"id": "upload", "title": "📄 Upload File", "description": "Upload a document"},
                    {"id": "crawl", "title": "🌐 Crawl Website", "description": "Crawl a website"}
                ]
            }]
        """
        url = f"{self.base_url}/message/sendList/{self.instance_name}"
        
        payload = {
            "number": phone_number,
            "options": {
                "delay": 1200,
                "presence": "composing"
            },
            "listMessage": {
                "title": title,
                "description": description,
                "buttonText": button_text,
                "footerText": "NEO Chat",
                "sections": sections
            }
        }
        
        logger.info(
            "Sending list message",
            extra={
                "phone_number": phone_number,
                "title": title,
                "sections_count": len(sections)
            }
        )
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            
            logger.info(
                "List message sent successfully",
                extra={
                    "phone_number": phone_number,
                    "message_id": result.get("key", {}).get("id")
                }
            )
            
            return result
    
    @with_retry(max_retries=3, base_delay=1.0)
    async def send_buttons_message(
        self,
        phone_number: str,
        text: str,
        buttons: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Send a message with Reply Buttons (up to 3 buttons) (T086).
        
        Args:
            phone_number: Recipient phone number in E.164 format
            text: Message text
            buttons: List of buttons with id and displayText
            
        Returns:
            API response with message ID
            
        Example:
            buttons = [
                {"id": "yes", "displayText": "✅ Yes"},
                {"id": "no", "displayText": "❌ No"}
            ]
        """
        url = f"{self.base_url}/message/sendButtons/{self.instance_name}"
        
        # Limit to 3 buttons as per WhatsApp API
        if len(buttons) > 3:
            logger.warning(
                f"Too many buttons ({len(buttons)}), limiting to 3",
                extra={"phone_number": phone_number}
            )
            buttons = buttons[:3]
        
        payload = {
            "number": phone_number,
            "options": {
                "delay": 1200,
                "presence": "composing"
            },
            "buttonMessage": {
                "text": text,
                "buttons": buttons,
                "footerText": "NEO Chat"
            }
        }
        
        logger.info(
            "Sending buttons message",
            extra={
                "phone_number": phone_number,
                "buttons_count": len(buttons)
            }
        )
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            
            logger.info(
                "Buttons message sent successfully",
                extra={
                    "phone_number": phone_number,
                    "message_id": result.get("key", {}).get("id")
                }
            )
            
            return result
