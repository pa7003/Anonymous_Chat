const btnStart = document.getElementById('btn-start');
const btnCancel = document.getElementById('btn-cancel');
const btnSkip = document.getElementById('btn-skip');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');

const landingView = document.getElementById('landing-view');
const searchingView = document.getElementById('searching-view');
const chatView = document.getElementById('chat-view');

const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');

let ws = null;
const WS_URL = "ws://localhost:8000/ws";

// UI Functions
function showView(viewId) {
    [landingView, searchingView, chatView].forEach(v => {
        if (v.id === viewId) {
            v.classList.remove('hidden', 'view-fade-out');
            v.classList.add('view-fade-in');
        } else {
            v.classList.add('hidden', 'view-fade-out');
            v.classList.remove('view-fade-in');
        }
    });
}

function updateStatus(state) {
    statusDot.className = 'w-3 h-3 rounded-full mr-2 transition-colors duration-300 ';
    switch (state) {
        case 'disconnected':
            statusDot.classList.add('bg-red-500');
            statusText.textContent = 'Disconnected';
            break;
        case 'searching':
            statusDot.classList.add('bg-yellow-500', 'animate-pulse');
            statusText.textContent = 'Searching...';
            break;
        case 'connected':
            statusDot.classList.add('bg-green-500');
            statusText.textContent = 'Connected to Stranger';
            break;
    }
}

function appendMessage(text, type) {
    const msgDiv = document.createElement('div');

    if (type === 'system') {
        msgDiv.className = 'message-system';
        const span = document.createElement('span');
        span.textContent = text;
        msgDiv.appendChild(span);
    } else {
        msgDiv.className = `message-bubble ${type === 'sent' ? 'message-sent' : 'message-received'}`;
        msgDiv.textContent = text;
    }

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function clearChat() {
    chatMessages.innerHTML = `
        <div class="text-center text-xs text-gray-500 my-4 uppercase tracking-wider font-semibold">
            <span class="bg-gray-800 px-3 py-1 rounded-full border border-gray-700">Chat Started</span>
        </div>
    `;
}

// WebSocket Logic
function connect() {
    showView('searching-view');
    updateStatus('searching');

    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
        console.log("Connected to server");
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        switch (data.type) {
            case 'connected':
                // Still searching, but server knows us
                break;
            case 'match_found':
                showView('chat-view');
                updateStatus('connected');
                clearChat();
                appendMessage(data.message, 'system');
                chatInput.focus();
                break;
            case 'chat_message':
                appendMessage(data.content, 'received');
                break;
            case 'partner_disconnected':
                appendMessage(data.message, 'system');
                updateStatus('searching');
                // Auto transition back to searching after a brief pause
                setTimeout(() => {
                    showView('searching-view');
                }, 2000);
                break;
        }
    };

    ws.onclose = () => {
        updateStatus('disconnected');
        showView('landing-view');
        ws = null;
    };

    ws.onerror = (error) => {
        console.error("WebSocket Error: ", error);
        ws.close();
    };
}

// Event Listeners
btnStart.addEventListener('click', () => {
    connect();
});

btnCancel.addEventListener('click', () => {
    if (ws) {
        ws.close(); // Cleanly close connection
    }
    showView('landing-view');
    updateStatus('disconnected');
});

btnSkip.addEventListener('click', () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'skip' }));
        updateStatus('searching');
        showView('searching-view');
    }
});

chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;

    // Send to server
    ws.send(JSON.stringify({
        type: 'chat_message',
        content: text
    }));

    // Display locally
    appendMessage(text, 'sent');
    chatInput.value = '';
    chatInput.focus();
});
