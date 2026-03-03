<div align="center">

# ⚡ Anonymous Random Text Chat

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9+-yellow.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![HTML](https://img.shields.io/badge/Frontend-Vanilla--HTML%2FJS-orange.svg)

> A blazing fast, fully anonymous, one-on-one real-time chat platform. Built with Python WebSockets and extreme simplicity in mind.

</div>

---

## 🌟 Features

- **No Sign-ups**: 100% anonymous. Jump straight into a chat.
- **Real-Time Matchmaking**: Connects you with a stranger instantly using a custom in-memory queue.
- **Lightning Fast**: Powered by Python's **FastAPI** natively handling WebSockets. No external message brokers needed for a single instance.
- **Zero-Dependency Frontend**: Pure HTML, CSS (Tailwind styling), and Vanilla JS. Zero bloat. Instant load times.
- **SQL Backend**: Utilizing **SQLAlchemy** with **SQLite** (out of the box) for easy transition to **PostgreSQL**.

---

## 🏗️ Architecture

The app is distinctively split between a Python backend and a static frontend:

| Component | Tech Stack | Responsibility |
| :--- | :--- | :--- |
| **Backend** | Python, FastAPI, WebSockets | Handles `wss://` connections, manages the matchmaking queue, pairs users, and acts as the real-time message relay. |
| **Database** | SQLAlchemy, SQLite | Tracks user sessions and active connection states natively using SQL. Easily swappable to Postgres for production. |
| **Frontend** | HTML, TailwindCSS, Vanilla JS | Provides a beautiful, responsive UI. Uses the browser's native `WebSocket` API to communicate with the server. |

---

## 🚀 Getting Started Locally

It takes less than 60 seconds to run both the frontend and backend locally.

### 1. Start the Backend

Open a terminal and navigate to the backend folder:

```bash
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
*The backend is now listening for WebSocket connections at `ws://localhost:8000/ws`.*

### 2. Start the Frontend

Open a new terminal and serve the frontend:

```bash
cd frontend
python -m http.server 3000
```

*Open your browser to `http://localhost:3000`. Open it in two separate tabs to test the matchmaking!*

---

## 🌐 Live Deployment Guide

Deploying this stack is completely free and requires zero credit cards using **Render** and **Vercel**.

### Deploy Backend (Render)

1. Fork or push this repository to your GitHub account.
2. Go to [Render.com](https://render.com/) and create a **Web Service**.
3. Connect your repository.
4. Set the **Root Directory** to `backend`.
5. Set the **Start Command** to:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```
6. Click **Deploy**. Render will give you a live URL (e.g., `https://your-app.onrender.com`).

### Deploy Frontend (Vercel)

1. In `frontend/script.js`, currently the `WS_URL` is set to `ws://localhost:8000/ws`. **Change this** to your new secure Render WebSocket URL (e.g., `wss://your-app.onrender.com/ws`).
2. Go to [Vercel](https://vercel.com/) and create a new project.
3. Import your repository, but set the **Root Directory** to `frontend`.
4. Click **Deploy**. Vercel will instantly host your static files globally.

---

## 🧠 Logic Flow

1. **`Start Searching`**: Client opens a WebSocket to the server. Server creates a `Session ID`, saves it to SQL, and adds them to a Queue.
2. **`Match Found`**: Server constantly checks the Queue. When 2 users are waiting, they are popped, paired via an SQL `Chat` record, and both notified.
3. **`Messaging`**: Server relays texts between the two paired WebSocket connections.
4. **`Skip / Disconnect`**: Closing the browser or hitting "Skip" triggers a close event. Server cleans the SQL state, ends the Chat, notifies the partner, and attempts a re-match.

---

<div align="center">
  <i>Built as a demonstration of high-performance WebSockets in Python.</i>
</div>
