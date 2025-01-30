from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import math
from pydub import AudioSegment
from pydub.utils import make_chunks
import speech_recognition as sr

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
CHUNK_FOLDER = 'chunks'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHUNK_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return "Transcription Service is Running"

def transcribe_audio_chunk(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data, language="fr-FR")
        except sr.UnknownValueError:
            return "[Unintelligible]"
        except sr.RequestError:
            return "[API Error]"

def split_audio(file_path):
    audio = AudioSegment.from_file(file_path)
    chunk_length_ms = 59000  # 59 seconds per chunk
    chunks = make_chunks(audio, chunk_length_ms)
    chunk_paths = []

    for i, chunk in enumerate(chunks):
        chunk_path = os.path.join(CHUNK_FOLDER, f"chunk_{i}.wav")
        chunk.export(chunk_path, format="wav")
        chunk_paths.append(chunk_path)

    return chunk_paths

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    chunk_paths = split_audio(file_path)
    transcription = ""

    for chunk_path in chunk_paths:
        transcription += transcribe_audio_chunk(chunk_path) + " "
        os.remove(chunk_path)

    os.remove(file_path)
    return jsonify({"transcription": transcription.strip()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
