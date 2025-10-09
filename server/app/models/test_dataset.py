from sqlalchemy import Column, Identity, Integer, String

from app.db.database import Base


class Dataset(Base):
  __tablename__ = "dataset"

  id = Column(Integer, Identity(start=1, increment=1), nullable=False, primary_key=True)

  product_name = Column(String, nullable=False)
  year = Column(String, nullable=False)
  month = Column(String, nullable=False)
  revenue = Column(Integer, nullable=False)
  expenses = Column(Integer, nullable=False)
  current_employees = Column(Integer, nullable=False)
