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
    try:
        audio_file.save(file_path)

        # Transcrire l'audio
        recognizer = sr.Recognizer()
        with sr.AudioFile(file_path) as source:
            audio_data = recognizer.record(source)
            transcription = recognizer.recognize_google(audio_data, language="fr-FR")

        # Supprimer le fichier temporaire après utilisation
        os.remove(file_path)
        return jsonify({"transcription": transcription})

    except Exception as e:
        # Supprimer le fichier temporaire en cas d'erreur
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Point d'entrée principal pour Gunicorn
if __name__ == "__main__":
    # Debug est désactivé en production
    app.run(host="0.0.0.0", port=5000)