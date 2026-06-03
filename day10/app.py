from ultralytics import YOLO

print("Loading Disaster Assessment Model...")

model = YOLO("best.pt")

print("Analyzing image...")

results = model.predict(
    source="test.jpg",
    save=True,
    conf=0.25
)

print("\n===== DISASTER DAMAGE ASSESSMENT REPORT =====")

detected = False

for result in results:
    if result.boxes is not None and len(result.boxes) > 0:

        detected = True

        for box in result.boxes:

            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            disaster = model.names[class_id]

            # Severity estimation based on confidence
            if confidence >= 0.80:
                severity = "High"
            elif confidence >= 0.50:
                severity = "Medium"
            else:
                severity = "Low"

            print(f"\nDisaster Type      : {disaster}")
            print(f"Confidence Score  : {confidence:.2f}")
            print(f"Estimated Severity: {severity}")

            print("\nRecovery Recommendations:")

            recommendations = {
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

            for rec in recommendations.get(disaster, ["No recommendation available"]):
                print(f"- {rec}")

if not detected:
    print("No disaster detected in the image.")

print("\nAssessment Completed Successfully.")