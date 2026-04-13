"""
schemas.py — Pydantic schemas for API request/response validation.
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ModSummary(BaseModel):
    """Lightweight mod representation used in list responses."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    author: Optional[str] = None
    thumbnail_url: Optional[str] = None
    size_bytes: Optional[int] = None
    rating: Optional[float] = None
    tags: Optional[List[str]] = None
    workshop_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    scraped_at: Optional[datetime] = None
    download_count: int = 0


class ModDetail(ModSummary):
    """Full mod data including description and screenshot URLs."""
    description: Optional[str] = None
    image_urls: Optional[List[str]] = None


class ModListResponse(BaseModel):
    """Paginated list of mods."""
    total: int
    page: int
    limit: int
    items: List[ModSummary]


class TagCount(BaseModel):
    """Tag name with occurrence count."""
    tag: str
    count: int


class StatsResponse(BaseModel):
    """High-level stats about the scrape state."""
    total_mods: int
    last_scraped_at: Optional[datetime] = None
    db_engine: str
