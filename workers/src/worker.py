import os
import sys
import json
import time
import redis
import requests
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Add parent directories to path for imports
# Project root (for agent.src.* imports)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
# Workers root (for src.k8s.* and src.storage.* imports)
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.src.config import settings
from agent.src.analyzer.repo_analyzer import RepoAnalyzer
from agent.src.llm.llm_client import LLMClient
from agent.src.generators.dockerfile_generator import DockerfileGenerator
from agent.src.generators.training_generator import TrainingScriptGenerator
from agent.src.generators.fastapi_generator import FastAPIGenerator

# Import managers
from src.k8s import K8sJobManager
from src.k8s.training_manager import TrainingManager
from src.k8s.inference_manager import InferenceManager
from src.storage import S3Manager

# Load environment
load_dotenv()

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")

# Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8080")

# Feature flags
ENABLE_K8S_BUILD = os.getenv("ENABLE_K8S_BUILD", "false").lower() == "true"
ENABLE_TRAINING = os.getenv("ENABLE_TRAINING", "false").lower() == "true"
ENABLE_DEPLOYMENT = os.getenv("ENABLE_DEPLOYMENT", "false").lower() == "true"
ENABLE_S3_UPLOAD = os.getenv("ENABLE_S3_UPLOAD", "false").lower() == "true"

# Configuration
REGISTRY_URL = os.getenv("REGISTRY_URL", "registry.digitalocean.com/automlops")
S3_BUCKET = os.getenv("S3_BUCKET", "automlops-models")
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "nyc3.digitaloceanspaces.com")

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

JOB_QUEUE_KEY = "automlops:jobs"

# Initialize managers
k8s_manager = K8sJobManager() if (ENABLE_K8S_BUILD or ENABLE_TRAINING or ENABLE_DEPLOYMENT) else None
training_manager = TrainingManager(k8s_manager) if ENABLE_TRAINING and k8s_manager else None
inference_manager = InferenceManager(k8s_manager) if ENABLE_DEPLOYMENT and k8s_manager else None
s3_manager = S3Manager() if ENABLE_S3_UPLOAD else None

