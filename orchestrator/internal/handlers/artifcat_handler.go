package handlers

import (
	"archive/zip"
	"bytes"
	"io"
	"net/http"
	"path/filepath"

	"github.com/AyaanShaheer/automlops-copilot/orchestrator/internal/storage"
	"github.com/gin-gonic/gin"
)

// GetArtifacts handles GET /api/jobs/:id/artifacts
func GetArtifacts(c *gin.Context) {
	jobID := c.Param("id")

	if storage.GlobalS3Client == nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "S3 client not initialized"})
		return
	}

	artifacts, err := storage.GlobalS3Client.ListJobArtifacts(jobID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch artifacts from S3: " + err.Error()})
		return
	}

	if len(artifacts) == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "No artifacts found"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"job_id":    jobID,
		"artifacts": artifacts,
	})
}

// DownloadArtifact handles GET /api/jobs/:id/artifacts/:filename
func DownloadArtifact(c *gin.Context) {
	jobID := c.Param("id")
	filename := c.Param("filename")

	// Security: validate filename to prevent directory traversal
	if filepath.Base(filename) != filename {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid filename"})
		return
	}

	if storage.GlobalS3Client == nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "S3 client not initialized"})
		return
	}

	content, err := storage.GlobalS3Client.DownloadFile(jobID, filename)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "File not found: " + err.Error()})
		return
	}

	// Set headers to force download
	c.Header("Content-Description", "File Transfer")
	c.Header("Content-Transfer-Encoding", "binary")
	c.Header("Content-Disposition", "attachment; filename="+filename)
	c.Header("Content-Type", "application/octet-stream")

	// Serve the file content
	c.Data(http.StatusOK, "application/octet-stream", content)
}

// DownloadAllArtifacts handles GET /api/jobs/:id/artifacts-zip
func DownloadAllArtifacts(c *gin.Context) {
	jobID := c.Param("id")

	if storage.GlobalS3Client == nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "S3 client not initialized"})
		return
	}

	// For zip, we need to fetch all artifacts first
	artifacts, err := storage.GlobalS3Client.ListJobArtifacts(jobID)
	if err != nil || len(artifacts) == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "Artifacts not found"})
		return
	}

	// Create a buffer for zip
	buf := new(bytes.Buffer)
	zipWriter := zip.NewWriter(buf)

	for filename, content := range artifacts {
		f, err := zipWriter.Create(filename)
		if err != nil {
			continue
		}
		_, err = io.WriteString(f, content)
		if err != nil {
			continue
		}
	}

	zipWriter.Close()

	// Set headers
	c.Header("Content-Description", "File Transfer")
	c.Header("Content-Transfer-Encoding", "binary")
	c.Header("Content-Disposition", "attachment; filename="+jobID+"-artifacts.zip")
	c.Header("Content-Type", "application/zip")

	c.Data(http.StatusOK, "application/zip", buf.Bytes())
}
