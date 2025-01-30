from flask import Flask, request, jsonify
import os
import speech_recognition as sr
import logging
from pydub import AudioSegment
import subprocess

# Vérifier et installer ffmpeg si nécessaire
def ensure_ffmpeg_installed():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except FileNotFoundError:
        raise RuntimeError("FFmpeg is not installed. Please install it manually.")

# Initialisation de l'application Flask
app = Flask(__name__)

# Configuration des logs
logging.basicConfig(filename="error.log", level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

def convert_audio(file_path, target_format="wav"):
    """Convertit un fichier audio en WAV pour la transcription."""
    converted_path = file_path.rsplit(".", 1)[0] + ".wav"
    audio = AudioSegment.from_file(file_path)
    audio.export(converted_path, format=target_format)
    return converted_path

def transcribe_long_audio(file_path):
    """Transcrit un fichier audio en le découpant en segments de 30s."""
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        transcript = ""
        while True:
            try:
                audio_data = recognizer.record(source, duration=30)
                if not audio_data.frame_data:
                    break
                transcript += recognizer.recognize_google(audio_data, language="fr-FR") + " "
            except sr.UnknownValueError:
                transcript += "[Inaudible] "
            except sr.RequestError as e:
                transcript += f"[Erreur API: {str(e)}] "
    return transcript.strip()

@app.route("/")
def index():
    return "Bienvenue sur l'API de transcription ! Utilisez /transcribe pour envoyer un fichier audio."

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file found"}), 400

    audio_file = request.files["audio"]
    allowed_extensions = {"wav", "mp3", "m4a", "ogg", "flac", "mp4"}
    file_extension = audio_file.filename.rsplit(".", 1)[-1].lower()
    
    if file_extension not in allowed_extensions:
        return jsonify({"error": f"Invalid file format '{file_extension}'. Allowed formats: {allowed_extensions}"}), 400
    
    file_path = f"temp_audio.{file_extension}"
    audio_file.save(file_path)
    
    try:
        ensure_ffmpeg_installed()  # Vérifier si ffmpeg est installé
        
        # Convertir en WAV si nécessaire
        if file_extension != "wav":
            file_path = convert_audio(file_path)
        
        # Transcrire l'audio
        transcription = transcribe_long_audio(file_path)
        
        # Supprimer le fichier temporaire
        os.remove(file_path)
        return jsonify({"transcription": transcription})
    
    except Exception as e:
        logging.error(f"Erreur inattendue: {str(e)}", exc_info=True)
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": f"Erreur inattendue: {str(e)}"}), 500

# Point d'entrée principal
if __name__ == "__main__":
    from waitress import serve
    print("Serveur en cours d'exécution...")
    serve(app, host="0.0.0.0", port=5000, threads=4)