def update_job_status(job_id: str, status: str, error_message: str = "", 
                     api_endpoint: str = "", model_s3_path: str = "",
                     python_files: int = 0, notebooks: int = 0, frameworks: str = ""):
    """Update job status and metadata via orchestrator API"""
    try:
        url = f"{ORCHESTRATOR_URL}/api/jobs/{job_id}/status"
        payload = {"status": status}
        
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
    """Process a single job through the complete pipeline"""
    logger.info(f"🚀 Processing job {job_id}: {repo_url}")
    
    try:
        # ============================================
        # PHASE 1: ANALYSIS & CODE GENERATION
        # ============================================
        update_job_status(job_id, "analyzing")
        
        llm_client = LLMClient()
        dockerfile_gen = DockerfileGenerator(llm_client)
        training_gen = TrainingScriptGenerator(llm_client)
        fastapi_gen = FastAPIGenerator(llm_client)
        
        logger.info("📊 Phase 1: Analyzing repository...")
        analyzer = RepoAnalyzer(repo_url, settings.TEMP_REPO_DIR)
        
        if not analyzer.clone_repository():
            raise Exception("Failed to clone repository")
        
        analysis = analyzer.analyze_structure()
        
        python_files_count = len(analysis.get("python_files", []))
        notebooks_count = len(analysis.get("notebooks", []))
        frameworks_list = analysis.get("ml_frameworks", [])
        frameworks = ", ".join(frameworks_list) if frameworks_list else "None detected"
        
        logger.info(f"✅ Analysis: {python_files_count} Python files, {notebooks_count} notebooks, Frameworks: {frameworks}")
        
        output_dir = Path(f"/tmp/automlops-output/{job_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "analysis.json", "w") as f:
            json.dump(analysis, f, indent=2)
        
        # Generate artifacts
        logger.info("🐳 Generating Dockerfile...")
        update_job_status(job_id, "building", python_files=python_files_count, 
                         notebooks=notebooks_count, frameworks=frameworks)
        
        dockerfile = dockerfile_gen.generate(analysis)
        with open(output_dir / "Dockerfile", "w") as f:
            f.write(dockerfile)
        
        logger.info("🚂 Generating training script...")
        training_script = training_gen.generate(analysis)
        with open(output_dir / "training_wrapper.py", "w") as f:
            f.write(training_script)
        
        logger.info("⚡ Generating FastAPI service...")
        fastapi_app = fastapi_gen.generate(analysis)
        with open(output_dir / "app.py", "w") as f:
            f.write(fastapi_app)
        
        base_requirements = [
            "fastapi==0.109.0",
            "uvicorn==0.27.0",
            "pydantic==2.5.3",
            "numpy>=1.24.0",
            "joblib>=1.3.0",
            "boto3>=1.34.0"
        ]
        
        if "pytorch" in frameworks_list:
            base_requirements.append("torch>=2.0.0")
        if "tensorflow" in frameworks_list:
            base_requirements.append("tensorflow>=2.13.0")
        if "sklearn" in frameworks_list:
            base_requirements.append("scikit-learn>=1.3.0")
        
        with open(output_dir / "requirements.txt", "w") as f:
            f.write("\n".join(base_requirements))
        
        logger.success(f"✅ All artifacts generated in {output_dir}")
        
        # ============================================
        # PHASE 2: DOCKER BUILD (if enabled)
        # ============================================
        if ENABLE_K8S_BUILD and k8s_manager and k8s_manager.enabled:
            logger.info("🔨 Phase 2: Building Docker image...")
            build_job_name = k8s_manager.create_build_job(job_id, REGISTRY_URL)
            
            if build_job_name:
                logger.success(f"✅ Build job created: {build_job_name}")
                # TODO: Wait for build completion
            else:
                logger.warning("⚠️ Failed to create build job")
        
        # ============================================
        # PHASE 3: MODEL TRAINING (if enabled)
        # ============================================
        if ENABLE_TRAINING and training_manager:
            logger.info("🎓 Phase 3: Training model on GPU...")
            update_job_status(job_id, "training")
            
            training_job_name = training_manager.create_training_job(
                job_id=job_id,
                registry_url=REGISTRY_URL,
                s3_bucket=S3_BUCKET,
                s3_endpoint=S3_ENDPOINT
            )
            
            if training_job_name:
                logger.success(f"✅ Training job created: {training_job_name}")
            else:
                logger.warning("⚠️ Failed to create training job")
        
        # ============================================
        # PHASE 4: S3 UPLOAD (if enabled)
        # ============================================
        model_s3_path = ""
        if ENABLE_S3_UPLOAD and s3_manager and s3_manager.enabled:
            logger.info("☁️ Phase 4: Uploading artifacts to S3...")
            s3_prefix = f"jobs/{job_id}"
            
            if s3_manager.upload_directory(str(output_dir), s3_prefix):
                logger.success(f"✅ Artifacts uploaded to s3://{S3_BUCKET}/{s3_prefix}")
                model_s3_path = f"s3://{S3_BUCKET}/{s3_prefix}/"
            else:
                logger.warning("⚠️ S3 upload failed")
        else:
            model_s3_path = f"s3://{S3_BUCKET}/jobs/{job_id}/"
        
        # ============================================
        # PHASE 5: DEPLOY INFERENCE API (if enabled)
        # ============================================
        api_endpoint = f"http://pending-deployment/{job_id}"
        
        if ENABLE_DEPLOYMENT and inference_manager:
            logger.info("🚀 Phase 5: Deploying inference API...")
            update_job_status(job_id, "deploying")
            
            deployment_result = inference_manager.deploy_inference_api(
                job_id=job_id,
                registry_url=REGISTRY_URL,
                s3_bucket=S3_BUCKET,
                s3_endpoint=S3_ENDPOINT,
                replicas=2,
                min_replicas=1,
                max_replicas=10
            )
            
            if deployment_result:
                api_endpoint = deployment_result.get("endpoint", api_endpoint)
                logger.success(f"✅ Inference API deployed: {api_endpoint}")
            else:
                logger.warning("⚠️ Failed to deploy inference API")
        
        # ============================================
        # COMPLETION
        # ============================================
        update_job_status(
            job_id, 
            "completed",
            api_endpoint=api_endpoint,
            model_s3_path=model_s3_path,
            python_files=python_files_count,
            notebooks=notebooks_count,
            frameworks=frameworks
        )
        
        logger.success(f"🎉 Job {job_id} completed successfully!")
        logger.info(f"📍 API Endpoint: {api_endpoint}")
        logger.info(f"📦 Model Storage: {model_s3_path}")
        
    except Exception as e:
        logger.error(f"❌ Job {job_id} failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        update_job_status(job_id, "failed", error_message=str(e))

def main():
    """Main worker loop"""
    logger.info("=" * 60)
    logger.info("🤖 AutoMLOps Worker Starting...")
    logger.info("=" * 60)
    logger.info(f"📡 Redis: {REDIS_HOST}:{REDIS_PORT}")
    logger.info(f"🎯 Orchestrator: {ORCHESTRATOR_URL}")
    logger.info(f"🐳 K8s Build: {'✅ Enabled' if ENABLE_K8S_BUILD else '❌ Disabled'}")
    logger.info(f"🎓 Training: {'✅ Enabled' if ENABLE_TRAINING else '❌ Disabled'}")
    logger.info(f"🚀 Deployment: {'✅ Enabled' if ENABLE_DEPLOYMENT else '❌ Disabled'}")
    logger.info(f"☁️ S3 Upload: {'✅ Enabled' if ENABLE_S3_UPLOAD else '❌ Disabled'}")
    logger.info("=" * 60)
    
    while True:
        try:
            logger.info("⏳ Waiting for jobs...")
            result = redis_client.blpop(JOB_QUEUE_KEY, timeout=5)
            
            if result:
                _, job_data = result
                job_msg = json.loads(job_data)
                
                job_id = job_msg.get("job_id")
                repo_url = job_msg.get("repo_url")
                
                logger.info(f"📥 Received job: {job_id}")
                process_job(job_id, repo_url)
            
        except KeyboardInterrupt:
            logger.info("👋 Worker shutting down...")
            break
        except Exception as e:
            logger.error(f"⚠️ Worker error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()