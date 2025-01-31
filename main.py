import asyncio
import logging
from typing import List, Optional
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import GPT_MODEL, MAX_CONCURRENT_REQUESTS, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW
from services.cache import get_cached_response, cache_response
from services.gpt import process_with_gpt
from services.news import get_itmo_news
from services.search import search_google

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI()

request_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
request_counts: dict[str, dict[str, any]] = {}

class Request(BaseModel):
    id: int
    query: str

class Response(BaseModel):
    id: int
    answer: Optional[int]
    reasoning: str
    sources: List[str]
    model: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    current_time = int(time.time())
    
    if client_ip in request_counts:
        if current_time - request_counts[client_ip]["timestamp"] >= RATE_LIMIT_WINDOW:
            request_counts[client_ip] = {"count": 0, "timestamp": current_time}
    else:
        request_counts[client_ip] = {"count": 0, "timestamp": current_time}
    
    if request_counts[client_ip]["count"] >= RATE_LIMIT_REQUESTS:
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    
    request_counts[client_ip]["count"] += 1
    
    async with request_semaphore:
        response = await call_next(request)
        return response

@app.post("/api/request")
async def process_request(request: Request) -> Response:
    try:
        logger.info(f"Processing request {request.id}: {request.query}")
        
        cached = await get_cached_response(request.id)
        if cached:
            logger.info(f"Found cached response for request {request.id}")
            return Response(
                id=request.id,
                answer=cached["answer"],
                reasoning=cached["reasoning"],
                sources=cached["sources"],
                model=cached.get("model", GPT_MODEL)
            )
        
        news = await get_itmo_news()
        search_results = await search_google(request.query)
        
        context = ""
        if news:
            context += "\n\nITMO News:\n" + "\n".join(news)
        if search_results:
            context += "\n\nSearch Results:\n" + "\n".join(search_results)
        
        response = await process_with_gpt(request.query, context)
        await cache_response(request.id, response)
        
        return Response(
            id=request.id,
            answer=response["answer"],
            reasoning=response["reasoning"],
            sources=response["sources"],
            model=response["model"]
        )
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
