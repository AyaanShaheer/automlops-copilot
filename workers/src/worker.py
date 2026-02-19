import os
import sys
import json
import time
import redis
import requests
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# ============================================================
# PATH SETUP
# ============================================================

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================
# IMPORTS
# ============================================================

from agent.src.config import settings
from agent.src.analyzer.repo_analyzer import RepoAnalyzer
from agent.src.llm.llm_client import LLMClient

# Core Generators
from agent.src.generators.dockerfile_generator import DockerfileGenerator
from agent.src.generators.training_generator import TrainingScriptGenerator
from agent.src.generators.fastapi_generator import FastAPIGenerator

# Phase 2 generators (from agent)
from agent.src.generators.github_actions_generator import GitHubActionsGenerator as AgentGitHubActionsGenerator
from agent.src.generators.k8s_generator import KubernetesGenerator

# CI/CD Generators (from workers - NEW!)
from workers.src.generators import (
    GitHubActionsGenerator,
    GitLabCIGenerator,
    JenkinsGenerator
)

# Managers
from src.k8s import K8sJobManager
from src.k8s.training_manager import TrainingManager
from src.k8s.inference_manager import InferenceManager
from src.storage import S3Manager

# Phase 2 GitHub
from src.github import GitHubClient

# ============================================================
# INIT
# ============================================================

load_dotenv()

logger.remove()
logger.add(sys.stdout, level="INFO")

# ============================================================
# CONFIG
# ============================================================

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8080")

REGISTRY_URL = os.getenv("REGISTRY_URL", "registry.digitalocean.com/automlops")

S3_BUCKET = os.getenv("S3_BUCKET", "automlops-models")
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "nyc3.digitaloceanspaces.com")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# ============================================================
# FEATURE FLAGS
# ============================================================

ENABLE_K8S_BUILD = os.getenv("ENABLE_K8S_BUILD", "false") == "true"
ENABLE_TRAINING = os.getenv("ENABLE_TRAINING", "false") == "true"
ENABLE_DEPLOYMENT = os.getenv("ENABLE_DEPLOYMENT", "false") == "true"
ENABLE_S3_UPLOAD = os.getenv("ENABLE_S3_UPLOAD", "true") == "true"  # Changed to true

# Phase 2
ENABLE_GITHUB_PUSH = os.getenv("ENABLE_GITHUB_PUSH", "false") == "true"
ENABLE_CICD_GENERATION = os.getenv("ENABLE_CICD_GENERATION", "true") == "true"

# ============================================================
# REDIS
# ============================================================

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

JOB_QUEUE_KEY = "automlops:jobs"

# ============================================================
# MANAGERS
# ============================================================

k8s_manager = K8sJobManager() if ENABLE_K8S_BUILD else None
training_manager = TrainingManager(k8s_manager) if ENABLE_TRAINING else None
inference_manager = InferenceManager(k8s_manager) if ENABLE_DEPLOYMENT else None
s3_manager = S3Manager() if ENABLE_S3_UPLOAD else None

github_client = GitHubClient(GITHUB_TOKEN) if ENABLE_GITHUB_PUSH else None

# ============================================================
# HELPERS
# ============================================================


def update_job_status(
    job_id,
    status,
    error_message="",
    api_endpoint="",
    model_s3_path="",
    python_files=0,
    notebooks=0,
    frameworks="",
    github_repo_url="",
    deployment_url="",
    github_actions_url="",
    gitlab_ci_url="",
    jenkinsfile_url="",
):
    """
    Update orchestrator
    """
    try:
        payload = {
            "status": status,
            "error_message": error_message,
            "api_endpoint": api_endpoint,
            "model_s3_path": model_s3_path,
            "python_files": python_files,
            "notebooks": notebooks,
            "frameworks": frameworks,
            "github_repo_url": github_repo_url,
            "deployment_url": deployment_url,
            "github_actions_url": github_actions_url,
            "gitlab_ci_url": gitlab_ci_url,
            "jenkinsfile_url": jenkinsfile_url,
        }

        url = f"{ORCHESTRATOR_URL}/api/jobs/{job_id}/status"

        response = requests.patch(url, json=payload, timeout=10)
        response.raise_for_status()

        logger.info(f"Updated job {job_id} -> {status}")

    except Exception as e:
        logger.error(f"Failed to update job status: {e}")


