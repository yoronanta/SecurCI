import redis
import json
import subprocess
import tempfile
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_client = redis.Redis(
    host='redis',
    port=6379,
    db=0,
    decode_responses=True
)

def update_task(task_id: str, data):
    redis_client.set(f"task:{task_id}", json.dumps(data))  

def run_bandit(repo_path: str):
    try:
        result = subprocess.run(
            ["bandit", "-r", repo_path, "-f", "json"],
            capture_output=True,
            text=True,
            timeout=300
        )
        return json.loads(result.stdout) if result.stdout else {"results": []}
    except Exception as e:
        return {"error": str(e)}
    
def run_safety(repo_path: str):
    try:
        req_file = Path(repo_path) / "requirements.txt"
        if req_file.exists():  
            result = subprocess.run(
                ["safety", "check", "-r", str(req_file), "--json"],
                capture_output=True,
                text=True,
                timeout=120 
            )
            return json.loads(result.stdout) if result.stdout else {"vulnerabilities": []}
        else:
            return {"message": "No requirements.txt found"}
    except Exception as e:
        return {"error": str(e)}
    
def process_task(task_data):
    task_id = task_data["task_id"]  
    repo_url = task_data["repo_url"]
    
    task_data["status"] = "in_progress"
    update_task(task_id, task_data)
    logger.info(f"Processing task {task_id}: {repo_url}")

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            logger.info("Cloning repository")
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, tmpdir],  
                check=True,
                capture_output=True,
                timeout=60
            )

            logger.info("Running bandit")
            bandit_results = run_bandit(tmpdir)

            logger.info("Running safety")
            safety_results = run_safety(tmpdir)

            report = {
                "task_id": task_id,
                "status": "completed",
                "repo_url": repo_url,
                "sast": {
                    "tool": "bandit",
                    "issues": len(bandit_results.get("results", [])),
                    "details": bandit_results
                },
                "dependencies": {
                    "tool": "safety",
                    "vulnerabilities": len(safety_results.get("vulnerabilities", [])),  
                    "details": safety_results
                },     
                "summary": {
                    "total_issues": (
                        len(bandit_results.get("results", [])) +
                        len(safety_results.get("vulnerabilities", []))  
                    )
                }
            }
            update_task(task_id, report)
            logger.info(f"Task {task_id} completed")
            
        except Exception as e:
            task_data["status"] = "failed"
            task_data["error"] = str(e)
            update_task(task_id, task_data)
            logger.error(f"Task {task_id} failed: {e}")

def main():
    logger.info("Worker started, waiting for tasks")
    while True:
        _, task_json = redis_client.brpop("scan_queue")
        task_data = json.loads(task_json)
        process_task(task_data)

if __name__ == "__main__":
    main()