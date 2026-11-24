function ModelSelector({ models, selectedModel, onChange, disabled }) {
  return (
    <div className="relative">
      <select
        value={selectedModel}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="appearance-none bg-white/5 border border-white/10 rounded-lg px-4 py-2 pr-8 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:bg-white/10"
      >
        {models.map((model) => (
          <option key={model.name} value={model.name} className="bg-gray-900 text-white">
            {model.name}
          </option>
        ))}
      </select>
      <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>
  );
}

export default ModelSelector;
