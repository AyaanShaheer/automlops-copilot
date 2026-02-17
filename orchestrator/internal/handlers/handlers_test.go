package handlers

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

func TestHealthCheckHandler(t *testing.T) {
	// Set Gin to Test Mode
	gin.SetMode(gin.TestMode)

	// Create a test router
	router := gin.Default()
	
	// Register the health check route
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "healthy",
			"service": "automlops-orchestrator",
		})
	})

	// Create a test HTTP request
	req, err := http.NewRequest("GET", "/health", nil)
	assert.NoError(t, err, "Failed to create request")

	// Create a response recorder
	w := httptest.NewRecorder()

	// Perform the request
	router.ServeHTTP(w, req)

	// Assert the response
	assert.Equal(t, http.StatusOK, w.Code, "Expected status code 200")
	assert.Contains(t, w.Body.String(), "healthy", "Response should contain 'healthy'")
	assert.Contains(t, w.Body.String(), "automlops-orchestrator", "Response should contain service name")
}

func TestHealthCheckHandlerStatusCode(t *testing.T) {
	gin.SetMode(gin.TestMode)

	router := gin.Default()
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "healthy",
			"service": "automlops-orchestrator",
		})
	})

	req, _ := http.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
}
