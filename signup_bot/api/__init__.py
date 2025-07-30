"""
API module for the Signup Bot.
"""
from flask import Flask, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os
import base64
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import Config after setting up logging to ensure logging is configured
from .. import Config

def create_app():
    # Create and configure the Flask application
    app = Flask(__name__)
    # Configure CORS
    CORS(app, 
         resources={
             r"/api/*": {
                 "origins": ["*"],
                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization"]
             }
         },
         supports_credentials=True
    )
    
    # Initialize Firebase only if it hasn't been initialized yet
    try:
        if not firebase_admin._apps:
            logger.info("Starting Firebase initialization...")
            
            # Get Firebase credentials from Config
            firebase_credentials = Config.get_firebase_credentials()
            logger.info("Successfully decoded Firebase credentials")
            
            # Initialize Firebase with the credentials
            cred = credentials.Certificate(firebase_credentials)
            firebase_admin.initialize_app(cred)
            
            logger.info("Firebase initialized successfully")
            
            # Test Firestore connection
            try:
                db = firestore.client()
                # Try a simple operation to verify the connection
                db.collection('test_connection').document('test').set({'test': True, 'timestamp': firestore.SERVER_TIMESTAMP})
                logger.info("Successfully connected to Firestore")
            except Exception as e:
                logger.error(f"Failed to connect to Firestore: {str(e)}")
                raise ValueError(f"Failed to connect to Firestore: {str(e)}")
        else:
            logger.info("Firebase already initialized, skipping...")
            db = firestore.client()
            
    except ValueError as e:
        logger.error(f"Value error initializing Firebase: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error initializing Firebase: {str(e)}")
        raise ValueError(f"Failed to initialize Firebase: {str(e)}")
    
    # Register blueprints
    from .routes import events_bp, admin_bp
    app.register_blueprint(events_bp, url_prefix='/api/events')
    app.register_blueprint(admin_bp, url_prefix='/api/servers')
    
    @app.errorhandler(500)
    def handle_500_error(e):
        logger.error(f"500 Error: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "Internal Server Error",
            "error": str(e)
        }), 500
    
    # Add a simple health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "ok", "service": "signup-bot-api"})
        
    # Add a 404 handler
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            "status": "error",
            "message": "Resource not found"
        }), 404
        
    return app
