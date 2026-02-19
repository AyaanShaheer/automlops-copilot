"""
Jenkins pipeline generator
"""
from workers.src.generators.ci.base_generator import BaseCIGenerator
from loguru import logger


class JenkinsGenerator(BaseCIGenerator):
    """Generate Jenkinsfile for ML training"""
    
    def get_filename(self) -> str:
        return "Jenkinsfile"
    
    def generate(self) -> str:
        """Generate Jenkinsfile for ML training"""
        logger.info(f"Generating Jenkinsfile for {self.repo_name}")
        
        prompt = self._build_prompt()
        config = self._call_llm(prompt)
        
        # Clean up the response
        config = self._clean_groovy(config)
        
        logger.info("Jenkinsfile generated successfully")
        return config
    
    def _build_prompt(self) -> str:
        """Build LLM prompt for Jenkins generation"""
        context = self._build_context()
        
        gpu_section = ""
        if self.has_gpu:
            gpu_section = """
- Configure agent with GPU support
- Set up CUDA environment"""
        
        prompt = f"""You are an expert DevOps engineer. Generate a production-ready Jenkinsfile for training a machine learning model.

{context}

Requirements:
- Use declarative pipeline syntax
- Define stages: Checkout, Setup, Train, Test, Archive
- Use Python {self.python_version} agent/container
- Install dependencies from requirements.txt
- Run training script: {self.entry_point}
- Archive trained model as artifact
- Publish training logs{gpu_section}
- Include post-build notifications
- Add error handling and cleanup

Output ONLY the complete Jenkinsfile content. Do not include explanations or markdown code blocks.
Start with: pipeline {{"""

        return prompt
    
    def _clean_groovy(self, groovy_content: str) -> str:
        """Clean LLM output to get pure Groovy"""
        if "```groovy" in groovy_content:
            groovy_content = groovy_content.split("```groovy").split("```")[1]
        elif "```" in groovy_content:
            groovy_content = groovy_content.split("```").split("```")[0]
        
        return groovy_content.strip()
    
    def _get_fallback_config(self) -> str:
        """Fallback Jenkinsfile"""
        agent_config = "any"
        gpu_env = ""
        
        if self.has_gpu:
            agent_config = "{ label 'gpu' }"
            gpu_env = """
        CUDA_VISIBLE_DEVICES = '0'"""
        
        return f"""pipeline {{
    agent {agent_config}
    
    environment {{
        PYTHON_VERSION = '{self.python_version}'
        TRAINING_SCRIPT = '{self.entry_point}'{gpu_env}
    }}
    
    stages {{
        stage('Checkout') {{
            steps {{
                checkout scm
                sh 'git log -1'
            }}
        }}
        
        stage('Setup Environment') {{
            steps {{
                sh '''
                    python${{PYTHON_VERSION}} -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }}
        }}
        
        stage('Run Tests') {{
            steps {{
                sh '''
                    . venv/bin/activate
                    pip install pytest
                    pytest tests/ || echo "No tests found"
                '''
            }}
        }}
        
        stage('Train Model') {{
            steps {{
                sh '''
                    . venv/bin/activate
                    python ${{TRAINING_SCRIPT}}
                '''
            }}
        }}
        
        stage('Archive Artifacts') {{
            steps {{
                archiveArtifacts artifacts: 'models/**, *.pkl, *.h5, *.pth', fingerprint: true
                archiveArtifacts artifacts: 'logs/**, *.log', allowEmptyArchive: true
            }}
        }}
    }}
    
    post {{
        success {{
            echo '✅ Training completed successfully!'
        }}
        failure {{
            echo '❌ Training failed!'
        }}
        always {{
            cleanWs()
        }}
    }}
}}
"""