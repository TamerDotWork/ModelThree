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

1. Identify the main container (Screen or Popup) and provide a descriptive 'context' for it.
   - Include whether it is a screen or popup.
   - If the container has a title or header text, include it in the container, not as a separate element.
2. Include all child elements in an 'elements' array.
3. Combine label + input fields into a single UI element if:
   - The text is near, small, or above the input field
   - The text visually looks like the label for the input
4. Each element must have the following fields (if applicable):
    - type: The type of element (Text, Input/text, Button/primary, Button/close, etc.)
    - label/title: The text label or title associated with the element
    - value: The content or default value of the element
    - status: Optional state info (enabled, disabled, selected, etc.)
    - context: Optional description/context for the element's use
5. Maintain the hierarchy of containers and their inner elements.
6. Do not duplicate container title/head text as a separate element.
7. Return valid JSON only.
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


def enhance_ui_elements(ui_elements, is_root=False):
    """Enhance UI elements, merge label+input, handle container context, merge container metadata into context."""
    enhanced = []
    skip_next = False

    for i, elem in enumerate(ui_elements):
        if skip_next:
            skip_next = False
            continue

        e_type = elem.get("type", "Text")
        new_elem = {}

        # Combine label + input if next element is input
        if e_type == "Text" and i+1 < len(ui_elements) and ui_elements[i+1].get("type", "") == "Input/text":
            input_elem = ui_elements[i+1]
            new_elem = {
                "type": "Input/text",
                "label": elem.get("value", "Label"),
                "value": input_elem.get("value", ""),
                "status": input_elem.get("status", "editable"),
                "context": "Label and input combined"
            }
            skip_next = True

        else:
            # Status and context
            new_elem["status"] = elem.get("status", "visible")
            new_elem["context"] = elem.get("context", "")

            # Values
            new_elem["value"] = elem.get("value", "") if e_type.startswith("Input") or e_type.startswith("Text") else elem.get("value", "Submit")

            # Type
            if e_type.startswith("Button"):
                new_elem["type"] = "Button/close" if "close" in e_type.lower() else "Button/primary"
            else:
                new_elem["type"] = e_type

            # Label
            new_elem["label"] = elem.get("label") or elem.get("title") or "Label"

        # Recursive enhancement for container elements
        if "elements" in elem:
            new_elem["elements"] = enhance_ui_elements(elem.get("elements", []))

            # Merge container metadata into context if root or container
            if is_root or e_type.lower() in ["screen/main", "popup/modal", "popup/bottom"]:
                container_desc = f"{new_elem['context']}".strip()
                meta_info = f"Type: {e_type}, Label: {elem.get('label', elem.get('title', ''))}, Status: {elem.get('status', 'visible')}"
                new_elem["context"] = f"{container_desc} {meta_info}".strip()
                new_elem.pop("label", None)
                new_elem.pop("status", None)
                new_elem.pop("type", None)

        enhanced.append(new_elem)

    return enhanced


@app.route("/api", methods=["GET", "POST"])
def api():
    if request.method == "GET":
        return jsonify({
            "message": "UI Processing API is running",
            "allowed_methods": ["GET", "POST"]
        })

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
        enhanced_ui = enhance_ui_elements(ui_elements, is_root=True)

        return jsonify({"enhanced_ui": enhanced_ui, "raw_text": raw_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5003)