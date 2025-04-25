# app.py
from flask import Flask, request, jsonify, send_file
import io
import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
import requests
from dotenv import load_dotenv
from typing import List
import base64
import json

# Load environment variables
load_dotenv()
AUTH = os.environ['AUTH']

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase
firebase_json_base64 = os.environ['FIREBASE_CRED']

if firebase_json_base64 is None:
    raise ValueError("FIREBASE_CRED environment variable not found")

try:
    firebase_json_bytes = base64.b64decode(firebase_json_base64)
    firebase_dict = json.loads(firebase_json_bytes.decode('utf-8'))
except Exception as e:
    raise ValueError("Failed to decode and parse Firebase credentials: " + str(e))

cred = credentials.Certificate(firebase_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()

# Helper Functions
def player_get(player_tag: str) -> dict:
    """Retrieve player data from the external API."""
    url = f'https://cocproxy.royaleapi.dev/v1/players/%23{player_tag}'
    response = requests.get(url, headers={'Authorization': AUTH})
    return response.json()

def get_highest_index(event_name: str):
    """Retrieve the highest signup index for a given event."""
    event_ref = db.collection('events').document(event_name).collection('signups')
    query = event_ref.order_by('index', direction=firestore.Query.DESCENDING).limit(1)
    results = query.stream()
    
    highest_index = None
    for doc in results:
        highest_index = doc.get('index')
    return highest_index

# API Routes
@app.route('/api/events', methods=['POST'])
def create_event():
    try:
        data = request.json
        event_name = data.get('event_name')
        event_role = data.get('event_role', 675730248175976458)
        guild_id = data.get('guild_id')
        message_id = data.get('message_id')  # Add message_id to the request

        if not event_name or not guild_id:
            return jsonify({'error': 'Event name and guild ID are required'}), 400

        # Check if event already exists
        event_ref = db.collection('servers').document(str(guild_id)).collection('events').document(event_name)
        if event_ref.get().exists:
            return jsonify({'error': 'Event already exists'}), 409

        # Create event document with message ID
        event_document = {
            'event_name': event_name,
            'created_at': datetime.now().isoformat(),
            'role_id': event_role,
            'registration': 'open',
            'signup_count': 0,
            'message_id': message_id,  # Store the message ID
            'embed': {
                'title': f"{event_name.upper()} Roster",
                'description': "Event roster and signups",
                'fields': [
                    {'name': 'Total Signups', 'value': '0', 'inline': False},
                    {'name': 'TH Composition', 'value': 'No signups yet', 'inline': False}
                ],
                'color': 0x00ff00  # Green color
            }
        }
        event_ref.set(event_document)

        return jsonify({'message': 'Event created successfully', 'event_name': event_name}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/events/<event_name>/signup', methods=['POST'])
def signup_player(event_name):
    try:
        data = request.json
        player_tag = data.get('player_tag')
        discord_name = data.get('discord_name')
        guild_id = data.get('guild_id')

        if not all([player_tag, discord_name, guild_id]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Check if event exists and is open
        event_ref = db.collection('servers').document(str(guild_id)).collection('events').document(event_name)
        event_doc = event_ref.get()
        
        if not event_doc.exists:
            return jsonify({'error': 'Event not found'}), 404
            
        event_data = event_doc.to_dict()
        if event_data.get('registration') == 'closed':
            return jsonify({'error': 'Registration is closed'}), 403

        # Check if player is already signed up
        existing_signup = event_ref.collection('signups').where('player_tag', '==', player_tag).limit(1).get()
        if len(list(existing_signup)) > 0:
            return jsonify({'error': 'Player already signed up'}), 409

        # Get player data from API
        player_data = player_get(player_tag[1:])
        player_name = player_data['name']
        player_th = player_data['townHallLevel']

        # Create signup
        signup_count = get_highest_index(event_name) or 0
        signup_count += 1
        
        user_signup = {
            'index': signup_count,
            'player_name': player_name,
            'player_tag': player_tag,
            'player_th': player_th,
            'player_discord': discord_name
        }
        
        event_ref.collection('signups').add(user_signup)
        event_ref.update({'signup_count': signup_count})

        return jsonify({
            'message': 'Signup successful',
            'player_name': player_name,
            'player_th': player_th
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/events/<event_name>/remove', methods=['POST'])
def remove_player(event_name):
    try:
        data = request.json
        player_tag = data.get('player_tag')
        requester_discord_name = data.get('requester_discord_name')
        is_leader = data.get('is_leader', False)
        guild_id = data.get('guild_id')

        if not all([player_tag, requester_discord_name, guild_id]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Check if event exists
        event_ref = db.collection('servers').document(str(guild_id)).collection('events').document(event_name)
        event_doc = event_ref.get()
        if not event_doc.exists:
            return jsonify({'error': 'Event not found'}), 404

        # Find player signup
        signup_query = event_ref.collection('signups').where('player_tag', '==', player_tag.upper())
        signup_docs = list(signup_query.stream())

        if not signup_docs:
            return jsonify({'error': 'Player not found in roster'}), 404

        signup_doc = signup_docs[0]
        signup_data = signup_doc.to_dict()

        # Check permissions
        if not is_leader and requester_discord_name != signup_data.get('player_discord'):
            return jsonify({'error': 'Unauthorized to remove this player'}), 403

        # Get player data for response
        player_data = {
            'player_name': signup_data.get('player_name'),
            'player_th': signup_data.get('player_th')
        }

        # Remove player and update indices
        target_index = signup_data['index']
        signup_doc.reference.delete()

        # Update subsequent indices in batches
        batch = db.batch()
        subsequent_signups = event_ref.collection('signups').where('index', '>', target_index).stream()
        
        for doc in subsequent_signups:
            doc_ref = doc.reference
            new_data = doc.to_dict()
            new_data['index'] = new_data['index'] - 1
            batch.update(doc_ref, new_data)

        # Update total count
        current_count = event_doc.to_dict()['signup_count']
        batch.update(event_ref, {'signup_count': current_count - 1})
        
        # Commit all updates
        batch.commit()

        return jsonify({
            'message': 'Player removed successfully',
            'player_data': player_data
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/events/<event_name>/export', methods=['GET'])
def export_event_data(event_name):
    try:
        guild_id = request.args.get('guild_id')
        if not guild_id:
            return jsonify({'error': 'Guild ID is required'}), 400

        event_ref = db.collection('servers').document(str(guild_id)).collection('events').document(event_name)
        if not event_ref.get().exists:
            return jsonify({'error': 'Event not found'}), 404

        signups = event_ref.collection('signups').stream()
        data = [signup.to_dict() for signup in signups]

        if not data:
            return jsonify({'error': 'No signups found'}), 404

        df = pd.DataFrame(data)
        
        # Create a temporary file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Signups')
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = workbook.active

            # Format headers
            for cell in worksheet[1]:
                cell.font = Font(bold=True)

            # Adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column = [cell for cell in column]
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[get_column_letter(column[0].column)].width = adjusted_width

        # Prepare the response with the file content
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{event_name}_export.xlsx"
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/events/<event_name>', methods=['DELETE'])
def delete_event(event_name):
    try:
        guild_id = request.args.get('guild_id')
        if not guild_id:
            return jsonify({'error': 'Guild ID is required'}), 400

        event_ref = db.collection('servers').document(str(guild_id)).collection('events').document(event_name)
        if not event_ref.get().exists:
            return jsonify({'error': 'Event not found'}), 404

        # Delete all signups
        signups = event_ref.collection('signups').stream()
        for signup in signups:
            signup.reference.delete()

        # Delete event document
        event_ref.delete()

        return jsonify({'message': 'Event deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events/<event_name>/check', methods=['POST'])
def check_player(event_name):
    try:
        data = request.json
        player_tag = data.get('player_tag')
        guild_id = data.get('guild_id')

        if not player_tag or not guild_id:
            return jsonify({'error': 'Player tag and guild ID are required'}), 400

        # Check if event exists
        event_ref = db.collection('servers').document(str(guild_id)).collection('events').document(event_name)
        if not event_ref.get().exists:
            return jsonify({'error': 'Event not found'}), 404

        # Check if player is signed up
        signup_query = event_ref.collection('signups').where('player_tag', '==', player_tag.upper())
        signup_docs = list(signup_query.stream())

        if not signup_docs:
            return jsonify({
                'is_signed_up': False,
                'message': 'Player is not signed up for this event'
            }), 200

        # Get player details if signed up
        signup_data = signup_docs[0].to_dict()
        return jsonify({
            'is_signed_up': True,
            'message': 'Player is signed up for this event',
            'player_data': {
                'name': signup_data.get('player_name'),
                'th_level': signup_data.get('player_th'),
                'discord_name': signup_data.get('player_discord'),
                'index': signup_data.get('index')
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events/<event_name>/close', methods=['POST'])
def close_registration(event_name):
    try:
        guild_id = request.json.get('guild_id')
        if not guild_id:
            return jsonify({'error': 'Guild ID is required'}), 400

        # Check if event exists
        event_ref = db.collection('servers').document(str(guild_id)).collection('events').document(event_name)
        event_doc = event_ref.get()
        
        if not event_doc.exists:
            return jsonify({'error': 'Event not found'}), 404
            
        event_data = event_doc.to_dict()
        
        # Check if registration is already closed
        if event_data.get('registration') == 'closed':
            return jsonify({'error': 'Registration is already closed'}), 400

        # Update registration status
        event_ref.update({'registration': 'closed'})

        return jsonify({
            'message': 'Registration closed successfully',
            'event_name': event_name
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events', methods=['GET'])
def list_events():
    try:
        guild_id = request.args.get('guild_id')
        if not guild_id:
            return jsonify({'error': 'Guild ID is required'}), 400

        events_ref = db.collection('servers').document(str(guild_id)).collection('events')
        events = []
        
        for doc in events_ref.stream():
            event_data = doc.to_dict()
            event_data['id'] = doc.id
            events.append(event_data)
            
        return jsonify({
            'events': events,
            'count': len(events)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events/<event_name>', methods=['GET'])
def get_event(event_name):
    try:
        guild_id = request.args.get('guild_id')
        if not guild_id:
            return jsonify({'error': 'Guild ID is required'}), 400

        # Fetch the event data from Firestore
        event_ref = db.collection('servers').document(str(guild_id)).collection('events').document(event_name)
        event_doc = event_ref.get()
        if not event_doc.exists:
            return jsonify({'error': 'Event not found'}), 404

        event_data = event_doc.to_dict()

        # Fetch signups for the event
        signups = event_ref.collection('signups').stream()
        signup_data = [signup.to_dict() for signup in signups]

        # Add signup data to the event data
        event_data['signups'] = signup_data

        return jsonify(event_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/servers/<guild_id>/add_leader_role', methods=['POST'])
def add_leader_role(guild_id):
    try:
        data = request.json
        role_id = data.get('role_id')

        if not role_id:
            return jsonify({'error': 'Role ID is required'}), 400

        # Fetch the leader roles for the server
        leader_ref = db.collection('servers').document(guild_id).collection('server_leaders').document('roles')
        leader_data = leader_ref.get().to_dict() or {"leader_role_ids": []}

        # Add the role if it doesn't already exist
        if role_id not in leader_data["leader_role_ids"]:
            leader_data["leader_role_ids"].append(role_id)
            leader_ref.set(leader_data)

        return jsonify({'message': 'Leader role added successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers/<guild_id>/remove_leader_role', methods=['POST'])
def remove_leader_role(guild_id):
    try:
        data = request.json
        role_id = data.get('role_id')

        if not role_id:
            return jsonify({'error': 'Role ID is required'}), 400

        # Fetch the leader roles for the server
        leader_ref = db.collection('servers').document(guild_id).collection('server_leaders').document('roles')
        leader_data = leader_ref.get().to_dict() or {"leader_role_ids": []}

        # Remove the role if it exists
        if role_id in leader_data["leader_role_ids"]:
            leader_data["leader_role_ids"].remove(role_id)
            leader_ref.set(leader_data)

        return jsonify({'message': 'Leader role removed successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers/<guild_id>/leader_roles', methods=['GET'])
def get_leader_roles(guild_id):
    try:
        # Fetch the leader roles for the server
        leader_ref = db.collection('servers').document(guild_id).collection('server_leaders').document('roles')
        leader_data = leader_ref.get().to_dict() or {"leader_role_ids": []}

        return jsonify({'leader_role_ids': leader_data["leader_role_ids"]}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
@app.route('/api/events/<event_name>/update_message_id', methods=['POST'])
def update_message_id(event_name):
    try:
        data = request.json
        guild_id = data.get('guild_id')
        message_id = data.get('message_id')

        if not guild_id or not message_id:
            return jsonify({'error': 'Guild ID and message ID are required'}), 400

        # Update the message ID in Firestore
        event_ref = db.collection('servers').document(str(guild_id)).collection('events').document(event_name)
        if not event_ref.get().exists:
            return jsonify({'error': 'Event not found'}), 404

        event_ref.update({'message_id': message_id})

        return jsonify({'message': 'Message ID updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/events/<event_name>/signups', methods=['GET'])
def get_signups(event_name):
    try:
        guild_id = request.args.get('guild_id')
        if not guild_id:
            return jsonify({'error': 'Guild ID is required'}), 400

        # Fetch signups for the event
        event_ref = db.collection('servers').document(str(guild_id)).collection('events').document(event_name)
        if not event_ref.get().exists:
            return jsonify({'error': 'Event not found'}), 404

        signups = event_ref.collection('signups').stream()
        signup_data = [signup.to_dict() for signup in signups]

        return jsonify({'signups': signup_data}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    app.run(host="0.0.0.0", port= 8080, debug=True)