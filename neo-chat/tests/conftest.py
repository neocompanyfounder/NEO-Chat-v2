"""Pytest configuration and shared fixtures."""

import asyncio
from typing import AsyncGenerator, Generator
import pytest
from httpx import AsyncClient

# Import app components (will be implemented)
# from src.api.main import app
# from src.db.supabase_client import get_supabase_client
# from src.utils.config import settings


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing.
    
    Yields:
        AsyncClient instance for making test requests
    """
    # TODO: Uncomment when app is implemented
    # async with AsyncClient(app=app, base_url="http://test") as client:
    #     yield client
    
    # Placeholder for now
    async with AsyncClient(base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_user_id() -> str:
    """Provide a mock user ID for testing.
    
    Returns:
        Test user phone number in E.164 format
    """
    return "+1234567890"


@pytest.fixture
def mock_message() -> dict:
    """Provide a mock WhatsApp message for testing.
    
    Returns:
        Dictionary representing a WhatsApp message
    """
    return {
        "key": {
            "remoteJid": "+1234567890@s.whatsapp.net",
            "fromMe": False,
            "id": "test-message-id-123"
        },
        "message": {
            "conversation": "Hello, what can you help me with?"
        },
        "messageTimestamp": "1705420800",
        "pushName": "Test User"
    }


@pytest.fixture
def mock_webhook_payload() -> dict:
    """Provide a mock Evolution API webhook payload.
    
    Returns:
        Dictionary representing a webhook event
    """
    return {
        "event": "messages.upsert",
        "instance": "neo-chat",
        "data": {
            "key": {
                "remoteJid": "+1234567890@s.whatsapp.net",
                "fromMe": False,
                "id": "test-message-id-123"
            },
            "message": {
                "conversation": "Test message"
            },
            "messageTimestamp": "1705420800"
        }
    }


@pytest.fixture
def mock_pdf_file() -> bytes:
    """Provide mock PDF file content for testing.
    
    Returns:
        Bytes representing a minimal PDF file
    """
    # Minimal valid PDF
    return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000015 00000 n 
0000000068 00000 n 
0000000125 00000 n 
0000000317 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
410
%%EOF"""


@pytest.fixture
def mock_embedding() -> list[float]:
    """Provide a mock embedding vector for testing.
    
    Returns:
        List of 768 floats (text-embedding-004 dimension)
    """
    import random
    random.seed(42)  # Deterministic for tests
    return [random.random() for _ in range(768)]


@pytest.fixture
def mock_chunks() -> list[dict]:
    """Provide mock text chunks for testing.
    
    Returns:
        List of chunk dictionaries
    """
    return [
        {
            "content": "This is the first chunk of text from a document.",
            "chunk_index": 0,
            "token_count": 12
        },
        {
            "content": "This is the second chunk with more information.",
            "chunk_index": 1,
            "token_count": 10
        },
        {
            "content": "Final chunk containing conclusion and summary.",
            "chunk_index": 2,
            "token_count": 8
        }
    ]


# Database fixtures (to be implemented)
@pytest.fixture
async def db_session():
    """Provide a database session for testing.
    
    TODO: Implement when database client is ready
    """
    # async with get_supabase_client() as session:
    #     yield session
    pass


# Mock external services
@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response."""
    return {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": "This is a test AI response."
                }]
            }
        }]
    }


@pytest.fixture
def mock_evolution_api_response():
    """Mock Evolution API response."""
    return {
        "status": "success",
        "message": "Message sent successfully"
    }


# Cleanup fixtures
@pytest.fixture(autouse=True)
async def cleanup():
    """Cleanup after each test."""
    yield
    # Add cleanup logic here if needed
    pass
