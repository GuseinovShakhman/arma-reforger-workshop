"""
main.py — FastAPI application entry point and route definitions.
"""

from __future__ import annotations
import os
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from api.database import Base, engine, get_db
from api.models import Mod
from api.schemas import ModDetail, ModListResponse, ModSummary, StatsResponse, TagCount

# Create all tables on startup (idempotent)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Arma Reforger Workshop Mirror",
    description="Self-hosted mirror of the Arma Reforger Workshop with advanced sorting and filtering.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # public read-only API — no auth needed
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

SORT_OPTIONS = {
    "newest":        Mod.created_at.desc(),
    "popular":       Mod.download_count.desc(),
    "updated":       Mod.updated_at.desc(),
    "alphabetical":  Mod.name.asc(),
    "popular_week":  Mod.download_count.desc(),  # TODO: weekly counter column
}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/mods", response_model=ModListResponse, summary="List mods with filters")
def list_mods(
    search: Optional[str] = Query(None, description="Text search in name + description"),
    tags: Optional[str] = Query(None, description="Comma-separated tag names"),
    sort: str = Query("newest", description="Sort order: newest|popular|updated|alphabetical|popular_week"),
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ModListResponse:
    q = db.query(Mod)

    if search:
        term = f"%{search}%"
        q = q.filter(or_(Mod.name.ilike(term), Mod.description.ilike(term)))

    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        for tag in tag_list:
            # JSON contains — works for both SQLite and PostgreSQL via cast
            q = q.filter(Mod.tags.contains(tag))

    order_col = SORT_OPTIONS.get(sort, Mod.created_at.desc())
    q = q.order_by(order_col)

    total = q.count()
    items = q.offset((page - 1) * limit).limit(limit).all()

    return ModListResponse(total=total, page=page, limit=limit, items=items)


@app.get("/api/mods/{mod_id}", response_model=ModDetail, summary="Single mod detail")
def get_mod(mod_id: str, db: Session = Depends(get_db)) -> ModDetail:
    mod = db.query(Mod).filter(Mod.id == mod_id.upper()).first()
    if not mod:
        raise HTTPException(status_code=404, detail=f"Mod '{mod_id}' not found")
    return mod


@app.get("/api/tags", response_model=List[TagCount], summary="All unique tags with counts")
def list_tags(db: Session = Depends(get_db)) -> List[TagCount]:
    mods = db.query(Mod.tags).filter(Mod.tags.isnot(None)).all()
    counts: dict[str, int] = {}
    for (tags,) in mods:
        if isinstance(tags, list):
            for tag in tags:
                counts[tag] = counts.get(tag, 0) + 1
    return [TagCount(tag=t, count=c) for t, c in sorted(counts.items(), key=lambda x: -x[1])]


@app.get("/api/stats", response_model=StatsResponse, summary="Total mods, last scrape time, etc.")
def get_stats(db: Session = Depends(get_db)) -> StatsResponse:
    total = db.query(func.count(Mod.id)).scalar() or 0
    last_scraped = db.query(func.max(Mod.scraped_at)).scalar()
    return StatsResponse(
        total_mods=total,
        last_scraped_at=last_scraped,
        db_engine=os.getenv("DATABASE_URL", "sqlite:///./workshop.db").split(":")[0],
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
