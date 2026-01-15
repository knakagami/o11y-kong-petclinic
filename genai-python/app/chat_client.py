"""
Chat client using LangChain Agent for conversational AI.
This module handles chat interactions with the LLM and function calling.
"""

import os
import logging
from typing import Optional
# #region agent log
import json
def _debug_log(location, message, data, hypothesis_id):
    import time
    log_entry = json.dumps({"location": location, "message": message, "data": data, "hypothesisId": hypothesis_id, "timestamp": int(time.time()*1000)})
    print(f"[DEBUG] {log_entry}", flush=True)
# #endregion
# LangChain 1.x imports - using new create_agent API
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

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
        
        # Conversation history (stored in memory)
        self.messages = []
        
        # Create agent graph
        self.agent_graph = self._create_agent()
    
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
    
    def _create_agent(self):
        """Create the LangChain agent graph with tools"""
        
        # System prompt matching the Spring version
        system_message = """You are a friendly AI assistant designed to help with the management of a veterinarian pet clinic called Spring Petclinic.

Your job is to answer questions about and to perform actions on the user's behalf, mainly around veterinarians, owners, owners' pets and owners' visits.

You are required to answer in a professional manner. If you don't know the answer, politely tell the user you don't know the answer, then ask the user a followup question to try and clarify the question they are asking.

If you do know the answer, provide the answer but do not provide any additional followup questions.

When dealing with vets, if the user is unsure about the returned results, explain that there may be additional data that was not returned. Only if the user is asking about the total number of all vets, answer that there are a lot and ask for some additional criteria.

For owners, pets or visits - provide the correct data."""
        
        # Get tools
        tools = self.ai_functions.get_tools()
        
        # Create agent using LangChain 1.x API with Splunk AI Agent Monitoring metadata
        # Per Splunk documentation: agent_name and workflow_name should be set via metadata
        # Reference: https://docs.splunk.com/observability/en/apm/apm-spans-traces/ai-agent-monitoring.html
        agent_graph = create_agent(
            model=self.llm,
            tools=tools,
            system_prompt=system_message,
            debug=True
        ).with_config({
            "metadata": {
                "agent_name": "petclinic_assistant",
                "workflow_name": "petclinic_ai_workflow"
            }
        })
        
        return agent_graph
    
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
            
            # #region agent log
            _debug_log("chat_client.py:chat", "Chat method entry", {"query": query[:30], "history_len": len(self.messages), "instance_id": id(self)}, "A")
            # #endregion
            
            # Add user message to conversation history
            self.messages.append(HumanMessage(content=query))
            
            # Invoke the agent graph with messages
            response = await self.agent_graph.ainvoke({"messages": self.messages})
            
            # Extract the AI messages from response
            ai_messages = [msg for msg in response.get("messages", []) if isinstance(msg, AIMessage)]
            
            if ai_messages:
                # Get the last AI message
                last_ai_message = ai_messages[-1]
                output = last_ai_message.content
                
                # Update conversation history with the response
                self.messages = response.get("messages", self.messages)
                
                logger.info(f"Chat response generated successfully")
                return output
            else:
                return "I'm sorry, I couldn't process that request."
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}", exc_info=True)
            return "Chat is currently unavailable. Please try again later."
    
    def reset_memory(self):
        """Reset the conversation memory"""
        # #region agent log
        _debug_log("chat_client.py:reset_memory", "Reset called", {"history_len_before": len(self.messages)}, "C")
        # #endregion
        self.messages = []
        logger.info("Conversation memory reset")

