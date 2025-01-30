from flask import Flask, request, jsonify
import os
import speech_recognition as sr
import logging
import subprocess
from pydub import AudioSegment

# Vérifier et installer ffmpeg si nécessaire
def ensure_ffmpeg_installed():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except FileNotFoundError:
        raise RuntimeError("FFmpeg is not installed. Please install it manually.")

# Initialisation de l'application Flask
app = Flask(__name__)

# Configuration des logs
logging.basicConfig(filename="error.log", level=logging.DEBUG,
                    format="%(asctime)s - %(levelname)s - %(message)s")

def convert_audio(file_path, target_format="wav"):
    """Convertit un fichier audio en WAV avec ffmpeg."""
    converted_path = file_path.rsplit(".", 1)[0] + ".wav"
    os.system(f"ffmpeg -i {file_path} -ar 16000 -ac 1 -ab 192k {converted_path} -y")
    return converted_path

def transcribe_long_audio(file_path):
    """Transcrit un fichier audio en segments de 3 secondes pour éviter le timeout."""
    recognizer = sr.Recognizer()
    transcript = ""
    with sr.AudioFile(file_path) as source:
        while True:
            try:
                audio_data = recognizer.record(source, duration=3)  # Segmentation 3s
                if not audio_data.frame_data:
                    break
                logging.debug("Envoi de l'audio à Google Speech API...")
                part_transcript = recognizer.recognize_google(audio_data, language="fr-FR")
                logging.debug("Réponse reçue : %s", part_transcript)
                transcript += part_transcript + " "
            except sr.UnknownValueError:
                transcript += "[Inaudible] "
            except sr.RequestError as e:
                transcript += f"[Erreur API: {str(e)}] "
            except Exception as e:
                logging.error(f"Erreur pendant la transcription : {e}")
                transcript += "[Erreur de transcription] "
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
        
        # Convertir en WAV si nécessaire et réduire la qualité pour optimisation
        if file_extension != "wav":
            file_path = convert_audio(file_path)
        audio = AudioSegment.from_file(file_path)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio.export(file_path, format="wav")
        
        # Transcrire l'audio
        logging.debug("Début de la transcription pour le fichier : %s", file_path)
        transcription = transcribe_long_audio(file_path)
        logging.debug("Transcription terminée : %s", transcription)
        
        # Supprimer le fichier temporaire
        os.remove(file_path)
        return jsonify({"transcription": transcription})
    
    except Exception as e:
        logging.error(f"Erreur inattendue: {str(e)}", exc_info=True)
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": f"Erreur inattendue: {str(e)}"}), 500

# Point d'entrée principal avec timeout augmenté
if __name__ == "__main__":
    from waitress import serve
    print("Serveur en cours d'exécution...")
    serve(app, host="0.0.0.0", port=5000, threads=4)
