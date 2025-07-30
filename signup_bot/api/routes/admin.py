# Admin-related API routes.
from flask import Blueprint, request, jsonify
import firebase_admin
from firebase_admin import firestore

# Create blueprint
admin_bp = Blueprint('admin', __name__)
db = firestore.client()

@admin_bp.route('/<guild_id>/add_leader_role', methods=['POST'])
def add_leader_role(guild_id):
    """Add a role as a leader role."""
    try:
        data = request.json
        role_id = data.get('role_id')
        
        if not role_id:
            return jsonify({'error': 'Role ID is required'}), 400
        
        # Get or create the leader roles document
        leader_ref = db.collection('servers').document(str(guild_id)).collection('server_leaders').document('roles')
        leader_doc = leader_ref.get()
        
        if leader_doc.exists:
            leader_data = leader_doc.to_dict()
            leader_roles = leader_data.get('leader_role_ids', [])
            
            # Add the role if it's not already a leader
            if role_id not in leader_roles:
                leader_roles.append(role_id)
                leader_ref.update({'leader_role_ids': leader_roles})
        else:
            # Create new leader roles document
            leader_ref.set({'leader_role_ids': [role_id]})
        
        return jsonify({'message': 'Leader role added successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/<guild_id>/remove_leader_role', methods=['POST'])
def remove_leader_role(guild_id):
    """Remove a leader role."""
    try:
        data = request.json
        role_id = data.get('role_id')
        
        if not role_id:
            return jsonify({'error': 'Role ID is required'}), 400
        
        # Get the leader roles document
        leader_ref = db.collection('servers').document(str(guild_id)).collection('server_leaders').document('roles')
        leader_doc = leader_ref.get()
        
        if not leader_doc.exists:
            return jsonify({'error': 'No leader roles found'}), 404
        
        leader_data = leader_doc.to_dict()
        leader_roles = leader_data.get('leader_role_ids', [])
        
        # Remove the role if it exists
        if role_id in leader_roles:
            leader_roles.remove(role_id)
            leader_ref.update({'leader_role_ids': leader_roles})
            return jsonify({'message': 'Leader role removed successfully'}), 200
        else:
            return jsonify({'error': 'Role is not a leader role'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/<guild_id>/leader_roles', methods=['GET'])
def get_leader_roles(guild_id):
    """Get all leader roles for a server."""
    try:
        # Get the leader roles document
        leader_ref = db.collection('servers').document(str(guild_id)).collection('server_leaders').document('roles')
        leader_doc = leader_ref.get()
        
        if not leader_doc.exists:
            return jsonify({'leader_role_ids': []}), 200
        
        leader_data = leader_doc.to_dict()
        return jsonify({'leader_role_ids': leader_data.get('leader_role_ids', [])}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
