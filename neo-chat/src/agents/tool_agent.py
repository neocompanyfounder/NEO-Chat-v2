"""Tool agent for knowledge base operations (T038, T057, T071, T080-T081)."""

from crewai import Agent
from typing import Dict, Any, Optional
from src.services.knowledge_base import KnowledgeBaseService
from src.services.whatsapp_service import WhatsAppService
from src.services.rag_ingestion_service import RAGIngestionService
from src.services.crawler_service import CrawlerService
from src.services.speech_service import SpeechService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ToolAgent:
    """Agent responsible for executing tools (knowledge base operations, WhatsApp, file processing, web crawling)."""

    def __init__(
        self,
        knowledge_base_service: KnowledgeBaseService,
        whatsapp_service: WhatsAppService,
        rag_ingestion_service: Optional[RAGIngestionService] = None,
        crawler_service: Optional[CrawlerService] = None,
        speech_service: Optional[SpeechService] = None
    ):
        """Initialize tool agent with required services.
        
        Args:
            knowledge_base_service: Service for knowledge base operations
            whatsapp_service: Service for WhatsApp operations
            rag_ingestion_service: Optional service for RAG ingestion (T057)
            crawler_service: Optional service for web crawling (T071)
            speech_service: Optional service for speech-to-text (T080-T081)
        """
        self.knowledge_base_service = knowledge_base_service
        self.whatsapp_service = whatsapp_service
        self.rag_ingestion_service = rag_ingestion_service
        self.crawler_service = crawler_service
        self.speech_service = speech_service
        self.agent = self._create_agent()

    def _create_agent(self) -> Agent:
        """Create CrewAI agent with tool execution capabilities.
        
        Returns:
            Configured CrewAI Agent
        """
        agent = Agent(
            role="Tool Execution Specialist",
            goal="Execute tools and operations for knowledge base management, file processing, web crawling, and WhatsApp communication",
            backstory="""You are an expert at executing various tools and operations.
            You can store conversations in the knowledge base, process uploaded files,
            crawl websites to extract content, send WhatsApp messages, and manage 
            knowledge base operations like resets. You handle file uploads by extracting 
            text, chunking it, generating embeddings, and storing everything in the vector 
            database. You can also crawl websites to extract content and add it to the 
            knowledge base. You ensure all operations are executed correctly and provide 
            clear feedback on success or failure.""",
            verbose=True,
            allow_delegation=False
        )
        
        return agent
    
    async def process_file_upload(
        self,
        user_id: str,
        filename: str,
        file_content: bytes,
        mime_type: str
    ) -> Dict[str, Any]:
        """Process uploaded file through RAG ingestion pipeline (T057).
        
        Args:
            user_id: User identifier
            filename: Original filename
            file_content: Raw file bytes
            mime_type: MIME type
            
        Returns:
            Processing result dictionary
        """
        if not self.rag_ingestion_service:
            logger.error("RAG ingestion service not initialized")
            return {
                "success": False,
                "error": "File processing service not available"
            }
        
        logger.info(
            "Processing file upload",
            extra={
                "user_id": user_id,
                "filename": filename,
                "file_size": len(file_content)
            }
        )
        
        try:
            result = await self.rag_ingestion_service.ingest_document(
                user_id=user_id,
                filename=filename,
                file_content=file_content,
                mime_type=mime_type
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"File processing failed: {str(e)}",
                extra={
                    "user_id": user_id,
                    "filename": filename,
                    "error": str(e)
                }
            )
            return {
                "success": False,
                "error": f"File processing failed: {str(e)}"
            }
    
    async def process_web_crawl(
        self,
        user_id: str,
        url: str,
        max_depth: int = 3,
        max_pages: int = 100
    ) -> Dict[str, Any]:
        """Process web crawl request (T071).
        
        Args:
            user_id: User identifier
            url: URL to crawl
            max_depth: Maximum crawl depth
            max_pages: Maximum pages to crawl
            
        Returns:
            Processing result dictionary
        """
        if not self.crawler_service:
            logger.error("Crawler service not initialized")
            return {
                "success": False,
                "error": "Web crawling service not available"
            }
        
        logger.info(
            "Processing web crawl request",
            extra={
                "user_id": user_id,
                "url": url,
                "max_depth": max_depth,
                "max_pages": max_pages
            }
        )
        
        try:
            # Validate URL
            is_valid, error_msg = self.crawler_service.validate_url(url)
            if not is_valid:
                return {
                    "success": False,
                    "error": error_msg
                }
            
            # Create crawl job
            from src.models.crawl_job import CrawlJobCreate
            crawl_job_create = CrawlJobCreate(
                user_id=user_id,
                url=url,
                max_depth=max_depth,
                max_pages=max_pages
            )
            
            crawl_job = await self.crawler_service.crawl_job_repo.create(crawl_job_create)
            
            # Start crawling (async, will update job status)
            result = await self.crawler_service.crawl_website(
                job_id=crawl_job.id,
                start_url=url,
                max_depth=max_depth,
                max_pages=max_pages
            )
            
            return {
                "success": result.get("success", False),
                "job_id": crawl_job.id,
                "pages_crawled": result.get("pages_crawled", 0),
                "chunks_created": result.get("chunks_created", 0),
                "error": result.get("error")
            }
            
        except Exception as e:
            logger.error(
                f"Web crawl processing failed: {str(e)}",
                extra={
                    "user_id": user_id,
                    "url": url,
                    "error": str(e)
                }
            )
            return {
                "success": False,
                "error": f"Web crawl failed: {str(e)}"
            }
    
    async def process_voice_message(
        self,
        user_id: str,
        media_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process voice message with transcription (T080-T081).
        
        Args:
            user_id: User identifier
            media_info: Media information from webhook
            
        Returns:
            Processing result dictionary
        """
        if not self.speech_service:
            logger.error("Speech service not initialized")
            return {
                "success": False,
                "error": "Voice message processing service not available"
            }
        
        logger.info(
            "Processing voice message",
            extra={
                "user_id": user_id,
                "duration": media_info.get("data", {}).get("seconds", 0)
            }
        )
        
        try:
            # Extract media details
            media_data = media_info.get("data", {})
            media_url = media_data.get("url")
            mime_type = media_data.get("mimetype", "audio/ogg")
            duration = media_data.get("seconds")
            
            if not media_url:
                error_msg = "No media URL found in voice message"
                logger.error(error_msg, extra={"user_id": user_id})
                return {
                    "success": False,
                    "error": error_msg
                }
            
            # Download audio from WhatsApp
            audio_content = await self.whatsapp_service.download_media(media_url)
            
            if not audio_content:
                error_msg = "Failed to download voice message"
                logger.error(error_msg, extra={"user_id": user_id})
                return {
                    "success": False,
                    "error": error_msg
                }
            
            # Transcribe audio
            result = await self.speech_service.transcribe_audio(
                audio_content=audio_content,
                filename=f"voice_{user_id}.ogg",
                mime_type=mime_type,
                duration_seconds=duration
            )
            
            if result.get("success"):
                # Store transcribed text in conversation history (T081)
                transcribed_text = result.get("text", "")
                
                # Note: The conversation will be stored by crew_manager
                # after the AI responds to the transcribed text
                
                logger.info(
                    "Voice message transcribed successfully",
                    extra={
                        "user_id": user_id,
                        "text_length": len(transcribed_text),
                        "confidence": result.get("confidence", 0.0)
                    }
                )
                
                return {
                    "success": True,
                    "text": transcribed_text,
                    "confidence": result.get("confidence", 0.0),
                    "language": result.get("language", "en-US"),
                    "warning": result.get("warning")
                }
            else:
                return {
                    "success": False,
                    "error": "Transcription failed"
                }
            
        except Exception as e:
            logger.error(
                f"Voice message processing failed: {str(e)}",
                extra={
                    "user_id": user_id,
                    "error": str(e)
                }
            )
            return {
                "success": False,
                "error": f"Voice message processing failed: {str(e)}"
            }

    def get_agent(self) -> Agent:
        """Get the configured CrewAI agent.
        
        Returns:
            CrewAI Agent instance
        """
        return self.agent
