import { Construction } from 'lucide-react';

export default function VideoTestingPage() {
  return (
    <div className="flex flex-col items-center justify-center h-full p-12 text-center">
      <Construction size={48} className="text-cyan-400 mb-4" />
      <h1 className="text-xl font-bold text-white mb-2">Video Testing</h1>
      <p className="text-sm" style={{ color: '#64748b' }}>
        Upload and test videos with AI models
      </p>
      <p
        className="text-xs mt-4 px-4 py-2 rounded-lg"
        style={{
          background: 'rgba(0,181,212,0.08)',
          color: '#22d3ee',
          border: '1px solid rgba(0,181,212,0.2)',
        }}
      >
        Phase 9+ — This page will be implemented in the next development phase.
      </p>
    </div>
  );
}