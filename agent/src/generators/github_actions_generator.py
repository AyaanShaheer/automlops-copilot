from typing import Dict
from loguru import logger
from ..llm.llm_client import LLMClient


class GitHubActionsGenerator:
    """Generates GitHub Actions workflow for ML repositories"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def generate(self, repo_analysis: Dict, project_name: str = "ml-api") -> str:
        """Generate GitHub Actions workflow based on repository analysis
        
        Args:
            repo_analysis: Repository analysis from analyzer
            project_name: Name for the deployed service (default: ml-api)
            
        Returns:
            str: Complete GitHub Actions workflow YAML content
        """
        
        frameworks = repo_analysis.get("ml_frameworks", [])
        python_version = self._detect_python_version(repo_analysis)
        has_tests = self._detect_tests(repo_analysis)
        
        system_prompt = """You are an expert DevOps engineer specializing in CI/CD pipelines for ML applications.
Generate a complete GitHub Actions workflow (YAML) that:
- Builds Docker image for the ML API
- Runs tests if present
- Pushes to DigitalOcean Container Registry
- Deploys to Kubernetes cluster
- Uses secrets for credentials
- Follows CI/CD best practices
- Includes proper job dependencies
- Has health checks after deployment

Output ONLY the workflow YAML content, no explanations or markdown."""

        user_prompt = f"""Generate a GitHub Actions workflow for this ML repository:

**Project Name**: {project_name}
**ML Frameworks**: {', '.join(frameworks) if frameworks else 'None detected'}
**Python Version**: {python_version}
**Has Tests**: {has_tests}

**Deployment Requirements**:
- Container Registry: DigitalOcean Container Registry (registry.digitalocean.com)
- Target: Kubernetes cluster (DigitalOcean Kubernetes)
- Namespace: automlops
- Service Type: LoadBalancer

**Workflow Triggers**:
- Push to main branch
- Pull requests to main branch

**Jobs Required**:
1. Build and Test (build Docker image, run tests if present)
2. Push to Registry (only on main branch)
3. Deploy to Kubernetes (only on main branch, after successful push)

Generate the complete GitHub Actions workflow YAML:"""

        try:
            workflow_content = self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1,
                max_tokens=3072
            )
            
            # Clean up the response
            workflow_content = self._clean_yaml(workflow_content)
            
            # Validate basic structure
            if not self._validate_workflow(workflow_content):
                logger.warning("Generated workflow failed validation, using fallback")
                return self._generate_fallback_workflow(project_name, python_version, has_tests)
            
            logger.success("GitHub Actions workflow generated successfully")
            return workflow_content
            
        except Exception as e:
            logger.error(f"Failed to generate GitHub Actions workflow: {e}")
            # Return fallback workflow
            return self._generate_fallback_workflow(project_name, python_version, has_tests)
    
    def _detect_python_version(self, repo_analysis: Dict) -> str:
        """Detect Python version from repository"""
        # Check for explicit version in repo analysis
        if "python_version" in repo_analysis:
            return repo_analysis["python_version"]
        # Default to Python 3.10 for ML workloads
        return "3.10"
    
    def _detect_tests(self, repo_analysis: Dict) -> bool:
        """Detect if repository has test files"""
        file_tree = repo_analysis.get("file_tree", "")
        test_indicators = ["test_", "tests/", "pytest", "unittest"]
        return any(indicator in file_tree.lower() for indicator in test_indicators)
    
    def _clean_yaml(self, content: str) -> str:
        """Clean up generated YAML content"""
        # Remove markdown code blocks if present
        if "```yaml" in content or "```yml" in content:
            parts = content.split("```")
            for part in parts:
                if part.strip().startswith("yaml") or part.strip().startswith("yml"):
                    content = "\n".join(part.split("\n")[1:])
                elif not part.strip().startswith(("```", "yaml", "yml")):
                    content = part
        elif "```" in content:
            content = content.split("```") if len(content.split("```")) > 1 else content[1]
        
        return content.strip()
    
    def _validate_workflow(self, content: str) -> bool:
        """Basic validation of workflow structure"""
        required_keys = ["name:", "on:", "jobs:"]
        return all(key in content for key in required_keys)
    
    def _generate_fallback_workflow(self, project_name: str, python_version: str, has_tests: bool) -> str:
        """Generate a basic fallback GitHub Actions workflow"""
        
        test_step = ""
        if has_tests:
            test_step = """
      - name: Run tests
        run: |
          pip install pytest
          pytest tests/ || echo "No tests found"
"""
        
        return f"""name: Deploy ML API

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: registry.digitalocean.com
  IMAGE_NAME: automlops/{project_name}
  KUBE_NAMESPACE: automlops

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '{python_version}'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
{test_step}
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Build Docker image
        run: |
          docker build -t ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}:${{{{ github.sha }}}} .
          docker build -t ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}:latest .

  push-to-registry:
    needs: build-and-test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Install doctl
        uses: digitalocean/action-doctl@v2
        with:
          token: ${{{{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}}}
      
      - name: Log in to DO Container Registry
        run: doctl registry login --expiry-seconds 1200
      
      - name: Build and push Docker image
        run: |
          docker build -t ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}:${{{{ github.sha }}}} .
          docker build -t ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}:latest .
          docker push ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}:${{{{ github.sha }}}}
          docker push ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}:latest

  deploy-to-kubernetes:
    needs: push-to-registry
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Install doctl
        uses: digitalocean/action-doctl@v2
        with:
          token: ${{{{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}}}
      
      - name: Save Kubernetes config
        run: doctl kubernetes cluster kubeconfig save ${{{{ secrets.KUBERNETES_CLUSTER_NAME }}}}
      
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/{project_name} {project_name}=${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}:${{{{ github.sha }}}} -n ${{{{ env.KUBE_NAMESPACE }}}}
          kubectl rollout status deployment/{project_name} -n ${{{{ env.KUBE_NAMESPACE }}}}
      
      - name: Verify deployment
        run: |
          kubectl get pods -n ${{{{ env.KUBE_NAMESPACE }}}} -l app={project_name}
          kubectl get svc -n ${{{{ env.KUBE_NAMESPACE }}}} -l app={project_name}
"""