def sanitize_project_name(repo_url, job_id):
    try:
        name = repo_url.split("/")[-1].replace(".git", "")
        name = "".join(c if c.isalnum() else "-" for c in name.lower())
        return name[:50]
    except:
        return f"ml-api-{job_id[:8]}"


def generate_ci_configs(analysis_data, llm_client):
    """
    Generate all CI/CD configurations using LLM
    
    Args:
        analysis_data: Repository analysis results
        llm_client: LLM client (Groq or Gemini)
        
    Returns:
        dict: CI configurations {filename: content}
    """
    configs = {}
    
    try:
        # GitHub Actions
        github_gen = GitHubActionsGenerator(llm_client, analysis_data)
        configs[github_gen.get_filename()] = github_gen.generate()
        logger.info("✅ GitHub Actions workflow generated")
    except Exception as e:
        logger.error(f"GitHub Actions generation failed: {e}")
    
    try:
        # GitLab CI
        gitlab_gen = GitLabCIGenerator(llm_client, analysis_data)
        configs[gitlab_gen.get_filename()] = gitlab_gen.generate()
        logger.info("✅ GitLab CI configuration generated")
    except Exception as e:
        logger.error(f"GitLab CI generation failed: {e}")
    
    try:
        # Jenkins
        jenkins_gen = JenkinsGenerator(llm_client, analysis_data)
        configs[jenkins_gen.get_filename()] = jenkins_gen.generate()
        logger.info("✅ Jenkinsfile generated")
    except Exception as e:
        logger.error(f"Jenkins generation failed: {e}")
    
    return configs


# ============================================================
# MAIN PIPELINE
# ============================================================


