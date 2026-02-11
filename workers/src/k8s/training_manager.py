import os
import time
from kubernetes import client
from kubernetes.client.rest import ApiException
from loguru import logger
from jinja2 import Template
from pathlib import Path

class TrainingManager:
    """Manages model training jobs on Kubernetes with GPU support"""
    
    def __init__(self, k8s_job_manager):
        self.k8s = k8s_job_manager
        self.namespace = "automlops"
        
    def create_training_job(
        self, 
        job_id: str, 
        registry_url: str,
        s3_bucket: str = "automlops-models",
        s3_endpoint: str = "nyc3.digitaloceanspaces.com",
        gpu_type: str = "V100"
    ):
        """Create a Kubernetes job to train the model"""
        
        if not self.k8s.enabled:
            logger.warning("Kubernetes not configured - skipping training job creation")
            return None
        
        # Load job template
        template_path = Path(__file__).parent.parent.parent.parent / "k8s-manifests" / "training" / "training-job-template.yaml"
        
        if not template_path.exists():
            logger.error(f"Training job template not found at {template_path}")
            return None
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Render template
        template = Template(template_content)
        job_yaml = template.render(
            JOB_ID=job_id,
            REGISTRY_URL=registry_url,
            S3_BUCKET=s3_bucket,
            S3_ENDPOINT=s3_endpoint,
            GPU_TYPE=gpu_type
        )
        
        # Parse YAML
        import yaml
        job_manifest = yaml.safe_load(job_yaml)
        
        try:
            # Create the job
            logger.info(f"Creating training job for {job_id} with GPU: {gpu_type}")
            response = self.k8s.batch_v1.create_namespaced_job(
                namespace=self.namespace,
                body=job_manifest
            )
            
            logger.success(f"Training job created: {response.metadata.name}")
            return response.metadata.name
            
        except ApiException as e:
            logger.error(f"Failed to create training job: {e}")
            return None
    
    def monitor_training_job(self, job_name: str, timeout: int = 3600):
        """Monitor training job progress"""
        
        if not self.k8s.enabled:
            return None
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.k8s.get_job_status(job_name)
            
            if status == "completed":
                logger.success(f"Training job {job_name} completed successfully")
                return "completed"
            elif status == "failed":
                logger.error(f"Training job {job_name} failed")
                logs = self.k8s.get_job_logs(job_name)
                logger.error(f"Job logs:\n{logs}")
                return "failed"
            elif status in ["running", "pending"]:
                logger.info(f"Training job {job_name} status: {status}")
            
            time.sleep(30)  # Check every 30 seconds
        
        logger.warning(f"Training job {job_name} timed out after {timeout}s")
        return "timeout"
    
    def get_training_metrics(self, job_name: str):
        """Extract training metrics from job logs"""
        
        if not self.k8s.enabled:
            return None
        
        try:
            logs = self.k8s.get_job_logs(job_name)
            
            # Parse logs for common metrics
            metrics = {
                "accuracy": None,
                "loss": None,
                "epochs_completed": None,
                "training_time": None
            }
            
            # Simple log parsing (can be enhanced)
            for line in logs.split('\n'):
                if 'accuracy' in line.lower():
                    # Extract accuracy value
                    pass
                if 'loss' in line.lower():
                    # Extract loss value
                    pass
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get training metrics: {e}")
            return None
