import { useState, useEffect, useRef } from 'react';
import ChatContainer from './components/ChatContainer';
import { fetchModels, checkHealth } from './services/api';

function App() {
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [currentChatId, setCurrentChatId] = useState('default');

  useEffect(() => {
    async function init() {
      try {
        const health = await checkHealth();
        setIsConnected(health.ollama_connected);

        if (health.ollama_connected) {
          const availableModels = await fetchModels();
          setModels(availableModels);
          if (availableModels.length > 0) {
            setSelectedModel(availableModels[0].name);
          }
        }
      } catch (error) {
        console.error('Failed to initialize:', error);
        setIsConnected(false);
      } finally {
        setIsLoading(false);
      }
    }
    init();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">Connecting to Ollama...</p>
        </div>
      </div>
    );
  }

  if (!isConnected) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="glass rounded-2xl p-8 max-w-md text-center">
          <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold mb-2">Connection Failed</h2>
          <p className="text-gray-400 mb-4">
            Could not connect to Ollama. Please make sure:
          </p>
          <ul className="text-left text-gray-400 text-sm space-y-2 mb-6">
            <li className="flex items-start gap-2">
              <span className="text-indigo-400">•</span>
              Ollama is running on localhost:11434
            </li>
            <li className="flex items-start gap-2">
              <span className="text-indigo-400">•</span>
              Backend server is running on localhost:8000
            </li>
            <li className="flex items-start gap-2">
              <span className="text-indigo-400">•</span>
              You have at least one model installed
            </li>
          </ul>
          <button
            onClick={() => window.location.reload()}
            className="btn-primary px-6 py-2 rounded-lg text-white font-medium"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Fixed background layer - won't affect scroll */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="bg-orb bg-orb-1"></div>
        <div className="bg-orb bg-orb-2"></div>
        <div className="bg-orb bg-orb-3"></div>
      </div>

      {/* Main content layer */}
      <div className="relative h-full">
        <ChatContainer
          models={models}
          selectedModel={selectedModel}
          onModelChange={setSelectedModel}
          chatId={currentChatId}
          onChatChange={setCurrentChatId}
        />
      </div>
    </>
  );
}

export default App;