def process_job(job_id, repo_url):
    logger.info(f"Processing {job_id}")

    github_repo_url = ""
    deployment_url = ""
    github_actions_url = ""
    gitlab_ci_url = ""
    jenkinsfile_url = ""

    try:
        update_job_status(job_id, "analyzing")

        # ====================================================
        # ANALYSIS
        # ====================================================

        llm = LLMClient()

        analyzer = RepoAnalyzer(repo_url, settings.TEMP_REPO_DIR)
        analyzer.clone_repository()
        analysis = analyzer.analyze_structure()

        python_files = len(analysis.get("python_files", []))
        notebooks = len(analysis.get("notebooks", []))
        frameworks_list = analysis.get("ml_frameworks", [])
        frameworks = ", ".join(frameworks_list)

        # ====================================================
        # OUTPUT DIR
        # ====================================================

        output_dir = Path(f"/tmp/automlops-output/{job_id}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # ====================================================
        # GENERATE CORE FILES
        # ====================================================

        update_job_status(job_id, "generating")

        dockerfile = DockerfileGenerator(llm).generate(analysis)
        (output_dir / "Dockerfile").write_text(dockerfile)

        training = TrainingScriptGenerator(llm).generate(analysis)
        (output_dir / "training_wrapper.py").write_text(training)

        fastapi = FastAPIGenerator(llm).generate(analysis)
        (output_dir / "app.py").write_text(fastapi)

        requirements = ["fastapi", "uvicorn", "numpy", "joblib", "boto3"]
        (output_dir / "requirements.txt").write_text("\n".join(requirements))

        # ====================================================
        # PHASE 2 — EXISTING CI/CD FILE GENERATION
        # ====================================================

        if ENABLE_CICD_GENERATION:
            project_name = sanitize_project_name(repo_url, job_id)

            # GitHub actions (from agent - for deployment)
            gha = AgentGitHubActionsGenerator(llm)
            gha_yaml = gha.generate(analysis, project_name)
            gha_dir = output_dir / ".github" / "workflows"
            gha_dir.mkdir(parents=True, exist_ok=True)
            (gha_dir / "deploy.yml").write_text(gha_yaml)

            # Kubernetes
            k8s = KubernetesGenerator(llm)
            dep, svc = k8s.generate(analysis, project_name)
            k8s_dir = output_dir / "k8s"
            k8s_dir.mkdir(exist_ok=True)
            (k8s_dir / "deployment.yaml").write_text(dep)
            (k8s_dir / "service.yaml").write_text(svc)

        # ====================================================
        # NEW: AI-POWERED CI/CD CONFIGS FOR ML TRAINING
        # ====================================================

        if ENABLE_CICD_GENERATION:
            try:
                logger.info(f"Generating AI-powered CI/CD configurations for job {job_id}")

                # Generate CI/CD configs using LLM
                ci_configs = generate_ci_configs(analysis, llm)

                # Save CI configs to output directory
                for config_filename, config_content in ci_configs.items():
                    config_path = output_dir / config_filename
                    config_path.parent.mkdir(parents=True, exist_ok=True)
                    config_path.write_text(config_content)
                    logger.info(f"Saved {config_filename} to disk")

                # Upload CI configs to S3 if enabled
                if ENABLE_S3_UPLOAD and s3_manager:
                    for config_filename, config_content in ci_configs.items():
                        # Clean filename for S3 key
                        s3_key = f"jobs/{job_id}/ci/{config_filename.replace('/', '-')}"
                        
                        # Upload to S3
                        s3_manager.upload_file(
                            file_path=str(output_dir / config_filename),
                            s3_key=s3_key
                        )
                        
                        # Generate S3 URL
                        s3_url = f"https://{S3_BUCKET}.{S3_ENDPOINT}/{s3_key}"
                        
                        # Map to appropriate URL variable
                        if ".github/workflows/train.yml" in config_filename:
                            github_actions_url = s3_url
                        elif ".gitlab-ci.yml" in config_filename:
                            gitlab_ci_url = s3_url
                        elif "Jenkinsfile" in config_filename:
                            jenkinsfile_url = s3_url
                        
                        logger.info(f"Uploaded {config_filename} to S3: {s3_url}")

                logger.success(f"✅ Generated {len(ci_configs)} CI/CD configurations")

            except Exception as e:
                logger.error(f"CI generation failed: {e}")
                # Continue even if CI generation fails

        # ====================================================
        # PHASE 2 — PUSH TO GITHUB
        # ====================================================

        if ENABLE_GITHUB_PUSH and github_client:
            project_name = sanitize_project_name(repo_url, job_id)
            repo = github_client.create_repository(
                f"{project_name}-automlops", 
                description="Auto generated ML API"
            )
            github_repo_url = repo.get("html_url")
            github_client.push_code(
                repo.get("clone_url"), str(output_dir), "Initial commit"
            )

        # ====================================================
        # S3 UPLOAD
        # ====================================================

        if ENABLE_S3_UPLOAD and s3_manager:
            prefix = f"jobs/{job_id}"
            s3_manager.upload_directory(str(output_dir), prefix)
            model_s3_path = f"s3://{S3_BUCKET}/{prefix}"
        else:
            model_s3_path = ""

        # ====================================================
        # DEPLOY
        # ====================================================

        if ENABLE_DEPLOYMENT and inference_manager:
            result = inference_manager.deploy_inference_api(
                job_id, REGISTRY_URL, S3_BUCKET, S3_ENDPOINT
            )
            deployment_url = result.get("endpoint", "")

        # ====================================================
        # COMPLETE
        # ====================================================

        update_job_status(
            job_id,
            "completed",
            api_endpoint=deployment_url,
            model_s3_path=model_s3_path,
            python_files=python_files,
            notebooks=notebooks,
            frameworks=frameworks,
            github_repo_url=github_repo_url,
            deployment_url=deployment_url,
            github_actions_url=github_actions_url,
            gitlab_ci_url=gitlab_ci_url,
            jenkinsfile_url=jenkinsfile_url,
        )

        logger.success(f"✅ Completed {job_id}")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        update_job_status(job_id, "failed", error_message=str(e))


# ============================================================
# WORKER LOOP
# ============================================================


def main():
    logger.info("🚀 Worker started")
    logger.info(f"Redis: {REDIS_HOST}:{REDIS_PORT}")
    logger.info(f"Orchestrator: {ORCHESTRATOR_URL}")
    logger.info(f"S3 Upload: {ENABLE_S3_UPLOAD}")
    logger.info(f"CI/CD Generation: {ENABLE_CICD_GENERATION}")

    while True:
        try:
            result = redis_client.blpop(JOB_QUEUE_KEY, timeout=5)

            if result:
                _, data = result
                msg = json.loads(data)
                process_job(msg["job_id"], msg["repo_url"])

        except Exception as e:
            logger.error(f"Worker error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
