import json
import os
import io
import base64
import hashlib
import hmac
import numpy as np
from flask import Flask, request, jsonify, send_file, render_template
from PIL import Image
from PIL import ImageOps
from scipy.stats import chisquare
from werkzeug.exceptions import RequestEntityTooLarge

HEADER_SIZE = 32

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024

@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(e):

    return jsonify({
        "error":
        "The selected file is too large. Maximum upload size is 25 MB."
    }), 413

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

STOP_MARKER = '1111111111111110'


def derive_key(password: str, salt: bytes, dklen: int = 32) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200000, dklen)


def keystream_from_key(key: bytes, salt: bytes, length: int) -> bytes:
    # Expand key into a keystream using HMAC-SHA256 in counter mode
    out = bytearray()
    counter = 0
    while len(out) < length:
        ctr = counter.to_bytes(4, 'big')
        block = hmac.new(key, salt + ctr, hashlib.sha256).digest()
        out.extend(block)
        counter += 1
    return bytes(out[:length])


def xor_bytes(data: bytes, password: str) -> bytes:
    # legacy fallback (not used for protected payloads)
    if not password:
        return data
    key = password.encode('utf-8')
    if not key:
        return data
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def encode_payload(payload_obj: dict, password: str = "") -> bytes:
    raw = json.dumps(payload_obj, separators=(",", ":")).encode("utf-8")
    if password:
        salt = os.urandom(16)
        key = derive_key(password, salt)
        mac = hmac.new(key, raw, hashlib.sha256).digest()
        to_encrypt = mac + raw
        ks = keystream_from_key(key, salt, len(to_encrypt))
        ciphertext = bytes(t ^ ks[i] for i, t in enumerate(to_encrypt))
        return b'PWS1' + salt + ciphertext
    return raw

def decode_payload(payload: bytes, password: str = "") -> dict:
    if payload.startswith(b'PWS1'):
        if not password:
            raise ValueError('PASSWORD_REQUIRED')
        if len(payload) < 4 + 16 + 32:
            raise ValueError('PASSWORD_INCORRECT')
        salt = payload[4:20]
        ciphertext = payload[20:]
        key = derive_key(password, salt)
        ks = keystream_from_key(key, salt, len(ciphertext))
        plain = bytes(c ^ ks[i] for i, c in enumerate(ciphertext))
        mac = plain[:32]
        raw = plain[32:]
        verify = hmac.new(key, raw, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, verify):
            raise ValueError('PASSWORD_INCORRECT')
    else:
        raw = payload

    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        raise ValueError("INVALID_PAYLOAD")

def img_to_base64(img: Image.Image, fmt='PNG') -> str:
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

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/embed', methods=['POST'])
def embed():
    try:
        file = request.files['image']
        file.seek(0, 2)
        original_file_mb = file.tell() / (1024 * 1024)
        file.seek(0)
        message = request.form.get('message', '')
        password = request.form.get('password', '').strip()
        payload_type = request.form.get('payload_type', 'text').strip().lower()
        
        embedding_profile = request.form.get(
            "embedding_profile",
            "standard"
        ).strip().lower()

        img = Image.open(file)
        original_format = (img.format or "").upper()
        

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

        # ---------- FINAL PAYLOAD ----------

        payload = encode_payload(
            payload_obj,
            password
        )


        payload_bits = ''.join(
            format(byte, '08b')
            for byte in payload
        )


        # optimize using REAL payload size

        img, optimized, original_size, preserved = optimize_cover_image(
            img,
            len(payload_bits)
        )


        img = img.convert("RGB")


        arr = np.array(img)


        payload_length = format(
            len(payload_bits),
            '032b'
        )


        binary_message = (
            payload_length +
            payload_bits
        )
        
        # ---------------- ROBUST PROFILE ----------------

        if embedding_profile == "robust":

            target_bits = int(
                arr.size * 0.45
            )

            if len(binary_message) < target_bits:

                padding_needed = (
                    target_bits - len(binary_message)
                )

                robust_padding = (
                    "0" * padding_needed
                )

                binary_message += robust_padding
        
      
        if len(binary_message) > arr.size:
            max_mb = (
                arr.size / 8
            ) / (1024 * 1024)
            required_mb = (len(binary_message) / 8) / (1024 * 1024)

            return jsonify({
                "error":
                f"Hidden data is too large for this image. "
                f"This cover image can hide about {max_mb:.2f} MB, "
                f"but your data needs {required_mb:.2f} MB."
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

        'original_file_mb': round(
            original_file_mb,
            2
        ),

        'new_mb': round(
            (img.size[0] * img.size[1] * 3)
            / (1024*1024),
            2
        ),
        'original_size': original_size,
        'new_size': img.size,
        'preserved': preserved
    })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/extract', methods=['POST'])
