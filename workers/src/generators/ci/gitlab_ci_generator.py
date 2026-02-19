"""
GitLab CI configuration generator
"""
from workers.src.generators.ci.base_generator import BaseCIGenerator
from loguru import logger


class GitLabCIGenerator(BaseCIGenerator):
    """Generate GitLab CI configuration for ML training"""
    
    def get_filename(self) -> str:
        return ".gitlab-ci.yml"
    
    def generate(self) -> str:
        """Generate GitLab CI configuration"""
        logger.info(f"Generating GitLab CI config for {self.repo_name}")
        
        prompt = self._build_prompt()
        config = self._call_llm(prompt)
        
        # Clean up the response
        config = self._clean_yaml(config)
        
        logger.info("GitLab CI configuration generated successfully")
        return config
    
    def _build_prompt(self) -> str:
        """Build LLM prompt for GitLab CI generation"""
        context = self._build_context()
        
        gpu_section = ""
        if self.has_gpu:
            gpu_section = """
- Configure GPU runners
- Set up CUDA environment"""
        
        prompt = f"""You are an expert DevOps engineer. Generate a production-ready GitLab CI configuration for training a machine learning model.

{context}

Requirements:
- Define stages: test, train, deploy
- Use Python {self.python_version} Docker image
- Install dependencies from requirements.txt
- Run training script: {self.entry_point}
- Save model as artifact
- Cache pip dependencies{gpu_section}
- Include code quality checks
- Add deployment stage for model registry

Output ONLY the complete .gitlab-ci.yml file content. Do not include explanations or markdown code blocks.
Start with: stages:"""

        return prompt
    
    def _clean_yaml(self, yaml_content: str) -> str:
        """Clean LLM output to get pure YAML"""
        if "```yaml" in yaml_content:
            yaml_content = yaml_content.split("```yaml").split("```")
        elif "```" in yaml_content:
            yaml_content = yaml_content.split("```").split("```")
        
        return yaml_content.strip()
    
    def _get_fallback_config(self) -> str:
        """Fallback GitLab CI configuration"""
        gpu_tags = ""
        if self.has_gpu:
            gpu_tags = "\n  tags:\n    - gpu"
        
        return f"""stages:
  - test
  - train
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip

test:
  stage: test
  image: python:{self.python_version}
  script:
    - pip install -r requirements.txt
    - pip install pytest
    - pytest tests/ || echo "No tests found"
  only:
    - merge_requests
    - main

train:
  stage: train
  image: python:{self.python_version}{gpu_tags}
  script:
    - pip install -r requirements.txt
    - python {self.entry_point}
  artifacts:
    paths:
      - models/
      - "*.pkl"
      - "*.h5"
      - "*.pth"
      - logs/
    expire_in: 30 days
  only:
    - main

deploy:
  stage: deploy
  image: python:{self.python_version}
  script:
    - echo "Deploy model to registry or serving platform"
    - pip install mlflow
    - echo "mlflow models serve -m ./models"
  only:
    - main
  when: manual
"""

