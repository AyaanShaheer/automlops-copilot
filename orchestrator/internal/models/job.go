package models

import (
	"time"
)

type JobStatus string

const (
	StatusQueued     JobStatus = "queued"
	StatusAnalyzing  JobStatus = "analyzing"
	StatusGenerating JobStatus = "generating"
	StatusCompleted  JobStatus = "completed"
	StatusFailed     JobStatus = "failed"
)

type Job struct {
	ID        string    `json:"id" gorm:"primaryKey"`
	RepoURL   string    `json:"repo_url" gorm:"not null"`
	Status    JobStatus `json:"status" gorm:"default:'queued'"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`

	// Completion
	CompletedAt *time.Time `json:"completed_at,omitempty"`

	// Results
	APIEndpoint  string `json:"api_endpoint,omitempty" gorm:"type:text"`
	ModelS3Path  string `json:"model_s3_path,omitempty" gorm:"type:text"`
	ErrorMessage string `json:"error_message,omitempty" gorm:"type:text"`

	// Analysis metadata
	PythonFiles int    `json:"python_files,omitempty"`
	Notebooks   int    `json:"notebooks,omitempty"`
	Frameworks  string `json:"frameworks,omitempty" gorm:"type:text"`

	// Phase 2: GitHub and deployment
	GitHubRepoURL string `json:"github_repo_url,omitempty" gorm:"type:text"`
	DeploymentURL string `json:"deployment_url,omitempty" gorm:"type:text"`

	// NEW: CI/CD configuration URLs
	GitHubActionsURL string `json:"github_actions_url,omitempty" gorm:"type:text"`
	GitLabCIURL      string `json:"gitlab_ci_url,omitempty" gorm:"type:text"`
	JenkinsfileURL   string `json:"jenkinsfile_url,omitempty" gorm:"type:text"`
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
