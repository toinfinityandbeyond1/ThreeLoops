#!/bin/bash
# Create React frontend for Autonomous AI System

echo "Creating React frontend structure..."

# Create directories
mkdir -p web-ui/src/components
mkdir -p web-ui/src/pages
mkdir -p web-ui/src/styles
mkdir -p web-ui/public

# Create package.json
cat > web-ui/package.json << 'EOF'
{
  "name": "autonomous-ai-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "recharts": "^2.10.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "devDependencies": {
    "react-scripts": "5.0.1"
  }
}
EOF

# Create public/index.html
cat > web-ui/public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Autonomous AI System Web Interface" />
    <title>Autonomous AI System</title>
    <style>
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }

      body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
          'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
          sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
        color: #e0e0e0;
      }

      code {
        font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New', monospace;
      }

      html, body, #root {
        height: 100%;
        width: 100%;
      }
    </style>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
EOF

# Create src/index.js
cat > web-ui/src/index.js << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
EOF

# Create src/index.css
cat > web-ui/src/index.css << 'EOF'
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
  color: #e0e0e0;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}

* {
  box-sizing: border-box;
}
EOF

# Create src/App.js
cat > web-ui/src/App.js << 'EOF'
import React, { useState, useEffect } from 'react';
import ChatBox from './components/ChatBox';
import StatusPanel from './components/StatusPanel';
import LogStream from './components/LogStream';
import ControlPanel from './components/ControlPanel';
import './App.css';

function App() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const API_BASE = 'http://localhost:8000';

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/status`);
      const data = await response.json();
      setStatus(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>⚙️ Autonomous AI System</h1>
        <p>Always-on learning with resource awareness</p>
      </header>

      <main className="app-main">
        <div className="left-column">
          <ChatBox apiBase={API_BASE} onMessageSent={fetchStatus} />
          <ControlPanel apiBase={API_BASE} onStateChange={fetchStatus} />
        </div>

        <div className="right-column">
          <StatusPanel status={status} loading={loading} />
          <LogStream apiBase={API_BASE} />
        </div>
      </main>

      <footer className="app-footer">
        <p>Status: {status?.autonomy_running ? '🟢 Running' : '🔴 Stopped'} | Strain: {status?.resources?.strain?.toFixed(2)}%</p>
      </footer>
    </div>
  );
}

export default App;
EOF

# Create src/App.css
cat > web-ui/src/App.css << 'EOF'
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
  color: #e0e0e0;
}

.app-header {
  background: linear-gradient(90deg, #0d47a1 0%, #1565c0 100%);
  padding: 20px;
  text-align: center;
  border-bottom: 2px solid #0d47a1;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.app-header h1 {
  margin: 0;
  font-size: 28px;
  color: #ffffff;
}

.app-header p {
  margin: 5px 0 0 0;
  color: #b3e5fc;
  font-size: 14px;
}

.app-main {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  padding: 20px;
  flex: 1;
  overflow: auto;
}

.left-column, .right-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.app-footer {
  background: #1a1a1a;
  padding: 15px;
  text-align: center;
  border-top: 1px solid #333;
  font-size: 12px;
  color: #888;
}

@media (max-width: 1024px) {
  .app-main {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .app-main {
    padding: 10px;
    gap: 10px;
  }

  .app-header h1 {
    font-size: 20px;
  }
}
EOF

# Create component files
echo "Creating component files..."

# ChatBox.js
cat > web-ui/src/components/ChatBox.js << 'EOF'
import React, { useState } from 'react';
import './ChatBox.css';

function ChatBox({ apiBase, onMessageSent }) {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    setLoading(true);
    try {
      const response = await fetch(`${apiBase}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      });
      const data = await response.json();

      setMessages([...messages, 
        { role: 'user', text: message },
        { role: 'ai', text: data.response }
      ]);
      setMessage('');
      onMessageSent();
    } catch (error) {
      console.error('Error:', error);
      alert('Error sending message');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chatbox">
      <h2>💬 Chat</h2>
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <span className="role">{msg.role === 'user' ? 'You' : 'AI'}</span>
            <p>{msg.text}</p>
          </div>
        ))}
      </div>
      <form onSubmit={sendMessage} className="input-form">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type message..."
          disabled={loading}
        />
        <button type="submit" disabled={loading}>{loading ? 'Sending...' : 'Send'}</button>
      </form>
    </div>
  );
}

export default ChatBox;
EOF

# ChatBox.css
cat > web-ui/src/components/ChatBox.css << 'EOF'
.chatbox {
  background: #2a2a2a;
  border-radius: 8px;
  padding: 15px;
  display: flex;
  flex-direction: column;
  height: 100%;
  border: 1px solid #444;
}

.chatbox h2 {
  margin: 0 0 10px 0;
  font-size: 18px;
  color: #64b5f6;
}

