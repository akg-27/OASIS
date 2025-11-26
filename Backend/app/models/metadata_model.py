from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class Metadata(Base):
    __tablename__ = "metadata"

    id = Column(Integer, primary_key=True, index=True)
    dtype = Column(String, index=True)
    info = Column(String)  # store metadata dictionary as string
    created_at = Column(DateTime)
