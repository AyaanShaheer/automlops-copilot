import os
import yaml
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from loguru import logger
from jinja2 import Template
from pathlib import Path


class K8sJobManager:
    """Manages Kubernetes jobs for building and training"""

    def __init__(self):
        # Try to load in-cluster config first, fall back to kubeconfig
        try:
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes config")
        except:
            try:
                config.load_kube_config()
                logger.info("Loaded kubeconfig from ~/.kube/config")
            except:
                logger.warning(
                    "Could not load Kubernetes config - K8s features disabled"
                )
                self.enabled = False
                return

        self.enabled = True
        self.batch_v1 = client.BatchV1Api()
        self.core_v1 = client.CoreV1Api()
        self.namespace = "automlops"

    def create_build_job(
        self, job_id: str, registry_url: str = "registry.digitalocean.com/automlops"
    ):
        """Create a Kubernetes job to build Docker image"""

        if not self.enabled:
            logger.warning("Kubernetes not configured - skipping build job creation")
            return None

        # Load job template
        template_path = (
            Path(__file__).parent.parent.parent.parent
            / "k8s-manifests"
            / "build"
            / "kaniko-build-job-template.yaml"
        )

        if not template_path.exists():
            logger.error(f"Build job template not found at {template_path}")
            return None

        with open(template_path, "r") as f:
            template_content = f.read()

        # Render template
        template = Template(template_content)
        job_yaml = template.render(
            JOB_ID=job_id,
            REGISTRY_URL=registry_url,
            IMAGE_NAME=f"model-{job_id}",
            IMAGE_TAG="latest",
        )

        # Parse YAML
        job_manifest = yaml.safe_load(job_yaml)

        try:
            # Create the job
            logger.info(f"Creating build job for {job_id}")
            response = self.batch_v1.create_namespaced_job(
                namespace=self.namespace, body=job_manifest
            )

            logger.success(f"Build job created: {response.metadata.name}")
            return response.metadata.name

        except ApiException as e:
            logger.error(f"Failed to create build job: {e}")
            return None

    def get_job_status(self, job_name: str):
        """Get the status of a Kubernetes job"""

        if not self.enabled:
            return None

        try:
            job = self.batch_v1.read_namespaced_job_status(
                name=job_name, namespace=self.namespace
            )

            # Check job conditions
            if job.status.succeeded:
                return "completed"
            elif job.status.failed:
                return "failed"
            elif job.status.active:
                return "running"
            else:
                return "pending"

        except ApiException as e:
            logger.error(f"Failed to get job status: {e}")
            return None

    def get_job_logs(self, job_name: str):
        """Get logs from a Kubernetes job"""

        if not self.enabled:
            return None

        try:
            # Get pods for this job
            pods = self.core_v1.list_namespaced_pod(
                namespace=self.namespace, label_selector=f"job-name={job_name}"
            )

            if not pods.items:
                return "No pods found for job"

            # Get logs from the first pod
            pod_name = pods.items[0].metadata.name
            logs = self.core_v1.read_namespaced_pod_log(
                name=pod_name, namespace=self.namespace
            )

            return logs

        except ApiException as e:
            logger.error(f"Failed to get job logs: {e}")
            return None

    def delete_job(self, job_name: str):
        """Delete a Kubernetes job"""

        if not self.enabled:
            return False

        try:
            self.batch_v1.delete_namespaced_job(
                name=job_name,
                namespace=self.namespace,
                body=client.V1DeleteOptions(
                    propagation_policy="Foreground", grace_period_seconds=5
                ),
            )

            logger.info(f"Job {job_name} deleted")
            return True

        except ApiException as e:
            logger.error(f"Failed to delete job: {e}")
            return False
