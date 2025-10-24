import logging
from typing import Optional

from fastapi import HTTPException
from langgraph.checkpoint.base import BaseCheckpointSaver
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.chat_session import ChatSession, Message

logger = logging.getLogger(__name__)


class ChatSessionService:
  def __init__(self, db: Session, checkpointer: BaseCheckpointSaver):
    self.session = db
    self.checkpointer = checkpointer

  def lifecheck(self):
    return {"status": "alive", "database": "connected"}

  async def get_chat_sessions(self):
    try:
      stmt = select(ChatSession)
      response = self.session.scalars(stmt).all()

      logger.info(f"get_chat_session successfully returned {len(response)} chat sessions.")

      sorted_by_session_id = sorted(response, key=lambda chat: chat.session_id, reverse=True)

      return sorted_by_session_id
    except Exception as e:
      logger.error(f"Couldn't retrieve chat sessions from database: {e}")
      raise HTTPException(
        status_code=500, detail=f"Couldn't retrieve chat sessions from database, {e}"
      )

  async def get_messages_by_session_id(self, session_id: str):
    try:
      stmt = select(ChatSession).where(ChatSession.session_id == session_id)
      chat_session = self.session.scalars(stmt).first()

      if not chat_session:
        logger.error(f"Chat session with id {session_id} not found.")
        raise HTTPException(status_code=404, detail=f"Chat session with id {session_id} not found.")

      sorted_by_id = sorted(chat_session.messages, key=lambda message: message.id)

      return sorted_by_id
    except Exception as e:
      logger.error(f"Couldn't retrieve messages for session_id {session_id}: {e}")
      raise HTTPException(
        status_code=500, detail=f"Couldn't retrieve messages for session {session_id}: {e}"
      )

  async def add_chat_session(self, session_id: str):
    title = f"Session id: {session_id}"
    try:
      if session_id and title:
        new_chat_session = ChatSession(session_id=session_id, title=title)
        self.session.add(new_chat_session)
        self.session.commit()
        self.session.refresh(new_chat_session)  # refresh to get autoincrement ID
        return {"session_id": session_id, "title": title}
      else:
        logger.error("Couldn't add chat session because either session_id or title are missing.")
        raise HTTPException(
          status_code=400,
          detail="Couldn't add chat session because either session_id or title are missing.",
        )
    except Exception as e:
      self.session.rollback()
      logger.error(f"Couldn't add new chat session: {e}")
      raise HTTPException(status_code=500, detail=f"New chat session insertion failed: {e}")

  async def add_user_message(self, session_id: str, content: str):
    try:
      session_stmt = select(ChatSession).where(ChatSession.session_id == session_id)
      chat_session = self.session.scalars(session_stmt).first()

      if not chat_session:
        await self.add_chat_session(session_id=session_id)

      stmt = select(Message.id).where(Message.session_id == session_id).order_by(Message.id.desc())
      latest_message_id = self.session.scalars(stmt).first()

      if latest_message_id:
        latest_message_id += 1
      else:
        latest_message_id = 1

      new_message = Message(
        session_id=session_id, id=latest_message_id, type="user", content=content
      )
      self.session.add(new_message)
      self.session.commit()
      self.session.refresh(new_message)  # refresh to get autoincrement ID
      return {"session_id": session_id, "content": content}
    except Exception as e:
      self.session.rollback()
      logger.error(f"Couldn't add new user message: {e}")
      raise HTTPException(status_code=500, detail=f"New user message insertion failed: {e}")

  async def add_assistant_message(
    self, session_id: str, option: Optional[str], content: Optional[str], component: Optional[str]
  ):
    try:
      stmt = select(Message.id).where(Message.session_id == session_id).order_by(Message.id.desc())
      latest_message_id = self.session.scalars(stmt).first()

      new_message = Message(
        session_id=session_id,
        id=latest_message_id + 1,
        type="assistant",
        content=content,
        option=option,
        component=component,
      )
      self.session.add(new_message)
      self.session.commit()
      self.session.refresh(new_message)  # refresh to get autoincrement ID
      return {
        "session_id": session_id,
        "content": content,
        "option": option,
        "component": component,
      }
    except Exception as e:
      self.session.rollback()
      logger.error(f"Couldn't add new assistant message: {e}")
      raise HTTPException(status_code=500, detail=f"New assistant message insertion failed: {e}")

  async def delete_chat_session(self, session_id: str):
    try:
      stmt = select(ChatSession).where(ChatSession.session_id == session_id)
      chat_session = self.session.scalars(stmt).first()

      if chat_session:
        await self.checkpointer.adelete_thread(session_id)
        self.session.delete(chat_session)
        self.session.commit()
      else:
        logger.error(
          f"Chat session have not been found with id {session_id} when deleting chat session."
        )
    except Exception as e:
      self.session.rollback()
      logger.error(f"Couldn't delete chat session: {e}")
      raise HTTPException(status_code=500, detail=f"Session deletion failed: {e}")

  async def reset_db(self):
    try:
      self.session.execute(delete(ChatSession))
      self.session.commit()
    except Exception as e:
      self.session.rollback()
      raise HTTPException(status_code=500, detail=f"Resetting database have failed. {e}")
