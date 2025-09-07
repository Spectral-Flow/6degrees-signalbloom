"""
Database models and setup for Signal Bloom
"""

import asyncio
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, String, DateTime, Float, Integer, Text, create_engine, event, 
    ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
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
    innovation_object_id = Column(String, ForeignKey('innovation_objects.id'), nullable=True)
    
    # Relationship to innovation object
    innovation_object = relationship("InnovationObject", back_populates="signals")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'text': self.text,
            'x': self.x,
            'y': self.y,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'has_innovation_tree': self.innovation_object_id is not None,
            'innovation_object_id': self.innovation_object_id
        }


class InnovationObject(Base):
    """Objects that have innovation histories (e.g., smartphone, computer)"""
    __tablename__ = 'innovation_objects'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)  # e.g., 'technology', 'tool', 'concept'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    signals = relationship("Signal", back_populates="innovation_object")
    innovation_links = relationship("InnovationLink", foreign_keys="InnovationLink.object_id", back_populates="innovation_object")
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category
        }


class Innovation(Base):
    """Historical innovations/inventions"""
    __tablename__ = 'innovations'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    year = Column(Integer)  # Year of innovation
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    innovation_links = relationship("InnovationLink", foreign_keys="InnovationLink.innovation_id", back_populates="innovation")
    inventor_links = relationship("InventorInnovation", back_populates="innovation")
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'year': self.year
        }


class Inventor(Base):
    """Historical inventors/creators"""
    __tablename__ = 'inventors'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    birth_year = Column(Integer)
    death_year = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    inventor_links = relationship("InventorInnovation", back_populates="inventor")
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'birth_year': self.birth_year,
            'death_year': self.death_year
        }


class InnovationLink(Base):
    """Links between objects and their contributing innovations"""
    __tablename__ = 'innovation_links'
    
    id = Column(String, primary_key=True)
    object_id = Column(String, ForeignKey('innovation_objects.id'), nullable=False)
    innovation_id = Column(String, ForeignKey('innovations.id'), nullable=False)
    relationship_type = Column(String, default='contributes_to')  # e.g., 'enables', 'contributes_to', 'precedes'
    description = Column(Text)  # How this innovation contributes to the object
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    innovation_object = relationship("InnovationObject", back_populates="innovation_links")
    innovation = relationship("Innovation", back_populates="innovation_links")
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'object_id': self.object_id,
            'innovation_id': self.innovation_id,
            'relationship_type': self.relationship_type,
            'description': self.description
        }


