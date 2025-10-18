"""Crew manager for sequential agent orchestration (T039, T080-T081)."""

from crewai import Crew, Task, Process
from typing import Dict, Any
from src.agents.retrieval_agent import RetrievalAgent
from src.agents.response_agent import ResponseAgent
from src.agents.tool_agent import ToolAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CrewManager:
    """Manager for orchestrating CrewAI agents in sequential workflow."""

    def __init__(
        self,
        retrieval_agent: RetrievalAgent,
        response_agent: ResponseAgent,
        tool_agent: ToolAgent
    ):
        """Initialize crew manager with agents.
        
        Args:
            retrieval_agent: Agent for knowledge base retrieval
            response_agent: Agent for response generation
            tool_agent: Agent for tool execution
        """
        self.retrieval_agent = retrieval_agent
        self.response_agent = response_agent
        self.tool_agent = tool_agent

    async def process_message(
        self,
        user_id: str,
        phone_number: str,
        message: str
    ) -> Dict[str, Any]:
        """Process incoming WhatsApp message through agent workflow.
        
        Sequential workflow:
        1. Retrieval Agent: Search knowledge base for context
        2. Response Agent: Generate AI response with context
        3. Tool Agent: Send response and store conversation
        
        Args:
            user_id: User identifier
            phone_number: User's phone number
            message: User's message text
            
        Returns:
            Processing result with response and metadata
        """
        logger.info(
            "Crew manager processing message",
            extra={
                "user_id": user_id,
                "phone_number": phone_number,
                "message_length": len(message)
            }
        )
        
        try:
            # Task 1: Retrieve context from knowledge base
            retrieval_task = Task(
                description=f"""Search the knowledge base for information relevant to this query: "{message}"
                User ID: {user_id}
                
                Return the most relevant context found, or indicate if no relevant information exists.""",
                agent=self.retrieval_agent.get_agent(),
                expected_output="Relevant context from knowledge base or indication that no context was found"
            )
            
            # Task 2: Generate AI response
            response_task = Task(
                description=f"""Generate a helpful response to the user's query: "{message}"
                
                Use the context provided by the retrieval agent if available.
                If no context is available, provide a general helpful response.
                Be concise, accurate, and friendly.""",
                agent=self.response_agent.get_agent(),
                expected_output="A helpful AI-generated response to the user's query",
                context=[retrieval_task]
            )
            
            # Task 3: Send response and store conversation
            tool_task = Task(
                description=f"""Complete these actions:
                1. Send the AI response to the user via WhatsApp (phone: {phone_number})
                2. Store the conversation in the knowledge base (user_id: {user_id})
                   - User message: "{message}"
                   - AI response: Use the response from the response agent
                
                Provide confirmation of both actions.""",
                agent=self.tool_agent.get_agent(),
                expected_output="Confirmation that message was sent and conversation was stored",
                context=[response_task]
            )
            
            # Create crew with sequential process
            crew = Crew(
                agents=[
                    self.retrieval_agent.get_agent(),
                    self.response_agent.get_agent(),
                    self.tool_agent.get_agent()
                ],
                tasks=[retrieval_task, response_task, tool_task],
                process=Process.sequential,
                verbose=True
            )
            
            # Execute crew workflow
            logger.info(
                "Starting crew execution",
                extra={"user_id": user_id}
            )
            
            result = crew.kickoff()
            
            logger.info(
                "Crew execution completed",
                extra={
                    "user_id": user_id,
                    "result_type": type(result).__name__
                }
            )
            
            return {
                "success": True,
                "user_id": user_id,
                "phone_number": phone_number,
                "message": message,
                "result": str(result),
                "workflow": "sequential"
            }
            
        except Exception as e:
            logger.error(
                "Crew execution failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "user_id": user_id
                }
            )
            
            # Fallback: Send error message to user
            try:
                await self.tool_agent.whatsapp_service.send_text_message(
                    phone_number=phone_number,
                    message="Sorry, I encountered an error processing your message. Please try again later."
                )
            except Exception as send_error:
                logger.error(
                    "Failed to send error message",
                    extra={"error": str(send_error)}
                )
            
            return {
                "success": False,
                "user_id": user_id,
                "phone_number": phone_number,
                "message": message,
                "error": str(e),
                "workflow": "sequential"
            }

    async def process_simple_message(
        self,
        user_id: str,
        phone_number: str,
        message: str
    ) -> Dict[str, Any]:
        """Simplified message processing without full crew orchestration (for MVP).
        
        This is a simpler implementation that doesn't use full CrewAI orchestration,
        suitable for MVP deployment.
        
        Args:
            user_id: User identifier
            phone_number: User's phone number
            message: User's message text
            
        Returns:
            Processing result with response
        """
        logger.info(
            "Processing message (simple mode)",
            extra={
                "user_id": user_id,
                "message_length": len(message)
            }
        )
        
        try:
            # Step 1: Retrieve context
            context = await self.retrieval_agent.knowledge_base_service.retrieve_context(
                user_id=user_id,
                query=message
            )
            
            # Step 2: Generate response
            ai_response = await self.response_agent.generate_response(
                query=message,
                context=context if context else None
            )
            
            # Step 3: Send response
            await self.tool_agent.whatsapp_service.send_text_message(
                phone_number=phone_number,
                message=ai_response
            )
            
            # Step 4: Store conversation
            await self.tool_agent.knowledge_base_service.store_conversation(
                user_id=user_id,
                user_message=message,
                ai_response=ai_response
            )
            
            logger.info(
                "Message processed successfully",
                extra={
                    "user_id": user_id,
                    "response_length": len(ai_response)
                }
            )
            
            return {
                "success": True,
                "user_id": user_id,
                "phone_number": phone_number,
                "message": message,
                "response": ai_response,
                "has_context": bool(context)
            }
            
        except Exception as e:
            logger.error(
                "Message processing failed",
                extra={
                    "error": str(e),
                    "user_id": user_id
                }
            )
            
            # Send error message
            try:
                await self.tool_agent.whatsapp_service.send_text_message(
                    phone_number=phone_number,
                    message="Sorry, I encountered an error. Please try again."
                )
            except:
                pass
            
            return {
                "success": False,
                "user_id": user_id,
                "error": str(e)
            }
    
    async def process_file_upload(
        self,
        user_id: str,
        phone_number: str,
        media_info: Dict[str, Any],
        caption: str = ""
    ) -> Dict[str, Any]:
        """Process file upload through RAG ingestion pipeline (User Story 2).
        
        Args:
            user_id: User identifier
            phone_number: User's phone number
            media_info: Media information from webhook
            caption: Optional caption text
            
        Returns:
            Processing result
        """
        logger.info(
            "Processing file upload",
            extra={
                "user_id": user_id,
                "media_type": media_info.get("type"),
                "has_caption": bool(caption)
            }
        )
        
        try:
            # Extract media details
            media_type = media_info.get("type")
            media_data = media_info.get("data", {})
            media_url = media_data.get("url")
            mime_type = media_data.get("mimetype", "application/octet-stream")
            filename = media_data.get("fileName", f"file_{user_id}")
            
            if not media_url:
                error_msg = "No media URL found in upload"
                logger.error(error_msg, extra={"user_id": user_id})
                
                await self.tool_agent.whatsapp_service.send_text_message(
                    phone_number=phone_number,
                    message="Sorry, I couldn't access the uploaded file. Please try again."
                )
                
                return {
                    "success": False,
                    "user_id": user_id,
                    "error": error_msg
                }
            
            # Send processing notification
            await self.tool_agent.whatsapp_service.send_text_message(
                phone_number=phone_number,
                message=f"📄 Processing your file: {filename}\nThis may take a moment..."
            )
            
            # Download file from WhatsApp
            file_content = await self.tool_agent.whatsapp_service.download_media(
                media_url=media_url,
                media_type=media_type
            )
            
            # Process through RAG ingestion pipeline
            result = await self.tool_agent.process_file_upload(
                user_id=user_id,
                filename=filename,
                file_content=file_content,
                mime_type=mime_type
            )
            
            # Send result notification
            if result.get("success"):
                chunks_count = result.get("chunks_count", 0)
                file_type = result.get("file_type", "file")
                
                success_msg = (
                    f"✅ File processed successfully!\n\n"
                    f"📄 {filename}\n"
                    f"📊 {chunks_count} chunks added to your knowledge base\n\n"
                    f"You can now ask me questions about this {file_type}!"
                )
                
                if caption:
                    success_msg += f"\n\n💬 Your note: {caption}"
                
                await self.tool_agent.whatsapp_service.send_text_message(
                    phone_number=phone_number,
                    message=success_msg
                )
                
                logger.info(
                    "File upload processed successfully",
                    extra={
                        "user_id": user_id,
                        "filename": filename,
                        "chunks_count": chunks_count
                    }
                )
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "filename": filename,
                    "chunks_count": chunks_count
                }
            else:
                # Handle processing errors
                error_type = result.get("error_type", "unknown")
                error_msg = result.get("error", "Processing failed")
                
                if error_type == "file_size_exceeded":
                    user_msg = error_msg
                elif error_type == "unsupported_file_type":
                    user_msg = f"❌ {error_msg}\n\nSupported formats: PDF, DOCX, XLSX, PPTX, TXT, and images"
                elif error_type == "no_text_extracted":
                    user_msg = f"❌ No text could be extracted from {filename}. Please make sure the file contains readable text."
                else:
                    user_msg = f"❌ Failed to process {filename}. Please try again or use a different file."
                
                await self.tool_agent.whatsapp_service.send_text_message(
                    phone_number=phone_number,
                    message=user_msg
                )
                
                logger.warning(
                    "File upload processing failed",
                    extra={
                        "user_id": user_id,
                        "filename": filename,
                        "error_type": error_type,
                        "error": error_msg
                    }
                )
                
                return {
                    "success": False,
                    "user_id": user_id,
                    "filename": filename,
                    "error": error_msg,
                    "error_type": error_type
                }
                
        except Exception as e:
            logger.error(
                "File upload processing exception",
                extra={
                    "error": str(e),
                    "user_id": user_id
                }
            )
            
            # Send error message
            try:
                await self.tool_agent.whatsapp_service.send_text_message(
                    phone_number=phone_number,
                    message="❌ An error occurred while processing your file. Please try again later."
                )
            except:
                pass
            
            return {
                "success": False,
                "user_id": user_id,
                "error": str(e)
            }
    
    async def process_web_crawl(
        self,
        user_id: str,
        phone_number: str,
        url: str,
        max_depth: int = 3,
        max_pages: int = 100
    ) -> Dict[str, Any]:
        """Process web crawl request (User Story 3).
        
        Args:
            user_id: User identifier
            phone_number: User's phone number
            url: URL to crawl
            max_depth: Maximum crawl depth (default: 3)
            max_pages: Maximum pages to crawl (default: 100)
            
        Returns:
            Processing result
        """
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
            # Send initial notification
            await self.tool_agent.whatsapp_service.send_text_message(
                phone_number=phone_number,
                message=f"🌐 Starting to crawl: {url}\n\nThis may take a few minutes..."
            )
            
            # Process web crawl
            result = await self.tool_agent.process_web_crawl(
                user_id=user_id,
                url=url,
                max_depth=max_depth,
                max_pages=max_pages
            )
            
            if result.get("success"):
                # Send success notification
                pages_crawled = result.get("pages_crawled", 0)
                chunks_created = result.get("chunks_created", 0)
                
                success_msg = (
                    f"✅ Web crawl completed!\n\n"
                    f"📄 Pages crawled: {pages_crawled}\n"
                    f"📦 Content chunks: {chunks_created}\n\n"
                    f"The content has been added to your knowledge base. "
                    f"You can now ask me questions about it!"
                )
                
                await self.tool_agent.whatsapp_service.send_text_message(
                    phone_number=phone_number,
                    message=success_msg
                )
                
                logger.info(
                    "Web crawl completed successfully",
                    extra={
                        "user_id": user_id,
                        "url": url,
                        "pages_crawled": pages_crawled,
                        "chunks_created": chunks_created
                    }
                )
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "url": url,
                    "pages_crawled": pages_crawled,
                    "chunks_created": chunks_created,
                    "job_id": result.get("job_id")
                }
            else:
                # Send error notification
                error_msg = result.get("error", "Unknown error")
                
                user_msg = (
                    f"❌ Web crawl failed\n\n"
                    f"URL: {url}\n"
                    f"Error: {error_msg}\n\n"
                    f"Please check the URL and try again."
                )
                
                await self.tool_agent.whatsapp_service.send_text_message(
                    phone_number=phone_number,
                    message=user_msg
                )
                
                logger.warning(
                    "Web crawl failed",
                    extra={
                        "user_id": user_id,
                        "url": url,
                        "error": error_msg
                    }
                )
                
                return {
                    "success": False,
                    "user_id": user_id,
                    "url": url,
                    "error": error_msg
                }
                
        except Exception as e:
            logger.error(
                "Web crawl processing exception",
                extra={
                    "error": str(e),
                    "user_id": user_id,
                    "url": url
                }
            )
            
            # Send error message
            try:
                await self.tool_agent.whatsapp_service.send_text_message(
                    phone_number=phone_number,
                    message="❌ An error occurred while crawling the website. Please try again later."
                )
            except:
                pass
            
            return {
                "success": False,
                "user_id": user_id,
                "url": url,
                "error": str(e)
            }
    
    async def process_voice_message(
        self,
        user_id: str,
        phone_number: str,
        media_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process voice message with transcription (User Story 4, T080-T081).
        
        Args:
            user_id: User identifier
            phone_number: User's phone number
            media_info: Media information from webhook
            
        Returns:
            Processing result
        """
        logger.info(
            "Processing voice message",
            extra={
                "user_id": user_id,
                "duration": media_info.get("data", {}).get("seconds", 0)
            }
        )
        
        try:
            # Send processing notification
            await self.tool_agent.whatsapp_service.send_text_message(
                phone_number=phone_number,
                message="🎤 Transcribing your voice message..."
            )
            
            # Process voice message (transcription happens in tool agent)
            result = await self.tool_agent.process_voice_message(
                user_id=user_id,
                media_info=media_info
            )
            
            if result.get("success"):
                # Get transcribed text
                transcribed_text = result.get("text", "")
                confidence = result.get("confidence", 0.0)
                
                # Send transcription to user
                transcription_msg = f"📝 Transcription:\n\n{transcribed_text}"
                
                if confidence < 0.85:
                    transcription_msg += f"\n\n⚠️ Low confidence ({confidence:.0%}). The transcription may not be accurate."
                
                await self.tool_agent.whatsapp_service.send_text_message(
                    phone_number=phone_number,
                    message=transcription_msg
                )
                
                # Now process the transcribed text as a regular message (T081)
                # This allows the AI to respond to the voice message content
                await self.process_simple_message(
                    user_id=user_id,
                    phone_number=phone_number,
                    message=transcribed_text
                )
                
                logger.info(
                    "Voice message processed successfully",
                    extra={
                        "user_id": user_id,
                        "text_length": len(transcribed_text),
                        "confidence": confidence
                    }
                )
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "text": transcribed_text,
                    "confidence": confidence
                }
            else:
                # Send error notification
                error_msg = result.get("error", "Unknown error")
                
                user_msg = (
                    f"❌ Failed to transcribe voice message\n\n"
                    f"Error: {error_msg}\n\n"
                    f"Please try recording again or send a text message."
                )
                
                await self.tool_agent.whatsapp_service.send_text_message(
                    phone_number=phone_number,
                    message=user_msg
                )
                
                logger.warning(
                    "Voice message transcription failed",
                    extra={
                        "user_id": user_id,
                        "error": error_msg
                    }
                )
                
                return {
                    "success": False,
                    "user_id": user_id,
                    "error": error_msg
                }
                
        except Exception as e:
            logger.error(
                "Voice message processing exception",
                extra={
                    "error": str(e),
                    "user_id": user_id
                }
            )
            
            # Send error message
            try:
                await self.tool_agent.whatsapp_service.send_text_message(
                    phone_number=phone_number,
                    message="❌ An error occurred while processing your voice message. Please try again."
                )
            except:
                pass
            
            return {
                "success": False,
                "user_id": user_id,
                "error": str(e)
            }
