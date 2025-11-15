#!/usr/bin/env python3
"""
Direct startup script for debugging the Banking Bot API
"""
import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Banking Bot API for debugging...")
    print(f"📁 Project root: {PROJECT_ROOT}")
    print(f"🐍 Python path: {sys.path}")
    
    # Run the server
    uvicorn.run(
        "src.app.main:app",
        host="0.0.0.0",
        port=2024,
        reload=True,
        log_level="debug",
        access_log=True
    )