def extract():
    try:
        file = request.files['image']
        password = request.form.get('password', '').strip()
        img = Image.open(file).convert("RGB")
        arr = np.array(img)
        flat = arr.flatten()

        bits = ''.join(
    str(v & 1)
    for v in flat
)
       

        payload_length = int(
            bits[:32],
            2
        )
       


        payload_bits = bits[
            32 : 32 + payload_length
        ]
        
        


        if len(payload_bits) != payload_length:
            return jsonify({
                'message': '',
                'found': False,
                'password_required': False
            })

        payload_bytes = bytearray()
        for i in range(0, len(payload_bits), 8):

            byte = payload_bits[i:i+8]
            if len(byte) < 8:
                break
            try:
                payload_bytes.append(int(byte, 2))
            except ValueError:
                return jsonify({'message': '', 'found': False, 'password_required': False})

        if not payload_bytes:
            return jsonify({'message': '', 'found': False, 'password_required': False})
        
  

        try:
            message = decode_payload(bytes(payload_bytes), password)
            
          

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
    

def chi_pair_analysis(flat):
    counts = np.bincount(flat, minlength=256).astype(float)

    obs = []
    exp = []

    for i in range(0, 256, 2):
        total = counts[i] + counts[i + 1]
        if total > 0:
            obs.extend([counts[i], counts[i + 1]])
            exp.extend([total / 2, total / 2])

    obs = np.array(obs)
    exp = np.array(exp)

    stat, p = chisquare(obs, exp)

    return float(stat), float(p)    


def lsb_balance(channel):
    """
    Returns the proportion of 1s in the LSB plane.
    Natural images usually aren't perfectly balanced.
    """
    bits = channel & 1
    ones = np.sum(bits)
    total = bits.size
    ratio = ones / total

    return {
        "ratio": float(ratio),
        "ones": int(ones),
        "zeros": int(total - ones)
    }

def lsb_entropy(channel):
    """
    Shannon entropy of the LSB plane.

    Maximum entropy = 1
    """

    bits = (channel & 1).flatten()

    p1 = np.mean(bits)
    p0 = 1-p1

    entropy = 0

    if p0>0:
        entropy -= p0*np.log2(p0)

    if p1>0:
        entropy -= p1*np.log2(p1)

    return float(entropy) 

def lsb_flip_rate(channel):
    """
    Calculates how frequently the LSB changes
    between consecutive pixels.
    """

    bits = (channel.flatten() & 1).astype(np.uint8)

    flips = np.sum(bits[:-1] != bits[1:])

    total = len(bits) - 1

    return flips / total

def region_lsb_statistics(channel, parts=10):
    """
    Divide the image into equal regions and calculate
    the LSB ratio for each region.
    """

    bits = (channel & 1).flatten()

    section = len(bits) // parts

    ratios = []

    for i in range(parts):

        start = i * section

        if i == parts - 1:
            end = len(bits)
        else:
            end = (i + 1) * section

        region = bits[start:end]

        ratios.append(float(np.mean(region)))

    return ratios


def cal_region_difference(channel):

    ratios = region_lsb_statistics(channel, parts=20)

    diffs = []

    for i in range(len(ratios) - 1):
        diffs.append(abs(ratios[i] - ratios[i + 1]))

    avg_diff = float(np.mean(diffs))

    return ratios, avg_diff

def optimize_cover_image(img, payload_bits):

    original_size = img.size
    original_bytes = len(img.tobytes())

    width, height = img.size


    # payload size in MB
    payload_mb = payload_bits / 8 / (1024 * 1024)


    # adaptive max dimension
    if payload_mb < 1:
        max_size = 1800

    elif payload_mb < 5:
        max_size = 2500

    else:
        max_size = max(width, height)


    optimized_img = img.copy()


    if max(width, height) > max_size:

        optimized_img.thumbnail(
            (max_size, max_size),
            Image.LANCZOS
        )

        optimized = True

    else:
        optimized = False


    return (
        optimized_img,
        optimized,
        original_size,
        max_size == max(width, height)
    )


