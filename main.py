import os
import wave
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
import speech_recognition as sr
from pydub import AudioSegment

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def convert_to_wav(input_path, output_path):
    """ Convertir un fichier en WAV valide avec ffmpeg """
    try:
        command = [
            "ffmpeg", "-y", "-i", input_path, 
            "-acodec", "pcm_s16le", "-ac", "1", "-ar", "16000", output_path
        ]
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erreur FFmpeg : {e}")
        return False

def is_valid_wav(file_path):
    """ Vérifie si le fichier WAV est bien valide """
    try:
        with wave.open(file_path, "rb") as wf:
            return wf.getnchannels() > 0  # Vérifie s'il y a au moins un canal audio
    except wave.Error:
        return False

def split_audio(file_path, chunk_length_ms=30000):
    """ Découpe un fichier audio en morceaux de 30 secondes """
    audio = AudioSegment.from_wav(file_path)
    chunks = []
    for i in range(0, len(audio), chunk_length_ms):
        chunk = audio[i : i + chunk_length_ms]
        chunk_path = f"{file_path[:-4]}_part{i//chunk_length_ms}.wav"
        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)
    return chunks

def transcribe_audio_chunk(chunk_path):
    """ Transcrit un seul morceau audio avec Google Speech API """
    recognizer = sr.Recognizer()
    with sr.AudioFile(chunk_path) as source:
        audio_data = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio_data, language="fr-FR")
    except sr.UnknownValueError:
        return "[Inaudible]"
    except sr.RequestError:
        return "[Erreur de connexion à l'API]"

@app.route("/transcribe", methods=["POST"])
def transcribe():
    """ API Flask pour uploader et transcrire un fichier audio """
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier reçu"}), 400
    
    file = request.files["file"]
    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    output_wav_path = os.path.join(UPLOAD_FOLDER, "temp_audio.wav")

    file.save(input_path)

    # Convertir en WAV
    if not convert_to_wav(input_path, output_wav_path):
        return jsonify({"error": "Échec de la conversion en WAV"}), 500

    # Vérifier si le WAV est valide
    if not is_valid_wav(output_wav_path):
        return jsonify({"error": "Fichier audio non valide"}), 500

    # Découper le fichier si nécessaire
    chunk_paths = split_audio(output_wav_path)

    # Transcription de chaque morceau
    transcription = " ".join(transcribe_audio_chunk(chunk) for chunk in chunk_paths)

    # Nettoyer les fichiers temporaires
    os.remove(input_path)
    os.remove(output_wav_path)
    for chunk in chunk_paths:
        os.remove(chunk)

    return jsonify({"transcription": transcription})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
