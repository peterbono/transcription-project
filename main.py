from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    # Vérifiez si un fichier est inclus
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    # Vérifiez si un fichier a été sélectionné
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Sauvegarde temporaire
    temp_dir = "./temp"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, file.filename)
    file.save(file_path)

    # Placeholder pour votre logique de transcription
    try:
        transcription_result = f"Transcription successful for {file.filename}"
        return jsonify({"message": transcription_result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
