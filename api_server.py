from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from agent.base_agent import agent
import uvicorn
import os

# Initialize FastAPI app
app = FastAPI(title="Text-to-SQL Agent API", version="1.0.0")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all origins. In production, be specific.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint to receive user message and return agent response.
    """
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        # Run agent logic
        # Note: agent.run currently is synchronous. 
        # For high concurrency, we might want to make it async or run in a threadpool,
        # but for this demo, direct call is fine.
        response_text = agent.run(request.message)
        return ChatResponse(response=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    # Run server
    uvicorn.run(app, host="0.0.0.0", port=8000)
