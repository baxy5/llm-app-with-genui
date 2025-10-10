from fastapi import Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db


class DatasetService:
  def __init__(self, db: Session):
    self.session = db

  def run_sql_query(self, sql_query: str):
    try:
      result = self.session.execute(text(sql_query))
      rows = result.mappings().all()
      return [dict(row) for row in rows]
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Couldn't retrieve data from dataset table: {e}")


def get_dataset_db_session(db: Session = Depends(get_db)) -> DatasetService:
  return DatasetService(db)
