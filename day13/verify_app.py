import sys
import os
import io

try:
    from app import app, model
except Exception as e:
    print("Failed to import app.py:", e)
    sys.exit(1)

print("YOLO Model loaded successfully:", model is not None)

client = app.test_client()

# 1. Test GET /
print("\n--- Testing GET / ---")
response = client.get('/')
print("GET / Status Code:", response.status_code)
if response.status_code == 200:
    print("GET / passed!")
else:
    print("GET / failed!")
    sys.exit(1)

# 2. Test POST /detect with no file
print("\n--- Testing POST /detect with no file ---")
response = client.post('/detect')
print("POST /detect (no file) Status Code:", response.status_code)
print("POST /detect (no file) Response:", response.get_json())
if response.status_code == 400:
    print("POST /detect (no file) validation passed!")
else:
    print("POST /detect (no file) validation failed!")
    sys.exit(1)

# 3. Test POST /detect with invalid file type
print("\n--- Testing POST /detect with invalid file type ---")
response = client.post('/detect', data={
    'image': (io.BytesIO(b"fake text data"), 'test.txt')
})
print("POST /detect (invalid file) Status Code:", response.status_code)
print("POST /detect (invalid file) Response:", response.get_json())
if response.status_code == 400:
    print("POST /detect (invalid file) validation passed!")
else:
    print("POST /detect (invalid file) validation failed!")
    sys.exit(1)

# 4. Test POST /detect with a real image test.jpg
print("\n--- Testing POST /detect with test.jpg ---")
test_image_path = 'test.jpg'
if os.path.exists(test_image_path):
    with open(test_image_path, 'rb') as img_file:
        response = client.post('/detect', data={
            'image': (img_file, 'test.jpg'),
            'confidence': '0.1'
        })
    print("POST /detect Status Code:", response.status_code)
    data = response.get_json()
    print("POST /detect Response success:", data.get('success'))
    if response.status_code == 200 and data.get('success') is True:
        print("Detections count:", len(data.get('detections', [])))
        print("Detections details:", data.get('detections'))
        print("Original Image URL:", data.get('original_image_url'))
        print("Annotated Image URL:", data.get('annotated_image_url'))
        print("POST /detect with test.jpg passed!")
    else:
        print("POST /detect with test.jpg failed!", data)
        sys.exit(1)
else:
    print(f"Warning: test_image_path '{test_image_path}' not found, skipping inference test.")

print("\nAll Flask app verification tests passed successfully!")
sys.exit(0)
