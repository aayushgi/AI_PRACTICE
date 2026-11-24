import { useState, useRef, useEffect, useCallback } from 'react';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import ModelSelector from './ModelSelector';
import Sidebar from './Sidebar';
import { streamChat, stopChat, fetchMessages } from '../services/api';

function ChatContainer({ models, selectedModel, onModelChange, chatId, onChatChange }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [think, setThink] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [nextCursor, setNextCursor] = useState(null);
  const [initialLoadDone, setInitialLoadDone] = useState(false);

  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const abortControllerRef = useRef(null);
  const currentPromptRef = useRef('');
  const currentResponseRef = useRef('');
  const [canLoadMore, setCanLoadMore] = useState(false); // Prevent auto-load on initial render

  // Load initial messages on mount or when chatId changes
  useEffect(() => {
    const loadInitialMessages = async () => {
      setMessages([]);
      setInitialLoadDone(false);
      setCanLoadMore(false);
      setHasMore(true);
      setNextCursor(null);

      try {
        const data = await fetchMessages(chatId, null, 20);
        setMessages(data.messages);
        setHasMore(data.has_more);
        setNextCursor(data.next_cursor);
        setInitialLoadDone(true);

        // Wait before enabling scroll-triggered loading (prevent immediate auto-load)
        setTimeout(() => {
          setCanLoadMore(true);
        }, 500);
      } catch (error) {
        console.error('Failed to load messages:', error);
        setInitialLoadDone(true);
        setCanLoadMore(true);
      }
    };
    loadInitialMessages();
  }, [chatId]);

  // Ref to track scroll container for position preservation
  const scrollContainerRef = useRef(null);
  const prevScrollHeightRef = useRef(0);
  const prevScrollTopRef = useRef(0);

  // Load more messages when scrolling to top
  const loadMoreMessages = useCallback(async () => {
    if (isLoadingMore || !hasMore || !nextCursor) return;

    // Save current scroll position before loading
    if (scrollContainerRef.current) {
      prevScrollHeightRef.current = scrollContainerRef.current.scrollHeight;
      prevScrollTopRef.current = scrollContainerRef.current.scrollTop;
    }

    setIsLoadingMore(true);
    try {
      const data = await fetchMessages(chatId, nextCursor, 20);
      if (data.messages.length > 0) {
        // Prepend older messages
        setMessages(prev => [...data.messages, ...prev]);
        setHasMore(data.has_more);
        setNextCursor(data.next_cursor);
      }
    } catch (error) {
      console.error('Failed to load more messages:', error);
    } finally {
      setIsLoadingMore(false);
    }
  }, [isLoadingMore, hasMore, nextCursor, chatId]);

  // Restore scroll position after loading older messages (runs synchronously after DOM update)
  useEffect(() => {
    if (scrollContainerRef.current && prevScrollHeightRef.current > 0) {
      // Use requestAnimationFrame for smoother transition
      requestAnimationFrame(() => {
        if (scrollContainerRef.current) {
          const newScrollHeight = scrollContainerRef.current.scrollHeight;
          const heightDiff = newScrollHeight - prevScrollHeightRef.current;

          // Smoothly adjust scroll position
          scrollContainerRef.current.scrollTo({
            top: prevScrollTopRef.current + heightDiff,
            behavior: 'instant' // Use 'instant' for immediate position, then it feels natural
          });

          prevScrollHeightRef.current = 0;
          prevScrollTopRef.current = 0;
        }
      });
    }
  }, [messages]);

  // Scroll handler for infinite scroll - only trigger if user has scrolled
  const handleScroll = useCallback((e) => {
    if (!initialLoadDone || !canLoadMore) return; // Don't load during initial setup or cooldown

    const { scrollTop, scrollHeight, clientHeight } = e.target;
    // Only load more if user is near top AND there's content to scroll (not just initial view)
    if (scrollTop < 100 && hasMore && !isLoadingMore && scrollHeight > clientHeight) {
      loadMoreMessages();
    }
  }, [hasMore, isLoadingMore, loadMoreMessages, initialLoadDone, canLoadMore]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Track if we just finished loading older messages (to prevent scroll to bottom)
  const wasLoadingMoreRef = useRef(false);

  useEffect(() => {
    wasLoadingMoreRef.current = isLoadingMore;
  }, [isLoadingMore]);

  // Scroll to bottom only on initial load (scroll after short delay for render)
  useEffect(() => {
    if (initialLoadDone && messages.length > 0 && !wasLoadingMoreRef.current) {
      // Only scroll on initial load, not when loading more
      const timeoutId = setTimeout(() => {
        if (!wasLoadingMoreRef.current) {
          scrollToBottom();
        }
      }, 100);
      return () => clearTimeout(timeoutId);
    }
  }, [initialLoadDone]); // Only run on initial load

  const handleSendMessage = async (content) => {
    if (!content.trim() || isStreaming) return;

    const trimmedContent = content.trim();
    currentPromptRef.current = trimmedContent;
    currentResponseRef.current = '';

    // Add user message
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: trimmedContent,
    };
    setMessages((prev) => [...prev, userMessage]);

    // Scroll to bottom when user sends a message
    setTimeout(() => scrollToBottom(), 50);

    // Add empty assistant message for streaming
    const assistantMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
    };
    setMessages((prev) => [...prev, assistantMessage]);
    setIsStreaming(true);

    // Create abort controller for this request
    abortControllerRef.current = new AbortController();

    try {
      let fullResponse = '';
      for await (const chunk of streamChat(
        selectedModel,
        trimmedContent,
        chatId,
        think,
        abortControllerRef.current.signal
      )) {
        fullResponse += chunk;
        currentResponseRef.current = fullResponse;
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content: fullResponse,
          };
          return updated;
        });
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        // User stopped the generation - don't show error
        console.log('Generation stopped by user');
      } else {
        console.error('Streaming error:', error);
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content: currentResponseRef.current || 'Sorry, an error occurred while generating the response.',
            isError: !currentResponseRef.current,
          };
          return updated;
        });
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const handleStopGeneration = async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();

      // Save partial history to backend
      if (currentPromptRef.current && currentResponseRef.current) {
        await stopChat(currentPromptRef.current, currentResponseRef.current, chatId);
      }
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <>
      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        currentChatId={chatId}
        onChatSelect={onChatChange}
        onNewChat={onChatChange}
      />

      <div className="flex flex-col h-full max-w-4xl mx-auto p-4">
        {/* Header */}
        <header className="glass rounded-2xl p-4 mb-4 flex items-center justify-between animate-fade-in">
          <div className="flex items-center gap-3">
            {/* Hamburger Menu Button */}
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors"
              title="Open chats"
            >
              <svg className="w-6 h-6 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold gradient-text">Knowledge Copilot</h1>
              <p className="text-xs text-gray-400">Powered by Ollama</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <ModelSelector
              models={models}
              selectedModel={selectedModel}
              onChange={onModelChange}
              disabled={isStreaming}
            />
            <button
              onClick={clearChat}
              disabled={isStreaming || messages.length === 0}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Clear chat"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 glass rounded-2xl overflow-hidden flex flex-col">
          <MessageList
            messages={messages}
            isStreaming={isStreaming}
            messagesEndRef={messagesEndRef}
            onScroll={handleScroll}
            isLoadingMore={isLoadingMore}
            scrollContainerRef={scrollContainerRef}
          />

          {/* Input */}
          <ChatInput
            onSend={handleSendMessage}
            disabled={isStreaming}
            isStreaming={isStreaming}
            onStop={handleStopGeneration}
            think={think}
            onThinkToggle={() => setThink(!think)}
          />
        </div>
      </div>
    </>
  );
}

export default ChatContainer;
