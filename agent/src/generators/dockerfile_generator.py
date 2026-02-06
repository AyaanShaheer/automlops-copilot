from typing import Dict, List
from loguru import logger
from src.llm.llm_client import LLMClient

class DockerfileGenerator:
    """Generates Dockerfile for ML repositories"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def generate(self, repo_analysis: Dict) -> str:
        """Generate Dockerfile based on repository analysis"""
        
        frameworks = repo_analysis.get("ml_frameworks", [])
        python_version = self._detect_python_version(repo_analysis)
        requirements = repo_analysis.get("requirements_files", [])
        entry_points = repo_analysis.get("entry_points", [])
        
        system_prompt = """You are an expert DevOps engineer specializing in containerizing ML applications.
Generate a production-ready Dockerfile that:
- Uses appropriate base image for ML workloads
- Installs all dependencies efficiently
- Follows Docker best practices (multi-stage builds, layer caching)
- Sets up proper working directory and entry point
- Handles GPU support if needed
- Minimizes image size

Output ONLY the Dockerfile content, no explanations."""

        user_prompt = f"""Generate a Dockerfile for this ML repository:

**ML Frameworks Detected**: {', '.join(frameworks) if frameworks else 'None detected'}
**Python Version**: {python_version}
**Requirements Files**: {', '.join(requirements) if requirements else 'requirements.txt (assumed)'}
**Entry Points**: {', '.join(entry_points) if entry_points else 'train.py (assumed)'}

**File Structure**:
{repo_analysis.get('file_tree', 'Not available')[:1000]}

Generate the Dockerfile:"""

        try:
            dockerfile_content = self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1,
                max_tokens=2048
            )
            
            # Clean up the response
            dockerfile_content = self._clean_dockerfile(dockerfile_content)
            
            logger.success("Dockerfile generated successfully")
            return dockerfile_content
            
        except Exception as e:
            logger.error(f"Failed to generate Dockerfile: {e}")
            # Return a basic fallback Dockerfile
            return self._generate_fallback_dockerfile(python_version, frameworks)
    
    def _detect_python_version(self, repo_analysis: Dict) -> str:
        """Detect Python version from repository"""
        # Default to Python 3.10 for ML workloads
        return "3.10"
    
    def _clean_dockerfile(self, content: str) -> str:
        """Clean up generated Dockerfile content"""
        # Remove markdown code blocks if present
        if "```dockerfile" in content or "```Dockerfile" in content:
            content = content.split("```")[1]
            if content.startswith("dockerfile") or content.startswith("Dockerfile"):
                content = "\n".join(content.split("\n")[1:])
        elif "```" in content:
            content = content.split("```")[1]
        
        return content.strip()
    
    def _generate_fallback_dockerfile(self, python_version: str, frameworks: List[str]) -> str:
        """Generate a basic fallback Dockerfile"""
        base_image = "python:3.10-slim"
        
        if "pytorch" in frameworks:
            base_image = "pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime"
        elif "tensorflow" in frameworks:
            base_image = "tensorflow/tensorflow:2.15.0-gpu"
        
        return f"""FROM {base_image}

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set entry point
CMD ["python", "train.py"]
"""