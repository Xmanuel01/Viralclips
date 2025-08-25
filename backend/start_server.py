#!/usr/bin/env python3
"""
Startup script for ViralClips.ai backend server
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'backend'))
sys.path.insert(0, str(project_root / 'shared'))
sys.path.insert(0, str(project_root / 'workers'))

# Set environment variables
os.environ['PYTHONPATH'] = f"{project_root}:{project_root}/backend:{project_root}/shared:{project_root}/workers"

# Import and start the server
if __name__ == "__main__":
    try:
        import uvicorn
        print("🚀 Starting ViralClips.ai Backend Server...")
        print(f"📁 Project root: {project_root}")
        print(f"🐍 Python path: {sys.path[:4]}...")
        
        # Start the server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=[str(project_root / "backend"), str(project_root / "shared")],
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        print("🔧 Make sure all dependencies are installed:")
        print("   pip install fastapi uvicorn python-dotenv")
        sys.exit(1)
