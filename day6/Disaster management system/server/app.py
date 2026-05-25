import os
import sys
# pyrefly: ignore [missing-import]
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add current folder to sys.path to enable local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import predict_emergency, load_artifacts

# Resolve the absolute path to the client folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_DIR = os.path.join(os.path.dirname(BASE_DIR), "client")

# Initialize Flask app serving frontend files directly from the client directory
app = Flask(__name__, static_folder=CLIENT_DIR, static_url_path="")
CORS(app) # Enable Cross-Origin Resource Sharing for API flexibility

# Load artifacts during application startup to fail fast and warm up memory
try:
    load_artifacts()
    print("Machine learning models and configurations loaded successfully.")
except Exception as e:
    print(f"Error loading machine learning models: {e}")
    # We do not exit here to allow server debug analysis, but future API calls will report failure.

@app.route("/")
def serve_index():
    """Serves the main dashboard user interface."""
    return app.send_static_file("index.html")

@app.route("/api/predict", methods=["POST"])
def api_predict():
    """
    Accepts JSON containing emergency message and location,
    computes predicted categories, priority, and suggestions,
    and returns a clean JSON response.
    """
    data = request.get_json()
    if not data:
        return jsonify({
            "status": "error",
            "message": "Invalid request: No JSON payload found."
        }), 400

    message = data.get("message", "").strip()
    location = data.get("location", "").strip()

    if not message:
        return jsonify({
            "status": "error",
            "message": "Validation failed: 'message' is a required field."
        }), 400

    try:
        results = predict_emergency(message, location)
        return jsonify({
            "status": "success",
            "message": message,
            "location": location or "Unknown Location",
            "predictions": results["predictions"],
            "active_categories": results["active_categories"],
            "priority": results["priority"],
            "suggestions": results["suggestions"]
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred during inference: {str(e)}"
        }), 500

@app.errorhandler(404)
def not_found(e):
    """Fallback handler to serve index.html for single page route layouts if needed."""
    return app.send_static_file("index.html")

if __name__ == "__main__":
    # Host on 0.0.0.0 for container/network access; default Flask port is 5000
    app.run(host="0.0.0.0", port=5000, debug=True)
