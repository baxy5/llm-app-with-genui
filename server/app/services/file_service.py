import hashlib
from io import BytesIO
from typing import List

import pandas as pd
import PyPDF2
from fastapi import Depends, HTTPException, UploadFile
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

        extracted_text = await self._extract_text(content, file.content_type)

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

  async def _extract_text(self, content: bytes, content_type: str):
    if not content_type:
      return None

    try:
      if content_type == "application/pdf":
        return self._extract_pdf_text(content)
      elif content_type in [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
      ]:
        return self._extract_xlsx_text(content)
      # TODO: Implement these file supports
      elif content_type == "application/json":
        return None
      elif content_type == "text/csv":
        return None
      elif content_type in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
      ]:
        return None
      else:
        raise HTTPException(
          status_code=500, detail=f"Failed to parse file with content_type: {content_type}"
        )

    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Failed to extract content from file: {e}")

  def _extract_pdf_text(self, content: bytes) -> str:
    try:
      pdf_file = BytesIO(content)
      pdf_reader = PyPDF2.PdfReader(pdf_file)

      text_content = []
      for page in pdf_reader.pages:
        text_content.append(page.extract_text())

      return "\n\n".join(text_content)

    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Failed to extract text from PDF: {e}")

  def _extract_xlsx_text(self, content: bytes) -> str:
    try:
      excel_file = BytesIO(content)

      excel_data = pd.read_excel(excel_file, sheet_name=None, engine="openpyxl")

      text_content = []
      for sheet_name, df in excel_data.items():
        text_content.append(f"Sheet: {sheet_name}")
        text_content.append("=" * (len(sheet_name) + 7))

        df_filled = df.fillna("")
        text_content.append(df_filled.to_string(index=False))
        text_content.append("")

      return "\n".join(text_content)

    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Failed to extract text from Excel file: {e}")


def get_file_service_db_session(db: Session = Depends(get_db)) -> FileService:
  return FileService(db)
