"""
Base class for all CI/CD generators
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from loguru import logger


class BaseCIGenerator(ABC):
    """Base class for CI/CD configuration generators"""
    
    def __init__(self, llm_client, analysis_data: Dict[str, Any]):
        """
        Initialize generator
        
        Args:
            llm_client: LLM client (Groq or Gemini)
            analysis_data: Repository analysis data
        """
        self.llm = llm_client
        self.analysis = analysis_data
        self.repo_name = analysis_data.get('repo_name', 'ml-project')
        self.framework = analysis_data.get('framework', 'unknown')
        self.python_version = analysis_data.get('python_version', '3.10')
        self.requirements = analysis_data.get('requirements', [])
        self.has_gpu = analysis_data.get('needs_gpu', False)
        self.entry_point = analysis_data.get('training_script', 'train.py')
    
    @abstractmethod
    def generate(self) -> str:
        """
        Generate CI/CD configuration
        
        Returns:
            str: Generated configuration file content
        """
        pass
    
    @abstractmethod
    def get_filename(self) -> str:
        """
        Get the filename for this CI/CD config
        
        Returns:
            str: Filename (e.g., '.github/workflows/train.yml')
        """
        pass
    
    def _build_context(self) -> str:
        """Build context string for LLM prompt"""
        context = f"""
Repository: {self.repo_name}
ML Framework: {self.framework}
Python Version: {self.python_version}
Training Script: {self.entry_point}
Requires GPU: {self.has_gpu}
Dependencies: {', '.join(self.requirements[:10])}
"""
        return context.strip()
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call LLM with prompt
        
        Args:
            prompt: Prompt to send to LLM
            
        Returns:
            str: LLM response
        """
        try:
            response = self.llm.generate(prompt)
            return response
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._get_fallback_config()
    
    @abstractmethod
    def _get_fallback_config(self) -> str:
        """
        Get fallback configuration if LLM fails
        
        Returns:
            str: Basic fallback configuration
        """
        pass
