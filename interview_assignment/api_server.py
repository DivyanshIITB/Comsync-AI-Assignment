"""
Simple Mock Call API Server for Interview Assignment
Minimal dependencies - only Flask required
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import uuid
import time
from threading import Thread

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# In-memory storage
calls = {}

def simulate_call_progression(call_id):
    """Simulate call status changes over time"""
    time.sleep(2)
    if call_id in calls:
        calls[call_id]['status'] = 'ringing'
        calls[call_id]['updated_at'] = datetime.now().isoformat()

    time.sleep(3)
    if call_id in calls:
        calls[call_id]['status'] = 'connected'
        calls[call_id]['updated_at'] = datetime.now().isoformat()

    time.sleep(5)
    if call_id in calls:
        calls[call_id]['status'] = 'completed'
        calls[call_id]['duration'] = 10  # Mock duration in seconds
        calls[call_id]['updated_at'] = datetime.now().isoformat()


@app.route('/api/call', methods=['POST'])
def initiate_call():
    """
    Initiate a new call
    Body: {
        "phone_number": "string (required)"
    }
    """
    data = request.get_json()

    if not data or 'phone_number' not in data:
        return jsonify({'error': 'phone_number is required'}), 400

    phone_number = data['phone_number']

    # Basic phone number validation
    if not phone_number or len(phone_number) < 10:
        return jsonify({'error': 'Invalid phone number'}), 400

    call_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    call_data = {
        'id': call_id,
        'phone_number': phone_number,
        'status': 'initiated',
        'created_at': now,
        'updated_at': now,
        'duration': None
    }

    calls[call_id] = call_data

    # Start call progression in background
    Thread(target=simulate_call_progression, args=(call_id,), daemon=True).start()

    return jsonify({
        'success': True,
        'call': call_data
    }), 201


@app.route('/api/call/<call_id>', methods=['GET'])
def get_call_status(call_id):
    """
    Get status of a specific call
    """
    if call_id not in calls:
        return jsonify({'error': 'Call not found'}), 404

    return jsonify({
        'success': True,
        'call': calls[call_id]
    }), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    print("=" * 50)
    print("Mock Call API Server Starting...")
    print("Server running on: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000, host='0.0.0.0')