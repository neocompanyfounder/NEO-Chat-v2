"""Data models for NEO Chat."""

from .user import User, UserCreate, UserUpdate
from .message import Message, MessageCreate, ConversationHistory
from .chunk import Chunk, ChunkCreate, ChunkWithEmbedding, ChunkSearchResult
from .webhook_events import (
    WebhookEvent,
    WhatsAppMessage,
    SendMessageRequest,
    SendMessageResponse
)

__all__ = [
    "User",
    "UserCreate",
    "UserUpdate",
    "Message",
    "MessageCreate",
    "ConversationHistory",
    "Chunk",
    "ChunkCreate",
    "ChunkWithEmbedding",
    "ChunkSearchResult",
    "WebhookEvent",
    "WhatsAppMessage",
    "SendMessageRequest",
    "SendMessageResponse",
]
