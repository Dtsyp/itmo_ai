import asyncio
import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from config.settings import GPT_MODEL
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

class Request(BaseModel):
    id: int
    query: str

class Response(BaseModel):
    id: int
    answer: Optional[int]
    reasoning: str
    sources: List[str]
    model: str

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
        context = "\n\n".join(news + search_results)
        
        gpt_response = await process_with_gpt(request.query, context)
        
        response = Response(
            id=request.id,
            answer=gpt_response["answer"],
            reasoning=gpt_response["reasoning"],
            sources=gpt_response.get("sources", [])[:3],
            model=GPT_MODEL
        )
        
        await cache_response(request.id, response.dict())
        
        logger.info(f"Successfully processed request {request.id}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing request {request.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
