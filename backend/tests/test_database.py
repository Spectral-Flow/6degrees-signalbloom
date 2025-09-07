"""Unit tests for database operations."""

import asyncio
from datetime import datetime, timedelta

import pytest

from database import InnovationObject, Signal, db_manager


class TestDatabaseOperations:
    """Test database operations."""

    @pytest.fixture(autouse=True)
    async def setup_db(self, temp_db):
        """Set up test database for each test."""
        await db_manager.initialize()
        yield
        await db_manager.close()

    async def test_database_initialization(self):
        """Test database initialization."""
        # Database should be initialized by the fixture
        session = await db_manager.get_session()
        assert session is not None
        await session.close()

    async def test_signal_creation_and_retrieval(self):
        """Test creating and retrieving signals."""
        # Create a test signal
        test_signal = Signal(
            id="test_signal_001",
            text="Test signal content",
            x=50.0,
            y=75.0,
            timestamp=datetime.utcnow(),
        )

        # Save signal
        saved_signal = await db_manager.save_signal(test_signal)
        assert saved_signal.id == test_signal.id
        assert saved_signal.text == test_signal.text

        # Retrieve signal
        retrieved_signal = await db_manager.get_signal(test_signal.id)
        assert retrieved_signal is not None
        assert retrieved_signal.id == test_signal.id
        assert retrieved_signal.text == test_signal.text
        assert retrieved_signal.x == 50.0
        assert retrieved_signal.y == 75.0

    async def test_signal_to_dict(self):
        """Test signal serialization to dictionary."""
        test_signal = Signal(
            id="test_signal_dict",
            text="Test signal for dict conversion",
            x=25.0,
            y=80.0,
            timestamp=datetime.utcnow(),
        )

        signal_dict = test_signal.to_dict()
        assert signal_dict["id"] == test_signal.id
        assert signal_dict["text"] == test_signal.text
        assert signal_dict["x"] == 25.0
        assert signal_dict["y"] == 80.0
        assert signal_dict["type"] == "signal"
        assert "timestamp" in signal_dict

    async def test_recent_signals_retrieval(self):
        """Test retrieving recent signals."""
        # Create multiple test signals with different timestamps
        signals = []
        for i in range(5):
            signal = Signal(
                id=f"test_signal_{i:03d}",
                text=f"Test signal {i}",
                x=float(i * 10),
                y=float(i * 10),
                timestamp=datetime.utcnow() - timedelta(minutes=i),
            )
            signals.append(signal)
            await db_manager.save_signal(signal)

        # Retrieve recent signals (limit 3)
        recent_signals = await db_manager.get_recent_signals(limit=3)
        assert len(recent_signals) == 3

        # Should be ordered by timestamp (most recent first)
        assert recent_signals[0].id == "test_signal_000"  # Most recent
        assert recent_signals[1].id == "test_signal_001"
        assert recent_signals[2].id == "test_signal_002"

    async def test_signal_cleanup(self):
        """Test signal cleanup functionality."""
        # Create multiple test signals
        for i in range(10):
            signal = Signal(
                id=f"cleanup_signal_{i:03d}",
                text=f"Cleanup test signal {i}",
                x=float(i * 10),
                y=float(i * 10),
                timestamp=datetime.utcnow() - timedelta(hours=i),
            )
            await db_manager.save_signal(signal)

        # Verify signals were created
        all_signals = await db_manager.get_recent_signals(limit=20)
        cleanup_signals = [s for s in all_signals if s.id.startswith("cleanup_signal_")]
        assert len(cleanup_signals) == 10

        # Perform cleanup (keep only 5 most recent)
        cleaned_count = await db_manager.cleanup_old_signals(limit=5)
        assert cleaned_count > 0

        # Verify cleanup worked
        remaining_signals = await db_manager.get_recent_signals(limit=20)
        cleanup_remaining = [s for s in remaining_signals if s.id.startswith("cleanup_signal_")]
        assert len(cleanup_remaining) <= 5

    async def test_innovation_object_operations(self):
        """Test innovation object database operations."""
        # Test creating innovation object
        innovation_obj = InnovationObject(
            id="test_innovation_001",
            name="Test Innovation",
            description="A test innovation object",
            category="test",
            year_invented=2024,
            inventor="Test Inventor",
            significance_score=7.5,
        )

        # Save innovation object
        async with await db_manager.get_session() as session:
            session.add(innovation_obj)
            await session.commit()

        # Test retrieving innovation tree
        tree = await db_manager.get_innovation_tree("test_innovation_001")
        assert tree is not None
        assert tree["id"] == "test_innovation_001"
        assert tree["name"] == "Test Innovation"
        assert tree["category"] == "test"

    async def test_innovation_data_seeding(self):
        """Test innovation data seeding."""
        # Seed innovation data
        await db_manager.seed_innovation_data()

        # Verify some innovation objects were created
        async with await db_manager.get_session() as session:
            from sqlalchemy import func, select

            count_stmt = select(func.count(InnovationObject.id))
            result = await session.execute(count_stmt)
            count = result.scalar()

            assert count > 0  # Should have seeded some innovation objects

    async def test_database_session_management(self):
        """Test database session creation and management."""
        session1 = await db_manager.get_session()
        session2 = await db_manager.get_session()

        # Sessions should be different instances
        assert session1 is not session2

        # Both sessions should be usable
        assert session1 is not None
        assert session2 is not None

        # Clean up sessions
        await session1.close()
        await session2.close()
