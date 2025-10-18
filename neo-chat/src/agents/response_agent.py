"""Response agent for LLM response generation (T037)."""

from crewai import Agent
from typing import Optional
from src.services.gemini_service import GeminiService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ResponseAgent:
    """Agent responsible for generating AI responses using Gemini."""

    def __init__(self, gemini_service: GeminiService):
        """Initialize response agent with Gemini service.
        
        Args:
            gemini_service: Service for Gemini LLM operations
        """
        self.gemini_service = gemini_service
        self.agent = self._create_agent()

    def _create_agent(self) -> Agent:
        """Create CrewAI agent for response generation.
        
        Returns:
            Configured CrewAI Agent
        """
        agent = Agent(
            role="AI Response Generator",
            goal="Generate helpful, accurate, and contextual responses to user queries using retrieved knowledge",
            backstory="""You are an expert AI assistant powered by Gemini Flash 2.5.
            You excel at understanding user queries and generating helpful responses based on
            the context provided from their knowledge base. You always cite your sources when
            using information from the knowledge base, and you're honest when you don't have
            enough information to answer a question. You communicate clearly and concisely,
            adapting your tone to match the user's needs.""",
            verbose=True,
            allow_delegation=False,
            llm="gemini/gemini-2.0-flash-exp"  # CrewAI Gemini integration
        )
        
        return agent

    async def generate_response(
        self,
        query: str,
        context: Optional[str] = None
    ) -> str:
        """Generate AI response for user query.
        
        Args:
            query: User's query text
            context: Optional context from knowledge base
            
        Returns:
            Generated AI response
        """
        logger.info(
            "Response agent generating response",
            extra={
                "query_length": len(query),
                "has_context": bool(context)
            }
        )
        
        try:
            response = await self.gemini_service.generate_response(
                prompt=query,
                context=context,
                temperature=0.7
            )
            
            logger.info(
                "Response generated successfully",
                extra={
                    "response_length": len(response)
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "Response generation failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise

    def get_agent(self) -> Agent:
        """Get the configured CrewAI agent.
        
        Returns:
            CrewAI Agent instance
        """
        return self.agent
