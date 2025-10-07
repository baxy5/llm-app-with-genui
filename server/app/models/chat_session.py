import enum

from sqlalchemy import (
  JSON,
  Column,
  DateTime,
  Enum,
  ForeignKey,
  Identity,
  Integer,
  String,
  Text,
  func,
)
from sqlalchemy.orm import relationship

from app.services.database import Base


class TypeEnum(enum.Enum):
  user = "user"
  assistant = "assistant"


class Message(Base):
  __tablename__ = "messages"

  session_id = Column(
    Integer,
    ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
    nullable=False,
    primary_key=True,
  )
  id = Column(Integer, nullable=False, primary_key=True)

  type = Column(Enum(TypeEnum), nullable=False)
  content = Column(String, nullable=True)
  option = Column(JSON, nullable=True)

  session = relationship("ChatSession", back_populates="messages")


class ChatSession(Base):
  __tablename__ = "chat_sessions"

  session_id = Column(Integer, primary_key=True, nullable=False)
  title = Column(String(500), nullable=False)
  messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
  files = relationship("FileRecord", back_populates="session", cascade="all, delete-orphan")
  created_at = Column(DateTime(timezone=True), server_default=func.now())
  updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FileRecord(Base):
  __tablename__ = "files"

  session_id = Column(
    Integer,
    ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
    nullable=False,
    primary_key=True,
  )
  file_id = Column(Integer, Identity(start=1, increment=1), primary_key=True)

  filename = Column(String, nullable=False)
  file_hash = Column(String, nullable=False, index=True)
  content_type = Column(String, nullable=False)
  upload_time = Column(DateTime(timezone=True), server_default=func.now())
  content = Column(Text, nullable=True)

  session = relationship("ChatSession", back_populates="files")

  def to_dict(self):
    return {
      "file_id": self.file_id,
      "session_id": self.session_id,
      "filename": self.filename,
      "file_hash": self.file_hash,
      "content_type": self.content_type,
      "upload_time": self.upload_time.isoformat() if self.upload_time else None,
      "content": self.content,
    }
