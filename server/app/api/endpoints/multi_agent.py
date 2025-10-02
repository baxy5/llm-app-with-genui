from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.endpoints.chat_sessions import get_db_session
from app.models.state_model import MultiAgentRequest
from app.services.chat_session_service import ChatSessionService
from app.services.multi_agent_orchestrator_service import MultiAgentOrchestratorService

router = APIRouter()


@router.post("/")
async def multi_agent_generate(
  req: MultiAgentRequest,
  service: Annotated[
    MultiAgentOrchestratorService,
    Depends(),
  ],
  cs_service: Annotated[ChatSessionService, Depends(get_db_session)],
):
  try:
    await cs_service.add_user_message(session_id=req.session_id, content=req.input)
    return StreamingResponse(service.generate(req), media_type="text/event-stream")
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Multi agent generation have failed, {e}")
