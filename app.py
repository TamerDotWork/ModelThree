import os
import base64
import json
import requests
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

GEMINI_API_KEY = 'AIzaSyAtH6b2eUlVWQ1dfkVbnzsp_zHhaY9rzFA'
GEMINI_MODEL = "gemini-2.5-flash-preview-05-20"
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def call_gemini_api(image_bytes):
    if not GEMINI_API_KEY:
        raise Exception("Missing GEMINI_API_KEY")

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    
    prompt_text = """
You are a UX-aware assistant. Analyze this UI sketch image and return JSON ONLY.
Follow these instructions strictly:

1. Start with the main container element: either "Screen/main" or a "Popup" type.
2. Each container should have a "title" or "label".
3. Include all child elements in an "elements" array.
4. Each element must have the following fields (if applicable):
    - type: The type of element (Text, Input/text, Button/primary, Button/close, etc.)
    - label/title: The text label or title associated with the element
    - value: The content or default value of the element
    - status: Optional state info (enabled, disabled, selected, etc.)
    - context: Optional description/context for the element's use
5. Maintain the hierarchy of containers and their inner elements.
6. Return valid JSON only. Example structure:

{
    "ui_elements": [
        {
            "type": "Screen/main",
            "title": "Main Screen",
            "elements": [
                {
                    "type": "Text",
                    "label": "Welcome",
                    "value": "Welcome to the app",
                    "status": "visible",
                    "context": "Header text"
                },
                {
                    "type": "Input/text",
                    "label": "Username",
                    "value": "",
                    "status": "editable",
                    "context": "User login field"
                },
                {
                    "type": "Button/primary",
                    "label": "Submit",
                    "value": "Submit",
                    "status": "enabled",
                    "context": "Login submission"
                }
            ]
        }
    ]
}
"""

    payload = {
        "contents": [
            {
                "parts": [
                    {"inline_data": {"mime_type": "image/png", "data": image_b64}},
                    {"text": prompt_text}
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
    """Recursively enhance the UI elements by adding defaults and cleaning hierarchy."""
    enhanced = []
    for i, elem in enumerate(ui_elements):
        e_type = elem.get("type", "Text")
        new_elem = {"type": e_type}

        # Labels / titles
        new_elem["label"] = elem.get("label") or elem.get("title") or "Label"

        # Values
        if e_type == "Text":
            new_elem["value"] = elem.get("value", "Text")
        elif e_type.startswith("Input"):
            new_elem["value"] = elem.get("value", "")
        elif e_type.startswith("Button"):
            new_elem["value"] = elem.get("value", "Submit")
            if "close" in e_type.lower():
                new_elem["type"] = "Button/close"
            else:
                new_elem["type"] = "Button/primary"

        # Status and context
        new_elem["status"] = elem.get("status", "visible")
        new_elem["context"] = elem.get("context", "")

        # Recursive enhancement for container elements
        if "elements" in elem:
            new_elem["elements"] = enhance_ui_elements(elem.get("elements", []))

        enhanced.append(new_elem)

    return enhanced


@app.route("/api", methods=["GET", "POST"])
def api():
    if request.method == "GET":
        return jsonify({
            "message": "UI Processing API is running",
            "allowed_methods": ["GET", "POST"]
        })

    # POST flow
    image_bytes = None
    if "image" in request.files:
        image_bytes = request.files["image"].read()
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

        ui_elements = json.loads(raw_text).get("ui_elements", [])
        enhanced_ui = enhance_ui_elements(ui_elements)

        return jsonify({"enhanced_ui": enhanced_ui, "raw_text": raw_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5003)
