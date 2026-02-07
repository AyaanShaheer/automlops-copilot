import os
import sys
import json
import time
import redis
import requests
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Add parent directory to path to enable agent imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.src.config import settings
from agent.src.analyzer.repo_analyzer import RepoAnalyzer
from agent.src.llm.llm_client import LLMClient
from agent.src.generators.dockerfile_generator import DockerfileGenerator
from agent.src.generators.training_generator import TrainingScriptGenerator
from agent.src.generators.fastapi_generator import FastAPIGenerator

# Load environment
load_dotenv()

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")

# Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8080")

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

JOB_QUEUE_KEY = "automlops:jobs"

def update_job_status(job_id: str, status: str, error_message: str = "", 
                     api_endpoint: str = "", model_s3_path: str = "",
                     python_files: int = 0, notebooks: int = 0, frameworks: str = ""):
    """Update job status and metadata via orchestrator API"""
    try:
        url = f"{ORCHESTRATOR_URL}/api/jobs/{job_id}/status"
        payload = {
            "status": status,
        }
        
        if error_message:
            payload["error_message"] = error_message
        if api_endpoint:
            payload["api_endpoint"] = api_endpoint
        if model_s3_path:
            payload["model_s3_path"] = model_s3_path
        if python_files > 0:
            payload["python_files"] = python_files
        if notebooks > 0:
            payload["notebooks"] = notebooks
        if frameworks:
            payload["frameworks"] = frameworks
            
        response = requests.patch(url, json=payload)
        if response.status_code == 200:
            logger.info(f"Job {job_id} updated: status={status}")
        else:
            logger.error(f"Failed to update job status: {response.text}")
    except Exception as e:
        logger.error(f"Error updating job status: {e}")

def process_job(job_id: str, repo_url: str):
    """Process a single job"""
    logger.info(f"Processing job {job_id}: {repo_url}")
    
    try:
        # Update status to analyzing
        update_job_status(job_id, "analyzing")
        
        # Initialize LLM and generators
        llm_client = LLMClient()
        dockerfile_gen = DockerfileGenerator(llm_client)
        training_gen = TrainingScriptGenerator(llm_client)
        fastapi_gen = FastAPIGenerator(llm_client)
        
        # Step 1: Clone and analyze repository
        logger.info("Step 1: Analyzing repository...")
        analyzer = RepoAnalyzer(repo_url, settings.TEMP_REPO_DIR)
        
        if not analyzer.clone_repository():
            raise Exception("Failed to clone repository")
        
        analysis = analyzer.analyze_structure()
        
        # Extract analysis metadata
        python_files_count = len(analysis.get("python_files", []))
        notebooks_count = len(analysis.get("notebooks", []))
        frameworks_list = analysis.get("ml_frameworks", [])
        frameworks = ", ".join(frameworks_list) if frameworks_list else "None detected"
        
        logger.info(f"Analysis: {python_files_count} Python files, {notebooks_count} notebooks, Frameworks: {frameworks}")
        
        # Create output directory for this job
        output_dir = Path(f"/tmp/automlops-output/{job_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save analysis
        with open(output_dir / "analysis.json", "w") as f:
            json.dump(analysis, f, indent=2)
        
        # Step 2: Generate artifacts
        logger.info("Step 2: Generating Dockerfile...")
        update_job_status(
            job_id, 
            "building", 
            python_files=python_files_count,
            notebooks=notebooks_count, 
            frameworks=frameworks
        )
        
        dockerfile = dockerfile_gen.generate(analysis)
        with open(output_dir / "Dockerfile", "w") as f:
            f.write(dockerfile)
        
        logger.info("Step 3: Generating training script...")
        training_script = training_gen.generate(analysis)
        with open(output_dir / "training_wrapper.py", "w") as f:
            f.write(training_script)
        
        logger.info("Step 4: Generating FastAPI service...")
        fastapi_app = fastapi_gen.generate(analysis)
        with open(output_dir / "app.py", "w") as f:
            f.write(fastapi_app)
        
        # Generate requirements for inference
        base_requirements = [
            "fastapi==0.109.0",
            "uvicorn==0.27.0",
            "pydantic==2.5.3",
            "numpy>=1.24.0",
            "joblib>=1.3.0"
        ]
        
        if "pytorch" in frameworks_list:
            base_requirements.append("torch>=2.0.0")
        if "tensorflow" in frameworks_list:
            base_requirements.append("tensorflow>=2.13.0")
        if "sklearn" in frameworks_list:
            base_requirements.append("scikit-learn>=1.3.0")
        
        with open(output_dir / "requirements.txt", "w") as f:
            f.write("\n".join(base_requirements))
        
        logger.success(f"All artifacts generated in {output_dir}")
        
        # Update to completed with all metadata
        update_job_status(
            job_id, 
            "completed",
            api_endpoint=f"http://pending-deployment/{job_id}",
            model_s3_path=f"s3://automlops-models/{job_id}/",
            python_files=python_files_count,
            notebooks=notebooks_count,
            frameworks=frameworks
        )
        
        logger.success(f"Job {job_id} completed successfully!")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        update_job_status(job_id, "failed", error_message=str(e))

def main():
    """Main worker loop"""
    logger.info("Starting AutoMLOps Worker...")
    logger.info(f"Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}")
    logger.info(f"Orchestrator URL: {ORCHESTRATOR_URL}")
    
    while True:
        try:
            # Block and wait for a job (BLPOP)
            logger.info("Waiting for jobs...")
            result = redis_client.blpop(JOB_QUEUE_KEY, timeout=5)
            
            if result:
                _, job_data = result
                job_msg = json.loads(job_data)
                
                job_id = job_msg.get("job_id")
                repo_url = job_msg.get("repo_url")
                
                logger.info(f"Received job: {job_id}")
                process_job(job_id, repo_url)
            
        except KeyboardInterrupt:
            logger.info("Worker shutting down...")
            break
        except Exception as e:
            logger.error(f"Worker error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()