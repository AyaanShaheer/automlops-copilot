from typing import Dict, Tuple
from loguru import logger
from ..llm.llm_client import LLMClient


class KubernetesGenerator:
    """Generates Kubernetes manifests (Deployment + Service) for ML APIs"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def generate(self, repo_analysis: Dict, project_name: str = "ml-api") -> Tuple[str, str]:
        """Generate Kubernetes deployment and service manifests
        
        Args:
            repo_analysis: Repository analysis from analyzer
            project_name: Name for the Kubernetes deployment (default: ml-api)
            
        Returns:
            Tuple[str, str]: (deployment.yaml content, service.yaml content)
        """
        
        frameworks = repo_analysis.get("ml_frameworks", [])
        requires_gpu = self._detect_gpu_requirement(frameworks)
        
        system_prompt = """You are an expert Kubernetes engineer specializing in ML application deployments.
Generate production-ready Kubernetes manifests that:
- Use proper resource limits and requests
- Include health checks (liveness and readiness probes)
- Support horizontal pod autoscaling
- Use secrets for sensitive data
- Follow Kubernetes best practices
- Handle GPU resources if needed
- Include proper labels and selectors
- Use LoadBalancer service type for external access

Output ONLY the YAML content for BOTH deployment and service, separated by '---'. No explanations."""

        user_prompt = f"""Generate Kubernetes manifests for this ML API:

**Project Name**: {project_name}
**ML Frameworks**: {', '.join(frameworks) if frameworks else 'Generic ML'}
**GPU Required**: {requires_gpu}
**Container Port**: 8000 (FastAPI default)

**Deployment Requirements**:
- Namespace: automlops
- Replicas: 2 (for high availability)
- Container registry: registry.digitalocean.com/automlops/{project_name}
- Image tag: latest
- Environment variables from ConfigMap/Secrets
- Resource limits: CPU 1000m, Memory 2Gi
- Resource requests: CPU 500m, Memory 1Gi
{'- GPU limit: 1 nvidia.com/gpu' if requires_gpu else ''}

**Service Requirements**:
- Type: LoadBalancer
- Port: 80 (external) -> 8000 (container)
- Selector: app={project_name}

**Health Checks**:
- Liveness probe: HTTP GET /health on port 8000
- Readiness probe: HTTP GET /health on port 8000
- Initial delay: 30s
- Period: 10s

Generate both deployment.yaml and service.yaml separated by '---':"""

        try:
            manifests_content = self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1,
                max_tokens=3072
            )
            
            # Clean up the response
            manifests_content = self._clean_yaml(manifests_content)
            
            # Split into deployment and service
            deployment_yaml, service_yaml = self._split_manifests(manifests_content)
            
            # Validate basic structure
            if not self._validate_manifests(deployment_yaml, service_yaml):
                logger.warning("Generated manifests failed validation, using fallback")
                return self._generate_fallback_manifests(project_name, requires_gpu)
            
            logger.success("Kubernetes manifests generated successfully")
            return deployment_yaml, service_yaml
            
        except Exception as e:
            logger.error(f"Failed to generate Kubernetes manifests: {e}")
            # Return fallback manifests
            return self._generate_fallback_manifests(project_name, requires_gpu)
    
    def _detect_gpu_requirement(self, frameworks: list) -> bool:
        """Detect if GPU is required based on frameworks"""
        gpu_frameworks = ["tensorflow", "pytorch", "keras"]
        return any(fw.lower() in gpu_frameworks for fw in frameworks)
    
    def _clean_yaml(self, content: str) -> str:
        """Clean up generated YAML content"""
        # Remove markdown code blocks if present
        if "```yaml" in content or "```yml" in content:
            parts = content.split("```")
            for part in parts:
                if part.strip().startswith("yaml") or part.strip().startswith("yml"):
                    content = "\n".join(part.split("\n")[1:])
                elif not part.strip().startswith(("```", "yaml", "yml")) and len(part.strip()) > 50:
                    content = part
        elif "```" in content:
            parts = content.split("```")
            content = parts[1] if len(parts) > 1 else content
        
        return content.strip()
    
    def _split_manifests(self, content: str) -> Tuple[str, str]:
        """Split combined YAML into deployment and service"""
        # Split by YAML document separator
        parts = content.split("---")
        
        deployment = ""
        service = ""
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if "kind: Deployment" in part or "kind: deployment" in part:
                deployment = part
            elif "kind: Service" in part or "kind: service" in part:
                service = part
        
        # If not found, try to extract differently
        if not deployment or not service:
            logger.warning("Could not split manifests properly")
            # Assume first is deployment, second is service
            parts = [p.strip() for p in parts if p.strip()]
            if len(parts) >= 2:
                deployment = parts[0]
                service = parts[1]
        
        return deployment, service
    
    def _validate_manifests(self, deployment: str, service: str) -> bool:
        """Basic validation of manifest structure"""
        deployment_keys = ["apiVersion:", "kind: Deployment", "metadata:", "spec:"]
        service_keys = ["apiVersion:", "kind: Service", "metadata:", "spec:"]
        
        deployment_valid = all(key in deployment for key in deployment_keys)
        service_valid = all(key in service for key in service_keys)
        
        return deployment_valid and service_valid
    
    def _generate_fallback_manifests(self, project_name: str, requires_gpu: bool) -> Tuple[str, str]:
        """Generate basic fallback Kubernetes manifests"""
        
        gpu_resources = ""
        if requires_gpu:
            gpu_resources = """
            limits:
              nvidia.com/gpu: 1"""
        
        deployment = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {project_name}
  namespace: automlops
  labels:
    app: {project_name}
    version: v1
    managed-by: automlops-copilot
spec:
  replicas: 2
  selector:
    matchLabels:
      app: {project_name}
  template:
    metadata:
      labels:
        app: {project_name}
        version: v1
    spec:
      containers:
      - name: {project_name}
        image: registry.digitalocean.com/automlops/{project_name}:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP
        env:
        - name: PORT
          value: "8000"
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"{gpu_resources}
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
      imagePullSecrets:
      - name: do-registry-secret
      restartPolicy: Always
"""

        service = f"""apiVersion: v1
kind: Service
metadata:
  name: {project_name}-service
  namespace: automlops
  labels:
    app: {project_name}
    managed-by: automlops-copilot
  annotations:
    service.beta.kubernetes.io/do-loadbalancer-name: "{project_name}-lb"
    service.beta.kubernetes.io/do-loadbalancer-protocol: "http"
    service.beta.kubernetes.io/do-loadbalancer-healthcheck-path: "/health"
spec:
  type: LoadBalancer
  selector:
    app: {project_name}
  ports:
  - name: http
    protocol: TCP
    port: 80
    targetPort: 8000
  sessionAffinity: None
  externalTrafficPolicy: Cluster
"""
        
        return deployment, service
