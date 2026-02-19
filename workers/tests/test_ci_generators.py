"""
Test CI/CD generators
"""
import os
import sys
import pytest
from unittest.mock import Mock

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from workers.src.generators import (
    GitHubActionsGenerator,
    GitLabCIGenerator,
    JenkinsGenerator
)


class MockLLM:
    """Mock LLM for testing"""
    
    def generate(self, prompt):
        if "GitHub Actions" in prompt:
            return """name: Train ML Model
on:
  push:
    branches: [main]
jobs:
  train:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python train.py
"""
        elif "GitLab" in prompt:
            return """stages:
  - train
train:
  stage: train
  script:
    - python train.py
"""
        else:
            return """pipeline {
    agent any
    stages {
        stage('Train') {
            steps {
                sh 'python train.py'
            }
        }
    }
}
"""


@pytest.fixture
def analysis_data():
    return {
        'repo_name': 'test-ml-project',
        'framework': 'tensorflow',
        'python_version': '3.10',
        'requirements': ['tensorflow', 'numpy', 'pandas'],
        'needs_gpu': True,
        'training_script': 'train.py'
    }


@pytest.fixture
def mock_llm():
    return MockLLM()


class TestGitHubActionsGenerator:
    
    def test_generates_workflow(self, analysis_data, mock_llm):
        generator = GitHubActionsGenerator(mock_llm, analysis_data)
        config = generator.generate()
        
        assert 'name: Train ML Model' in config
        assert 'jobs:' in config
        assert len(config) > 50
    
    def test_correct_filename(self, analysis_data, mock_llm):
        generator = GitHubActionsGenerator(mock_llm, analysis_data)
        assert generator.get_filename() == '.github/workflows/train.yml'
    
    def test_fallback_config(self, analysis_data, mock_llm):
        generator = GitHubActionsGenerator(mock_llm, analysis_data)
        fallback = generator._get_fallback_config()
        
        assert 'name: Train ML Model' in fallback
        assert 'train.py' in fallback


class TestGitLabCIGenerator:
    
    def test_generates_config(self, analysis_data, mock_llm):
        generator = GitLabCIGenerator(mock_llm, analysis_data)
        config = generator.generate()
        
        assert 'stages:' in config
        assert 'train' in config
    
    def test_correct_filename(self, analysis_data, mock_llm):
        generator = GitLabCIGenerator(mock_llm, analysis_data)
        assert generator.get_filename() == '.gitlab-ci.yml'


class TestJenkinsGenerator:
    
    def test_generates_jenkinsfile(self, analysis_data, mock_llm):
        generator = JenkinsGenerator(mock_llm, analysis_data)
        config = generator.generate()
        
        assert 'pipeline' in config
        assert 'stages' in config or 'stage' in config
    
    def test_correct_filename(self, analysis_data, mock_llm):
        generator = JenkinsGenerator(mock_llm, analysis_data)
        assert generator.get_filename() == 'Jenkinsfile'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