.messages {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message {
  padding: 10px;
  border-radius: 8px;
  background: #333;
  border-left: 3px solid #64b5f6;
}

.message.user {
  border-left-color: #81c784;
  background: #1b5e20;
  margin-left: 20px;
}

.message.ai {
  border-left-color: #64b5f6;
  background: #0d47a1;
  margin-right: 20px;
}

.message .role {
  display: block;
  font-size: 12px;
  font-weight: bold;
  color: #aaa;
  margin-bottom: 5px;
}

.message p {
  margin: 0;
  font-size: 14px;
  line-height: 1.4;
}

.input-form {
  display: flex;
  gap: 10px;
}

.input-form input {
  flex: 1;
  padding: 10px;
  border: 1px solid #444;
  background: #333;
  color: #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
}

.input-form input:focus {
  outline: none;
  border-color: #64b5f6;
  background: #3a3a3a;
}

.input-form button {
  padding: 10px 20px;
  background: #0d47a1;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: background 0.2s;
}

.input-form button:hover:not(:disabled) {
  background: #1565c0;
}

.input-form button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
EOF

# StatusPanel.js
cat > web-ui/src/components/StatusPanel.js << 'EOF'
import React from 'react';
import './StatusPanel.css';

function StatusPanel({ status, loading }) {
  if (loading || !status) {
    return <div className="status-panel"><p>Loading...</p></div>;
  }

  const getStrainColor = (strain) => {
    if (strain < 0.3) return '#4caf50';
    if (strain < 0.6) return '#ff9800';
    return '#f44336';
  };

  return (
    <div className="status-panel">
      <h2>📊 System Status</h2>

      <div className="status-section">
        <h3>Resources</h3>
        <ProgressBar label="CPU" value={status.resources.cpu_percent} />
        <ProgressBar label="Memory" value={status.resources.memory_percent} />
        <ProgressBar label="Disk" value={status.resources.disk_percent} />
        <div className="status-item">
          <span>Strain:</span>
          <div className="strain-bar" style={{ backgroundColor: getStrainColor(status.resources.strain) }}>
            {(status.resources.strain * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      <div className="status-section">
        <h3>Memory</h3>
        <div className="status-item">
          <span>Fast:</span>
          <span>{status.memory.fast}</span>
        </div>
        <div className="status-item">
          <span>Medium:</span>
          <span>{status.memory.medium}</span>
        </div>
        <div className="status-item">
          <span>Long-term:</span>
          <span>{status.memory.long_term}</span>
        </div>
      </div>

      <div className="status-section">
        <h3>Autonomy</h3>
        <div className="status-item">
          <span>Running:</span>
          <span>{status.autonomy_running ? '🟢 Yes' : '🔴 No'}</span>
        </div>
        <div className="status-item">
          <span>Pending Tasks:</span>
          <span>{status.tasks.pending}</span>
        </div>
      </div>

      <div className="status-section">
        <h3>Phase Sync</h3>
        <div className="status-item">
          <span>Aligned:</span>
          <span>{status.phase.aligned ? '✓' : '✗'}</span>
        </div>
      </div>
    </div>
  );
}

function ProgressBar({ label, value }) {
  const getColor = (v) => {
    if (v < 50) return '#4caf50';
    if (v < 80) return '#ff9800';
    return '#f44336';
  };

  return (
    <div className="progress-item">
      <span>{label}</span>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${value}%`, backgroundColor: getColor(value) }}></div>
      </div>
      <span className="progress-value">{value.toFixed(1)}%</span>
    </div>
  );
}

export default StatusPanel;
EOF

# StatusPanel.css
cat > web-ui/src/components/StatusPanel.css << 'EOF'
.status-panel {
  background: #2a2a2a;
  border-radius: 8px;
  padding: 15px;
  border: 1px solid #444;
  overflow-y: auto;
}

.status-panel h2 {
  margin: 0 0 15px 0;
  font-size: 18px;
  color: #64b5f6;
}

.status-section {
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid #444;
}

.status-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.status-section h3 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #90caf9;
  font-weight: bold;
  text-transform: uppercase;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
  font-size: 13px;
}

.status-item span:first-child {
  color: #aaa;
}

.status-item span:last-child {
  color: #e0e0e0;
  font-weight: bold;
}

.progress-item {
  display: grid;
  grid-template-columns: 50px 1fr 40px;
  gap: 10px;
  align-items: center;
  margin: 8px 0;
  font-size: 12px;
}

.progress-bar {
  background: #1a1a1a;
  border-radius: 4px;
  height: 8px;
  overflow: hidden;
  border: 1px solid #444;
}

.progress-fill {
  height: 100%;
  transition: width 0.3s;
}

.progress-value {
  text-align: right;
  color: #aaa;
}

.strain-bar {
  padding: 5px 10px;
  border-radius: 4px;
  color: white;
  font-weight: bold;
  font-size: 12px;
  text-align: center;
  min-width: 50px;
}
EOF

# LogStream.js
cat > web-ui/src/components/LogStream.js << 'EOF'
import React, { useState, useEffect } from 'react';
import './LogStream.css';

function LogStream({ apiBase }) {
  const [logs, setLogs] = useState([]);
  const [ws, setWs] = useState(null);

  useEffect(() => {
    fetchLogs();
    connectWebSocket();

    return () => {
      if (ws) ws.close();
    };
  }, []);

  const fetchLogs = async () => {
    try {
      const response = await fetch(`${apiBase}/logs?limit=20`);
      const data = await response.json();
      setLogs(data.logs || []);
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  };

  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//localhost:8000/ws/logs`;
    
    try {
      const websocket = new WebSocket(wsUrl);
      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'log') {
          setLogs(prev => {
            const updated = [data.data, ...prev];
            return updated.slice(0, 50);
          });
        }
      };
      websocket.onerror = (error) => console.error('WebSocket error:', error);
      setWs(websocket);
    } catch (error) {
      console.error('WebSocket connection error:', error);
    }
  };

  return (
    <div className="log-stream">
      <h2>📝 Event Log</h2>
      <div className="logs">
        {logs.length === 0 ? (
          <p className="empty">No events yet</p>
        ) : (
          logs.map((log, i) => (
            <div key={i} className="log-entry">
              <span className="timestamp">{new Date(log.iso).toLocaleTimeString()}</span>
              <span className="category" style={{ color: getCategoryColor(log.category) }}>
                {log.category.toUpperCase()}
              </span>
              <span className="message">{log.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function getCategoryColor(category) {
  const colors = {
    autonomy: '#64b5f6',
    learning: '#81c784',
    task: '#ffb74d',
    chat: '#ba68c8',
    event: '#64b5f6',
    default: '#aaa'
  };
  return colors[category] || colors.default;
}

export default LogStream;
EOF

# LogStream.css
cat > web-ui/src/components/LogStream.css << 'EOF'
.log-stream {
  background: #2a2a2a;
  border-radius: 8px;
  padding: 15px;
  border: 1px solid #444;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.log-stream h2 {
  margin: 0 0 10px 0;
  font-size: 18px;
  color: #64b5f6;
}

.logs {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column-reverse;
  gap: 5px;
}

.logs .empty {
  text-align: center;
  color: #666;
  padding: 20px;
  font-size: 13px;
}

.log-entry {
  display: grid;
  grid-template-columns: 80px 80px 1fr;
  gap: 10px;
  padding: 8px;
  background: #333;
  border-radius: 4px;
  border-left: 3px solid #64b5f6;
  font-size: 12px;
  font-family: 'Courier New', monospace;
}

.log-entry .timestamp {
  color: #90caf9;
  font-weight: bold;
}

.log-entry .category {
  font-weight: bold;
  padding: 0 5px;
  border-radius: 2px;
  background: rgba(100, 181, 246, 0.1);
}

.log-entry .message {
  color: #c0c0c0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
EOF

# ControlPanel.js
cat > web-ui/src/components/ControlPanel.js << 'EOF'
import React, { useState } from 'react';
import './ControlPanel.css';

function ControlPanel({ apiBase, onStateChange }) {
  const [loading, setLoading] = useState(false);

  const startAutonomy = async () => {
    setLoading(true);
    try {
      await fetch(`${apiBase}/autonomy/start`, { method: 'POST' });
      onStateChange();
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const stopAutonomy = async () => {
    setLoading(true);
    try {
      await fetch(`${apiBase}/autonomy/stop`, { method: 'POST' });
      onStateChange();
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="control-panel">
      <h2>⚙️ Controls</h2>
      <button onClick={startAutonomy} disabled={loading}>▶ Start Autonomy</button>
      <button onClick={stopAutonomy} disabled={loading}>⏹ Stop Autonomy</button>
      <p style={{ fontSize: '12px', color: '#888' }}>
        Click to control the background learning loop
      </p>
    </div>
  );
}

export default ControlPanel;
EOF

# ControlPanel.css
cat > web-ui/src/components/ControlPanel.css << 'EOF'
.control-panel {
  background: #2a2a2a;
  border-radius: 8px;
  padding: 15px;
  border: 1px solid #444;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.control-panel h2 {
  margin: 0;
  font-size: 18px;
  color: #64b5f6;
}

.control-panel button {
  padding: 10px 15px;
  background: #0d47a1;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.2s;
  font-size: 14px;
}

.control-panel button:hover:not(:disabled) {
  background: #1565c0;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(13, 71, 161, 0.3);
}

.control-panel button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.control-panel p {
  margin: 5px 0 0 0;
}
EOF

echo "✓ React frontend structure created in web-ui/"
echo ""
echo "To get started:"
echo "  1. cd web-ui"
echo "  2. npm install"
echo "  3. npm start"
EOF

# Make the script executable
chmod +x create-frontend.sh

echo "✓ Frontend creation script created!"
bash create-frontend.sh
