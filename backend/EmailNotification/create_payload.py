import base64
import json

# Load JSON data from an external file
with open('payload.json') as f:
    payload_data = json.load(f)

# Encode the JSON data to base64
encoded_data = base64.b64encode(json.dumps(payload_data).encode()).decode()
print(encoded_data)

