"""
models.py — SQLAlchemy ORM models.
"""

from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, JSON, String, Text

from api.database import Base


class Mod(Base):
    __tablename__ = "mods"

    id             = Column(String,     primary_key=True)   # e.g. "5965550F24A0C152"
    name           = Column(String,     nullable=False)
    author         = Column(String)
    description    = Column(Text)
    thumbnail_url  = Column(String)
    size_bytes     = Column(BigInteger)
    rating         = Column(Float)                          # 0–100 percentage
    tags           = Column(JSON)                           # ["Gameplay", "Weapons", …]
    workshop_url   = Column(String)
    created_at     = Column(DateTime)
    updated_at     = Column(DateTime)
    scraped_at     = Column(DateTime, default=datetime.utcnow)
    download_count = Column(Integer,   default=0)
    image_urls     = Column(JSON)                           # list of screenshot URLs

    def __repr__(self) -> str:
        return f"<Mod id={self.id!r} name={self.name!r}>"
