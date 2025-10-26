import logging

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.api.endpoints import chat_sessions, multi_agent
from app.models.chat_session import ChatSession, FileRecord, Message  # noqa: F401
from app.models.test_dataset import Dataset  # noqa: F401
from app.services.env_config_service import get_env_configs

logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
  handlers=[
    logging.StreamHandler(),
  ],
)

# SQLAlchemy pool logging
logging.getLogger("sqlalchemy.pool").setLevel(logging.DEBUG)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(_app: FastAPI):
  settings = get_env_configs()

  base_url = settings.postgres_url.unicode_string()
  connection_string = f"{base_url}?options=-c%20search_path%3Dlanggraph"

  async with AsyncPostgresSaver.from_conn_string(connection_string) as saver:
    await saver.setup()
    _app.state.checkpointer = saver
    yield


app = FastAPI(lifespan=lifespan)

origins = ["http://localhost:3000"]


app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["GET", "POST"],
  allow_headers=["*"],
)

app.include_router(multi_agent.router, prefix="/agent", tags=["Multi Agent"])
app.include_router(chat_sessions.router, prefix="/chat_sessions", tags=["Chat Sessions"])


@app.get("/health")
async def health_check():
  return {"status": "ok"}
