#!/bin/bash

# Signal Bloom - Comprehensive Test Script
# Tests all functionality including voice integration

set -e

echo "🌸 Signal Bloom - Running Comprehensive Tests"
echo "============================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "\n${YELLOW}Testing: $test_name${NC}"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✓ PASSED: $test_name${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAILED: $test_name${NC}"
        ((TESTS_FAILED++))
    fi
}

# Check prerequisites
echo -e "\n${YELLOW}Checking Prerequisites...${NC}"
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js is required but not installed."; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "npm is required but not installed."; exit 1; }

# Backend Tests
echo -e "\n${YELLOW}Backend Tests${NC}"
cd backend

# Test Python imports
run_test "Backend imports" "python3 -c 'import main; print(\"Backend imports successfully\")'"

# Test configuration loading
run_test "Configuration loading" "python3 -c 'from config import Config; print(f\"Database: {Config.DATABASE_URL}\")'"

# Test database module
run_test "Database module" "python3 -c 'import database; print(\"Database module loaded\")'"

# Test voice module
run_test "Voice module" "python3 -c 'import voice; print(\"Voice module loaded\")'"

# Start backend server for API tests
echo -e "\n${YELLOW}Starting backend server for API tests...${NC}"
python3 main.py &
BACKEND_PID=$!
sleep 5

# Test health endpoint
run_test "Health endpoint" "curl -f -s http://localhost:8000/status > /dev/null"

# Test voice status endpoint
run_test "Voice status endpoint" "curl -f -s http://localhost:8000/voice/status > /dev/null"

# Test development page
run_test "Development page" "curl -f -s http://localhost:8000/ > /dev/null"

# Kill backend server
kill $BACKEND_PID 2>/dev/null || true
sleep 2

cd ..

# Frontend Tests
echo -e "\n${YELLOW}Frontend Tests${NC}"
cd frontend

# Test npm install
run_test "Frontend dependencies" "npm ci --silent"

# Test build
run_test "Frontend build" "npm run build > /dev/null 2>&1"

# Check for build output
run_test "Build output exists" "test -d .svelte-kit/output"

cd ..

# Docker Tests (if Docker is available)
if command -v docker >/dev/null 2>&1 && command -v docker-compose >/dev/null 2>&1; then
    echo -e "\n${YELLOW}Docker Tests${NC}"
    
    # Test Docker build
    run_test "Backend Docker build" "docker build -t signal-bloom-backend backend > /dev/null 2>&1"
    run_test "Frontend Docker build" "docker build -t signal-bloom-frontend frontend > /dev/null 2>&1"
    
    # Test docker-compose validation
    run_test "Docker Compose validation" "docker-compose config > /dev/null 2>&1"
    
    # Cleanup Docker images
    docker rmi signal-bloom-backend signal-bloom-frontend 2>/dev/null || true
else
    echo -e "\n${YELLOW}Skipping Docker tests (Docker not available)${NC}"
fi

# Integration Test
echo -e "\n${YELLOW}Integration Test${NC}"

# Start both servers for integration test
echo "Starting backend..."
cd backend
python3 main.py &
BACKEND_PID=$!
sleep 3

echo "Starting frontend..."
cd ../frontend
npm run dev -- --host 0.0.0.0 --port 5173 > /dev/null 2>&1 &
FRONTEND_PID=$!
sleep 5

# Test WebSocket connectivity with a simple Python script
cat > ../test_websocket.py << 'EOF'
import asyncio
import websockets
import json
import sys

async def test_websocket():
    try:
        async with websockets.connect("ws://localhost:8000/ws") as websocket:
            # Send a test signal
            test_signal = {
                "type": "signal",
                "text": "Test signal from automated test",
                "x": 50,
                "y": 50
            }
            await websocket.send(json.dumps(test_signal))
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            
            if data.get("type") == "signal" and "Test signal" in data.get("text", ""):
                print("WebSocket test successful")
                return True
            else:
                print("WebSocket test failed - unexpected response")
                return False
                
    except Exception as e:
        print(f"WebSocket test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    sys.exit(0 if result else 1)
EOF

cd ..
run_test "WebSocket integration" "python3 test_websocket.py"

# Cleanup
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
rm -f test_websocket.py

# Test Summary
echo -e "\n${YELLOW}Test Summary${NC}"
echo "============"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed! Signal Bloom is ready for deployment.${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed. Please check the output above.${NC}"
    exit 1
fi