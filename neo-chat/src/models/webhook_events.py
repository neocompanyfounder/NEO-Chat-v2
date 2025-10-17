"""Evolution API webhook event models."""

from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class MessageKey(BaseModel):
    """WhatsApp message key."""
    
    remoteJid: str = Field(..., description="Sender's JID (phone@s.whatsapp.net)")
    fromMe: bool = Field(..., description="Whether message is from bot")
    id: str = Field(..., description="Message ID")


class TextMessage(BaseModel):
    """Text message content."""
    
    conversation: Optional[str] = Field(None, description="Text message content")


class ImageMessage(BaseModel):
    """Image message content."""
    
    url: Optional[str] = Field(None, description="Image URL")
    mimetype: Optional[str] = Field(None, description="Image MIME type")
    caption: Optional[str] = Field(None, description="Image caption")


class DocumentMessage(BaseModel):
    """Document message content."""
    
    url: Optional[str] = Field(None, description="Document URL")
    mimetype: Optional[str] = Field(None, description="Document MIME type")
    fileName: Optional[str] = Field(None, description="Document filename")
    caption: Optional[str] = Field(None, description="Document caption")


class AudioMessage(BaseModel):
    """Audio/voice message content."""
    
    url: Optional[str] = Field(None, description="Audio URL")
    mimetype: Optional[str] = Field(None, description="Audio MIME type")
    ptt: Optional[bool] = Field(None, description="Is push-to-talk (voice message)")


class MessageContent(BaseModel):
    """Message content union."""
    
    conversation: Optional[str] = None
    imageMessage: Optional[ImageMessage] = None
    documentMessage: Optional[DocumentMessage] = None
    audioMessage: Optional[AudioMessage] = None
    extendedTextMessage: Optional[Dict[str, Any]] = None


class WhatsAppMessage(BaseModel):
    """WhatsApp message from Evolution API."""
    
    key: MessageKey = Field(..., description="Message key")
    message: MessageContent = Field(..., description="Message content")
    messageTimestamp: str = Field(..., description="Message timestamp")
    pushName: Optional[str] = Field(None, description="Sender's display name")
    messageType: Optional[str] = Field(None, description="Message type")


class WebhookData(BaseModel):
    """Webhook event data."""
    
    key: MessageKey
    message: MessageContent
    messageTimestamp: str
    pushName: Optional[str] = None
    messageType: Optional[str] = None


class WebhookEvent(BaseModel):
    """Evolution API webhook event."""
    
    event: Literal[
        "messages.upsert",
        "messages.update",
        "messages.delete",
        "connection.update"
    ] = Field(..., description="Event type")
    instance: str = Field(..., description="Instance name")
    data: WebhookData = Field(..., description="Event data")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "event": "messages.upsert",
                "instance": "neo-chat",
                "data": {
                    "key": {
                        "remoteJid": "+1234567890@s.whatsapp.net",
                        "fromMe": False,
                        "id": "3EB0123456789ABCDEF"
                    },
                    "message": {
                        "conversation": "Hello, what can you help me with?"
                    },
                    "messageTimestamp": "1705420800",
                    "pushName": "John Doe"
                }
            }
        }


class SendMessageRequest(BaseModel):
    """Request to send a message via Evolution API."""
    
    number: str = Field(..., description="Recipient phone number")
    text: Optional[str] = Field(None, description="Text message content")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")


class SendMessageResponse(BaseModel):
    """Response from sending a message."""
    
    key: MessageKey = Field(..., description="Message key")
    message: Dict[str, Any] = Field(..., description="Message details")
    status: str = Field(..., description="Send status")
