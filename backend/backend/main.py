from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.database import engine, Base, get_db
from backend.matchmaking import manager
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init db
Base.metadata.create_all(bind=engine)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    session_id = await manager.connect(db, websocket)
    await manager.add_to_queue(session_id)
    await manager.try_match(db)

    try:
        while True:
            data_str = await websocket.receive_text()
            try:
                data = json.loads(data_str)
                type = data.get("type", "")
                
                if type == "chat_message":
                    content = data.get("content", "")
                    if content:
                        await manager.handle_message(db, session_id, content)
                elif type == "skip":
                    await manager.handle_skip(db, session_id)
            except json.JSONDecodeError:
                pass
            
    except WebSocketDisconnect:
        manager.disconnect(db, session_id)
        # Check if they were in an active chat and notify partner
        # We can trigger a skip equivalent to cleanly end the chat
        await manager.handle_skip(db, session_id)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Anonymous Chat Backend Running"}
