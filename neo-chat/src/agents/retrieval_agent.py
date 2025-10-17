"""Retrieval agent for vector search and context assembly (T036)."""

from crewai import Agent, Task
from typing import Dict, Any
from src.services.knowledge_base import KnowledgeBaseService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RetrievalAgent:
    """Agent responsible for retrieving relevant context from knowledge base."""

    def __init__(self, knowledge_base_service: KnowledgeBaseService):
        """Initialize retrieval agent with knowledge base service.
        
        Args:
            knowledge_base_service: Service for knowledge base operations
        """
        self.knowledge_base_service = knowledge_base_service
        self.agent = self._create_agent()

    def _create_agent(self) -> Agent:
        """Create CrewAI agent with retrieval tools.
        
        Returns:
            Configured CrewAI Agent
        """
        agent = Agent(
            role="Knowledge Base Retrieval Specialist",
            goal="Retrieve the most relevant information from the user's knowledge base to answer their queries",
            backstory="""You are an expert at finding relevant information in knowledge bases.
            You use vector similarity search to find the top-5 most relevant chunks of information
            with a similarity threshold of 0.7. You excel at understanding user queries and
            retrieving contextual information that helps answer their questions.""",
            verbose=True,
            allow_delegation=False
        )
        
        return agent

    def get_agent(self) -> Agent:
        """Get the configured CrewAI agent.
        
        Returns:
            CrewAI Agent instance
        """
        return self.agent
