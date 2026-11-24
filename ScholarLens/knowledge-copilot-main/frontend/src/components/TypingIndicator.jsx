function TypingIndicator() {
  return (
    <div className="flex justify-start animate-fade-in">
      <div className="assistant-bubble rounded-2xl px-4 py-3">
        <div className="flex items-center gap-2 mb-2 pb-2 border-b border-white/10">
          <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <span className="text-xs text-gray-400 font-medium">Assistant</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 bg-indigo-400 rounded-full typing-dot"></div>
          <div className="w-2 h-2 bg-indigo-400 rounded-full typing-dot"></div>
          <div className="w-2 h-2 bg-indigo-400 rounded-full typing-dot"></div>
        </div>
      </div>
    </div>
  );
}

export default TypingIndicator;
