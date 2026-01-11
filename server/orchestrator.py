import hashlib
import time
import asyncio
from typing import List, Dict
import aiohttp
import os
import json

HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HF_BASE_URL = "https://api-inference.huggingface.co/models"

MODELS = {
    "hf-gptj": {
        "name": "GPT-J (6B)",
        "model_id": "EleutherAI/gpt-j-6B",
        "type": "Text Generation",
        "params": "6B",
    },
    "hf-falcon": {
        "name": "Falcon 7B",
        "model_id": "tiiuae/falcon-7b",
        "type": "Text Generation",
        "params": "7B",
    },
    "hf-llama": {
        "name": "LLaMA 2 (7B)",
        "model_id": "meta-llama/Llama-2-7b-hf",
        "type": "Text Generation",
        "params": "7B",
    },
}

def generate_query_hash(query_text: str, agent_ids: List[str]) -> str:
    """Generate SHA-256 hash of query + agents"""
    content = f"{query_text}:{'|'.join(sorted(agent_ids))}"
    return hashlib.sha256(content.encode()).hexdigest()

async def query_huggingface(model_id: str, query_text: str, timeout: int = 30) -> Dict:
    """Query HuggingFace Inference API with error handling"""
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    url = f"{HF_BASE_URL}/{model_id}"
    
    payload = {
        "inputs": query_text,
        "parameters": {
            "max_length": 200,
            "temperature": 0.7,
        }
    }
    
    start_time = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                response_time_ms = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Parse response
                    if isinstance(result, list) and len(result) > 0:
                        response_text = result.get("generated_text", "")
                    else:
                        response_text = str(result)
                    
                    return {
                        "status": "success",
                        "response_text": response_text[:1000],  # Truncate for DB
                        "response_time_ms": response_time_ms,
                        "token_count": len(response_text.split()),
                    }
                else:
                    error_msg = await response.text()
                    return {
                        "status": "error",
                        "error_message": f"API error {response.status}",
                        "response_time_ms": response_time_ms,
                    }
    except asyncio.TimeoutError:
        return {
            "status": "error",
            "error_message": "Request timeout (30s)",
            "response_time_ms": (time.time() - start_time) * 1000,
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)[:100],
            "response_time_ms": (time.time() - start_time) * 1000,
        }

async def orchestrate_query(query_text: str, agent_ids: List[str], db) -> Dict:
    """
    Orchestrate parallel queries to multiple AI agents
    Handles caching and error handling per agent
    """
    from sqlalchemy import select
    from db import Cache
    
    query_hash = generate_query_hash(query_text, agent_ids)
    
    # Check cache for each agent
    cached_responses = {}
    uncached_agents = []
    
    for agent_id in agent_ids:
        result = await db.execute(
            select(Cache).where(
                (Cache.query_hash == query_hash) & (Cache.agent_id == agent_id)
            )
        )
        cached = result.scalar_one_or_none()
        
        if cached:
            cached_responses[agent_id] = cached.response_text
        else:
            uncached_agents.append(agent_id)
    
    # Query uncached agents in parallel
    new_responses = {}
    if uncached_agents:
        tasks = [
            query_huggingface(MODELS[agent_id]["model_id"], query_text)
            for agent_id in uncached_agents
        ]
        
        responses = await asyncio.gather(*tasks)
        
        for agent_id, response_data in zip(uncached_agents, responses):
            new_responses[agent_id] = response_data
            
            # Cache successful responses
            if response_data["status"] == "success":
                cache_entry = Cache(
                    query_hash=query_hash,
                    agent_id=agent_id,
                    response_text=response_data["response_text"],
                )
                db.add(cache_entry)
    
    await db.commit()
    
    # Combine all responses
    all_responses = []
    
    # Add cached responses
    for agent_id, response_text in cached_responses.items():
        all_responses.append({
            "agent_id": agent_id,
            "agent_name": MODELS[agent_id]["name"],
            "model_info": {
                "type": MODELS[agent_id]["type"],
                "params": MODELS[agent_id]["params"],
            },
            "response_text": response_text,
            "response_time_ms": 0,
            "token_count": len(response_text.split()),
            "status": "success",
            "cached": True,
        })
    
    # Add new responses
    for agent_id, response_data in new_responses.items():
        all_responses.append({
            "agent_id": agent_id,
            "agent_name": MODELS[agent_id]["name"],
            "model_info": {
                "type": MODELS[agent_id]["type"],
                "params": MODELS[agent_id]["params"],
            },
            "response_text": response_data.get("response_text", ""),
            "response_time_ms": response_data["response_time_ms"],
            "token_count": response_data.get("token_count", 0),
            "status": response_data["status"],
            "error_message": response_data.get("error_message"),
            "cached": False,
        })
    
    # Calculate metadata
    successful_responses = [r for r in all_responses if r["status"] == "success"]
    avg_response_time = (
        sum(r["response_time_ms"] for r in successful_responses) / len(successful_responses)
        if successful_responses else 0
    )
    
    return {
        "responses": all_responses,
        "avg_response_time_ms": avg_response_time,
        "total_agents": len(agent_ids),
        "cached_count": len(cached_responses),
    }
