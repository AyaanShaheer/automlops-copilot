package models

import (
	"time"
)

type JobStatus string

const (
	StatusPending    JobStatus = "pending"
	StatusQueued     JobStatus = "queued"
	StatusAnalyzing  JobStatus = "analyzing"
	StatusBuilding   JobStatus = "building"
	StatusTraining   JobStatus = "training"
	StatusDeploying  JobStatus = "deploying"
	StatusCompleted  JobStatus = "completed"
	StatusFailed     JobStatus = "failed"
)

type Job struct {
	ID              string    `json:"id" gorm:"primaryKey"`
	RepoURL         string    `json:"repo_url" gorm:"not null"`
	Status          JobStatus `json:"status" gorm:"default:'pending'"`
	ErrorMessage    string    `json:"error_message,omitempty"`
	
	// Generated artifacts
	DockerfileURL   string    `json:"dockerfile_url,omitempty"`
	TrainingScript  string    `json:"training_script,omitempty"`
	InferenceAPI    string    `json:"inference_api,omitempty"`
	
	// Deployment info
	ModelS3Path     string    `json:"model_s3_path,omitempty"`
	APIEndpoint     string    `json:"api_endpoint,omitempty"`
	
	// Metadata
	Frameworks      string    `json:"frameworks,omitempty"`
	PythonFiles     int       `json:"python_files"`
	Notebooks       int       `json:"notebooks"`
	
	CreatedAt       time.Time `json:"created_at"`
	UpdatedAt       time.Time `json:"updated_at"`
	CompletedAt     *time.Time `json:"completed_at,omitempty"`
}

type CreateJobRequest struct {
	RepoURL string `json:"repo_url" binding:"required"`
}

type JobResponse struct {
	Job     Job    `json:"job"`
	Message string `json:"message,omitempty"`
}

type ListJobsResponse struct {
	Jobs  []Job `json:"jobs"`
	Total int   `json:"total"`
}
