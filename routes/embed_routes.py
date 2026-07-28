import numpy as np
from flask import Blueprint, request, jsonify
from PIL import Image, ImageOps
from core.security import encode_payload
from core.stego_engine import (
    build_text_payload, build_file_payload, build_image_payload,
    optimize_cover_image, img_to_base64
)

embed_bp = Blueprint('embed_bp', __name__)

@embed_bp.route('/embed', methods=['POST'])
def embed():
    try:
        file = request.files['image']
        file.seek(0, 2)
        original_file_mb = file.tell() / (1024 * 1024)
        file.seek(0)
        message = request.form.get('message', '')
        password = request.form.get('password', '').strip()
        payload_type = request.form.get('payload_type', 'text').strip().lower()
        embedding_profile = request.form.get("embedding_profile", "standard").strip().lower()

        img = Image.open(file)
        img = ImageOps.exif_transpose(img)

        if payload_type == "text":
            payload_obj = build_text_payload(message)
        elif payload_type == "file":
            hidden_file = request.files.get('hidden_file')
            if not hidden_file:
                return jsonify({'error': 'hidden_file is required for file payload'}), 400
            payload_obj = build_file_payload(hidden_file)
        elif payload_type == "image":
            hidden_image = request.files.get('hidden_image')
            if not hidden_image:
                return jsonify({'error': 'hidden_image is required for image payload'}), 400
            payload_obj = build_image_payload(hidden_image)
        else:
            return jsonify({'error': 'Invalid payload_type. Use text, file, or image.'}), 400

        payload = encode_payload(payload_obj, password)
        payload_bits = ''.join(format(byte, '08b') for byte in payload)

        img, optimized, original_size, preserved = optimize_cover_image(img, len(payload_bits))
        
        # Consistently convert to RGB for 100% channel index alignment
        img = img.convert("RGB")
        arr = np.array(img)

        payload_length = format(len(payload_bits), '032b')
        binary_message = payload_length + payload_bits

        if embedding_profile == "robust":
            target_bits = int(arr.size * 0.45)
            if len(binary_message) < target_bits:
                padding_needed = target_bits - len(binary_message)
                binary_message += "0" * padding_needed

        if len(binary_message) > arr.size:
            max_mb = (arr.size / 8) / (1024 * 1024)
            required_mb = (len(binary_message) / 8) / (1024 * 1024)
            return jsonify({
                "error": f"Hidden data is too large for this image. "
                         f"This cover image can hide about {max_mb:.2f} MB, but your data needs {required_mb:.2f} MB."
            }), 400

        flat = arr.flatten().copy()
        for i, bit in enumerate(binary_message):
            flat[i] = (flat[i] & 0b11111110) | int(bit)

        stego_arr = flat.reshape(arr.shape)
        stego_img = Image.fromarray(stego_arr.astype(np.uint8))
        stego_b64 = img_to_base64(stego_img)

        return jsonify({
            'stego': stego_b64,
            'bits_used': len(binary_message),
            'capacity': arr.size,
            'optimized': optimized,
            'original_file_mb': round(original_file_mb, 2),
            'new_mb': round((img.size[0] * img.size[1] * 3) / (1024 * 1024), 2),
            'original_size': original_size,
            'new_size': img.size,
            'preserved': preserved
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
