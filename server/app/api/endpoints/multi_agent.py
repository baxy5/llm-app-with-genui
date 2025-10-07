from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.models.state_model import MultiAgentRequest
from app.services.chat_session_service import ChatSessionService, get_db_session
from app.services.file_service import FileService, get_file_service_db_session
from app.services.multi_agent_orchestrator_service import MultiAgentOrchestratorService

router = APIRouter()


@router.post("/")
async def multi_agent_generate(
  req: Request,
  service: Annotated[
    MultiAgentOrchestratorService,
    Depends(),
  ],
  cs_service: Annotated[ChatSessionService, Depends(get_db_session)],
  file_service: Annotated[FileService, Depends(get_file_service_db_session)],
):
  content_type = req.headers.get("content-type", "")

  if "application/json" in content_type:
    data = await req.json()
    files = []
  elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
    form = await req.form()
    data = {key: value for key, value in form.items() if not hasattr(value, "filename")}
    files = [file for key, file in form.multi_items() if hasattr(file, "filename")]
  else:
    return JSONResponse({"error": "Unsupported content type"}, status_code=400)

  try:
    user_request = MultiAgentRequest(**data)

    await cs_service.add_user_message(
      session_id=user_request.session_id, content=user_request.input
    )

    try:
      if files:
        await file_service.save_files(files=files, session_id=user_request.session_id)
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Multi agent saving files in db failed: {e}")

    return StreamingResponse(service.generate(user_request), media_type="text/event-stream")
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Multi agent generation have failed, {e}")
