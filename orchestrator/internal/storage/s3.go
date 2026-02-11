package storage

import (
	"fmt"
	"io/ioutil"

	"github.com/AyaanShaheer/automlops-copilot/orchestrator/internal/config"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/credentials"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
)

type S3Client struct {
	client *s3.S3
	bucket string
}

var GlobalS3Client *S3Client

func InitS3(cfg *config.Config) error {
	s3Config := &aws.Config{
		Credentials:      credentials.NewStaticCredentials(cfg.DOSpacesKey, cfg.DOSpacesSecret, ""),
		Endpoint:         aws.String(fmt.Sprintf("https://%s.digitaloceanspaces.com", cfg.DOSpacesRegion)),
		Region:           aws.String(cfg.DOSpacesRegion),
		S3ForcePathStyle: aws.Bool(false),
	}

	sess, err := session.NewSession(s3Config)
	if err != nil {
		return err
	}

	GlobalS3Client = &S3Client{
		client: s3.New(sess),
		bucket: cfg.DOSpacesBucket,
	}

	return nil
}

func (s *S3Client) GetFileContent(key string) (string, error) {
	result, err := s.client.GetObject(&s3.GetObjectInput{
		Bucket: aws.String(s.bucket),
		Key:    aws.String(key),
	})
	if err != nil {
		return "", err
	}
	defer result.Body.Close()

	content, err := ioutil.ReadAll(result.Body)
	if err != nil {
		return "", err
	}

	return string(content), nil
}

func (s *S3Client) ListJobArtifacts(jobID string) (map[string]string, error) {
	artifacts := make(map[string]string)

	// List of expected files
	files := []string{
		"Dockerfile",
		"training_wrapper.py",
		"app.py",
		"requirements.txt",
		"analysis.json",
	}

	prefix := fmt.Sprintf("jobs/%s/", jobID)

	for _, filename := range files {
		key := prefix + filename
		content, err := s.GetFileContent(key)
		if err == nil {
			artifacts[filename] = content
		}
	}

	return artifacts, nil
}

func (s *S3Client) DownloadFile(jobID, filename string) ([]byte, error) {
	key := fmt.Sprintf("jobs/%s/%s", jobID, filename)

	result, err := s.client.GetObject(&s3.GetObjectInput{
		Bucket: aws.String(s.bucket),
		Key:    aws.String(key),
	})
	if err != nil {
		return nil, err
	}
	defer result.Body.Close()

	return ioutil.ReadAll(result.Body)
}
