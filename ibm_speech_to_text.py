from flask import Flask, request, render_template, jsonify, send_file, redirect, url_for, flash
from cloudant.query import Query
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

from werkzeug.utils import secure_filename
import os
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from cloudant.client import Cloudant

import sounddevice as sd
import numpy as np
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import wave

app = Flask(__name__)
app.secret_key = 'lXq2PUtb'

ALLOWED_EXTENSIONS = {'wav', 'mp3'}  # Ajoutez les extensions de fichiers autorisées ici
UPLOAD_FOLDER = 'uploads'  # Définir le dossier de téléchargement des fichiers

# Définir les informations de connexion pour l'API IBM Watson Text to Speech
API_KEY_TEXT_TO_SPEECH = 'gxe8JabFkqkEGrLhfgOXRylHF3WkyDxXoKGRNT7t7M8z'
API_URL_TEXT_TO_SPEECH = 'https://api.au-syd.text-to-speech.watson.cloud.ibm.com/instances/474df056-a011-4d47-949d-89ce8dcad4c5'

# Initialiser le service IBM Watson Text to Speech
authenticator_text_to_speech = IAMAuthenticator(API_KEY_TEXT_TO_SPEECH)
text_to_speech = TextToSpeechV1(authenticator=authenticator_text_to_speech)
text_to_speech.set_service_url(API_URL_TEXT_TO_SPEECH)

# Définir les informations de connexion pour l'API IBM Watson Speech to Text
API_KEY_SPEECH_TO_TEXT = "9r63ExBLvZ7p07OcLZAzylLFBJoz7pMTO5rRG0rqD4Op"
API_URL_SPEECH_TO_TEXT = "https://api.au-syd.speech-to-text.watson.cloud.ibm.com/instances/a9b1e68e-4304-472f-a94a-f076c2f1806d"

# Initialiser le service IBM Watson Speech to Text
authenticator_speech_to_text = IAMAuthenticator(API_KEY_SPEECH_TO_TEXT)
speech_to_text = SpeechToTextV1(authenticator=authenticator_speech_to_text)
speech_to_text.set_service_url(API_URL_SPEECH_TO_TEXT)

# Connecter à Cloudant
client = Cloudant.iam("d9b08c7b-b6ef-4491-ad97-a6c7a9cbbb55-bluemix", "kTdhT7Wf4ef5Ed6j6OqVoYIHCaGdO2JJiFYKszXuei6G", connect=True)
db = client['app']  # Remplacez 'app' par le nom de votre base de données Cloudant

@app.route('/templates/speech2text.html')
def speech_to_text_index():
    return render_template('speech2text.html', models=models)

@app.route('/templates/text2speech.html')
def text_to_speech_index():
    return render_template('text2speech.html')

@app.route('/script.js')
def serve_script():
    return app.send_static_file('script.js')

@app.route('/output.wav')
def serve_audio():
    return send_file('output.wav', mimetype='audio/wav')

@app.route('/convert', methods=['POST'])
def convert_text_to_speech():
    try:
        text = request.json['text']
        voice = request.json.get('voice', 'en-US_AllisonV3Voice')

        response = text_to_speech.synthesize(text=text, voice=voice, accept='audio/wav').get_result()
        audio_data = response.content
        with open("output.wav", "wb") as output_file:
            output_file.write(audio_data)

        return jsonify({'audio_file': 'output.wav'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/download/output.wav')
def serve_audio_file():
    return send_file('downloads/output.wav', mimetype='audio/wav')

@app.route('/templates/Signup.html', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Récupérer les données du formulaire
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password']

        # Créer un document JSON avec les données de l'utilisateur
        user_data = {
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "password": password
        }

        # Insérer le document dans la base de données Cloudant
        try:
            db.create_document(user_data)
            print("User signed up successfully and added to the database!")
            # Rediriger vers dash.html lors de l'inscription réussie
            return redirect(url_for('dashboard'))
        except Exception as e:
            print("Error creating document in Cloudant:", e)
            return "Error signing up. Please try again."
    else:
        # Retourner le modèle HTML pour la page d'inscription
        return render_template('Signup.html')

@app.route('/templates/index.html', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_document = search_user(username)
        if user_document is None:
            flash("User not found", "error")
        elif 'password' not in user_document:
            flash("User document is missing 'password' field", "error")
        elif user_document['password'] != password:
            flash("Incorrect password", "error")
        else:
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dash.html')

def search_user(username):
    query = Query(db, selector={'username': username})
    result = query(limit=1)['docs']
    return result[0] if result else None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Liste des modèles de langue disponibles
models = {
    "Arabic (Modern Standard)": "ar-MS_Telephony",
    "Chinese (Mandarin)": "zh-CN_Telephony",
    "Czech": "cs-CZ_Telephony",
    "Dutch (Belgian)": "nl-BE_Telephony",
    "Dutch (Netherlands)": "nl-NL_Telephony",
    "English (Australian)": "en-AU_Telephony",
    "English (Indian)": "en-IN_Telephony",
    "English (United Kingdom)": "en-GB_Telephony",
    "English (United States)": "en-US_Telephony",
    "French (Canadian)": "fr-CA_Telephony",
    "French (France)": "fr-FR_Telephony",
    "German": "de-DE_Telehony",
    "Hindi (Indian)": "hi-IN_Telephony",
    "Italian": "it-IT_Telephony",
    "Japanese": "ja-JP_Telephony",
    "Korean": "ko-KR_Telephony",
    "Portuguese (Brazilian)": "pt-BR_Telephony",
    "Spanish (Castilian)": "es-ES_Telephony",
    "Spanish (Argentinian, Chilean, Colombian, Mexican, and Peruvian)": "es-LA_Telephony",
    "Swedish": "sv-SE_Telephony"
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert_audio', methods=['POST'])
def convert_audio():
    try:
        selected_model = request.form['model']
        if selected_model not in models.values():
            return jsonify({'error': 'Modèle de langue invalide.'}), 400

        duration = float(request.form['duration'])

        frames = int(duration * 44100)
        audio_data = sd.rec(frames, samplerate=44100, channels=1, dtype=np.int16)
        sd.wait()
        wav_filename = "audio.wav"
        write_wav(wav_filename, 44100, audio_data)

        content_type = "audio/wav"
        with open(wav_filename, "rb") as audio_file:
            response = speech_to_text.recognize(audio=audio_file, content_type=content_type, model=selected_model).get_result()
            if "results" in response and response["results"]:
                recognized_text = response["results"][0]["alternatives"][0]["transcript"]
                return jsonify({'text': recognized_text})
            else:
                return jsonify({'error': 'Conversion du texte échouée.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def write_wav(filename, rate, audio_data):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(audio_data.tobytes())


@app.route('/uploads', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        text = convert_audio_to_text(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'text': text})
    else:
        flash('Invalid file type', 'error')
        return redirect(request.url)


@app.route('/convert_audio_to_text', methods=['POST'])
def convert_audio_to_text():
    if 'audio_file' not in request.files:
        return "Aucun fichier audio n'a été fourni."
    
    audio_file = request.files['audio_file']
    if audio_file.filename == '':
        return "Aucun fichier sélectionné."
    
    content_type = "audio/wav"
    try:
        response = speech_to_text.recognize(audio=audio_file, content_type=content_type).get_result()
        if "results" in response and response["results"]:
            recognized_text = response["results"][0]["alternatives"][0]["transcript"]
            return recognized_text
        else:
            return "Conversion du texte échouée."
    except Exception as e:
        return "Erreur lors de la conversion : " + str(e)


if __name__ == '__main__':
    app.run(debug=True)
