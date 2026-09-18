
export default function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center min-h-screen" style={{background:'#020617'}}>
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 border-4 border-slate-700 border-t-cyan-400 rounded-full animate-spin" />
        <p className="text-slate-400 text-sm font-medium">Loading AquaGuard AI...</p>
      </div>
    </div>
  );
}
