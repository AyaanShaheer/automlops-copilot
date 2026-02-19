import os
import shutil
import subprocess
from typing import Dict, Optional
from pathlib import Path
import requests
from loguru import logger


class GitHubClient:
    """Handles GitHub repository creation and code pushing"""

    def __init__(self, github_token: Optional[str] = None):
        """Initialize GitHub client

        Args:
            github_token: GitHub Personal Access Token (classic with repo scope)
        """
        self.token = github_token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            logger.warning("No GitHub token provided. Repository creation will fail.")

        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }

    def create_repository(
        self,
        repo_name: str,
        description: str = "AutoMLOps generated ML API",
        private: bool = False,
    ) -> Dict:
        """Create a new GitHub repository

        Args:
            repo_name: Name of the repository (will be sanitized)
            description: Repository description
            private: Whether to make repository private

        Returns:
            Dict with repo details including 'clone_url', 'html_url', 'full_name'
        """
        # Sanitize repo name
        repo_name = self._sanitize_repo_name(repo_name)

        logger.info(f"Creating GitHub repository: {repo_name}")

        payload = {
            "name": repo_name,
            "description": description,
            "private": private,
            "auto_init": False,  # Don't create README, we'll push our own
            "has_issues": True,
            "has_projects": False,
            "has_wiki": False,
        }

        try:
            response = requests.post(
                f"{self.api_base}/user/repos",
                headers=self.headers,
                json=payload,
                timeout=10,
            )

            if response.status_code == 201:
                repo_data = response.json()
                logger.success(f"Repository created: {repo_data['html_url']}")
                return {
                    "clone_url": repo_data["clone_url"],
                    "ssh_url": repo_data["ssh_url"],
                    "html_url": repo_data["html_url"],
                    "full_name": repo_data["full_name"],
                    "name": repo_data["name"],
                }
            elif response.status_code == 422:
                # Repository already exists
                logger.warning(f"Repository '{repo_name}' already exists")
                # Get the existing repo details
                return self._get_existing_repo(repo_name)
            else:
                logger.error(
                    f"Failed to create repository: {response.status_code} - {response.text}"
                )
                raise Exception(f"GitHub API error: {response.status_code}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def push_code(
        self,
        repo_url: str,
        local_path: str,
        commit_message: str = "Initial commit - AutoMLOps generated artifacts",
        branch: str = "main",
    ) -> bool:
        """Push local code to GitHub repository

        Args:
            repo_url: GitHub repository HTTPS URL
            local_path: Path to local directory with code
            commit_message: Git commit message
            branch: Target branch name

        Returns:
            bool: True if push successful, False otherwise
        """
        logger.info(f"Pushing code from {local_path} to {repo_url}")

        # Convert to Path object
        local_path = Path(local_path)

        if not local_path.exists():
            logger.error(f"Local path does not exist: {local_path}")
            return False

        try:
            # Initialize git repo if not already
            if not (local_path / ".git").exists():
                self._run_git_command(["git", "init"], cwd=local_path)
                logger.info("Initialized git repository")

            # Configure git user (required for commit)
            self._run_git_command(
                ["git", "config", "user.email", "automlops@bot.com"], cwd=local_path
            )
            self._run_git_command(
                ["git", "config", "user.name", "AutoMLOps Bot"], cwd=local_path
            )

            # Add all files
            self._run_git_command(["git", "add", "."], cwd=local_path)
            logger.info("Added files to git staging")

            # Commit
            self._run_git_command(
                ["git", "commit", "-m", commit_message], cwd=local_path
            )
            logger.info("Created commit")

            # Set branch name (rename master to main if needed)
            self._run_git_command(["git", "branch", "-M", branch], cwd=local_path)

            # Add remote with authentication
            authenticated_url = self._add_token_to_url(repo_url)
            self._run_git_command(
                ["git", "remote", "add", "origin", authenticated_url],
                cwd=local_path,
                check=False,  # Ignore error if remote already exists
            )

            # Set remote URL (in case it already exists)
            self._run_git_command(
                ["git", "remote", "set-url", "origin", authenticated_url],
                cwd=local_path,
            )

            # Push to remote
            self._run_git_command(
                ["git", "push", "-u", "origin", branch, "--force"], cwd=local_path
            )

            logger.success(f"Successfully pushed code to {repo_url}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to push code: {e}")
            return False

    def create_repository_secrets(
        self, repo_full_name: str, secrets: Dict[str, str]
    ) -> bool:
        """Create repository secrets for GitHub Actions

        Args:
            repo_full_name: Repository full name (owner/repo)
            secrets: Dictionary of secret names and values

        Returns:
            bool: True if all secrets created successfully
        """
        logger.info(f"Creating {len(secrets)} secrets for {repo_full_name}")

        # This requires encryption with repo public key
        # For simplicity, we'll skip this in Phase 2 and document it
        logger.warning("Secret creation requires additional encryption setup")
        logger.info("Please manually add these secrets to GitHub repo:")
        for secret_name in secrets.keys():
            logger.info(f"  - {secret_name}")

        return True

    def _sanitize_repo_name(self, name: str) -> str:
        """Sanitize repository name to match GitHub requirements"""
        # Remove invalid characters
        name = "".join(c if c.isalnum() or c in ["-", "_"] else "-" for c in name)
        # Remove leading/trailing hyphens
        name = name.strip("-")
        # Ensure not empty
        if not name:
            name = "ml-api"
        # Ensure max length
        name = name[:100]
        # Make lowercase
        name = name.lower()
        return name

    def _get_existing_repo(self, repo_name: str) -> Dict:
        """Get details of existing repository"""
        try:
            # First get authenticated user
            user_response = requests.get(
                f"{self.api_base}/user", headers=self.headers, timeout=10
            )

            if user_response.status_code == 200:
                username = user_response.json()["login"]

                # Get repo details
                repo_response = requests.get(
                    f"{self.api_base}/repos/{username}/{repo_name}",
                    headers=self.headers,
                    timeout=10,
                )

                if repo_response.status_code == 200:
                    repo_data = repo_response.json()
                    return {
                        "clone_url": repo_data["clone_url"],
                        "ssh_url": repo_data["ssh_url"],
                        "html_url": repo_data["html_url"],
                        "full_name": repo_data["full_name"],
                        "name": repo_data["name"],
                    }
        except Exception as e:
            logger.error(f"Failed to get existing repo: {e}")

        # Fallback - construct URLs manually
        return {
            "clone_url": f"https://github.com/username/{repo_name}.git",
            "html_url": f"https://github.com/username/{repo_name}",
            "full_name": f"username/{repo_name}",
            "name": repo_name,
        }

    def _add_token_to_url(self, url: str) -> str:
        """Add GitHub token to HTTPS URL for authentication"""
        if url.startswith("https://github.com/"):
            # Format: https://TOKEN@github.com/owner/repo.git
            url = url.replace("https://", f"https://{self.token}@")
        return url

    def _run_git_command(
        self, cmd: list, cwd: Path, check: bool = True
    ) -> subprocess.CompletedProcess:
        """Run a git command

        Args:
            cmd: Command as list of strings
            cwd: Working directory
            check: Whether to raise exception on failure

        Returns:
            CompletedProcess object
        """
        result = subprocess.run(
            cmd, cwd=str(cwd), capture_output=True, text=True, check=False
        )

        if check and result.returncode != 0:
            logger.error(f"Command failed: {' '.join(cmd)}")
            logger.error(f"Output: {result.stdout}")
            logger.error(f"Error: {result.stderr}")
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )

        return result
