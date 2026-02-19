"""
GitHub Actions workflow generator
"""
from workers.src.generators.ci.base_generator import BaseCIGenerator
from loguru import logger


class GitHubActionsGenerator(BaseCIGenerator):
    """Generate GitHub Actions workflows for ML training"""
    
    def get_filename(self) -> str:
        return ".github/workflows/train.yml"
    
    def generate(self) -> str:
        """Generate GitHub Actions workflow for ML training"""
        logger.info(f"Generating GitHub Actions workflow for {self.repo_name}")
        
        prompt = self._build_prompt()
        config = self._call_llm(prompt)
        
        # Clean up the response
        config = self._clean_yaml(config)
        
        logger.info("GitHub Actions workflow generated successfully")
        return config
    
    def _build_prompt(self) -> str:
        """Build LLM prompt for GitHub Actions generation"""
        context = self._build_context()
        
        gpu_section = ""
        if self.has_gpu:
            gpu_section = """
- Configure GPU support (CUDA)
- Use self-hosted runners with GPU or GitHub-hosted GPU runners"""
        
        prompt = f"""You are an expert DevOps engineer. Generate a production-ready GitHub Actions workflow for training a machine learning model.

{context}

Requirements:
- Workflow should trigger on push to main and pull requests
- Set up Python {self.python_version} environment
- Install dependencies from requirements.txt
- Run the training script: {self.entry_point}
- Save trained model as artifact
- Upload metrics and logs{gpu_section}
- Include caching for dependencies
- Add job for running tests (if test files exist)
- Use best practices for ML workflows

Output ONLY the complete YAML workflow file content. Do not include explanations or markdown code blocks.
Start with: name: Train ML Model"""

        return prompt
    
    def _clean_yaml(self, yaml_content: str) -> str:
        """Clean LLM output to get pure YAML"""
        # Remove markdown code blocks if present
        if "```yaml" in yaml_content:
            yaml_content = yaml_content.split("```yaml").split("```")[1]
        elif "```" in yaml_content:
            yaml_content = yaml_content.split("```").split("```")[0]
        
        return yaml_content.strip()
    
    def _get_fallback_config(self) -> str:
        """Fallback GitHub Actions workflow"""
        gpu_jobs = ""
        if self.has_gpu:
            gpu_jobs = """
      - name: Setup CUDA
        uses: Jimver/cuda-toolkit@v0.2.11
        with:
          cuda: '11.8.0'
"""
        
        return f"""name: Train ML Model

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

jobs:
  train:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '{self.python_version}'
          cache: 'pip'
      {gpu_jobs}
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run training
        run: |
          python {self.entry_point}
      
      - name: Upload model artifact
        uses: actions/upload-artifact@v4
        with:
          name: trained-model
          path: |
            models/
            *.pkl
            *.h5
            *.pth
          retention-days: 30
      
      - name: Upload training logs
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: training-logs
          path: |
            logs/
            *.log
          retention-days: 7
"""
