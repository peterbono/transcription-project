import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import speech_recognition as sr
import subprocess
import logging

# Configuration de la journalisation
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def transcribe_long_audio(file_path):
    recognizer = sr.Recognizer()
    transcription = ""
    try:
        with sr.AudioFile(file_path) as source:
            audio = recognizer.record(source)
            duration = source.DURATION

            if duration > 60:
                transcription = "Fichier trop long. Veuillez utiliser un fichier de moins de 60 secondes."
            else:
                transcription = recognizer.recognize_google(audio, language="fr-FR")
    except sr.UnknownValueError:
        transcription = "Impossible de reconnaître la voix. Essayez un autre fichier."
    except sr.RequestError as e:
        transcription = f"Erreur de la requête API Google Speech; {e}"
    except Exception as e:
        transcription = f"Une erreur inattendue s'est produite : {e}"

    return transcription

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "file" not in request.files:
        return jsonify({"error": "No audio file found"}), 400

    audio_file = request.files["file"]

    if audio_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, audio_file.filename)
    audio_file.save(file_path)

    # Conversion du fichier MP4 en WAV
    wav_file_path = os.path.splitext(file_path)[0] + ".wav"
    try:
        subprocess.run([
            "ffmpeg", "-i", file_path, "-ac", "1", "-ar", "16000", wav_file_path
        ], check=True)

        transcription = transcribe_long_audio(wav_file_path)

        # Suppression des fichiers temporaires
        os.remove(file_path)
        os.remove(wav_file_path)

        return jsonify({"transcription": transcription})

    except subprocess.CalledProcessError as e:
        logging.error(f"Erreur lors de la conversion avec ffmpeg : {e}")
        return jsonify({"error": "Audio conversion failed"}), 500
    except Exception as e:
        logging.error(f"Erreur inattendue : {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
