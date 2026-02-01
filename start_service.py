"""
Simple script to start the Action Blocker Service
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from action_blocker_service import ActionBlockerService

if __name__ == "__main__":
    service = ActionBlockerService()
    
    if not service.start():
        print("Failed to start service")
        sys.exit(1)
    
    try:
        # Keep running
        import time
        while service.running:
            time.sleep(1)
    except KeyboardInterrupt:
        service.stop()










