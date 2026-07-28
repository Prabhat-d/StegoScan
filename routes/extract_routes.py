import io
import numpy as np
from flask import Blueprint, request, jsonify, send_file
from PIL import Image, ImageOps
from core.security import decode_payload
from core.stego_engine import payload_to_response

extract_bp = Blueprint('extract_bp', __name__)

@extract_bp.route('/extract', methods=['POST'])
def extract():
    try:
        file = request.files['image']
        password = request.form.get('password', '').strip()
        img = Image.open(file)
        img = ImageOps.exif_transpose(img)

        # Always convert to RGB to match embed layout
        img = img.convert("RGB")
        arr = np.array(img)
        flat = arr.flatten()
        total_pixels = flat.size

        if total_pixels < 32:
            return jsonify({'message': '', 'found': False, 'password_required': False})

        length_bits = ''.join(str(flat[i] & 1) for i in range(32))
        try:
            payload_length = int(length_bits, 2)
        except ValueError:
            return jsonify({'message': '', 'found': False, 'password_required': False})

        if payload_length <= 0 or payload_length > total_pixels - 32 or payload_length % 8 != 0:
            return jsonify({'message': '', 'found': False, 'password_required': False})

        payload_bits = ''.join(str(flat[32 + i] & 1) for i in range(payload_length))
        
        payload_bytes = bytearray()
        for b_idx in range(0, len(payload_bits), 8):
            chunk = payload_bits[b_idx:b_idx+8]
            if len(chunk) < 8:
                break
            payload_bytes.append(int(chunk, 2))
        payload_bytes = bytes(payload_bytes)

        if not payload_bytes:
            return jsonify({'message': '', 'found': False, 'password_required': False})

        try:
            message = decode_payload(payload_bytes, password)
        except ValueError as exc:
            code = str(exc)
            if code == 'PASSWORD_REQUIRED':
                return jsonify({'message': '', 'found': False, 'password_required': True})
            if code == 'PASSWORD_INCORRECT':
                return jsonify({'message': '', 'found': False, 'password_required': False, 'password_incorrect': True})
            return jsonify({'message': '', 'found': False, 'password_required': False})

        if not isinstance(message, dict):
            return jsonify({'message': '', 'found': False, 'password_required': False})

        result = payload_to_response(message)
        if isinstance(result, tuple):
            return result

        if isinstance(result, dict) and result.get("payload_type") in ("file", "image"):
            bio = io.BytesIO(result["file_bytes"])
            bio.seek(0)
            return send_file(
                bio,
                as_attachment=True,
                download_name=result["filename"],
                mimetype=result["mime"]
            )

        return result
    except Exception as e:
        return jsonify({'error': str(e)}), 500
