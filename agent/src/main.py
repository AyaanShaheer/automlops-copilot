import os
import sys
import json
from pathlib import Path
from typing import Dict
from loguru import logger
from src.config import settings
from src.analyzer.repo_analyzer import RepoAnalyzer
from src.llm.llm_client import LLMClient
from src.generators.dockerfile_generator import DockerfileGenerator
from src.generators.training_generator import TrainingScriptGenerator
from src.generators.fastapi_generator import FastAPIGenerator

# Configure logger
logger.remove()
logger.add(sys.stdout, level=settings.LOG_LEVEL)

class AutoMLOpsAgent:
    """Main agent that orchestrates the entire pipeline"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.dockerfile_gen = DockerfileGenerator(self.llm_client)
        self.training_gen = TrainingScriptGenerator(self.llm_client)
        self.fastapi_gen = FastAPIGenerator(self.llm_client)
    
    def process_repository(self, repo_url: str, output_dir: str = "./output"):
        """Process a GitHub repository end-to-end"""
        logger.info(f"Processing repository: {repo_url}")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Clone and analyze repository
        logger.info("Step 1: Analyzing repository...")
        analyzer = RepoAnalyzer(repo_url, settings.TEMP_REPO_DIR)
        
        if not analyzer.clone_repository():
            logger.error("Failed to clone repository")
            return False
        
        analysis = analyzer.analyze_structure()
        
        # Save analysis
        with open(output_path / "analysis.json", "w") as f:
            json.dump(analysis, f, indent=2)
        logger.success("Analysis saved to analysis.json")
        
        # Step 2: Generate Dockerfile
        logger.info("Step 2: Generating Dockerfile...")
        dockerfile = self.dockerfile_gen.generate(analysis)
        with open(output_path / "Dockerfile", "w") as f:
            f.write(dockerfile)
        logger.success("Dockerfile generated")
        
        # Step 3: Generate training script
        logger.info("Step 3: Generating training script...")
        training_script = self.training_gen.generate(analysis)
        with open(output_path / "training_wrapper.py", "w") as f:
            f.write(training_script)
        logger.success("Training script generated")
        
        # Step 4: Generate FastAPI service
        logger.info("Step 4: Generating inference API...")
        fastapi_app = self.fastapi_gen.generate(analysis)
        with open(output_path / "app.py", "w") as f:
            f.write(fastapi_app)
        logger.success("FastAPI service generated")
        
        # Step 5: Generate requirements.txt for inference
        logger.info("Step 5: Generating inference requirements...")
        self._generate_inference_requirements(analysis, output_path)
        
        logger.success(f"✅ All artifacts generated in {output_dir}")
        return True
    
    def _generate_inference_requirements(self, analysis: Dict, output_path: Path):
        """Generate requirements.txt for inference service"""
        base_requirements = [
            "fastapi==0.109.0",
            "uvicorn==0.27.0",
            "pydantic==2.5.3",
            "numpy>=1.24.0",
            "joblib>=1.3.0"
        ]
        
        frameworks = analysis.get("ml_frameworks", [])
        
        if "pytorch" in frameworks:
            base_requirements.append("torch>=2.0.0")
        if "tensorflow" in frameworks:
            base_requirements.append("tensorflow>=2.13.0")
        if "sklearn" in frameworks:
            base_requirements.append("scikit-learn>=1.3.0")
        if "xgboost" in frameworks:
            base_requirements.append("xgboost>=2.0.0")
        
        with open(output_path / "inference_requirements.txt", "w") as f:
            f.write("\n".join(base_requirements))
        
        logger.success("Inference requirements generated")

def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python -m src.main <github_repo_url>")
        sys.exit(1)
    
    repo_url = sys.argv[1]
    agent = AutoMLOpsAgent()
    
    try:
        agent.process_repository(repo_url)
    except Exception as e:
        logger.error(f"Failed to process repository: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
