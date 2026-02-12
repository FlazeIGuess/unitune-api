from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func
from db import Base

class Playlist(Base):
    __tablename__ = 'playlists'

    id = Column(String(32), primary_key=True, index=True)
    delete_token = Column(String(64), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)
    tracks = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True)
