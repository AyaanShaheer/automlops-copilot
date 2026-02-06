import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from git import Repo
from loguru import logger
import yaml

class RepoAnalyzer:
    """Analyzes GitHub ML repositories to extract structure and metadata"""
    
    def __init__(self, repo_url: str, clone_dir: str):
        self.repo_url = repo_url
        self.clone_dir = Path(clone_dir)
        self.repo_path: Optional[Path] = None
        
        # Ensure clone directory exists
        self.clone_dir.mkdir(parents=True, exist_ok=True)
        
    def clone_repository(self) -> bool:
        """Clone the GitHub repository"""
        try:
            repo_name = self.repo_url.rstrip('/').split('/')[-1].replace('.git', '')
            self.repo_path = self.clone_dir / repo_name
            
            if self.repo_path.exists():
                logger.info(f"Repository already exists at {self.repo_path}")
                return True
                
            logger.info(f"Cloning {self.repo_url}...")
            Repo.clone_from(self.repo_url, str(self.repo_path))
            logger.success(f"Repository cloned to {self.repo_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clone repository: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def analyze_structure(self) -> Dict:
        """Analyze repository structure and extract metadata"""
        if not self.repo_path or not self.repo_path.exists():
            raise ValueError("Repository not cloned")
        
        analysis = {
            "repo_url": self.repo_url,
            "repo_path": str(self.repo_path),
            "python_files": [],
            "notebooks": [],
            "requirements_files": [],
            "config_files": [],
            "model_files": [],
            "data_files": [],
            "readme": None,
            "entry_points": [],
            "ml_frameworks": [],
            "file_tree": ""
        }
        
        # Walk through repository
        for root, dirs, files in os.walk(self.repo_path):
            # Skip common non-code directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv', 'env']]
            
            try:
                rel_root = Path(root).relative_to(self.repo_path)
            except ValueError:
                continue
            
            for file in files:
                file_path = Path(root) / file
                rel_path = str(rel_root / file)
                
                # Python files
                if file.endswith('.py'):
                    analysis["python_files"].append(rel_path)
                    if file in ['train.py', 'main.py', 'run.py', 'model.py']:
                        analysis["entry_points"].append(rel_path)
                
                # Notebooks
                elif file.endswith('.ipynb'):
                    analysis["notebooks"].append(rel_path)
                
                # Requirements
                elif file in ['requirements.txt', 'environment.yml', 'Pipfile', 'pyproject.toml', 'setup.py']:
                    analysis["requirements_files"].append(rel_path)
                
                # Config files
                elif file.endswith(('.yaml', '.yml', '.json', '.toml', '.ini')):
                    analysis["config_files"].append(rel_path)
                
                # Model files
                elif file.endswith(('.pth', '.pt', '.h5', '.pkl', '.joblib', '.onnx', '.pb')):
                    analysis["model_files"].append(rel_path)
                
                # Data files
                elif file.endswith(('.csv', '.json', '.parquet', '.txt', '.xml')):
                    if 'data' in str(rel_root).lower():
                        analysis["data_files"].append(rel_path)
                
                # README
                elif file.lower().startswith('readme'):
                    analysis["readme"] = rel_path
        
        # Detect ML frameworks
        analysis["ml_frameworks"] = self._detect_frameworks(analysis["python_files"])
        
        # Generate file tree
        analysis["file_tree"] = self._generate_file_tree()
        
        logger.info(f"Analysis complete: {len(analysis['python_files'])} Python files, "
                   f"{len(analysis['notebooks'])} notebooks found")
        
        return analysis
    
    def _detect_frameworks(self, python_files: List[str]) -> List[str]:
        """Detect ML frameworks used in the repository"""
        frameworks = set()
        framework_imports = {
            'tensorflow': ['tensorflow', 'tf.'],
            'pytorch': ['torch', 'pytorch'],
            'sklearn': ['sklearn', 'scikit-learn', 'from sklearn'],
            'keras': ['keras'],
            'xgboost': ['xgboost'],
            'lightgbm': ['lightgbm'],
            'transformers': ['transformers'],
            'fastai': ['fastai']
        }
        
        for py_file in python_files[:20]:  # Check first 20 files
            try:
                file_path = self.repo_path / py_file
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for framework, patterns in framework_imports.items():
                    if any(pattern in content for pattern in patterns):
                        frameworks.add(framework)
            except Exception as e:
                logger.debug(f"Could not read {py_file}: {e}")
                continue
        
        return list(frameworks)
    
    def _generate_file_tree(self, max_depth: int = 3) -> str:
        """Generate a simple file tree representation"""
        tree_lines = []
        
        def add_tree(path: Path, prefix: str = "", depth: int = 0):
            if depth > max_depth:
                return
            
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                items = [i for i in items if not i.name.startswith('.')][:50]  # Skip hidden, limit to 50
                
                for i, item in enumerate(items):
                    is_last = i == len(items) - 1
                    current_prefix = "└── " if is_last else "├── "
                    tree_lines.append(f"{prefix}{current_prefix}{item.name}")
                    
                    if item.is_dir() and item.name not in ['__pycache__', '.git', 'node_modules', '.venv', 'venv']:
                        next_prefix = prefix + ("    " if is_last else "│   ")
                        add_tree(item, next_prefix, depth + 1)
            except PermissionError:
                pass
        
        tree_lines.append(self.repo_path.name)
        add_tree(self.repo_path)
        
        return "\n".join(tree_lines)
    
    def get_readme_content(self) -> Optional[str]:
        """Extract README content"""
        if not self.repo_path:
            return None
        
        readme_files = list(self.repo_path.glob('README*'))
        if readme_files:
            try:
                with open(readme_files[0], 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read README: {e}")
        
        return None
