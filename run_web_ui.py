#!/usr/bin/env python3
"""
Launcher for Gradio Web UI
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the client
from clients.gradio_client import demo

if __name__ == "__main__":
    demo.launch(share=False, show_error=True)
