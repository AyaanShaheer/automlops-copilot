package main

import (
	"log"

	"github.com/AyaanShaheer/automlops-copilot/orchestrator/internal/config"
	"github.com/AyaanShaheer/automlops-copilot/orchestrator/internal/database"
	"github.com/AyaanShaheer/automlops-copilot/orchestrator/internal/handlers"
	"github.com/AyaanShaheer/automlops-copilot/orchestrator/internal/queue"
	"github.com/AyaanShaheer/automlops-copilot/orchestrator/internal/storage"
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
)

func main() {
	// Load .env file
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found, using environment variables")
	}

	// Load configuration
	cfg := config.Load()

	// Connect to database
	if err := database.Connect(cfg); err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer database.Close()

	// Connect to Redis
	if err := queue.Connect(cfg); err != nil {
		log.Fatalf("Failed to connect to Redis: %v", err)
	}
	defer queue.Close()

	// Initialize S3 Client
	if err := storage.InitS3(cfg); err != nil {
		log.Printf("Warning: Failed to initialize S3 client: %v", err)
	}

	// Setup Gin router
	router := gin.Default()

	// CORS middleware
	router.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"*"},
		AllowMethods:     []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Accept", "Authorization"},
		ExposeHeaders:    []string{"Content-Length"},
		AllowCredentials: true,
	}))

	// Routes
	api := router.Group("/api")
	{
		// Job routes
		api.POST("/jobs", handlers.CreateJob)
		api.GET("/jobs", handlers.ListJobs)
		api.GET("/jobs/:id", handlers.GetJob)
		api.PATCH("/jobs/:id/status", handlers.UpdateJobStatus)
		api.DELETE("/jobs/:id", handlers.DeleteJob)

		// Artifact routes
		api.GET("/jobs/:id/artifacts", handlers.GetArtifacts)
		api.GET("/jobs/:id/artifacts/:filename", handlers.DownloadArtifact)
		api.GET("/jobs/:id/artifacts-zip", handlers.DownloadAllArtifacts) // NEW
	}

	// Health check
	router.GET("/health", handlers.HealthCheck)

	// Root
	router.GET("/", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"service": "AutoMLOps Orchestrator",
			"version": "1.0.0",
			"status":  "running",
		})
	})

	// Start server
	port := cfg.ServerPort
	log.Printf("Starting server on port %s", port)

	if err := router.Run(":" + port); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
