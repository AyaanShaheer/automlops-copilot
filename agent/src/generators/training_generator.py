from typing import Dict, List
from loguru import logger
from src.llm.llm_client import LLMClient

class TrainingScriptGenerator:
    """Generates training script wrapper for ML repositories"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def generate(self, repo_analysis: Dict) -> str:
        """Generate training script that wraps existing code"""
        
        frameworks = repo_analysis.get("ml_frameworks", [])
        entry_points = repo_analysis.get("entry_points", [])
        
        system_prompt = """You are an expert ML engineer. Generate a Python training script that:
- Wraps the existing training code
- Adds model saving to DigitalOcean Spaces (S3-compatible)
- Adds logging and progress tracking
- Handles errors gracefully
- Saves model artifacts with metadata
- Uses boto3 for S3 uploads

Output ONLY the Python code, no explanations."""

        user_prompt = f"""Generate a training wrapper script for this ML repository:

**ML Frameworks**: {', '.join(frameworks) if frameworks else 'scikit-learn'}
**Entry Points**: {', '.join(entry_points) if entry_points else 'train.py'}

**Requirements**:
1. Import and run the original training code
2. After training, save the model
3. Upload model to S3 (DO Spaces) using boto3
4. Log training metrics
5. Handle exceptions and report status

Generate the training_wrapper.py script:"""

        try:
            script_content = self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1,
                max_tokens=3072
            )
            
            script_content = self._clean_code(script_content)
            logger.success("Training script generated successfully")
            return script_content
            
        except Exception as e:
            logger.error(f"Failed to generate training script: {e}")
            return self._generate_fallback_training_script(frameworks, entry_points)
    
    def _clean_code(self, content: str) -> str:
        """Clean up generated code"""
        if "```python" in content:
            content = content.split("```python")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```").split("```")[1]
        
        return content.strip()
    
    def _generate_fallback_training_script(self, frameworks: List[str], entry_points: List[str]) -> str:
        """Generate fallback training script"""
        entry_point = entry_points if entry_points else "train.py"
        
        return f"""import os
import sys
import boto3
import joblib
from datetime import datetime
from pathlib import Path

# S3 Configuration
S3_ENDPOINT = os.getenv('DO_SPACES_ENDPOINT', 'https://nyc3.digitaloceanspaces.com')
S3_BUCKET = os.getenv('DO_SPACES_BUCKET', 'automlops-models')
S3_KEY = os.getenv('DO_SPACES_KEY')
S3_SECRET = os.getenv('DO_SPACES_SECRET')

def upload_to_s3(file_path, s3_key):
    '''Upload file to DigitalOcean Spaces'''
    s3_client = boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_KEY,
        aws_secret_access_key=S3_SECRET
    )
    
    s3_client.upload_file(file_path, S3_BUCKET, s3_key)
    print(f"Uploaded {{file_path}} to s3://{{S3_BUCKET}}/{{s3_key}}")

def main():
    print("Starting training...")
    
    try:
        # Import and run original training code
        import {entry_point.replace('.py', '').replace('/', '.')}
        
        # Look for saved model files
        model_files = list(Path('.').glob('*.pkl')) + \\
                     list(Path('.').glob('*.pth')) + \\
                     list(Path('.').glob('*.h5')) + \\
                     list(Path('.').glob('*.joblib'))
        
        if model_files:
            for model_file in model_files:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                s3_key = f"models/{{timestamp}}_{{model_file.name}}"
                upload_to_s3(str(model_file), s3_key)
        
        print("Training completed successfully!")
        
    except Exception as e:
        print(f"Training failed: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
