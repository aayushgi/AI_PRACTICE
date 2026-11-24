import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';

function MessageList({ messages, isStreaming, messagesEndRef, onScroll, isLoadingMore, scrollContainerRef }) {
  if (messages.length === 0 && !isLoadingMore) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-600/20 flex items-center justify-center mb-6">
          <svg className="w-10 h-10 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-gray-200 mb-2">Start a Conversation</h2>
        <p className="text-gray-400 max-w-sm">
          Type a message below to begin chatting with the AI assistant.
        </p>
      </div>
    );
  }

  return (
    <div
      className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth"
      onScroll={onScroll}
      ref={scrollContainerRef}
      style={{ scrollBehavior: 'smooth' }}
    >
      {isLoadingMore && (
        <div className="flex items-center justify-center gap-2 py-4 animate-fade-in">
          <div className="flex gap-1">
            <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
          <span className="text-gray-400 text-sm ml-2">Loading older messages...</span>
        </div>
      )}
      {messages.map((message, index) => {
        const isLastMessage = index === messages.length - 1;
        const isAssistantStreaming = isStreaming && isLastMessage && message.role === 'assistant';

        // Skip rendering empty assistant message while streaming - TypingIndicator handles it
        if (isAssistantStreaming && message.content === '') {
          return null;
        }

        return (
          <MessageBubble
            key={message.id}
            message={message}
            isLast={isLastMessage}
            isStreaming={isAssistantStreaming}
          />
        );
      })}
      {isStreaming && messages.length > 0 && messages[messages.length - 1].content === '' && (
        <TypingIndicator />
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}

export default MessageList;
