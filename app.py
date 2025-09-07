import os
import base64
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS for specific origin and all methods (GET, POST, OPTIONS)
CORS(app)

GEMINI_API_KEY = 'AIzaSyAtH6b2eUlVWQ1dfkVbnzsp_zHhaY9rzFA'
GEMINI_MODEL = "gemini-2.5-flash-preview-05-20"
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def call_gemini_api(image_bytes):
    if not GEMINI_API_KEY:
        raise Exception("Missing GEMINI_API_KEY environment variable")

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": image_b64
                        }
                    },
                    {
                        "text": """You are a UX-aware assistant. Analyze this UI sketch and return **JSON ONLY**.
Use these mappings:

- Input/text → include "label" above input if text label exists
- Button/primary → primary buttons
- Button/close → popup/modal close buttons
- Popup/bottom → popup frame
- Screen/main → main screen frame
- Title for popup/screen → use "title" field ("Myhead" if missing)

Output schema:
{
  "ui_elements": [
    {
      "type": "Input/text",
      "label": "Label text"
    },
    {
      "type": "Button/primary",
      "value": "Submit"
    },
    {
      "type": "Button/close",
      "value": "Close"
    },
    {
      "type": "Popup/bottom",
      "title": "Myhead",
      "elements": [...]
    },
    {
      "type": "Screen/main",
      "title": "Myhead",
      "elements": [...]
    }
  ]
}"""
                    }
                ]
            }
        ]
    }

    response = requests.post(
        GEMINI_ENDPOINT,
        params={"key": GEMINI_API_KEY},
        headers={"Content-Type": "application/json"},
        json=payload,
    )

    if response.status_code != 200:
        raise Exception(f"Gemini API error: {response.status_code} {response.text}")

    return response.json()


def enhance_ui_elements(ui_elements):
    """Ensure default fields and proper component mapping."""
    enhanced = []

    for i, elem in enumerate(ui_elements):
        e_type = elem.get("type", "Text")
        new_elem = {"type": e_type}

        # Input with label
        if e_type == "Input/text":
            label = elem.get("label")
            if not label and i > 0 and ui_elements[i - 1].get("type") == "Text":
                label = ui_elements[i - 1].get("value", "")
            new_elem["label"] = label or "Label"

        # Buttons
        if e_type.startswith("Button"):
            if "close" in e_type.lower():
                new_elem["type"] = "Button/close"
                new_elem["value"] = elem.get("value", "Close")
            else:
                new_elem["type"] = "Button/primary"
                new_elem["value"] = elem.get("value", "Submit")

        # Popups and Screens
        if e_type in ["Popup/bottom", "Screen/main"]:
            new_elem["title"] = elem.get("title") or "Myhead"
            new_elem["elements"] = enhance_ui_elements(elem.get("elements", []))

        # Text
        if e_type == "Text":
            new_elem["value"] = elem.get("value", "Text")

        enhanced.append(new_elem)

    return enhanced


@app.route("/ModelThree/process-ui", methods=["GET", "POST", "OPTIONS"])
def process_ui():
    # Handle preflight OPTIONS request
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight OK"}), 200

    # Simple GET request for testing service
    if request.method == "GET":
        return jsonify({
            "message": "UI Processing API is running",
            "allowed_methods": ["GET", "POST"]
        }), 200

    # --- POST flow ---
    image_bytes = None

    if "image" in request.files:
        image_file = request.files["image"]
        image_bytes = image_file.read()
    else:
        data = request.get_json()
        if data and "image_base64" in data:
            image_bytes = base64.b64decode(data["image_base64"])

    if not image_bytes:
        return jsonify({"error": "No image provided"}), 400

    try:
        raw_response = call_gemini_api(image_bytes)

        candidates = raw_response.get("candidates", [])
        if not candidates:
            return jsonify({"error": "No candidates returned"}), 500

        raw_text = candidates[0]["content"]["parts"][0].get("text", "").strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        ui_elements = json.loads(raw_text)
        if "ui_elements" in ui_elements:
            ui_elements = ui_elements["ui_elements"]

        enhanced_ui = enhance_ui_elements(ui_elements)

        return jsonify({"enhanced_ui": enhanced_ui, "raw_text": raw_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5003)
