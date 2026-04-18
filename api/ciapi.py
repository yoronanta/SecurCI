from fastapi import FastAPI
from pydantic import BaseModel
import redis 
import json
from datetime import datetime
import uuid
import os

app = FastAPI(title="SecurCIAPI")

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)

class ScanRequest(BaseModel):
    repo_url: str
    branch: str = "main"

class ScanResponse(BaseModel):
    task_id: str
    status: str
    create_time: str

@app.post("/scan", response_model=ScanResponse)
async def create_scan(request: ScanRequest):
    task_id = str(uuid.uuid4())

    task_data = {
        "task_id": task_id,
        "repo_url": request.repo_url,
        "branch": request.branch,
        "status": "queued",
        "create_time": datetime.now().isoformat()
    }

    redis_client.lpush("scan_queue", json.dumps(task_data))
    redis_client.set(f"task:{task_id}", json.dumps(task_data))

    return ScanResponse(
        task_id=task_id,
        status="queued",
        create_time=task_data["create_time"]
    )

@app.get("/scan/{task_id}")
async def get_scan_status(task_id: str):
    task_data = redis_client.get(f"task:{task_id}")
    if not task_data:
        return {"error": f"Task not found: {task_id}"}
    return json.loads(task_data)

@app.get("/status/{task_id}")  
async def check_status(task_id: str):    
    task_data = redis_client.get(f"task:{task_id}")
    if not task_data:
        return {"error": "Task not found"}
    data = json.loads(task_data)
    return {"status": data.get("status")}