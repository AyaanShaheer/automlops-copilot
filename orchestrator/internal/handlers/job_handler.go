package handlers

import (
	"net/http"
	"time"

	"github.com/AyaanShaheer/automlops-copilot/orchestrator/internal/database"
	"github.com/AyaanShaheer/automlops-copilot/orchestrator/internal/models"
	"github.com/AyaanShaheer/automlops-copilot/orchestrator/internal/queue"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

// CreateJob handles POST /api/jobs
func CreateJob(c *gin.Context) {
	var req models.CreateJobRequest

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Create new job
	job := models.Job{
		ID:        uuid.New().String(),
		RepoURL:   req.RepoURL,
		Status:    models.StatusQueued,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	// Save to database
	if err := database.DB.Create(&job).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create job"})
		return
	}

	// Enqueue job
	if err := queue.EnqueueJob(job.ID, job.RepoURL); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to enqueue job"})
		return
	}

	c.JSON(http.StatusCreated, models.JobResponse{
		Job:     job,
		Message: "Job created and queued successfully",
	})
}

// GetJob handles GET /api/jobs/:id
func GetJob(c *gin.Context) {
	jobID := c.Param("id")

	var job models.Job
	if err := database.DB.First(&job, "id = ?", jobID).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Job not found"})
		return
	}

	c.JSON(http.StatusOK, models.JobResponse{Job: job})
}

// ListJobs handles GET /api/jobs
func ListJobs(c *gin.Context) {
	var jobs []models.Job

	result := database.DB.Order("created_at DESC").Limit(50).Find(&jobs)
	if result.Error != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch jobs"})
		return
	}

	c.JSON(http.StatusOK, models.ListJobsResponse{
		Jobs:  jobs,
		Total: len(jobs),
	})
}

// UpdateJobStatus handles PATCH /api/jobs/:id/status (internal use)
func UpdateJobStatus(c *gin.Context) {
	jobID := c.Param("id")

	var req struct {
		Status       string `json:"status"`
		ErrorMessage string `json:"error_message"`
		APIEndpoint  string `json:"api_endpoint"`
		ModelS3Path  string `json:"model_s3_path"`
		PythonFiles  int    `json:"python_files"`
		Notebooks    int    `json:"notebooks"`
		Frameworks   string `json:"frameworks"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	var job models.Job
	if err := database.DB.First(&job, "id = ?", jobID).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Job not found"})
		return
	}

	// Update job fields
	updates := map[string]interface{}{
		"status":     models.JobStatus(req.Status),
		"updated_at": time.Now(),
	}

	if req.ErrorMessage != "" {
		updates["error_message"] = req.ErrorMessage
	}

	if req.APIEndpoint != "" {
		updates["api_endpoint"] = req.APIEndpoint
	}

	if req.ModelS3Path != "" {
		updates["model_s3_path"] = req.ModelS3Path
	}

	// Update analysis metadata
	if req.PythonFiles > 0 {
		updates["python_files"] = req.PythonFiles
	}

	if req.Notebooks > 0 {
		updates["notebooks"] = req.Notebooks
	}

	if req.Frameworks != "" {
		updates["frameworks"] = req.Frameworks
	}

	if req.Status == string(models.StatusCompleted) || req.Status == string(models.StatusFailed) {
		now := time.Now()
		updates["completed_at"] = &now
	}

	if err := database.DB.Model(&job).Updates(updates).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update job"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Job updated successfully"})
}

// DeleteJob handles DELETE /api/jobs/:id
func DeleteJob(c *gin.Context) {
	jobID := c.Param("id")

	if err := database.DB.Delete(&models.Job{}, "id = ?", jobID).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to delete job"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Job deleted successfully"})
}

// HealthCheck handles GET /health
func HealthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":    "healthy",
		"service":   "automlops-orchestrator",
		"timestamp": time.Now(),
	})
}
