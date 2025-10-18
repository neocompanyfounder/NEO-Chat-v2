"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..db import supabase_client
from ..utils.logger import logger
from ..utils.config import settings
from .routes import health, webhook, users
from .middleware.logging import LoggingMiddleware
from .middleware.error_handler import ErrorHandlerMiddleware

# Import services and agents
from ..services.whatsapp_service import WhatsAppService
from ..services.gemini_service import GeminiService
from ..services.vector_service import VectorService
from ..services.knowledge_base import KnowledgeBaseService
from ..db.repositories.user_repository import UserRepository
from ..db.repositories.chunk_repository import ChunkRepository
from ..db.repositories.embedding_repository import EmbeddingRepository
from ..agents.retrieval_agent import RetrievalAgent
from ..agents.response_agent import ResponseAgent
from ..agents.tool_agent import ToolAgent
from ..agents.crew_manager import CrewManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events.
    
    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    logger.info(
        "Starting NEO Chat application",
        extra={
            "event_type": "app_startup",
            "metadata": {
                "env": settings.APP_ENV,
                "version": "0.1.0"
            }
        }
    )
    
    # Connect to database
    try:
        await supabase_client.connect()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise
    
    # Initialize services
    whatsapp_service = WhatsAppService(settings)
    gemini_service = GeminiService(settings)
    vector_service = VectorService(settings)
    
    # Initialize repositories
    user_repository = UserRepository(settings)
    chunk_repository = ChunkRepository(settings)
    embedding_repository = EmbeddingRepository(settings)
    
    # Initialize knowledge base service
    knowledge_base_service = KnowledgeBaseService(
        settings=settings,
        gemini_service=gemini_service,
        vector_service=vector_service,
        chunk_repository=chunk_repository,
        embedding_repository=embedding_repository
    )
    
    # Initialize agents
    retrieval_agent = RetrievalAgent(knowledge_base_service)
    response_agent = ResponseAgent(gemini_service)
    tool_agent = ToolAgent(knowledge_base_service, whatsapp_service)
    
    # Initialize crew manager
    crew_manager = CrewManager(retrieval_agent, response_agent, tool_agent)
    
    # Store in app state for dependency injection
    app.state.crew_manager = crew_manager
    app.state.whatsapp_service = whatsapp_service
    app.state.gemini_service = gemini_service
    app.state.knowledge_base_service = knowledge_base_service
    
    logger.info("All services and agents initialized")
    
    yield
    
    # Shutdown
    logger.info(
        "Shutting down NEO Chat application",
        extra={"event_type": "app_shutdown"}
    )
    
    # Disconnect from database
    try:
        await supabase_client.disconnect()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error closing database connection: {e}")


# Create FastAPI application
app = FastAPI(
    title="NEO Chat - WhatsApp AI RAG Engine",
    description="A WhatsApp-based AI assistant with personalized knowledge bases",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.APP_ENV == "development" else None,
    redoc_url="/redoc" if settings.APP_ENV == "development" else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.APP_ENV == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(webhook.router, tags=["Webhook"])
app.include_router(users.router, tags=["Users"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "NEO Chat",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs" if settings.APP_ENV == "development" else None
    }
