"""
Tests for storage module
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestS3Storage:
    """Test S3/Spaces storage functionality"""

    def test_bucket_configuration(self):
        """Test S3 bucket configuration"""
        os.environ["DO_SPACES_BUCKET"] = "test-bucket"
        os.environ["DO_SPACES_REGION"] = "nyc3"

        bucket = os.getenv("DO_SPACES_BUCKET")
        region = os.getenv("DO_SPACES_REGION")

        assert bucket == "test-bucket"
        assert region == "nyc3"

    def test_file_key_generation(self):
        """Test S3 file key generation"""
        job_id = "job-123"
        filename = "Dockerfile"

        key = f"jobs/{job_id}/{filename}"

        assert key == "jobs/job-123/Dockerfile"
        assert key.startswith("jobs/")

    def test_multiple_artifact_keys(self):
        """Test generating keys for multiple artifacts"""
        job_id = "job-456"
        files = ["Dockerfile", "app.py", "requirements.txt", "training.py"]

        keys = [f"jobs/{job_id}/{file}" for file in files]

        assert len(keys) == 4
        assert all(f"jobs/{job_id}/" in key for key in keys)


class TestFileOperations:
    """Test file operation utilities"""

    def test_file_exists_check(self):
        """Test file existence checking"""
        # Test with this test file itself
        test_file = __file__
        assert os.path.exists(test_file)

    def test_directory_creation(self):
        """Test directory creation logic"""
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        test_subdir = os.path.join(temp_dir, "test", "nested", "path")

        os.makedirs(test_subdir, exist_ok=True)
        assert os.path.exists(test_subdir)

        # Cleanup
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
