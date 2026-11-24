import { useState, useEffect, useRef } from 'react';
import { fetchChatSessions, createNewChat, deleteChat, renameChat } from '../services/api';

function Sidebar({ isOpen, onClose, currentChatId, onChatSelect, onNewChat }) {
  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [menuOpen, setMenuOpen] = useState(null); // chat_id of open menu
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const menuRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      loadSessions();
    }
  }, [isOpen]);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const loadSessions = async () => {
    setIsLoading(true);
    try {
      const data = await fetchChatSessions();
      setSessions(data);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = async () => {
    try {
      const result = await createNewChat();
      await loadSessions();
      onNewChat(result.chat_id);
      onClose();
    } catch (error) {
      console.error('Failed to create new chat:', error);
    }
  };

  const handleDeleteChat = async (chatId) => {
    setMenuOpen(null);
    if (confirm('Delete this chat?')) {
      try {
        await deleteChat(chatId);
        await loadSessions();
        if (chatId === currentChatId) {
          onNewChat('default');
        }
      } catch (error) {
        console.error('Failed to delete chat:', error);
      }
    }
  };

  const handleRenameStart = (chatId, currentTitle) => {
    setMenuOpen(null);
    setEditingId(chatId);
    setEditTitle(currentTitle || '');
  };

  const handleRenameSubmit = async (chatId) => {
    if (editTitle.trim()) {
      try {
        await renameChat(chatId, editTitle.trim());
        await loadSessions();
      } catch (error) {
        console.error('Failed to rename chat:', error);
      }
    }
    setEditingId(null);
    setEditTitle('');
  };

  const handleChatSelect = (chatId) => {
    if (editingId) return; // Don't select while editing
    onChatSelect(chatId);
    onClose();
  };

  return (
    <>
      {/* Overlay */}
      <div
        className={`fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity duration-300 ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
          }`}
        onClick={onClose}
      />

      {/* Sidebar */}
      <div
        className={`fixed left-0 top-0 h-full w-72 glass z-50 transform transition-transform duration-300 ease-out border-r border-white/10 ${isOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-4 border-b border-white/10 flex items-center justify-between">
            <h2 className="text-lg font-semibold gradient-text">Chats</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* New Chat Button */}
          <div className="p-3">
            <button
              onClick={handleNewChat}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 rounded-xl text-white font-medium transition-all shadow-lg shadow-indigo-500/20"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Chat
            </button>
          </div>

          {/* Chat List */}
          <div className="flex-1 overflow-y-auto p-3 space-y-1">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : sessions.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No chats yet
              </div>
            ) : (
              sessions.map((session) => (
                <div
                  key={session.chat_id}
                  onClick={() => handleChatSelect(session.chat_id)}
                  className={`group relative flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all ${currentChatId === session.chat_id
                      ? 'bg-gradient-to-r from-indigo-600/20 to-purple-600/20 border border-indigo-500/30'
                      : 'hover:bg-white/5'
                    }`}
                >
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500/30 to-purple-600/30 flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>

                  {editingId === session.chat_id ? (
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onBlur={() => handleRenameSubmit(session.chat_id)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleRenameSubmit(session.chat_id);
                        if (e.key === 'Escape') { setEditingId(null); setEditTitle(''); }
                      }}
                      autoFocus
                      className="flex-1 bg-white/10 border border-indigo-500/50 rounded-lg px-2 py-1 text-sm text-white outline-none focus:border-indigo-500"
                      onClick={(e) => e.stopPropagation()}
                    />
                  ) : (
                    <span className="flex-1 text-sm text-gray-300 truncate">
                      {session.title || 'New Chat'}
                    </span>
                  )}

                  {/* 3-dot menu button */}
                  {session.chat_id !== 'default' && !editingId && (
                    <div className="relative" ref={menuOpen === session.chat_id ? menuRef : null}>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setMenuOpen(menuOpen === session.chat_id ? null : session.chat_id);
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-white/10 rounded-lg transition-all"
                      >
                        <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                          <circle cx="12" cy="5" r="2" />
                          <circle cx="12" cy="12" r="2" />
                          <circle cx="12" cy="19" r="2" />
                        </svg>
                      </button>

                      {/* Dropdown Menu */}
                      {menuOpen === session.chat_id && (
                        <div className="absolute right-0 top-8 w-32 bg-gray-800 border border-white/10 rounded-xl shadow-xl overflow-hidden z-50 animate-fade-in">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRenameStart(session.chat_id, session.title);
                            }}
                            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-300 hover:bg-white/10 transition-colors"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                            Rename
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteChat(session.chat_id);
                            }}
                            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                            Delete
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </>
  );
}

export default Sidebar;
