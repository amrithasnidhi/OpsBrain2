#!/bin/bash
set -e

echo "Starting OpsBrain2 Integration Setup..."

# 1. Setup Backend
echo "Setting up backend..."
# Activate venv if exists
if [ -d "venv" ]; then
    source venv/Scripts/activate || source venv/bin/activate
fi

cd app/backend
pip install -r requirements.txt
# Start backend in background
uvicorn main:app --reload &
BACKEND_PID=$!
cd ../..

# 2. Setup Frontend
echo "Setting up frontend..."
cd app/frontend
npm install
# Start frontend
npm run dev &
FRONTEND_PID=$!

echo "OpsBrain2 is running!"
echo "Backend: http://127.0.0.1:8000"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop both servers."

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM
wait $BACKEND_PID $FRONTEND_PID
