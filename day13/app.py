import os
import uuid
import logging
from flask import Flask, request, jsonify, render_template, url_for
from werkzeug.utils import secure_filename
from ultralytics import YOLO
import cv2

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure upload directory
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# Ensure upload directory exists and clean old files on startup
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
for f in os.listdir(UPLOAD_FOLDER):
    try:
        os.remove(os.path.join(UPLOAD_FOLDER, f))
    except Exception as e:
        logger.warning(f"Failed to delete old upload file {f}: {e}")

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Load YOLO Model Globally
print("Loading Disaster Assessment Model...")
try:
    model = YOLO("best.pt")
    logger.info("YOLOv8 Model loaded successfully.")
except Exception as e:
    logger.error(f"Critical error loading model 'best.pt': {e}")
    model = None

# Recovery recommendations dict
RECOVERY_RECOMMENDATIONS = {
    "earthquake": [
        "Inspect damaged buildings and infrastructure",
        "Deploy emergency medical teams",
        "Restore electricity and water supply"
    ],
    "flood": [
        "Evacuate affected residents",
        "Deploy rescue boats and relief teams",
        "Prevent water contamination"
    ],
    "forest_fire": [
        "Deploy fire suppression units",
        "Evacuate nearby communities",
        "Monitor air quality and hotspots"
    ],
    "structural_fire": [
        "Secure affected structures",
        "Extinguish remaining fire sources",
        "Assess structural stability"
    ],
    "cyclone": [
        "Clear debris from roads",
        "Restore communication networks",
        "Provide temporary shelters"
    ]
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detect', methods=['POST'])
def detect():
    if model is None:
        return jsonify({
            "success": False,
            "error": "YOLO model is not initialized. Please verify that 'best.pt' exists."
        }), 500

    # Check if files part is present
    if 'image' not in request.files:
        return jsonify({
            "success": False,
            "error": "No image file provided in request."
        }), 400

    file = request.files['image']
    
    if file.filename == '':
        return jsonify({
            "success": False,
            "error": "No image file selected."
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            "success": False,
            "error": "Unsupported file format. Please upload PNG, JPG, JPEG, or WEBP."
        }), 400

    try:
        # Get custom confidence threshold from form
        conf_str = request.form.get('confidence', '0.25')
        try:
            conf_threshold = float(conf_str)
            conf_threshold = max(0.01, min(0.99, conf_threshold))  # clamp between 0.01 and 0.99
        except ValueError:
            conf_threshold = 0.25

        # Create unique filenames to prevent browser cache problems
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_id = uuid.uuid4().hex
        
        orig_filename = f"orig_{unique_id}.{ext}"
        annotated_filename = f"ann_{unique_id}.{ext}"
        
        orig_filepath = os.path.join(app.config['UPLOAD_FOLDER'], orig_filename)
        annotated_filepath = os.path.join(app.config['UPLOAD_FOLDER'], annotated_filename)

        # Save uploaded original image
        file.save(orig_filepath)

        # Verify image is valid by reading it
        img = cv2.imread(orig_filepath)
        if img is None:
            # Delete corrupted file
            try:
                os.remove(orig_filepath)
            except:
                pass
            return jsonify({
                "success": False,
                "error": "Uploaded file is not a valid image or is corrupted."
            }), 400

        # Run model prediction
        results = model.predict(
            source=orig_filepath,
            conf=conf_threshold,
            save=False
        )

        detections = []
        annotated_img = None

        for result in results:
            # Generate annotated image
            # result.plot() returns BGR image as numpy array
            annotated_img = result.plot()

            if result.boxes is not None and len(result.boxes) > 0:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    disaster_name = model.names[class_id]

                    # Severity estimation based on confidence
                    if confidence >= 0.80:
                        severity = "High"
                    elif confidence >= 0.50:
                        severity = "Medium"
                    else:
                        severity = "Low"

                    # Normalize disaster name for recommendations key
                    disaster_key = disaster_name.lower().replace(" ", "_").replace("-", "_")
                    recs = RECOVERY_RECOMMENDATIONS.get(disaster_key, [
                        "Assess structural integrity and safety",
                        "Contact local civil protection/first responders",
                        "Monitor local weather and official news updates"
                    ])

                    detections.append({
                        "class": disaster_name,
                        "confidence": confidence,
                        "severity": severity,
                        "recommendations": recs
                    })

        # Save annotated image
        if annotated_img is not None:
            cv2.imwrite(annotated_filepath, annotated_img)
        else:
            # Fallback if result.plot() is empty
            cv2.imwrite(annotated_filepath, img)

        # Generate public URLs for the images
        original_image_url = url_for('static', filename=f'uploads/{orig_filename}')
        annotated_image_url = url_for('static', filename=f'uploads/{annotated_filename}')

        return jsonify({
            "success": True,
            "detections": detections,
            "original_image_url": original_image_url,
            "annotated_image_url": annotated_image_url
        })

    except Exception as e:
        logger.exception("Inference error occurred:")
        return jsonify({
            "success": False,
            "error": f"An internal error occurred during image analysis: {str(e)}"
        }), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "success": False,
        "error": "The uploaded file is too large. Maximum size is 16MB."
    }), 413

if __name__ == '__main__':
    # Run the server on port 5000 and bind to all network interfaces
    app.run(host='0.0.0.0', port=5000, debug=True)