"""
API routes package.
"""
from .events import events_bp
from .admin import admin_bp

# Export blueprints
__all__ = ['events_bp', 'admin_bp']
