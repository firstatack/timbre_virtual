import os
from flask import Flask, render_template , request, jsonify
from dotenv import load_dotenv
import requests
import json

app = Flask(__name__)

# *** CONFIGURACIÓN SEGURA DE LAS CREDENCIALES para variables de entorno ***

#API_KEY = os.environ.get('SINRIC_API_KEY')
#DEVICE_ID = os.environ.get('SINRIC_DEVICE_ID')
#PORTAL_ID = os.environ.get('SINRIC_PORTAL_ID')
#TOKEN_ID = os.environ.get('SINRIC_TOKEN_ID')

###Configuracion credenciales fichero .env y usando python-dotenv

load_dotenv()
API_KEY = os.getenv('SINRIC_API_KEY')
DEVICE_ID = os.getenv('SINRIC_DEVICE_ID')
PORTAL_ID = os.getenv('SINRIC_PORTAL_ID')
TOKEN_ID = os.getenv('SINRIC_TOKEN_ID')

if not API_KEY or not DEVICE_ID or not PORTAL_ID:
    raise ValueError("Las variables de entorno SINRIC_API_KEY, SINRIC_DEVICE_ID y SINRIC_PORTAL_ID y el TOKEN que es el appsecret codificado deben estar configuradas.")
# *********************************************
##Creamos la ruta raiz
@app.route('/')
def index():
    return render_template('index.html')

##Creamos la ruta para llamar al timbre con todos la valores necesarios para el metodo post
@app.route('/timbre', methods=['POST'])
def doorbell():
    headers = {
        'Authorization': f'Bearer {TOKEN_ID}',
        'Content-Type': 'application/json'
    }

    data = {
        'type': "event",
        'action': 'Dorbellpress',
        "values": json.dumps({
           "state": "pressed"
        })
    }

    ## Completamos la url con todos los datos obtenidos y formateados anteriormente 
    url = f'https://api.sinric.com/v1/devices/{DEVICE_ID}/action?clientId={PORTAL_ID}&messageId={API_KEY}&type=event&action=DoorbellPress&createdAt=1739217360&value=%7B%22state%22:%22pressed%22%7D'

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        return jsonify({"status": "succes", "message": "Timbre llamado correctamente"}), 200
    else:
        return jsonify({"status": "error", "message": "Hubo un error al activar el timbre."}), 500

if __name__ == '__main__':
    app.run(debug=True)
