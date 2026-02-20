import axios from 'axios';

const isServer = typeof window === 'undefined';
const API_URL = isServer
  ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080')
  : '';

export interface Job {
  id: string;
  repo_url: string;
  status: string;
  error_message?: string;
  model_s3_path?: string;
  api_endpoint?: string;
  frameworks?: string;
  python_files: number;
  notebooks: number;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface CreateJobRequest {
  repo_url: string;
}

export interface JobResponse {
  job: Job;
  message?: string;
}

export interface ListJobsResponse {
  jobs: Job[];
  total: number;
}

export interface ArtifactsResponse {
  job_id: string;
  artifacts: Record<string, string>;
}

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const jobsApi = {
  createJob: async (data: CreateJobRequest): Promise<JobResponse> => {
    const response = await api.post<JobResponse>('/api/jobs', data);
    return response.data;
  },

  getJob: async (id: string): Promise<JobResponse> => {
    const response = await api.get<JobResponse>(`/api/jobs/${id}`);
    return response.data;
  },

  listJobs: async (): Promise<ListJobsResponse> => {
    const response = await api.get<ListJobsResponse>('/api/jobs');
    return response.data;
  },

  deleteJob: async (id: string): Promise<void> => {
    await api.delete(`/api/jobs/${id}`);
  },

  getArtifacts: async (id: string): Promise<ArtifactsResponse> => {
    const response = await api.get<ArtifactsResponse>(`/api/jobs/${id}/artifacts`);
    return response.data;
  },

  downloadArtifact: (id: string, filename: string): string => {
    return `${API_URL}/api/jobs/${id}/artifacts/${filename}`;
  },
};
