import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function MessageBubble({ message, isLast, isStreaming }) {
  const isUser = message.role === 'user';

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}
    >
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${isUser
          ? 'user-bubble text-white'
          : message.isError
            ? 'bg-red-500/20 border border-red-500/30 text-red-200'
            : 'assistant-bubble text-gray-100'
          }`}
      >
        {/* Avatar for assistant */}
        {!isUser && (
          <div className="flex items-center gap-2 mb-2 pb-2 border-b border-white/10">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <span className="text-xs text-gray-400 font-medium">Assistant</span>
          </div>
        )}

        {/* Message content */}
        <div className={`text-sm leading-relaxed break-words ${isUser ? 'whitespace-pre-wrap' : 'markdown-content'}`}>
          {isUser ? (
            message.content
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          )}
          {isStreaming && isLast && (
            <span className="inline-block w-2 h-4 bg-indigo-400 ml-1 animate-pulse rounded-sm"></span>
          )}
        </div>
      </div>
    </div>
  );
}

export default MessageBubble;
