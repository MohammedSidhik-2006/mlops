import re
import string
import pickle
import os

# Base directory for absolute path resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")

MODEL_PATH = os.path.join(ARTIFACTS_DIR, "model.pkl")
VECTORIZER_PATH = os.path.join(ARTIFACTS_DIR, "vectorizer.pkl")
LABELS_PATH = os.path.join(ARTIFACTS_DIR, "label_columns.pkl")

# Global cached dictionary for loaded ML artifacts
_cached_artifacts = {}

def clean_text(text):
    """
    Standardizes and cleans input text (lowercasing, punctuation removal, tag stripping)
    to match the preprocessing steps used during training.
    """
    if not text or not isinstance(text, str):
        return ""
    
    text = text.lower()
    # Remove URLs
    text = re.sub(r"http\S+", "", text)
    # Remove usernames (@mentions)
    text = re.sub(r"@\w+", "", text)
    # Remove hashtags (#)
    text = re.sub(r"#", "", text)
    # Remove punctuation
    text = text.translate(
        str.maketrans("", "", string.punctuation)
    )
    # Remove outer whitespaces
    text = text.strip()
    return text

def load_artifacts():
    """
    Loads model, vectorizer, and label headers from disk. Caches the artifacts 
    globally for rapid inference response times.
    """
    global _cached_artifacts
    if not _cached_artifacts:
        if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH) or not os.path.exists(LABELS_PATH):
            raise FileNotFoundError(
                f"ML Artifacts missing. Please check if model.pkl, vectorizer.pkl, and "
                f"label_columns.pkl exist in {ARTIFACTS_DIR}"
            )
            
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
            
        with open(VECTORIZER_PATH, "rb") as f:
            vectorizer = pickle.load(f)
            
        with open(LABELS_PATH, "rb") as f:
            labels = pickle.load(f)
            
        _cached_artifacts = {
            "model": model,
            "vectorizer": vectorizer,
            "labels": labels
        }
    return _cached_artifacts

def determine_priority(active_categories):
    """
    Categorizes emergency alerts into LOW, MEDIUM, or HIGH priority based on 
    critical life safety indicators, shelter needs, and weather hazards.
    """
    # High priority tags represent threat to life, medical emergencies, or basic sustenance
    high_priority_categories = {
        "medical_help", "medical_products", "search_and_rescue",
        "water", "food", "shelter", "fire", "earthquake",
        "floods", "storm", "security", "military", "missing_people",
        "death", "refugees", "hospitals"
    }

    # Medium priority tags represent structural requests, resource needs, and helper logistics
    medium_priority_categories = {
        "request", "aid_related", "infrastructure_related",
        "transport", "buildings", "electricity", "cold",
        "clothing", "money", "other_weather"
    }

    active_set = set(active_categories)

    if active_set.intersection(high_priority_categories):
        return "HIGH"
    elif active_set.intersection(medium_priority_categories):
        return "MEDIUM"
    else:
        return "LOW"

# Actionable recommendation templates mapped to ML prediction labels
SUGGESTION_TEMPLATES = {
    "request": "Log request in the emergency database and coordinate triage operations.",
    "aid_related": "Dispatch regional humanitarian aid officers to coordinate logistical operations.",
    "medical_help": "Dispatch local emergency medical technicians (EMTs) and prepare critical treatment areas.",
    "medical_products": "Mobilize emergency medical supplies, bandaging, and vital pharmaceuticals from central reserves.",
    "search_and_rescue": "Deploy Search and Rescue (SAR) field squads and search canine units immediately.",
    "security": "Inform local law enforcement to secure the vicinity and secure transport lanes.",
    "military": "Liaise with civil-defense units and national guard units for heavy rescue clearance.",
    "water": "Coordinate water tanker dispatch and distribute hydration packets/purification tablets.",
    "food": "Establish dry food pack distribution centers and dispatch high-calorie food rations.",
    "shelter": "Deploy emergency tents, blankets, and temporary sleeping structures.",
    "clothing": "Mobilize warm clothing distributions and waterproof blankets.",
    "money": "Add incident zone to the emergency direct-financial-assistance queue.",
    "missing_people": "Create missing person file entries and coordinate with Red Cross family-tracing squads.",
    "refugees": "Activate refugee reception coordinates and coordinate emergency intake services.",
    "death": "Coordinate with emergency sanitation units and public health departments.",
    "infrastructure_related": "Deploy civil engineering specialists to inspect damaged facilities and utility corridors.",
    "transport": "Mobilize heavy road-clearing equipment to restore vehicle access on main transport arteries.",
    "buildings": "Establish safety exclusion perimeters around cracked structures and unstable buildings.",
    "electricity": "Deploy emergency power generator rigs and prioritize hospital power grid repairs.",
    "tools": "Distribute clearance tools (chainsaws, shovels, safety gear) to local rescue workers.",
    "hospitals": "Direct incoming patient flow to nearby fully operational medical clinics and establish field hubs.",
    "shops": "Liaise with local distribution markets to evaluate supply chain viability.",
    "aid_centers": "Broadcast coordinates of active aid distribution centers to affected residents.",
    "other_infrastructure": "Monitor structural damage to water pipelines and sewers.",
    "weather_related": "Review live weather radar dashboards and deploy storm warnings to region.",
    "floods": "Dispatch water pump gear, sandbag reinforcements, and emergency rubber boats.",
    "storm": "Broadcast high-velocity wind warnings and advise residents to stay inside secure shelters.",
    "fire": "Deploy containment engines and establish physical firebreaks.",
    "earthquake": "Coordinate structural aftershock monitoring and conduct immediate check for gas line leaks.",
    "cold": "Establish heated warming stations and dispatch heating fuel supplies.",
    "other_weather": "Assess severe weather metrics and prepare local contingency forces.",
    "direct_report": "Prioritize for instant field verification as a real-time eyewitness alert."
}

def generate_suggestions(active_categories):
    """
    Extracts high-level recommendations corresponding to detected labels.
    """
    suggestions = []
    for category in active_categories:
        if category in SUGGESTION_TEMPLATES:
            suggestions.append(SUGGESTION_TEMPLATES[category])
            
    if not suggestions:
        suggestions.append("Monitor incoming status updates and keep a mobile response team on standby.")
        
    return suggestions

def predict_emergency(message, location=""):
    """
    Preprocesses raw text message, computes model classification predictions,
    and returns parsed metadata labels, emergency priority, and suggested actions.
    """
    artifacts = load_artifacts()
    model = artifacts["model"]
    vectorizer = artifacts["vectorizer"]
    labels = artifacts["labels"]

    cleaned = clean_text(message)
    if not cleaned:
        return {
            "predictions": {label: 0 for label in labels},
            "active_categories": [],
            "priority": "LOW",
            "suggestions": ["No message text found. Please provide an active description of the emergency."]
        }

    # Vectorize and predict
    vector = vectorizer.transform([cleaned])
    predictions = model.predict(vector)
    prediction_values = predictions[0].tolist()

    pred_map = {}
    active_categories = []
    for label, val in zip(labels, prediction_values):
        pred_map[label] = int(val)
        if int(val) == 1:
            active_categories.append(label)

    priority = determine_priority(active_categories)
    suggestions = generate_suggestions(active_categories)

    return {
        "predictions": pred_map,
        "active_categories": active_categories,
        "priority": priority,
        "suggestions": suggestions
    }
