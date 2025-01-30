from flask import Flask, request, jsonify
from flask_cors import CORS  # Ajout de cette ligne
import os
from pydub import AudioSegment
from speech_recognition import Recognizer, AudioFile
import ffmpeg

app = Flask(__name__)
CORS(app)  # Activer le middleware CORS pour autoriser toutes les origines

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return "Mathieu Translator is running!"

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        # Vérifiez que le fichier est inclus dans la requête
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Sauvegarder le fichier temporairement
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Convertir l'audio MP4 en WAV avec ffmpeg
        wav_path = file_path.rsplit('.', 1)[0] + '.wav'
        (
            ffmpeg
            .input(file_path)
            .output(wav_path, format='wav', acodec='pcm_s16le', ar='16000', ac=1)
            .run()
        )

        # Transcrire l'audio WAV avec SpeechRecognition
        recognizer = Recognizer()
        with AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            transcription = recognizer.recognize_google(audio_data, language="fr-FR")

        # Nettoyer les fichiers temporaires
        os.remove(file_path)
        os.remove(wav_path)

        return jsonify({'transcription': transcription})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
