from pydantic import BaseModel
from typing import Optional, Dict, Any


class DataInfoCreate(BaseModel):
    dataset_name: str
    dataset_domain: str  # ocean | taxonomy | otolith | edna
    dataset_link: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
    curated_data: Optional[Dict[str, Any]] = None
    raw_data: Optional[Dict[str, Any]] = None
