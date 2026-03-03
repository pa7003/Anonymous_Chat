# Anonymous Random Text Chat System

This is a real-time, one-on-one anonymous chat application built with Python (FastAPI + WebSockets) and a vanilla HTML/JS frontend.

## Architecture Overview

- **Backend**: Python, FastAPI. It utilizes FastAPI's built-in `WebSocket` support to manage active connections without needing third-party messaging buses for a single-instance deployment.
- **Database**: SQLite locally via SQLAlchemy ORM. This fulfills the SQL requirement and makes it effortlessly compatible with PostgreSQL if deployed to a platform like Render or Railway. Two main models exist: `User` (tracks session and status) and `Chat` (tracks active pairings).
- **Matchmaking Engine**: Lives in memory (`backend/matchmaking.py`). It manages a queue of waiting users and pairs them up based on connection order.
- **Frontend**: Pure HTML, CSS (with Tailwind for layout), and Vanilla JavaScript utilizing the native browser `WebSocket` API.

## Matchmaking & Chat Flow

1. **Connection**: A user loads the frontend and clicks "Start Searching". A WebSocket connection is opened to `/ws`.
2. **Session Creation**: The backend accepts the connection, generates a unique UUID `session_id`, saves it to the SQL database, and adds the user to the `waiting_queue`.
3. **Matchmaking**: The server constantly checks the queue. When 2 or more users are waiting, it pops the first two, pair them up, creates a `Chat` record in the database, and sends a `match_found` WebSocket event to both clients.
4. **Messaging**: When User A sends a message, the server looks up their active `Chat`, finds User B's `session_id`, retrieves User B's active WebSocket connection from memory, and relays the message.
5. **Skip/Disconnect**:
   - If User A clicks "Skip", the server marks the `Chat` as inactive, notifies User B ("Stranger has disconnected"), puts User A back into the `waiting_queue`, and tries to match them again. User B is left on the searching screen and will manually need to search again.
   - If User A closes the browser, the WebSocket disconnects. The server catches the disconnect, cleans up their session, and gracefully ends any active chat they were in, notifying the partner.

## How to Run Locally

### 1. Start the Backend
```bash
cd backend
python -m venv venv
# Activate the virtual environment:
# Windows: .\venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
The backend will run on `ws://localhost:8000/ws`.

### 2. Start the Frontend
Simply open `frontend/index.html` in your web browser. Or, to avoid CORS/file protocol issues with some browsers, serve it locally:
```bash
cd frontend
python -m http.server 3000
```
Then visit `http://localhost:3000`. Open it in two different tabs to test matching!

## Deployment Approach

Because the backend relies on in-memory state for WebSocket connections (the `ConnectionManager`), it must be deployed as a **single instance** (no horizontal scaling) unless a Redis Pub/Sub backplane is added. Let's deploy the frontend and backend separately:

### Deploying the Backend (Render or Railway)
1. Push this code to a GitHub repository.
2. Go to [Render.com](https://render.com/) or [Railway.app](https://railway.app/).
3. Create a new **Web Service**.
4. Connect your GitHub repository and point it to the `backend` folder as the root directory.
5. Setup the start command:
   - Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
6. *Optional*: If you want persistent SQL data, provision a PostgreSQL database on the platform and add its connection string as a `DATABASE_URL` environment variable. SQLAlchemy will automatically use it instead of SQLite.

### Deploying the Frontend (Vercel or Netlify)
1. Go to `frontend/script.js` and update `WS_URL` on line 12 to your newly deployed backend WebSocket URL (e.g., `wss://your-backend-app.onrender.com/ws`).
2. Go to [Netlify.com](https://www.netlify.com/) or [Vercel.com](https://vercel.com/).
3. Create a new site and just drag-and-drop the `frontend` folder. It will deploy instantly.

## Known Limitations

- **Scalability**: The `waiting_queue` and `active_connections` are kept in server memory. If deployed across multiple server instances (horizontal scaling), User A on Server 1 cannot match with User B on Server 2. To fix this, a Redis layer must be introduced to share state between instances.
- **Data Persistence**: Currently, messages are not saved to the database to prioritize speed and anonymity. If chat history is required, the `handle_message` function needs a quick `db.add(Message(...))` call.
