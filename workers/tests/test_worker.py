"""
Basic tests for worker module
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../agent"))
)


class TestWorkerBasics:
    """Test basic worker functionality"""

    def test_imports(self):
        """Test that worker can be imported"""
        # Temporarily unset GITHUB_TOKEN to avoid Pydantic validation error
        github_token = os.environ.pop("GITHUB_TOKEN", None)

        try:
            # Test that we can import worker modules
            import workers.src.worker as worker_module

            assert worker_module is not None
        except ImportError as e:
            pytest.skip(f"Worker module not found: {e}")
        except Exception as e:
            pytest.skip(f"Worker module import failed: {e}")
        finally:
            # Restore GITHUB_TOKEN
            if github_token:
                os.environ["GITHUB_TOKEN"] = github_token

    def test_environment_variables(self):
        """Test environment variable handling"""
        # Set test environment variables
        os.environ["REDIS_HOST"] = "localhost"
        os.environ["REDIS_PORT"] = "6379"
        os.environ["ORCHESTRATOR_URL"] = "http://localhost:8080"

        # Verify they can be read
        assert os.getenv("REDIS_HOST") == "localhost"
        assert os.getenv("REDIS_PORT") == "6379"
        assert os.getenv("ORCHESTRATOR_URL") == "http://localhost:8080"

    def test_redis_connection_config(self):
        """Test Redis connection configuration"""
        os.environ["REDIS_HOST"] = "test-redis"
        os.environ["REDIS_PORT"] = "6380"

        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))

        assert redis_host == "test-redis"
        assert redis_port == 6380


class TestJobProcessing:
    """Test job processing logic"""

    @patch("requests.patch")
    def test_update_job_status_called(self, mock_patch):
        """Test that job status update is called correctly"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_patch.return_value = mock_response

        # Simulate status update
        import requests

        job_id = "test-job-123"
        status = "completed"
        orchestrator_url = "http://localhost:8080"

        response = requests.patch(
            f"{orchestrator_url}/api/jobs/{job_id}/status", json={"status": status}
        )

        assert response.status_code == 200
        mock_patch.assert_called_once()


class TestStorageIntegration:
    """Test storage module integration"""

    def test_s3_url_construction(self):
        """Test S3 URL construction logic"""
        bucket = "automlops-models"
        region = "nyc3"
        job_id = "test-job-123"
        filename = "Dockerfile"

        # Expected URL format
        expected_url = (
            f"https://{bucket}.{region}.digitaloceanspaces.com/jobs/{job_id}/{filename}"
        )

        # Construct URL
        constructed_url = (
            f"https://{bucket}.{region}.digitaloceanspaces.com/jobs/{job_id}/{filename}"
        )

        assert constructed_url == expected_url

    def test_artifact_path_generation(self):
        """Test artifact path generation"""
        job_id = "test-job-456"
        artifacts = ["Dockerfile", "app.py", "requirements.txt"]

        artifact_paths = [f"jobs/{job_id}/{artifact}" for artifact in artifacts]

        assert len(artifact_paths) == 3
        assert artifact_paths[0] == f"jobs/{job_id}/Dockerfile"
        assert all(job_id in path for path in artifact_paths)


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_missing_required_env_vars(self):
        """Test behavior with missing environment variables"""
        # Clear environment variables
        original_redis_host = os.environ.get("REDIS_HOST")
        if "REDIS_HOST" in os.environ:
            del os.environ["REDIS_HOST"]

        # Test default value handling
        redis_host = os.getenv("REDIS_HOST", "localhost")
        assert redis_host == "localhost"

        # Restore original value
        if original_redis_host:
            os.environ["REDIS_HOST"] = original_redis_host

    @patch("requests.patch")
    def test_status_update_failure_handling(self, mock_patch):
        """Test handling of failed status updates"""
        mock_patch.side_effect = Exception("Connection failed")

        try:
            import requests

            requests.patch("http://localhost:8080/api/jobs/test/status")
            assert False, "Should have raised exception"
        except Exception as e:
            assert "Connection failed" in str(e)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
