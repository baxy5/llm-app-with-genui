import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.services.chat_session_service import ChatSessionService
from app.services.multi_agent_orchestrator_service import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/lifecheck")
async def lifecheck(service: Annotated[ChatSessionService, Depends(get_db_session)]):
  try:
    return service.lifecheck()
  except Exception:
    logger.error("Lifecheck failed.")
    raise HTTPException(status_code=500, detail="Lifecheck failed.")


@router.get("/sessions")
async def get_chat_sessions(service: Annotated[ChatSessionService, Depends(get_db_session)]):
  try:
    response = await service.get_chat_sessions()
    logger.info("Successfully retrieved chat sessions.")
    return response
  except Exception as e:
    logger.error(f"Couldn't retrieve chat sessions: {e}")
    raise HTTPException(status_code=500, detail=f"Retrieving chat sessions has failed, {e}")


@router.get("/messages")
async def get_messages_by_sessions_id(
  session_id: str, service: Annotated[ChatSessionService, Depends(get_db_session)]
):
  try:
    response = await service.get_messages_by_session_id(session_id)
    logger.info(f"Successfully retrieved messages for session id {session_id}.")
    return response
  except Exception as e:
    logger.error(f"Couldn't retrieve messages for session id {session_id}: {e}")
    raise HTTPException(
      status_code=500, detail=f"Retriving messages for chat session id {session_id} has failed. {e}"
    )


@router.post("/add_session")
async def add_session(
  session_id: str, service: Annotated[ChatSessionService, Depends(get_db_session)]
):
  try:
    response = await service.add_chat_session(session_id=session_id)
    logger.info(f"Successfully added new chat session with session id {session_id}.")
    return response
  except Exception as e:
    logger.error(f"Couldn't add new chat session with session id {session_id}: {e}")
    raise HTTPException(status_code=500, detail=f"Add session failed: {e}")


@router.post("/add_message")
async def add_message(
  session_id: str, content: str, service: Annotated[ChatSessionService, Depends(get_db_session)]
):
  try:
    response = await service.add_user_message(session_id=session_id, content=content)
    logger.info(f"Successfully added new message to session with session id {session_id}.")
    return response
  except Exception as e:
    logger.error(f"Couldn't add new message to session with session id {session_id}: {e}")
    raise HTTPException(status_code=500, detail=f"Add message to session failed: {e}")


@router.delete("/delete_session")
async def delete_session(
  session_id: str, service: Annotated[ChatSessionService, Depends(get_db_session)]
):
  try:
    response = await service.delete_chat_session(session_id)
    logger.info(f"Successfully deleted chat session with session id {session_id}.")
    return response
  except Exception as e:
    logger.error(f"Couldn't delete chat session with session id {session_id}: {e}")
    raise HTTPException(status_code=500, detail=f"Delete session failed: {e}")


@router.delete("/reset")
async def reset_db(service: Annotated[ChatSessionService, Depends(get_db_session)]):
  try:
    response = await service.reset_db()
    logger.info("Successfully reseted database.")
    return response
  except Exception as e:
    logger.error(f"Couldn't reset database: {e}")
    raise HTTPException(status_code=500, detail=f"Resetting database failed. {e}")
