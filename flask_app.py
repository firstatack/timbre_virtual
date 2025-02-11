import os
import logging
from flask import Flask, request, jsonify, send_from_directory
import requests
import json
from datetime import datetime, timedelta
import uuid
import time

app = Flask(__name__, static_folder='static')

logging.basicConfig(level=logging.INFO)

# *** CONFIGURACIÓN SEGURA DE LAS CREDENCIALES ***
API_KEY = os.environ.get('SINRIC_API_KEY')
DEVICE_ID = os.environ.get('SINRIC_DEVICE_ID')
PORTAL_ID = os.environ.get('SINRIC_PORTAL_ID')  # Nueva variable para portalId

if not API_KEY or not DEVICE_ID or not PORTAL_ID:
    raise ValueError("Las variables de entorno SINRIC_API_KEY, SINRIC_DEVICE_ID y SINRIC_PORTAL_ID deben estar configuradas.")
# *********************************************

# Variables para almacenar el access token y su tiempo de expiración
access_token = None
expires_at = None

def get_access_token():
    global access_token, expires_at
    if access_token and expires_at and expires_at > datetime.utcnow():  # Token válido
        return access_token

    try:
        auth_response = requests.post(
            'https://api.sinric.pro/api/v1/auth',
            headers={'x-sinric-api-key': API_KEY}
        )
        auth_response.raise_for_status()  # Lanza una excepción si la respuesta no es 200
        auth_data = auth_response.json()
        access_token = auth_data['accessToken']
        expires_in = auth_data['expiresIn']
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        logging.info("Access token obtenido o renovado correctamente.")
        return access_token
    except requests.exceptions.RequestException as e:
        logging.error(f"Error al obtener access token: {e}")
        return None

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/timbre', methods=['POST'])
def timbre():
    access_token = get_access_token()
    if not access_token:
        return jsonify({'error': 'Error de autenticación'}), 500

    try:
        message_id = str(uuid.uuid4())
        created_at = int(time.time())

        url = f"https://api.sinric.pro/api/v1/devices/{DEVICE_ID}/action"
        url += f"?clientId={PORTAL_ID}&messageId={message_id}&type=event"
        url += f"&action=DoorbellPress&createdAt={created_at}"

        payload = {
            "type": "event",
            "action": "DoorbellPress",
            "value": json.dumps({"state": "pressed"})
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            return jsonify({'message': 'Timbre activado'}), 200
        else:
            try:  # Intenta obtener el mensaje de error específico de Sinric Pro
                error_data = response.json()
                error_message = error_data.get('message') or "Error desconocido al activar el timbre"
            except json.JSONDecodeError:  # Si la respuesta no es JSON
                error_message = f"Error {response.status_code} al activar el timbre"

            logging.error(f"Error al activar el timbre: {error_message}")  # Loggea el error específico
            return jsonify({'error': error_message}), response.status_code  # Devuelve el error específico

    except requests.exceptions.RequestException as e:
        logging.error(f'Error al activar el timbre: {e}')
        return jsonify({'error': str(e)}), 500  # Devuelve el mensaje de la excepción

if __name__ == '__main__':
    app.run(debug=True)
