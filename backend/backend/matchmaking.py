from typing import Dict, List, Optional
from fastapi import WebSocket
from sqlalchemy.orm import Session
from backend.models import User, Chat
import uuid
import json

class ConnectionManager:
    def __init__(self):
        # A dictionary holding active connections: {session_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # Queue holding session_ids of users waiting for a match
        self.waiting_queue: List[str] = []

    async def connect(self, db: Session, websocket: WebSocket) -> str:
        await websocket.accept()
        session_id = str(uuid.uuid4())
        self.active_connections[session_id] = websocket
        
        # Save user to DB
        user = User(session_id=session_id)
        db.add(user)
        db.commit()

        await self.send_system_message(websocket, {
            "type": "connected",
            "session_id": session_id,
            "message": "Connected to server. Looking for a partner..."
        })
        
        return session_id

    def disconnect(self, db: Session, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            
        if session_id in self.waiting_queue:
            self.waiting_queue.remove(session_id)
            
        # Clean up database state
        user = db.query(User).filter(User.session_id == session_id).first()
        if user:
            db.delete(user)
            db.commit()

    async def add_to_queue(self, session_id: str):
        if session_id not in self.waiting_queue:
            self.waiting_queue.append(session_id)

    async def try_match(self, db: Session):
        if len(self.waiting_queue) >= 2:
            # We have a match!
            user1_id = self.waiting_queue.pop(0)
            user2_id = self.waiting_queue.pop(0)

            # Update DB statuses
            user1 = db.query(User).filter(User.session_id == user1_id).first()
            user2 = db.query(User).filter(User.session_id == user2_id).first()
            
            if user1 and user2:
                user1.status = "connected"
                user2.status = "connected"
                
                # Create a Chat record
                new_chat = Chat(user1_id=user1_id, user2_id=user2_id)
                db.add(new_chat)
                db.commit()

                # Notify both users
                await self.notify_match(user1_id, user2_id)
            else:
                # If one disconnected mid-match, put the other back
                if user1 and not user2: self.waiting_queue.append(user1_id)
                elif user2 and not user1: self.waiting_queue.append(user2_id)

    async def notify_match(self, user1_id: str, user2_id: str):
        ws1 = self.active_connections.get(user1_id)
        ws2 = self.active_connections.get(user2_id)
        
        if ws1:
            await self.send_system_message(ws1, {"type": "match_found", "message": "You are now chatting with a stranger."})
        if ws2:
            await self.send_system_message(ws2, {"type": "match_found", "message": "You are now chatting with a stranger."})

    async def send_system_message(self, websocket: WebSocket, data: dict):
        try:
            await websocket.send_text(json.dumps(data))
        except Exception:
            pass

    async def handle_message(self, db: Session, sender_id: str, content: str):
        # Find active chat for this user
        chat = db.query(Chat).filter(
            Chat.active == True,
            (Chat.user1_id == sender_id) | (Chat.user2_id == sender_id)
        ).first()

        if chat:
            # Determine partner
            partner_id = chat.user2_id if chat.user1_id == sender_id else chat.user1_id
            partner_ws = self.active_connections.get(partner_id)
            
            if partner_ws:
                # Send to partner
                msg_data = {
                    "type": "chat_message",
                    "content": content
                }
                try:
                    await partner_ws.send_text(json.dumps(msg_data))
                except Exception:
                    # Partner disconnected abruptly
                    await self.handle_partner_disconnect(db, chat, sender_id)
            else:
                 await self.handle_partner_disconnect(db, chat, sender_id)

    async def handle_skip(self, db: Session, session_id: str):
        chat = db.query(Chat).filter(
            Chat.active == True,
            (Chat.user1_id == session_id) | (Chat.user2_id == session_id)
        ).first()

        if chat:
            chat.active = False
            db.commit()

            partner_id = chat.user2_id if chat.user1_id == session_id else chat.user1_id
            
            # Notify partner
            partner_ws = self.active_connections.get(partner_id)
            if partner_ws:
                await self.send_system_message(partner_ws, {"type": "partner_disconnected", "message": "Stranger has disconnected."})
            
            # Update statuses
            user1 = db.query(User).filter(User.session_id == session_id).first()
            user2 = db.query(User).filter(User.session_id == partner_id).first()
            if user1: user1.status = "searching"
            if user2: user2.status = "searching"
            db.commit()

            # Put skipper back in queue
            await self.add_to_queue(session_id)
            await self.try_match(db)

    async def handle_partner_disconnect(self, db: Session, chat: Chat, remaining_user_id: str):
         chat.active = False
         user = db.query(User).filter(User.session_id == remaining_user_id).first()
         if user:
             user.status = "searching"
         db.commit()

         ws = self.active_connections.get(remaining_user_id)
         if ws:
             await self.send_system_message(ws, {"type": "partner_disconnected", "message": "Stranger has disconnected."})

manager = ConnectionManager()