class InventorInnovation(Base):
    """Links between inventors and their innovations"""
    __tablename__ = 'inventor_innovations'
    
    id = Column(String, primary_key=True)
    inventor_id = Column(String, ForeignKey('inventors.id'), nullable=False)
    innovation_id = Column(String, ForeignKey('innovations.id'), nullable=False)
    role = Column(String, default='creator')  # e.g., 'creator', 'co-inventor', 'contributor'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    inventor = relationship("Inventor", back_populates="inventor_links")
    innovation = relationship("Innovation", back_populates="inventor_links")


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
                timestamp=datetime.fromisoformat(signal_data['timestamp']),
                innovation_object_id=signal_data.get('innovation_object_id')
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

    async def find_innovation_object(self, text: str) -> Optional['InnovationObject']:
        """Find innovation object by matching signal text"""
        async with await self.get_session() as session:
            from sqlalchemy import select
            
            # First try exact match
            stmt = select(InnovationObject).where(InnovationObject.name.ilike(text.strip()))
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            
            if obj:
                return obj
            
            # Try partial match
            stmt = select(InnovationObject).where(InnovationObject.name.ilike(f'%{text.strip()}%'))
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            
            return obj

    async def get_innovation_tree(self, object_id: str) -> dict:
        """Get complete innovation tree for an object"""
        async with await self.get_session() as session:
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            
            # Get object with all its innovation links
            stmt = (
                select(InnovationObject)
                .options(selectinload(InnovationObject.innovation_links).selectinload(InnovationLink.innovation))
                .where(InnovationObject.id == object_id)
            )
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            
            if not obj:
                return None
            
            # Build the tree structure
            tree = {
                'object': obj.to_dict(),
                'innovations': []
            }
            
            for link in obj.innovation_links:
                innovation = link.innovation
                
                # Get inventors for this innovation
                inventor_stmt = (
                    select(InventorInnovation)
                    .options(selectinload(InventorInnovation.inventor))
                    .where(InventorInnovation.innovation_id == innovation.id)
                )
                inventor_result = await session.execute(inventor_stmt)
                inventor_links = inventor_result.scalars().all()
                
                inventors = []
                for inv_link in inventor_links:
                    inventor_data = inv_link.inventor.to_dict()
                    inventor_data['role'] = inv_link.role
                    inventors.append(inventor_data)
                
                innovation_data = innovation.to_dict()
                innovation_data['inventors'] = inventors
                innovation_data['relationship'] = {
                    'type': link.relationship_type,
                    'description': link.description
                }
                
                tree['innovations'].append(innovation_data)
            
            return tree

    async def seed_innovation_data(self):
        """Seed database with sample innovation data"""
        async with await self.get_session() as session:
            from sqlalchemy import select
            
            # Check if data already exists
            stmt = select(InnovationObject).limit(1)
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                logger.info("Innovation data already exists, skipping seed")
                return
            
            logger.info("Seeding innovation database with sample data...")
            
            try:
                # Create inventors
                inventors_data = [
                    {'id': 'bell', 'name': 'Alexander Graham Bell', 'description': 'Inventor of the telephone', 'birth_year': 1847, 'death_year': 1922},
                    {'id': 'shockley', 'name': 'William Shockley', 'description': 'Co-inventor of the transistor', 'birth_year': 1910, 'death_year': 1989},
                    {'id': 'bardeen', 'name': 'John Bardeen', 'description': 'Co-inventor of the transistor', 'birth_year': 1908, 'death_year': 1991},
                    {'id': 'brattain', 'name': 'Walter Brattain', 'description': 'Co-inventor of the transistor', 'birth_year': 1902, 'death_year': 1987},
                    {'id': 'turing', 'name': 'Alan Turing', 'description': 'Father of computer science', 'birth_year': 1912, 'death_year': 1954},
                    {'id': 'vonneumann', 'name': 'John von Neumann', 'description': 'Computer architecture pioneer', 'birth_year': 1903, 'death_year': 1957},
                    {'id': 'jobs', 'name': 'Steve Jobs', 'description': 'Co-founder of Apple', 'birth_year': 1955, 'death_year': 2011},
                    {'id': 'wozniak', 'name': 'Steve Wozniak', 'description': 'Co-founder of Apple', 'birth_year': 1950, 'death_year': None}
                ]
                
                for inv_data in inventors_data:
                    inventor = Inventor(**inv_data)
                    session.add(inventor)
                
                # Create innovations
                innovations_data = [
                    {'id': 'telephone', 'name': 'Telephone', 'description': 'Device for voice communication over distance', 'year': 1876},
                    {'id': 'transistor', 'name': 'Transistor', 'description': 'Semiconductor device for amplifying and switching electronic signals', 'year': 1947},
                    {'id': 'computer', 'name': 'Electronic Computer', 'description': 'Programmable electronic device for processing data', 'year': 1943},
                    {'id': 'microprocessor', 'name': 'Microprocessor', 'description': 'Central processing unit on a single chip', 'year': 1971},
                    {'id': 'personal_computer', 'name': 'Personal Computer', 'description': 'Computer designed for individual use', 'year': 1975},
                    {'id': 'cellular_network', 'name': 'Cellular Network', 'description': 'Mobile phone network using cellular technology', 'year': 1973}
                ]
                
                for inn_data in innovations_data:
                    innovation = Innovation(**inn_data)
                    session.add(innovation)
                
                # Create innovation objects
                objects_data = [
                    {'id': 'smartphone', 'name': 'Smartphone', 'description': 'Mobile phone with computer capabilities', 'category': 'technology'},
                    {'id': 'computer', 'name': 'Computer', 'description': 'Electronic device for processing data', 'category': 'technology'},
                    {'id': 'telephone', 'name': 'Telephone', 'description': 'Device for voice communication', 'category': 'technology'}
                ]
                
                for obj_data in objects_data:
                    obj = InnovationObject(**obj_data)
                    session.add(obj)
                
                await session.commit()
                
                # Create inventor-innovation links
                inventor_innovation_data = [
                    {'id': 'bell_telephone', 'inventor_id': 'bell', 'innovation_id': 'telephone', 'role': 'inventor'},
                    {'id': 'shockley_transistor', 'inventor_id': 'shockley', 'innovation_id': 'transistor', 'role': 'co-inventor'},
                    {'id': 'bardeen_transistor', 'inventor_id': 'bardeen', 'innovation_id': 'transistor', 'role': 'co-inventor'},
                    {'id': 'brattain_transistor', 'inventor_id': 'brattain', 'innovation_id': 'transistor', 'role': 'co-inventor'},
                    {'id': 'turing_computer', 'inventor_id': 'turing', 'innovation_id': 'computer', 'role': 'theoretical_founder'},
                    {'id': 'vonneumann_computer', 'inventor_id': 'vonneumann', 'innovation_id': 'computer', 'role': 'architect'},
                    {'id': 'jobs_pc', 'inventor_id': 'jobs', 'innovation_id': 'personal_computer', 'role': 'popularizer'},
                    {'id': 'wozniak_pc', 'inventor_id': 'wozniak', 'innovation_id': 'personal_computer', 'role': 'engineer'}
                ]
                
                for link_data in inventor_innovation_data:
                    link = InventorInnovation(**link_data)
                    session.add(link)
                
                # Create innovation object links
                innovation_links_data = [
                    {
                        'id': 'smartphone_telephone',
                        'object_id': 'smartphone',
                        'innovation_id': 'telephone',
                        'relationship_type': 'builds_upon',
                        'description': 'Smartphones evolved from and incorporate telephone technology'
                    },
                    {
                        'id': 'smartphone_transistor',
                        'object_id': 'smartphone',
                        'innovation_id': 'transistor',
                        'relationship_type': 'enables',
                        'description': 'Transistors are fundamental components in smartphone electronics'
                    },
                    {
                        'id': 'smartphone_computer',
                        'object_id': 'smartphone',
                        'innovation_id': 'computer',
                        'relationship_type': 'combines_with',
                        'description': 'Smartphones are essentially handheld computers'
                    },
                    {
                        'id': 'smartphone_cellular',
                        'object_id': 'smartphone',
                        'innovation_id': 'cellular_network',
                        'relationship_type': 'requires',
                        'description': 'Smartphones depend on cellular networks for mobile communication'
                    },
                    {
                        'id': 'computer_transistor',
                        'object_id': 'computer',
                        'innovation_id': 'transistor',
                        'relationship_type': 'enables',
                        'description': 'Modern computers are built on transistor technology'
                    }
                ]
                
                for link_data in innovation_links_data:
                    link = InnovationLink(**link_data)
                    session.add(link)
                
                await session.commit()
                logger.info("Successfully seeded innovation database")
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to seed innovation data: {e}")
                raise


# Global database manager instance
db_manager = DatabaseManager()