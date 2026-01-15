"""
FastAPI application for GenAI Python Service.
Spring PetClinic GenAI Service - Python Implementation
"""

import logging
import os
# #region agent log
import json
def _debug_log(location, message, data, hypothesis_id):
    import time
    log_entry = json.dumps({"location": location, "message": message, "data": data, "hypothesisId": hypothesis_id, "timestamp": int(time.time()*1000)})
    print(f"[DEBUG] {log_entry}", flush=True)
# #endregion
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from app.data_provider import DataProvider
from app.vector_store import VectorStoreController
from app.chat_client import PetclinicChatClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
data_provider = DataProvider()
vector_store_controller = VectorStoreController(data_provider)
chat_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown.
    Initializes vector store on startup.
    """
    # Startup
    logger.info("Starting GenAI Python Service...")
    
    # Load vector store
    try:
        await vector_store_controller.load_vector_store_on_startup()
        logger.info("Vector store loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load vector store: {e}")
    
    # Initialize chat client
    global chat_client
    chat_client = PetclinicChatClient(data_provider, vector_store_controller)
    logger.info("Chat client initialized")
    
    logger.info("GenAI Python Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down GenAI Python Service...")


# Create FastAPI application
app = FastAPI(
    title="GenAI Python Service",
    description="Spring PetClinic GenAI Service - Python Implementation using FastAPI and LangChain",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "GenAI Python Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "UP",
        "service": "genai-python"
    }


@app.get("/actuator/health")
async def actuator_health():
    """Spring Boot Actuator compatible health check"""
    return {
        "status": "UP",
        "components": {
            "vectorStore": {
                "status": "UP" if vector_store_controller.get_vector_store() else "DOWN"
            },
            "chatClient": {
                "status": "UP" if chat_client else "DOWN"
            }
        }
    }


@app.post("/chatclient")
async def chat_endpoint(request: Request):
    """
    Chat endpoint compatible with Spring version.
    Accepts plain text query and returns plain text response.
    
    Request body: plain text query
    Response: plain text response
    """
    try:
        # Read request body as text
        query = await request.body()
        query_text = query.decode('utf-8')
        
        if not query_text or not query_text.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        logger.info(f"Received chat request: {query_text[:100]}...")
        
        # #region agent log
        _debug_log("main.py:chat_endpoint", "Chat request received", {"query": query_text[:50], "msg_count_before": len(chat_client.messages) if chat_client else 0, "client_id": id(chat_client)}, "A")
        # #endregion
        
        # Get response from chat client
        if not chat_client:
            raise HTTPException(status_code=503, detail="Chat client not initialized")
        
        response = await chat_client.chat(query_text)
        
        # #region agent log
        _debug_log("main.py:chat_endpoint", "Chat response generated", {"response_len": len(response), "msg_count_after": len(chat_client.messages) if chat_client else 0}, "A")
        # #endregion
        
        # Return plain text response
        return PlainTextResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        return PlainTextResponse(
            content="Chat is currently unavailable. Please try again later.",
            status_code=500
        )


@app.post("/chat/reset")
async def reset_chat_memory():
    """Reset the conversation memory"""
    # #region agent log
    _debug_log("main.py:reset_chat_memory", "Reset endpoint called", {"msg_count_before": len(chat_client.messages) if chat_client else 0}, "C")
    # #endregion
    try:
        if chat_client:
            chat_client.reset_memory()
            # #region agent log
            _debug_log("main.py:reset_chat_memory", "Memory reset complete", {"msg_count_after": len(chat_client.messages)}, "C")
            # #endregion
            return {"status": "success", "message": "Conversation memory reset"}
        else:
            raise HTTPException(status_code=503, detail="Chat client not initialized")
    except Exception as e:
        logger.error(f"Error resetting memory: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset memory")


@app.get("/info")
async def service_info():
    """Service information endpoint"""
    return {
        "service": "genai-python",
        "description": "Python implementation of Spring PetClinic GenAI Service",
        "framework": "FastAPI",
        "llm": "OpenAI / Azure OpenAI",
        "features": [
            "Conversational AI chatbot",
            "Function calling (list owners, add owner, list vets, add pet)",
            "RAG with vector store for vet data",
            "Conversation memory (10 messages)"
        ],
        "environment": {
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "azure_openai_configured": bool(os.getenv("AZURE_OPENAI_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT")),
            "customers_service_url": os.getenv("CUSTOMERS_SERVICE_URL", "http://customers-service"),
            "vets_service_url": os.getenv("VETS_SERVICE_URL", "http://vets-service")
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8084"))
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )

