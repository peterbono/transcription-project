from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import speech_recognition as sr
from pydub import AudioSegment

def split_audio(file_path, chunk_length_ms=30000):  # 30 secondes max
    audio = AudioSegment.from_wav(file_path)
    chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
    chunk_paths = []
    for idx, chunk in enumerate(chunks):
        chunk_path = f"chunk_{idx}.wav"
        chunk.export(chunk_path, format="wav")
        chunk_paths.append(chunk_path)
    return chunk_paths

def transcribe_audio_chunk(chunk_path, retry_count=3):
    recognizer = sr.Recognizer()
    with sr.AudioFile(chunk_path) as source:
        audio_data = recognizer.record(source)
    for attempt in range(retry_count):
        try:
            return recognizer.recognize_google(audio_data, language="fr-FR")
        except sr.RequestError:
            print(f"Erreur réseau. Retrying... ({attempt+1}/{retry_count})")
        except sr.UnknownValueError:
            print("Google Speech API n'a pas pu comprendre l'audio.")
            return ""
    return ""

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return "Mathieu Translator API"

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({"error": "Aucun fichier reçu."}), 400
    
    file = request.files['file']
    file_path = "temp_audio.wav"
    file.save(file_path)
    
    chunk_paths = split_audio(file_path)
    transcription = ""
    
    for chunk_path in chunk_paths:
        transcription += transcribe_audio_chunk(chunk_path) + " "
        os.remove(chunk_path)
    
    os.remove(file_path)
    
    return jsonify({"transcription": transcription})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