def lsb_plane_b64(channel):
    img = Image.fromarray(((channel & 1) * 255).astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()

def payload_to_response(message: dict):
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


@app.route('/detect', methods=['POST'])
def detect():
    try:
        file = request.files['image']
     

        # ---------- IMAGE LOAD ----------
        img = Image.open(file)

       # Fix JPG phone rotation
        img = ImageOps.exif_transpose(img)

        img = img.convert("RGB")


        # keep original pixels for LSB analysis
        arr = np.array(img)


        # create optimized copy only for heavy analysis/display
        analysis_img = img.copy()

        if max(analysis_img.size) > 1600:
            analysis_img.thumbnail(
                (1600, 1600),
                Image.LANCZOS
            )

        analysis_arr = np.array(analysis_img)


        warning = ""

        R, G, B = arr[:,:,0], arr[:,:,1], arr[:,:,2]
       

    # ---------- Feature Extraction ----------

        balance_r = lsb_balance(R)
        balance_g = lsb_balance(G)
        balance_b = lsb_balance(B)

        balance_ratio = (
            balance_r["ratio"] +
            balance_g["ratio"] +
            balance_b["ratio"]
        ) / 3
        region_r, diff_r = cal_region_difference(R)
        region_g, diff_g = cal_region_difference(G)
        region_b, diff_b = cal_region_difference(B)

        region_start = (
            region_r[0] +
            region_g[0] +
            region_b[0]
        ) / 3

        region_end = (
            region_r[-1] +
            region_g[-1] +
            region_b[-1]
        ) / 3

        region_difference = (
            diff_r +
            diff_g +
            diff_b
        ) / 3

        entropy_r = lsb_entropy(R)
        entropy_g = lsb_entropy(G)
        entropy_b = lsb_entropy(B)

        entropy_avg = (
            entropy_r +
            entropy_g +
            entropy_b
        ) / 3  
        
        flip_r = lsb_flip_rate(R)
        flip_g = lsb_flip_rate(G)
        flip_b = lsb_flip_rate(B)

        flip_rate = (
            flip_r +
            flip_g +
            flip_b
        ) / 3     

        # Chi-Square
        flat = arr.flatten()
        chi_stat, chi_p = chi_pair_analysis(flat)

        # LSB stats
        lsb = arr & 1
        ones = int(np.sum(lsb))
        total = int(lsb.size)
        ratio = round(ones / total, 4)

        # LSB plane image (Red channel)
        lsb_img = lsb_plane_b64(R)
        # ---------- Risk Scoring ----------
        score = 0
        reasons = []


        # Region analysis
        if region_difference > 0.015:
            score += 40
            reasons.append("Strong regional LSB variation detected")

        elif region_difference > 0.008:
            score += 15
            reasons.append("Moderate regional LSB variation detected")


        # LSB balance analysis
        balance_shift = abs(balance_ratio - 0.5)

        if balance_shift > 0.025:
            score += 45
            reasons.append("Abnormal LSB distribution detected")

        elif balance_shift > 0.012:
            score += 20
            reasons.append("Minor LSB distribution shift detected")


        # Entropy analysis
        if entropy_avg < 0.998:
            score += 30
            reasons.append("Reduced LSB randomness detected")

        elif entropy_avg < 0.999:
            score += 10
            reasons.append("Slight randomness reduction detected")

        # Chi-square support
        if chi_p < 0.05:
            score += 5
            reasons.append("Chi-square supports statistical alteration")

       # Keep score within 0-100 range
        score = min(score, 100)

        confidence = score


        if score >= 60:

            status = "Strong Indicators of Hidden Data"

        elif score >= 35:

            status = "Possible Hidden Data"

        else:

            status = "No strong Indicators of Hidden Data"


        suspected = score >= 35
        return jsonify({
            # existing keys kept for backward compat
            'chi_stat':     round(chi_stat, 2),
            'p_value':      round(chi_p, 6),
            'lsb_ratio':    ratio,
            'ones':         ones,
            'zeros':        total - ones,
            'total':        total,
            'suspected':    suspected,
            
            # chi
            'chi_p':        round(chi_p, 6),
            'chi_detected': chi_p < 0.05,
            # extras
            'lsb_plane':    lsb_img,
            'confidence':   confidence,
            'status': status,
            'score': score,
            'reasons': reasons,
            
            'region_start': round(region_start, 6),
            'region_end': round(region_end, 6),
            'region_difference': round(region_difference, 6),
            'balance_ratio': round(balance_ratio,4),
            'lsb_entropy': round(entropy_avg,4),
            'warning': warning

        })
       
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run()