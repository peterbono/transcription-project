from flask import Flask, request, jsonify
import os
import speech_recognition as sr
import requests

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

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """
    Vérifie le webhook avec le token fourni par Meta
    """
    challenge = request.args.get("hub.challenge")
    verify_token = request.args.get("hub.verify_token")

    # Utilise le token secret défini
    if verify_token == "lepetitcodesecretdepeterbono":
        return challenge, 200
    else:
        return "Token de vérification invalide", 403

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """
    Gère les événements envoyés par le webhook de Messenger
    """
    data = request.get_json()
    
    # Affiche les données reçues pour le debug
    print(data)
    
    # Vérifie les messages reçus
    if "entry" in data:
        for entry in data["entry"]:
            for message in entry.get("messaging", []):
                if "message" in message and "attachments" in message["message"]:
                    for attachment in message["message"]["attachments"]:
                        if attachment["type"] == "audio":
                            audio_url = attachment["payload"]["url"]
                            print(f"Audio file URL: {audio_url}")

                            # Télécharge et traite l'audio
                            try:
                                response = requests.get(audio_url)
                                with open("temp_audio.mp3", "wb") as audio_file:
                                    audio_file.write(response.content)

                                # Envoie l'audio au service de transcription
                                files = {'audio': open("temp_audio.mp3", "rb")}
                                transcribe_response = requests.post(
                                    "https://transcription-project-91w7.onrender.com/transcribe",
                                    files=files
                                )
                                print(transcribe_response.json())

                                # Supprime le fichier local
                                os.remove("temp_audio.mp3")

                            except Exception as e:
                                print(f"Erreur lors du traitement de l'audio : {str(e)}")
    return "Événement reçu", 200

# Point d'entrée principal pour Gunicorn
if __name__ == "__main__":
    # Debug est désactivé en production
    app.run(host="0.0.0.0", port=5000)