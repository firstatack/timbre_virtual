import os
import logging
from flask import Flask, request, jsonify, send_from_directory
import requests
import json
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='static')  # Configura la carpeta estática

logging.basicConfig(level=logging.INFO)

# *** CONFIGURACIÓN SEGURA DE LAS CREDENCIALES ***
###  ESTA FORMA SERIA INSEGURA 
#API_KEY = 'xxxxxxxxxx'
#DEVICE_ID = 'xxxxxxxxxx'

## mEJOR LAS CREAS COMO VARIABLE DE ENTORNO
API_KEY = os.environ.get('SINRIC_API_KEY')
DEVICE_ID = os.environ.get('SINRIC_DEVICE_ID')

if not API_KEY or not DEVICE_ID:
    raise ValueError("Las variables de entorno SINRIC_API_KEY y SINRIC_DEVICE_ID deben estar configuradas.")
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
        auth_response.raise_for_status()
        auth_data = auth_response.json()
        access_token = auth_data['accessToken']
        expires_in = auth_data['expiresIn']
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        logging.info("Access token obtenido o renovado correctamente.")
        return access_token
    except requests.exceptions.RequestException as e:
        logging.error(f"Error al obtener access token: {e}")
        return None

@app.route('/')  # Ruta para servir index.html
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/timbre', methods=['POST'])
def timbre():
    access_token = get_access_token()
    if not access_token:
        return jsonify({'error': 'Error de autenticación'}), 500

    try:
        action_payload = {
            "type": "request",
            "action": "DoorbellPress",  # Acción para el timbre (revisar manual)
            "value": json.dumps({"state": "pressed"})  # value debe ser un string JSON
        }
        device_action_response = requests.post(
            f'https://api.sinric.pro/api/v1/devices/{DEVICE_ID}/action',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            },
            data=json.dumps(action_payload)
        )

        device_action_response.raise_for_status()
        action_data = device_action_response.json()

        if action_data.get('success'):
            logging.info("Timbre activado correctamente.")
            return 'Timbre activado', 200
        else:
            error_message = action_data.get('message') or "Error desconocido al activar el timbre"
            logging.error(f"Error al activar el timbre: {error_message}")
            return jsonify({'error': error_message}), 500  # Devuelve JSON con el error

    except requests.exceptions.RequestException as e:
        logging.error(f'Error al activar el timbre: {e}')
        return jsonify({'error': 'Error al activar el timbre'}), 500  # Devuelve JSON con el error

if __name__ == '__main__':
    app.run(debug=True)