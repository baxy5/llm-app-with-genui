import hashlib
import json
import os
import tempfile
from typing import List

from fastapi import Depends, HTTPException, UploadFile
from langchain_community.document_loaders import (
  CSVLoader,
  Docx2txtLoader,
  JSONLoader,
  PyPDFLoader,
  UnstructuredExcelLoader,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat_session import FileRecord
from app.services.database import get_db


class FileService:
  def __init__(self, db: Session):
    self.session = db

  async def save_files(self, files: List[UploadFile], session_id: int):
    try:
      for file in files:
        if not file.filename:
          continue

        content = await file.read()
        file_hash = hashlib.md5(content).hexdigest()

        existing_file = (
          self.session.query(FileRecord)
          .filter_by(file_hash=file_hash, session_id=session_id)
          .first()
        )

        if existing_file:
          continue

        extracted_text = await self._extract_text(content, file.content_type, file.filename)

        file_record = FileRecord(
          session_id=session_id,
          filename=file.filename,
          file_hash=file_hash,
          content_type=file.content_type or "application/octet-stream",
          content=extracted_text,
        )

        self.session.add(file_record)

      self.session.commit()
      return True
    except Exception as e:
      self.session.rollback()
      raise HTTPException(status_code=500, detail=f"Error while saving files to db: {e}")

  async def retrieve_content_by_session_id(self, session_id: int):
    try:
      stmt = select(FileRecord).where(FileRecord.session_id == session_id)
      files = self.session.scalars(stmt).all()

      if not files:
        return None

      content = ""

      for file in files:
        content += f"Content of {file.filename}:\n"
        content += file.content
        content += "\n"

      return content
    except Exception as e:
      raise HTTPException(
        status_code=500,
        detail=f"Couldn't retrieve content from db by session_id:{session_id}, {e}",
      )

  async def _extract_text(self, content: bytes, content_type: str, filename: str = None):
    if not content_type:
      return None

    try:
      # Create temporary file for LangChain loaders
      with tempfile.NamedTemporaryFile(
        delete=False, suffix=self._get_file_extension(content_type, filename)
      ) as temp_file:
        temp_file.write(content)
        temp_file_path = temp_file.name

      try:
        if content_type == "application/pdf":
          loader = PyPDFLoader(temp_file_path)
        elif content_type in [
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
          "application/vnd.ms-excel",
        ]:
          loader = UnstructuredExcelLoader(temp_file_path)
        elif content_type == "application/json":
          loader = JSONLoader(temp_file_path, jq_schema=".", text_content=False)
        elif content_type == "text/csv":
          loader = CSVLoader(temp_file_path)
        elif content_type in [
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
          "application/msword",
        ]:
          loader = Docx2txtLoader(temp_file_path)
        else:
          raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}")

        # Load and extract text
        documents = loader.load()
        extracted_text = "\n\n".join(
          [self._extract_page_content(doc.page_content) for doc in documents]
        )

        return extracted_text

      finally:
        # Clean up temporary file
        os.unlink(temp_file_path)

    except Exception as e:
      print(f"Failed to extract content: {e}")
      raise HTTPException(status_code=500, detail=f"Failed to extract content from file: {e}")

  def _get_file_extension(self, content_type: str, filename: str = None) -> str:
    if filename and "." in filename:
      return "." + filename.split(".")[-1]

    extension_map = {
      "application/pdf": ".pdf",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
      "application/vnd.ms-excel": ".xls",
      "text/csv": ".csv",
      "application/json": ".json",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
      "application/msword": ".doc",
    }
    return extension_map.get(content_type, ".tmp")

  def _extract_page_content(self, page_content) -> str:
    """Extract string content from page_content, handling both string and dict types"""
    if isinstance(page_content, str):
      return page_content
    elif isinstance(page_content, dict):
      return json.dumps(page_content, indent=2)
    else:
      # Convert other types to string
      return str(page_content)


def get_file_service_db_session(db: Session = Depends(get_db)) -> FileService:
  return FileService(db)
