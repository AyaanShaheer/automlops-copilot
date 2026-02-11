'use client';

import { useState, useEffect } from 'react';
import { jobsApi, Job, ArtifactsResponse } from '@/lib/api';
import { Plus, RefreshCw, ExternalLink, Copy, Check, Trash2, FileCode, Eye } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import CodeViewer from '@/components/CodeViewer';

export default function Home() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [repoUrl, setRepoUrl] = useState('');
  const [creating, setCreating] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [viewingArtifacts, setViewingArtifacts] = useState<ArtifactsResponse | null>(null);
  const [loadingArtifacts, setLoadingArtifacts] = useState<string | null>(null);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const response = await jobsApi.listJobs();
      setJobs(response.jobs || []);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;

    try {
      setCreating(true);
      await jobsApi.createJob({ repo_url: repoUrl });
      setRepoUrl('');
      fetchJobs();
    } catch (error) {
      console.error('Failed to create job:', error);
      alert('Failed to create job');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this job?')) return;
    try {
      await jobsApi.deleteJob(id);
      fetchJobs();
    } catch (error) {
      console.error('Failed to delete job:', error);
    }
  };

  const handleViewCode = async (jobId: string) => {
    try {
      setLoadingArtifacts(jobId);
      const artifacts = await jobsApi.getArtifacts(jobId);
      setViewingArtifacts(artifacts);
    } catch (error) {
      console.error('Failed to fetch artifacts:', error);
      alert('Failed to load artifacts. Make sure the job has completed.');
    } finally {
      setLoadingArtifacts(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500';
      case 'failed': return 'bg-red-500';
      case 'analyzing': return 'bg-blue-500 animate-pulse';
      case 'building': return 'bg-yellow-500 animate-pulse';
      case 'training': return 'bg-purple-500 animate-pulse';
      case 'deploying': return 'bg-indigo-500 animate-pulse';
      default: return 'bg-gray-500';
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="bg-gray-800/50 backdrop-blur-sm border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                <span className="text-4xl">🚀</span>
                AutoMLOps Copilot
              </h1>
              <p className="text-gray-400 mt-1">Transform any ML repo into production-ready API</p>
            </div>
            <button
              onClick={fetchJobs}
              disabled={loading}
              className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-white transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700 mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">Create New Job</h2>
          <form onSubmit={handleCreateJob} className="flex gap-3">
            <input
              type="url"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/username/ml-repo"
              className="flex-1 px-4 py-3 rounded-lg bg-gray-700 border border-gray-600 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
            <button
              type="submit"
              disabled={creating}
              className="px-6 py-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium flex items-center gap-2 transition-colors disabled:opacity-50"
            >
              <Plus className="w-5 h-5" />
              {creating ? 'Creating...' : 'Create Job'}
            </button>
          </form>
        </div>

        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-white mb-4">Recent Jobs ({jobs.length})</h2>
          
          {jobs.length === 0 ? (
            <div className="bg-gray-800/30 rounded-xl p-12 text-center border border-gray-700">
              <p className="text-gray-400 text-lg">No jobs yet. Create one to get started! 🎯</p>
            </div>
          ) : (
            jobs.map((job) => (
              <div key={job.id} className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700 hover:border-gray-600 transition-colors">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`w-3 h-3 rounded-full ${getStatusColor(job.status)}`} />
                      <span className="text-white font-semibold text-lg capitalize">{job.status}</span>
                    </div>
                    <a href={job.repo_url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 flex items-center gap-2 group">
                      {job.repo_url}
                      <ExternalLink className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </a>
                  </div>
                  <div className="flex items-center gap-2">
                    <p className="text-gray-400 text-sm">{formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}</p>
                    
                    {job.status === 'completed' && (
                      <button
                        onClick={() => handleViewCode(job.id)}
                        disabled={loadingArtifacts === job.id}
                        className="p-2 rounded-lg bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 transition-colors disabled:opacity-50"
                        title="View generated code"
                      >
                        {loadingArtifacts === job.id ? (
                          <RefreshCw className="w-4 h-4 animate-spin" />
                        ) : (
                          <Eye className="w-4 h-4" />
                        )}
                      </button>
                    )}
                    
                    <button onClick={() => handleDelete(job.id)} className="p-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-400 transition-colors">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                  <div className="bg-gray-700/50 rounded-lg p-3">
                    <p className="text-gray-400 text-sm mb-1">Python Files</p>
                    <p className="text-white font-semibold text-xl">{job.python_files}</p>
                  </div>
                  <div className="bg-gray-700/50 rounded-lg p-3">
                    <p className="text-gray-400 text-sm mb-1">Notebooks</p>
                    <p className="text-white font-semibold text-xl">{job.notebooks}</p>
                  </div>
                  <div className="bg-gray-700/50 rounded-lg p-3">
                    <p className="text-gray-400 text-sm mb-1">Frameworks</p>
                    <p className="text-white font-semibold">{job.frameworks || 'N/A'}</p>
                  </div>
                </div>

                {job.status === 'completed' && job.api_endpoint && (
                  <div className="mt-4 p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
                    <p className="text-green-400 text-sm mb-2 font-medium">🎉 API Endpoint Ready</p>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 text-green-300 bg-gray-900/50 px-3 py-2 rounded text-sm">{job.api_endpoint}</code>
                      <button onClick={() => copyToClipboard(job.api_endpoint!, job.id)} className="p-2 rounded bg-green-600/20 hover:bg-green-600/30 text-green-400 transition-colors">
                        {copiedId === job.id ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                )}

                {job.status === 'failed' && job.error_message && (
                  <div className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                    <p className="text-red-400 text-sm font-medium">❌ Error</p>
                    <p className="text-red-300 text-sm mt-1">{job.error_message}</p>
                  </div>
                )}

                <div className="mt-4 pt-4 border-t border-gray-700">
                  <p className="text-gray-500 text-xs font-mono">Job ID: {job.id}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Code Viewer Modal */}
      {viewingArtifacts && (
        <CodeViewer
          artifacts={viewingArtifacts.artifacts}
          jobId={viewingArtifacts.job_id}
          onClose={() => setViewingArtifacts(null)}
        />
      )}
    </div>
  );
}
