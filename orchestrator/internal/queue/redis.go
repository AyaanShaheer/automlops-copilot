package queue

import (
	"context"
	"encoding/json"
	"fmt"
	"log"

	"github.com/AyaanShaheer/automlops-copilot/orchestrator/internal/config"
	"github.com/redis/go-redis/v9"
)

var Client *redis.Client

const JobQueueKey = "automlops:jobs"

type JobMessage struct {
	JobID   string `json:"job_id"`
	RepoURL string `json:"repo_url"`
}

func Connect(cfg *config.Config) error {
	Client = redis.NewClient(&redis.Options{
		Addr:     fmt.Sprintf("%s:%s", cfg.RedisHost, cfg.RedisPort),
		Password: cfg.RedisPassword,
		DB:       cfg.RedisDB,
	})

	ctx := context.Background()

	// Test connection
	_, err := Client.Ping(ctx).Result()
	if err != nil {
		return fmt.Errorf("failed to connect to Redis: %w", err)
	}

	log.Println("Redis connected successfully")
	return nil
}

func EnqueueJob(jobID, repoURL string) error {
	ctx := context.Background()

	msg := JobMessage{
		JobID:   jobID,
		RepoURL: repoURL,
	}

	data, err := json.Marshal(msg)
	if err != nil {
		return err
	}

	return Client.RPush(ctx, JobQueueKey, data).Err()
}

func DequeueJob() (*JobMessage, error) {
	ctx := context.Background()

	result, err := Client.BLPop(ctx, 0, JobQueueKey).Result()
	if err != nil {
		return nil, err
	}

	if len(result) < 2 {
		return nil, fmt.Errorf("invalid queue result")
	}

	var msg JobMessage
	err = json.Unmarshal([]byte(result[1]), &msg)
	if err != nil {
		return nil, err
	}

	return &msg, nil
}

func Close() error {
	return Client.Close()
}
