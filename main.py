from flask import Flask, request, jsonify
import os
import speech_recognition as sr

# Initialisation de l'application Flask
app = Flask(__name__)

@app.route("/")
def index():
    return "Bienvenue sur l'API de transcription ! Utilisez /transcribe pour envoyer un fichier audio."

@app.route("/transcribe", methods=["POST"])
def transcribe():
    # Vérifiez si un fichier audio a été envoyé dans la requête
    if "audio" not in request.files:
        return jsonify({"error": "No audio file found"}), 400

    audio_file = request.files["audio"]

    # Sauvegarder temporairement le fichier
    file_path = "temp_audio.wav"
    audio_file.save(file_path)

    # Transcrire l'audio
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(file_path) as source:
            audio_data = recognizer.record(source)
            transcription = recognizer.recognize_google(audio_data, language="fr-FR")
        os.remove(file_path)  # Supprimer le fichier temporaire après utilisation
        return jsonify({"transcription": transcription})
    except Exception as e:
        os.remove(file_path)  # Supprimer le fichier temporaire en cas d'erreur
        return jsonify({"error": str(e)}), 500

# Point d'entrée principal pour Gunicorn
if __name__ == "__main__":
    app.run(debug=True)