from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from pydub import AudioSegment
import speech_recognition as sr

def transcribe_long_audio(file_path):
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_file(file_path)
    duration = len(audio) // 1000  # duration in seconds

    if duration > 60:  # Split audio if longer than 60 seconds
        chunks = make_chunks(audio, 60000)
        transcription = ""
        for i, chunk in enumerate(chunks):
            chunk_name = f"chunk{i}.wav"
            chunk.export(chunk_name, format="wav")
            with sr.AudioFile(chunk_name) as source:
                audio_data = recognizer.record(source)
                transcription += recognizer.recognize_google(audio_data, language="fr-FR") + " "
            os.remove(chunk_name)
    else:
        with sr.AudioFile(file_path) as source:
            audio_data = recognizer.record(source)
            transcription = recognizer.recognize_google(audio_data, language="fr-FR")

    return transcription

def make_chunks(audio, chunk_length):
    return [audio[i:i + chunk_length] for i in range(0, len(audio), chunk_length)]

app = Flask(__name__)
CORS(app)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({"error": "No audio file found"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join("temp_audio.wav")
    file.save(file_path)

    try:
        transcription = transcribe_long_audio(file_path)
        os.remove(file_path)
        return jsonify({"message": transcription}), 200
    except Exception as e:
        os.remove(file_path)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
