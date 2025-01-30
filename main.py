from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import speech_recognition as sr
from pydub import AudioSegment

def transcribe_long_audio(file_path):
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_file(file_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    temp_wav_path = "temp_audio.wav"
    audio.export(temp_wav_path, format="wav")

    with sr.AudioFile(temp_wav_path) as source:
        audio_data = recognizer.record(source)
    
    transcription = recognizer.recognize_google(audio_data, language="fr-FR")
    os.remove(temp_wav_path)
    return transcription

app = Flask(__name__)
CORS(app)

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "file" not in request.files:
        return jsonify({"error": "No audio file found"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    file_path = os.path.join("temp_audio.mp4")
    file.save(file_path)

    try:
        transcription = transcribe_long_audio(file_path)
        os.remove(file_path)
        return jsonify({"message": f"Transcription successful for {file.filename}", "transcription": transcription})
    except Exception as e:
        os.remove(file_path)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
