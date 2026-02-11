package config

import (
	"os"
	"strconv"
)

type Config struct {
	// Server
	ServerPort string

	// Database
	DBHost     string
	DBPort     string
	DBUser     string
	DBPassword string
	DBName     string

	// Redis
	RedisHost     string
	RedisPort     string
	RedisPassword string
	RedisDB       int

	// DigitalOcean
	DOSpacesKey    string
	DOSpacesSecret string
	DOSpacesRegion string
	DOSpacesBucket string

	// Agent
	AgentImage string
}

func Load() *Config {
	return &Config{
		// Server
		ServerPort: getEnv("SERVER_PORT", "8080"),

		// Database
		DBHost:     getEnv("DB_HOST", "localhost"),
		DBPort:     getEnv("DB_PORT", "5432"),
		DBUser:     getEnv("DB_USER", "postgres"),
		DBPassword: getEnv("DB_PASSWORD", "postgres"),
		DBName:     getEnv("DB_NAME", "automlops"),

		// Redis
		RedisHost:     getEnv("REDIS_HOST", "localhost"),
		RedisPort:     getEnv("REDIS_PORT", "6379"),
		RedisPassword: getEnv("REDIS_PASSWORD", ""),
		RedisDB:       getEnvAsInt("REDIS_DB", 0),

		// DigitalOcean
		DOSpacesKey:    getEnv("DO_SPACES_KEY", ""),
		DOSpacesSecret: getEnv("DO_SPACES_SECRET", ""),
		DOSpacesRegion: getEnv("DO_SPACES_REGION", "nyc3"),
		DOSpacesBucket: getEnv("DO_SPACES_BUCKET", "automlops-models"),

		// Agent
		AgentImage: getEnv("AGENT_IMAGE", "automlops-agent:latest"),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvAsInt(key string, defaultValue int) int {
	valueStr := getEnv(key, "")
	if value, err := strconv.Atoi(valueStr); err == nil {
		return value
	}
	return defaultValue
}

func (c *Config) GetDBConnectionString() string {
	return "host=" + c.DBHost +
		" port=" + c.DBPort +
		" user=" + c.DBUser +
		" password=" + c.DBPassword +
		" dbname=" + c.DBName +
		" sslmode=require"
}
