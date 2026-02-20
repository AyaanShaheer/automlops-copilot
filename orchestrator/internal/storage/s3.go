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

	prefix := fmt.Sprintf("jobs/%s/", jobID)

	// Use ListObjectsV2 to discover ALL files dynamically (including ci/ subfolder)
	result, err := s.client.ListObjectsV2(&s3.ListObjectsV2Input{
		Bucket: aws.String(s.bucket),
		Prefix: aws.String(prefix),
	})
	if err != nil {
		return nil, err
	}

	for _, obj := range result.Contents {
		key := aws.StringValue(obj.Key)
		// Strip the job prefix to get the relative filename (e.g. "ci/github-actions.yml")
		relPath := key[len(prefix):]
		if relPath == "" {
			continue
		}
		content, err := s.GetFileContent(key)
		if err == nil {
			artifacts[relPath] = content
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
