const API_BASE_URL = 'http://localhost:8000';

export async function fetchModels() {
  const response = await fetch(`${API_BASE_URL}/api/models`);
  if (!response.ok) {
    throw new Error('Failed to fetch models');
  }
  const data = await response.json();
  return data.models;
}

// Chat Sessions API
export async function fetchChatSessions() {
  const response = await fetch(`${API_BASE_URL}/api/chat/sessions`);
  if (!response.ok) {
    throw new Error('Failed to fetch chat sessions');
  }
  const data = await response.json();
  return data.sessions;
}

export async function createNewChat() {
  const response = await fetch(`${API_BASE_URL}/api/chat/new`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error('Failed to create new chat');
  }
  return await response.json();
}

export async function deleteChat(chatId) {
  const response = await fetch(`${API_BASE_URL}/api/chat/delete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: chatId }),
  });
  return await response.json();
}

export async function renameChat(chatId, newTitle) {
  const response = await fetch(`${API_BASE_URL}/api/chat/rename`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: chatId, new_title: newTitle }),
  });
  return await response.json();
}

export async function fetchMessages(chatId = 'default', cursorId = null, limit = 20) {
  const params = new URLSearchParams({
    chat_id: chatId,
    limit: limit.toString()
  });
  if (cursorId) {
    params.append('cursor_id', cursorId.toString());
  }

  const response = await fetch(`${API_BASE_URL}/api/messages?${params}`);
  if (!response.ok) {
    throw new Error('Failed to fetch messages');
  }
  return await response.json();
}

export async function* streamChat(model, message, chatId = 'default', think = false, signal = null) {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ model, message, chat_id: chatId, think }),
    signal,
  });

  if (!response.ok) {
    throw new Error('Failed to send message');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.content) {
              yield data.content;
            }
            if (data.done) {
              return;
            }
            if (data.error) {
              throw new Error(data.error);
            }
          } catch (e) {
            // Skip invalid JSON
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export async function stopChat(prompt, partialResponse, chatId = 'default') {
  try {
    const response = await fetch(`${API_BASE_URL}/api/stop`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt, partial_response: partialResponse, chat_id: chatId }),
    });
    return await response.json();
  } catch (e) {
    console.error('Failed to save partial history:', e);
    return { success: false };
  }
}

export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    const data = await response.json();
    return data;
  } catch {
    return { status: 'error', ollama_connected: false };
  }
}

