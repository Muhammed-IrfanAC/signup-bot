#!/usr/bin/env python3
"""
Main entry point for the Signup Bot API.
"""
import os
import atexit
import signal
import logging
from signup_bot.api import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = create_app()

def cleanup():
    """Cleanup function to run on exit."""
    import firebase_admin
    
    try:
        # Get the Firebase app and delete it
        firebase_app = firebase_admin.get_app()
        firebase_admin.delete_app(firebase_app)
        logger.info("Firebase app deleted")
    except Exception as e:
        logger.error(f"Error deleting Firebase app: {e}")

# Register cleanup function
def signal_handler(sig, frame):
    logger.info("Shutting down gracefully...")
    cleanup()
    exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Register cleanup for normal exit
atexit.register(cleanup)

def find_available_port(start_port=8001, max_attempts=10):
    """Find an available port starting from start_port."""
    import socket
    
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return port
        except OSError:
            continue
    
    raise RuntimeError(f"Could not find an available port in range {start_port}-{start_port + max_attempts - 1}")

if __name__ == "__main__":
    import uvicorn
    from uvicorn.config import LOGGING_CONFIG
    
    # Configure logging
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOGGING_CONFIG["formatters"]["access"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    try:
        # Get port from environment variable or find an available one
        if "PORT" in os.environ:
            port = int(os.environ["PORT"])
            logger.info(f"Using port from environment variable: {port}")
        else:
            port = find_available_port(8001)
            logger.info(f"Found available port: {port}")
        
        # Run the app using uvicorn with WSGI interface for Flask
        config = uvicorn.Config(
            "signup_bot.api:create_app",
            factory=True,
            host="0.0.0.0",
            port=port,
            log_level="info",
            reload=False,  # Disable reload to avoid port conflicts
            proxy_headers=True,
            forwarded_allow_ips="*",  # In production, replace with your actual trusted IPs
            interface="wsgi"  # Explicitly use WSGI interface for Flask
        )
        
        server = uvicorn.Server(config)
        logger.info(f"Starting API server on port {port}")
        server.run()
        
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Error running the API server: {e}")
        raise
    finally:
        cleanup()