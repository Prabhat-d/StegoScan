import io
import base64
from PIL import Image
from flask import jsonify

def img_to_base64(img: Image.Image, fmt='PNG') -> str:
    # Serialize PIL Image into base64 string for JSON API responses
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode()

def build_text_payload(message: str) -> dict:
    return {
        "type": "text",
        "name": "message.txt",
        "mime": "text/plain",
        "data": message
    }

def build_file_payload(file_storage) -> dict:
    file_bytes = file_storage.read()
    return {
        "type": "file",
        "name": file_storage.filename or "hidden_file",
        "mime": file_storage.mimetype or "application/octet-stream",
        "data": base64.b64encode(file_bytes).decode("utf-8")
    }

def build_image_payload(file_storage) -> dict:
    file_bytes = file_storage.read()
    return {
        "type": "image",
        "name": file_storage.filename or "hidden_image.png",
        "mime": file_storage.mimetype or "image/png",
        "data": base64.b64encode(file_bytes).decode("utf-8")
    }

def optimize_cover_image(img: Image.Image, payload_bits: int):
    # Scale cover image dimensions to fit payload bit-capacity
    original_size = img.size
    width, height = img.size
    payload_mb = payload_bits / 8 / (1024 * 1024)

    if payload_mb < 1:
        max_size = 1800
    elif payload_mb < 5:
        max_size = 2500
    else:
        max_size = max(width, height)

    optimized_img = img.copy()
    if max(width, height) > max_size:
        optimized_img.thumbnail((max_size, max_size), Image.LANCZOS)
        optimized = True
    else:
        optimized = False

    return optimized_img, optimized, original_size, max_size == max(width, height)

def payload_to_response(message: dict):
    # Formats decoded JSON dictionary into API response format
    ptype = message.get("type", "text")
    if ptype == "text":
        return jsonify({
            "found": True,
            "payload_type": "text",
            "message": message.get("data", "")
        })

    data_b64 = message.get("data", "")
    filename = message.get("name", "download.bin")
    mime = message.get("mime", "application/octet-stream")

    if not data_b64:
        return jsonify({"found": False, "error": "EMPTY_PAYLOAD"}), 400

    file_bytes = base64.b64decode(data_b64)
    return {
        "found": True,
        "payload_type": ptype,
        "filename": filename,
        "mime": mime,
        "file_bytes": file_bytes
    }
