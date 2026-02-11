import time
from kubernetes import client
from kubernetes.client.rest import ApiException
from loguru import logger
from jinja2 import Template
from pathlib import Path
import yaml

class InferenceManager:
    """Manages inference API deployments on Kubernetes"""
    
    def __init__(self, k8s_job_manager):
        self.k8s = k8s_job_manager
        self.namespace = "automlops"
        self.apps_v1 = client.AppsV1Api()
        self.autoscaling_v2 = client.AutoscalingV2Api()
        
    def deploy_inference_api(
        self,
        job_id: str,
        registry_url: str,
        s3_bucket: str = "automlops-models",
        s3_endpoint: str = "nyc3.digitaloceanspaces.com",
        replicas: int = 2,
        min_replicas: int = 1,
        max_replicas: int = 10
    ):
        """Deploy inference API as a Kubernetes Deployment + Service"""
        
        if not self.k8s.enabled:
            logger.warning("Kubernetes not configured - skipping inference deployment")
            return None
        
        # Load deployment template
        template_path = Path(__file__).parent.parent.parent.parent / "k8s-manifests" / "inference" / "inference-deployment-template.yaml"
        
        if not template_path.exists():
            logger.error(f"Inference deployment template not found at {template_path}")
            return None
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Render template
        template = Template(template_content)
        deployment_yaml = template.render(
            JOB_ID=job_id,
            REGISTRY_URL=registry_url,
            S3_BUCKET=s3_bucket,
            S3_ENDPOINT=s3_endpoint,
            REPLICAS=replicas
        )
        
        # Parse YAML (contains both Deployment and Service)
        manifests = list(yaml.safe_load_all(deployment_yaml))
        
        try:
            # Create Deployment
            deployment_manifest = manifests[0]
            logger.info(f"Creating inference deployment for {job_id}")
            
            deployment = self.apps_v1.create_namespaced_deployment(
                namespace=self.namespace,
                body=deployment_manifest
            )
            
            logger.success(f"Deployment created: {deployment.metadata.name}")
            
            # Create Service
            service_manifest = manifests[1]
            logger.info(f"Creating inference service for {job_id}")
            
            service = self.k8s.core_v1.create_namespaced_service(
                namespace=self.namespace,
                body=service_manifest
            )
            
            logger.success(f"Service created: {service.metadata.name}")
            
            # Create HPA (Horizontal Pod Autoscaler)
            self._create_hpa(job_id, min_replicas, max_replicas)
            
            # Wait for LoadBalancer IP
            endpoint = self._wait_for_loadbalancer(f"inference-{job_id}")
            
            return {
                "deployment": deployment.metadata.name,
                "service": service.metadata.name,
                "endpoint": endpoint
            }
            
        except ApiException as e:
            logger.error(f"Failed to deploy inference API: {e}")
            return None
    
    def _create_hpa(self, job_id: str, min_replicas: int, max_replicas: int):
        """Create Horizontal Pod Autoscaler for the deployment"""
        
        # Load HPA template
        hpa_template_path = Path(__file__).parent.parent.parent.parent / "k8s-manifests" / "inference" / "inference-hpa-template.yaml"
        
        if not hpa_template_path.exists():
            logger.warning("HPA template not found - skipping autoscaling")
            return
        
        with open(hpa_template_path, 'r') as f:
            template_content = f.read()
        
        template = Template(template_content)
        hpa_yaml = template.render(
            JOB_ID=job_id,
            MIN_REPLICAS=min_replicas,
            MAX_REPLICAS=max_replicas
        )
        
        hpa_manifest = yaml.safe_load(hpa_yaml)
        
        try:
            hpa = self.autoscaling_v2.create_namespaced_horizontal_pod_autoscaler(
                namespace=self.namespace,
                body=hpa_manifest
            )
            
            logger.success(f"HPA created: {hpa.metadata.name}")
            
        except ApiException as e:
            logger.error(f"Failed to create HPA: {e}")
    
    def _wait_for_loadbalancer(self, service_name: str, timeout: int = 300):
        """Wait for LoadBalancer to get an external IP"""
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                service = self.k8s.core_v1.read_namespaced_service(
                    name=service_name,
                    namespace=self.namespace
                )
                
                if service.status.load_balancer.ingress:
                    ingress = service.status.load_balancer.ingress[0]
                    
                    # DigitalOcean LoadBalancer returns IP
                    if ingress.ip:
                        endpoint = f"http://{ingress.ip}"
                        logger.success(f"LoadBalancer ready: {endpoint}")
                        return endpoint
                    
                    # Some providers return hostname
                    if ingress.hostname:
                        endpoint = f"http://{ingress.hostname}"
                        logger.success(f"LoadBalancer ready: {endpoint}")
                        return endpoint
                
                logger.info(f"Waiting for LoadBalancer IP... ({int(time.time() - start_time)}s)")
                time.sleep(10)
                
            except ApiException as e:
                logger.error(f"Error checking LoadBalancer status: {e}")
                break
        
        logger.warning(f"LoadBalancer IP not available after {timeout}s")
        return f"http://pending/{service_name}"
    
    def get_deployment_status(self, job_id: str):
        """Get status of inference deployment"""
        
        if not self.k8s.enabled:
            return None
        
        try:
            deployment = self.apps_v1.read_namespaced_deployment_status(
                name=f"inference-{job_id}",
                namespace=self.namespace
            )
            
            return {
                "replicas": deployment.status.replicas or 0,
                "ready_replicas": deployment.status.ready_replicas or 0,
                "available_replicas": deployment.status.available_replicas or 0,
                "unavailable_replicas": deployment.status.unavailable_replicas or 0
            }
            
        except ApiException as e:
            logger.error(f"Failed to get deployment status: {e}")
            return None
    
    def scale_deployment(self, job_id: str, replicas: int):
        """Manually scale inference deployment"""
        
        if not self.k8s.enabled:
            return False
        
        try:
            # Update deployment replicas
            self.apps_v1.patch_namespaced_deployment_scale(
                name=f"inference-{job_id}",
                namespace=self.namespace,
                body={"spec": {"replicas": replicas}}
            )
            
            logger.info(f"Scaled deployment inference-{job_id} to {replicas} replicas")
            return True
            
        except ApiException as e:
            logger.error(f"Failed to scale deployment: {e}")
            return False
    
    def delete_deployment(self, job_id: str):
        """Delete inference deployment and service"""
        
        if not self.k8s.enabled:
            return False
        
        try:
            # Delete deployment
            self.apps_v1.delete_namespaced_deployment(
                name=f"inference-{job_id}",
                namespace=self.namespace,
                body=client.V1DeleteOptions(propagation_policy='Foreground')
            )
            
            # Delete service
            self.k8s.core_v1.delete_namespaced_service(
                name=f"inference-{job_id}",
                namespace=self.namespace
            )
            
            # Delete HPA
            try:
                self.autoscaling_v2.delete_namespaced_horizontal_pod_autoscaler(
                    name=f"inference-{job_id}-hpa",
                    namespace=self.namespace
                )
            except:
                pass
            
            logger.info(f"Deleted inference deployment for job {job_id}")
            return True
            
        except ApiException as e:
            logger.error(f"Failed to delete deployment: {e}")
            return False
    
    def get_deployment_logs(self, job_id: str, lines: int = 100):
        """Get recent logs from inference deployment"""
        
        if not self.k8s.enabled:
            return None
        
        try:
            # Get pods for this deployment
            pods = self.k8s.core_v1.list_namespaced_pod(
                namespace=self.namespace,
                label_selector=f"job-id={job_id}"
            )
            
            if not pods.items:
                return "No pods found"
            
            # Get logs from first pod
            pod_name = pods.items[0].metadata.name
            logs = self.k8s.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=self.namespace,
                tail_lines=lines
            )
            
            return logs
            
        except ApiException as e:
            logger.error(f"Failed to get deployment logs: {e}")
            return None
