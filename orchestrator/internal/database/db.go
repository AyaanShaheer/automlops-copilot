package database

import (
	"log"
	
	"github.com/AyaanShaheer/automlops-copilot/orchestrator/internal/config"
	"github.com/AyaanShaheer/automlops-copilot/orchestrator/internal/models"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

var DB *gorm.DB

func Connect(cfg *config.Config) error {
	var err error
	
	dsn := cfg.GetDBConnectionString()
	
	DB, err = gorm.Open(postgres.Open(dsn), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Info),
	})
	
	if err != nil {
		return err
	}
	
	log.Println("Database connected successfully")
	
	// Auto-migrate models
	err = DB.AutoMigrate(&models.Job{})
	if err != nil {
		return err
	}
	
	log.Println("Database migrations completed")
	
	return nil
}

func Close() error {
	sqlDB, err := DB.DB()
	if err != nil {
		return err
	}
	return sqlDB.Close()
}
