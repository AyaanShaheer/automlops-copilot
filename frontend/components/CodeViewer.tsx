'use client';

import { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check, Download, X, PackageOpen } from 'lucide-react';

interface CodeViewerProps {
  artifacts: Record<string, string>;
  jobId: string;
  onClose: () => void;
}

function getLanguage(filename: string): string {
  if (filename.endsWith('.py')) return 'python';
  if (filename.endsWith('.json')) return 'json';
  if (filename.endsWith('.yml') || filename.endsWith('.yaml')) return 'yaml';
  if (filename.endsWith('.txt')) return 'text';
  if (filename === 'Dockerfile') return 'docker';
  if (filename.includes('Jenkinsfile')) return 'groovy';
  return 'text';
}

function getIcon(filename: string): string {
  if (filename === 'Dockerfile') return '🐳';
  if (filename.includes('training')) return '🚂';
  if (filename === 'app.py') return '⚡';
  if (filename.endsWith('requirements.txt')) return '📦';
  if (filename.endsWith('.json')) return '📊';
  if (filename.includes('github')) return '🐙';
  if (filename.includes('gitlab')) return '🦊';
  if (filename.includes('jenkins')) return '🏗️';
  if (filename.endsWith('.yml') || filename.endsWith('.yaml')) return '⚙️';
  return '📄';
}

export default function CodeViewer({ artifacts, jobId, onClose }: CodeViewerProps) {
  const [copiedFile, setCopiedFile] = useState<string | null>(null);

  const tabs = Object.keys(artifacts).map((name) => ({
    name,
    language: getLanguage(name),
    icon: getIcon(name),
  }));

  const [activeTab, setActiveTab] = useState<string>(tabs[0]?.name || '');

  const copyToClipboard = (content: string, filename: string) => {
    navigator.clipboard.writeText(content);
    setCopiedFile(filename);
    setTimeout(() => setCopiedFile(null), 2000);
  };

  const downloadFile = (filename: string) => {
    const encodedPath = encodeURIComponent(filename);
    window.open(`/api/jobs/${jobId}/artifacts/${encodedPath}`, '_blank');
  };

  const downloadAllAsZip = () => {
    window.open(`/api/jobs/${jobId}/artifacts-zip`, '_blank');
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gray-900 rounded-xl w-full max-w-6xl max-h-[90vh] flex flex-col border border-gray-700">
        {/* Header */}
        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">Generated Artifacts</h2>
            <p className="text-gray-400 text-sm mt-1">AI-generated code for your ML project</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={downloadAllAsZip}
              className="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white font-medium flex items-center gap-2 transition-colors"
            >
              <PackageOpen className="w-4 h-4" />
              Download All (ZIP)
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 p-4 border-b border-gray-700 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.name}
              onClick={() => setActiveTab(tab.name)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 whitespace-nowrap ${activeTab === tab.name
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
                }`}
            >
              <span>{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </div>

        {/* Code Display */}
        <div className="flex-1 overflow-auto p-4">
          {artifacts[activeTab] ? (
            <div className="relative">
              {/* Action Buttons */}
              <div className="absolute top-2 right-2 flex gap-2 z-10">
                <button
                  onClick={() => copyToClipboard(artifacts[activeTab]!, activeTab)}
                  className="p-2 rounded-lg bg-gray-800/90 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors backdrop-blur-sm"
                  title="Copy to clipboard"
                >
                  {copiedFile === activeTab ? (
                    <Check className="w-4 h-4 text-green-400" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>
                <button
                  onClick={() => downloadFile(activeTab)}
                  className="p-2 rounded-lg bg-gray-800/90 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors backdrop-blur-sm"
                  title="Download file"
                >
                  <Download className="w-4 h-4" />
                </button>
              </div>

              {/* Code */}
              <SyntaxHighlighter
                language={tabs.find((t) => t.name === activeTab)?.language || 'text'}
                style={vscDarkPlus}
                customStyle={{
                  margin: 0,
                  borderRadius: '0.5rem',
                  fontSize: '0.875rem',
                  padding: '1.5rem',
                }}
                showLineNumbers
              >
                {artifacts[activeTab] || ''}
              </SyntaxHighlighter>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400">
              No content available
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
