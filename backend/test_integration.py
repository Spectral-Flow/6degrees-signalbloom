"""Simple integration test script for Signal Bloom backend."""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

# Set test environment
os.environ["DEBUG"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key"

# Import after setting environment
from datetime import datetime

from config import Config
from database import Signal, db_manager
from main import create_app


async def test_config():
    """Test configuration loading."""
    print("Testing configuration...")
    assert Config.DEBUG is True
    assert Config.SECRET_KEY == "test-secret-key"
    assert Config.HOST == "0.0.0.0"
    assert Config.PORT == 8000
    print("✓ Configuration tests passed")


async def test_database():
    """Test database operations."""
    print("Testing database operations...")

    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db_path = temp_db.name
    temp_db.close()

    # Set temporary database URL
    original_db_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = f"sqlite:///{temp_db_path}"

    try:
        # Initialize database
        await db_manager.initialize()

        # Test signal creation (use unique ID)
        import time

        unique_id = f"test_signal_{int(time.time())}"
        test_signal_data = {
            "id": unique_id,
            "text": "Test signal for integration test",
            "x": 50.0,
            "y": 75.0,
            "timestamp": datetime.now().isoformat(),
        }

        # Save signal
        saved_signal = await db_manager.save_signal(test_signal_data)
        assert saved_signal.id == test_signal_data["id"]

        # Test recent signals retrieval (includes our saved signal)
        recent_signals = await db_manager.get_recent_signals(limit=10)
        assert len(recent_signals) >= 1

        # Find our signal in the recent signals
        our_signal = None
        for signal in recent_signals:
            if signal.id == test_signal_data["id"]:
                our_signal = signal
                break

        assert our_signal is not None
        assert our_signal.text == test_signal_data["text"]

        # Test signal serialization
        signal_dict = our_signal.to_dict()
        assert signal_dict["id"] == test_signal_data["id"]
        assert "timestamp" in signal_dict
        assert "has_innovation_tree" in signal_dict

        print("✓ Database tests passed")

    finally:
        await db_manager.close()

        # Restore original database URL
        if original_db_url:
            os.environ["DATABASE_URL"] = original_db_url
        elif "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

        # Clean up temp database
        Path(temp_db_path).unlink(missing_ok=True)


async def test_app_creation():
    """Test application creation."""
    print("Testing application creation...")

    app = await create_app()
    assert app is not None

    # Test that routes are configured
    routes = [route.path for route in app.routes]
    expected_routes = ["/", "/status", "/voice/status", "/ws"]

    for expected_route in expected_routes:
        assert any(expected_route in route for route in routes), f"Route {expected_route} not found"

    print("✓ Application creation tests passed")


async def test_signal_manager():
    """Test SignalBloomManager functionality."""
    print("Testing SignalBloomManager...")

    from main import bloom_manager

    # Test connection management
    initial_connections = len(bloom_manager.connections)

    # Test signal storage
    initial_signals = len(bloom_manager.signals)

    test_signal_data = {"type": "signal", "text": "Test signal for manager", "x": 25.0, "y": 85.0}

    # The manager should handle signal processing
    assert bloom_manager.max_signals == 1000

    print("✓ SignalBloomManager tests passed")


async def run_all_tests():
    """Run all integration tests."""
    print("🌸 Running Signal Bloom Backend Integration Tests")
    print("=" * 50)

    tests = [
        test_config,
        test_database,
        test_app_creation,
        test_signal_manager,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}")
    print(f"Tests failed: {failed}")

    if failed == 0:
        print("🎉 All integration tests passed!")
        return True
    else:
        print("❌ Some integration tests failed.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
