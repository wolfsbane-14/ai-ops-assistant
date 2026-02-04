#!/bin/bash
# Test script to verify all functionality

BASE_URL="http://127.0.0.1:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================"
echo "AI Ops Assistant - Test Suite"
echo "========================================"
echo ""

# Test 1: Weather only
echo "Test 1: Weather API Integration"
echo "Task: Get weather in Paris"
response=$(curl -s -X POST "$BASE_URL/run" \
  -H "Content-Type: application/json" \
  -d '{"task":"Get weather in Paris"}')

if echo "$response" | grep -q "Paris"; then
    echo -e "${GREEN}✓ PASS${NC} - Weather API working"
else
    echo -e "${RED}✗ FAIL${NC} - Weather API failed"
fi
echo ""

# Test 2: GitHub only
echo "Test 2: GitHub API Integration"
echo "Task: Find FastAPI repositories"
response=$(curl -s -X POST "$BASE_URL/run" \
  -H "Content-Type: application/json" \
  -d '{"task":"Find popular FastAPI repositories"}')

if echo "$response" | grep -q "FastAPI\|fastapi"; then
    echo -e "${GREEN}✓ PASS${NC} - GitHub API working"
else
    echo -e "${RED}✗ FAIL${NC} - GitHub API failed"
fi
echo ""

# Test 3: Combined (both APIs)
echo "Test 3: Multi-API Integration"
echo "Task: Vector DB repo + Berlin weather"
response=$(curl -s -X POST "$BASE_URL/run" \
  -H "Content-Type: application/json" \
  -d '{"task":"Find a repo about vector databases and get weather in Berlin"}')

if echo "$response" | grep -q "Berlin" && echo "$response" | grep -q "repo\|repository"; then
    echo -e "${GREEN}✓ PASS${NC} - Multi-agent coordination working"
else
    echo -e "${RED}✗ FAIL${NC} - Multi-agent coordination failed"
fi
echo ""

echo "========================================"
echo "Test Suite Complete"
echo "========================================"
