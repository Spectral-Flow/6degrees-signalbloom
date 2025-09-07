"""
Database models and setup for Signal Bloom
"""

import asyncio
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, String, DateTime, Float, Integer, Text, create_engine, event
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import logging

from config import Config

logger = logging.getLogger(__name__)

Base = declarative_base()


class Signal(Base):
    """Signal model for database storage"""
    __tablename__ = 'signals'
    
    id = Column(String, primary_key=True)
    text = Column(Text, nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'text': self.text,
            'x': self.x,
            'y': self.y,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection and create tables"""
        try:
            # Handle SQLite async URL
            db_url = Config.DATABASE_URL
            if db_url.startswith('sqlite:///'):
                db_url = db_url.replace('sqlite:///', 'sqlite+aiosqlite:///')
            elif db_url.startswith('sqlite://'):
                db_url = db_url.replace('sqlite://', 'sqlite+aiosqlite://')
            
            self.engine = create_async_engine(
                db_url,
                echo=Config.DATABASE_ECHO,
                future=True
            )
            
            self.SessionLocal = sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            self._initialized = True
            logger.info(f"Database initialized successfully with URL: {db_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if not self._initialized:
            await self.initialize()
        return self.SessionLocal()
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")
    
    async def save_signal(self, signal_data: dict) -> Signal:
        """Save signal to database"""
        async with await self.get_session() as session:
            signal = Signal(
                id=signal_data['id'],
                text=signal_data['text'],
                x=signal_data['x'],
                y=signal_data['y'],
                timestamp=datetime.fromisoformat(signal_data['timestamp'])
            )
            session.add(signal)
            await session.commit()
            await session.refresh(signal)
            logger.debug(f"Signal saved to database: {signal.id}")
            return signal
    
    async def get_recent_signals(self, limit: int = 100) -> List[Signal]:
        """Get recent signals from database"""
        async with await self.get_session() as session:
            from sqlalchemy import select
            
            stmt = select(Signal).order_by(Signal.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            signals = result.scalars().all()
            logger.debug(f"Retrieved {len(signals)} signals from database")
            return signals
    
    async def cleanup_old_signals(self, max_signals: int = None) -> int:
        """Remove old signals beyond the limit"""
        if max_signals is None:
            max_signals = Config.MAX_SIGNALS
        
        async with await self.get_session() as session:
            from sqlalchemy import select, delete
            
            # Count total signals
            count_stmt = select(Signal).count()
            total_count = await session.scalar(count_stmt)
            
            if total_count <= max_signals:
                return 0
            
            # Get IDs of signals to delete (oldest ones)
            signals_to_delete = total_count - max_signals
            
            # Get oldest signal IDs
            oldest_stmt = (
                select(Signal.id)
                .order_by(Signal.created_at.asc())
                .limit(signals_to_delete)
            )
            result = await session.execute(oldest_stmt)
            oldest_ids = [row[0] for row in result.fetchall()]
            
            if oldest_ids:
                # Delete old signals
                delete_stmt = delete(Signal).where(Signal.id.in_(oldest_ids))
                await session.execute(delete_stmt)
                await session.commit()
                
                logger.info(f"Cleaned up {len(oldest_ids)} old signals")
                return len(oldest_ids)
            
            return 0


# Global database manager instance
db_manager = DatabaseManager()