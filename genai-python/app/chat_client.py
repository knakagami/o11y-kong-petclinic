"""
Chat client using LangChain Agent for conversational AI.
This module handles chat interactions with the LLM and function calling.
"""

import os
import logging
from typing import Optional
# LangChain 1.x imports - updated paths for compatibility
# AgentExecutor moved to langchain package in v1.x
try:
    from langchain.agents import AgentExecutor, create_openai_functions_agent
except ImportError:
    # Fallback for different module structure
    from langchain.agents.agent import AgentExecutor
    from langchain.agents.openai_functions_agent.base import create_openai_functions_agent

from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage

from app.ai_functions import AIFunctions
from app.data_provider import DataProvider
from app.vector_store import VectorStoreController

logger = logging.getLogger(__name__)


class PetclinicChatClient:
    """Chat client for the Pet Clinic AI assistant"""
    
    def __init__(self, data_provider: DataProvider, vector_store_controller: VectorStoreController):
        self.data_provider = data_provider
        self.vector_store_controller = vector_store_controller
        
        # Initialize AI functions
        self.ai_functions = AIFunctions(data_provider, vector_store_controller)
        
        # Initialize LLM
        self.llm = self._init_llm()
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            max_token_limit=2000  # Approximately 10 messages
        )
        
        # Create agent
        self.agent_executor = self._create_agent()
    
    def _init_llm(self):
        """Initialize the appropriate LLM based on environment variables"""
        azure_key = os.getenv("AZURE_OPENAI_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        if azure_key and azure_endpoint:
            logger.info("Using Azure OpenAI")
            return AzureChatOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=azure_key,
                azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
                temperature=0.7,
                api_version="2024-02-15-preview"
            )
        else:
            logger.info("Using OpenAI")
            openai_key = os.getenv("OPENAI_API_KEY", "demo")
            return ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=0.7,
                openai_api_key=openai_key
            )
    
    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain agent with tools and memory"""
        
        # System prompt matching the Spring version
        system_message = """You are a friendly AI assistant designed to help with the management of a veterinarian pet clinic called Spring Petclinic.

Your job is to answer questions about and to perform actions on the user's behalf, mainly around veterinarians, owners, owners' pets and owners' visits.

You are required to answer in a professional manner. If you don't know the answer, politely tell the user you don't know the answer, then ask the user a followup question to try and clarify the question they are asking.

If you do know the answer, provide the answer but do not provide any additional followup questions.

When dealing with vets, if the user is unsure about the returned results, explain that there may be additional data that was not returned. Only if the user is asking about the total number of all vets, answer that there are a lot and ask for some additional criteria.

For owners, pets or visits - provide the correct data."""
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Get tools
        tools = self.ai_functions.get_tools()
        
        # Create agent with agent_name metadata for Splunk AI Agent Monitoring
        # Per Splunk documentation: agent_name must be set at the Chain level using .with_config()
        # This ensures the instrumentation promotes the Chain to AgentInvocation
        # and enables LLM-as-a-Judge evaluation
        # Reference: https://docs.splunk.com/observability/en/apm/apm-spans-traces/ai-agent-monitoring.html
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        ).with_config({
            "metadata": {
                "agent_name": "petclinic_assistant"
            }
        })
        
        # Create agent executor with workflow_name metadata
        # Per Splunk documentation: workflow_name promotes the Chain/Graph to a workflow
        # This enables end-to-end workflow tracking in Splunk Observability Cloud
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        ).with_config({
            "metadata": {
                "workflow_name": "petclinic_ai_workflow"
            }
        })
        
        return agent_executor
    
    async def chat(self, query: str) -> str:
        """
        Process a chat message and return the response.
        
        Args:
            query: User's message
            
        Returns:
            AI assistant's response
        """
        try:
            logger.info(f"Processing chat query: {query}")
            
            # Invoke the agent
            response = await self.agent_executor.ainvoke({"input": query})
            
            # Extract the output
            output = response.get("output", "I'm sorry, I couldn't process that request.")
            
            logger.info(f"Chat response generated successfully")
            return output
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            return "Chat is currently unavailable. Please try again later."
    
    def reset_memory(self):
        """Reset the conversation memory"""
        self.memory.clear()
        logger.info("Conversation memory reset")

