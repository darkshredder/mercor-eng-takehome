from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import asyncio
from typing import List, Deque, Tuple
from collections import deque

CLASSIFICATION_SERVER_URL = "http://localhost:8001/classify"

app = FastAPI(
    title="Ultra-Optimized Classification Proxy",
    description="Handles dynamic batching, retries, and adaptive traffic patterns efficiently.",
)


class ProxyRequest(BaseModel):
    sequence: str


class ProxyResponse(BaseModel):
    result: str


# Shared resources
high_priority_queue: Deque[Tuple[int, str]] = deque()  # For bursty traffic (Client A)
low_priority_queue: Deque[Tuple[int, str]] = deque()  # For steady traffic (Client B)
response_dict = {}  # Maps request IDs to results
queue_lock = asyncio.Lock()  # Lock for thread-safe queue access
CONCURRENT_WORKERS = 3  # Number of parallel batch processors
BATCH_SIZE_BASE = 5  # Base batch size
MAX_BATCH_SIZE = 20  # Maximum batch size
BASE_INTERVAL = 0.05  # Base wait interval (seconds)
MAX_INTERVAL = 0.2  # Maximum interval between batch processing
RETRY_BACKOFF = 0.1  # Base retry backoff time
MAX_RETRIES = 3  # Maximum number of retries


@app.post("/proxy_classify")
async def proxy_classify(req: ProxyRequest):
    """
    Handles a single classification request by queuing it and waiting for a response.
    """
    request_id = id(req)

    # Enqueue the request based on priority
    async with queue_lock:
        if (
            len(req.sequence) > 50
        ):  # Example heuristic: classify larger requests as high priority
            high_priority_queue.append((request_id, req.sequence))
        else:
            low_priority_queue.append((request_id, req.sequence))

    # Wait for the response
    while request_id not in response_dict:
        await asyncio.sleep(0.01)

    # Return the response
    result = response_dict.pop(request_id)
    return ProxyResponse(result=result)


async def process_batch(worker_id: int, batch: List[Tuple[int, str]]):
    """
    Processes a single batch of requests.
    """
    request_ids, sequences = zip(*batch)
    retries = 0
    while retries < MAX_RETRIES:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    CLASSIFICATION_SERVER_URL,
                    json={"sequences": list(sequences)},
                )
                if response.status_code == 200:
                    results = response.json()["results"]

                    # Map results to request IDs
                    for request_id, result in zip(request_ids, results):
                        response_dict[request_id] = result
                    return  # Success
                else:
                    raise Exception(f"Server error: {response.status_code}")
        except Exception as e:
            print(f"[Worker {worker_id}] Error: {e}. Retrying...")
            retries += 1
            await asyncio.sleep(RETRY_BACKOFF * (2**retries))  # Exponential backoff

    # Handle failed requests after retries
    for request_id in request_ids:
        response_dict[request_id] = "error: classification failed"


async def batch_processor(worker_id: int):
    """
    Processes batches of requests from the high- and low-priority queues.
    """
    while True:
        batch = []

        async with queue_lock:
            # Prioritize high-priority requests
            while len(batch) < BATCH_SIZE_BASE and high_priority_queue:
                batch.append(high_priority_queue.popleft())

            # Fill remaining slots with low-priority requests
            while len(batch) < BATCH_SIZE_BASE and low_priority_queue:
                batch.append(low_priority_queue.popleft())

        if batch:
            await process_batch(worker_id, batch)

        # Dynamic sleep interval based on queue sizes
        async with queue_lock:
            total_queue_length = len(high_priority_queue) + len(low_priority_queue)
        sleep_interval = min(MAX_INTERVAL, BASE_INTERVAL + 0.01 * total_queue_length)
        await asyncio.sleep(sleep_interval)


@app.on_event("startup")
async def start_batch_processors():
    """
    Starts multiple batch processors on server startup for concurrent processing.
    """
    for i in range(CONCURRENT_WORKERS):
        asyncio.create_task(batch_processor(i))


@app.on_event("shutdown")
async def shutdown():
    """
    Gracefully shuts down the server, ensuring all requests are processed.
    """
    print("Shutting down...")
    while high_priority_queue or low_priority_queue:
        await asyncio.sleep(0.1)
    print("All requests processed. Shutdown complete.")
