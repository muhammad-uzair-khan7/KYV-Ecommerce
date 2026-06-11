#!/bin/bash
# Start KYV Frontend with Streamlit

echo "Starting KYV Frontend..."
echo ""
echo "Frontend will open at: http://localhost:8501"
echo ""
echo "Make sure backend is running on: http://localhost:8000"
echo ""
echo "To stop the frontend, press CTRL+C"
echo ""

streamlit run FRONTEND.py --logger.level=info
