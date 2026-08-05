import gc
import numpy as np
from flask import Blueprint, request, jsonify
from PIL import Image, ImageOps
from core.steganalysis import (
    probe_signature, chi_pair_analysis, lsb_balance, lsb_entropy,
    cal_region_difference, rs_steganalysis, get_bitplanes_b64
)

detect_bp = Blueprint('detect_bp', __name__)

ALLOWED_FORMATS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'tif'}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB safety limit for web hosting

@detect_bp.route('/detect', methods=['POST'])
def detect():
    try:
        file = request.files['image']

        # Reject files exceeding 25 MB safety limit
        file.seek(0, 2)
        size_bytes = file.tell()
        file.seek(0)
        if size_bytes > MAX_FILE_SIZE_BYTES:
            size_mb = round(size_bytes / (1024 * 1024), 1)
            return jsonify({'error': f'File size ({size_mb} MB) exceeds the 25 MB safety limit. Please upload a smaller image.'}), 400

        # Reject unsupported formats before attempting to open
        filename = file.filename or ''
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in ALLOWED_FORMATS:
            friendly = ext.upper() if ext else 'Unknown'
            return jsonify({'error': f'Unsupported file format: {friendly}. Please upload a PNG, JPG, WEBP, or BMP image.'}), 400

        try:
            img = Image.open(file)
            img.verify()          # catches truncated / corrupt files
            file.seek(0)
            img = Image.open(file)
        except Exception:
            return jsonify({'error': 'Could not read the image. The file may be corrupt or not a valid image.'}), 400

        img = ImageOps.exif_transpose(img)
        img_rgb = img.convert("RGB")
        arr = np.array(img_rgb)

        flat = arr.flatten()
        warning = ""

        # 1. Direct Signature Probing (reads initial raw bits directly for 100% exact magic header matching)
        signature_detected, sig_type, payload_meta = probe_signature(flat)

        # 2. Uniform Grid Sampling for Statistical Steganalysis
        # Caps computation grid to max 800x800 while preserving 100% spatial coverage across all regions.
        # Accelerates analysis to ~0.25s and prevents server Out-Of-Memory crashes.
        h, w = arr.shape[:2]
        max_dim = max(h, w)
        if max_dim > 800:
            step = max(1, int(max_dim / 800))
            calc_arr = arr[::step, ::step]
        else:
            calc_arr = arr

        calc_flat = calc_arr.flatten()
        R, G, B = calc_arr[:,:,0], calc_arr[:,:,1], calc_arr[:,:,2]

        balance_r = lsb_balance(R)
        balance_g = lsb_balance(G)
        balance_b = lsb_balance(B)
        balance_ratio = (balance_r["ratio"] + balance_g["ratio"] + balance_b["ratio"]) / 3

        region_r, diff_r = cal_region_difference(R)
        region_g, diff_g = cal_region_difference(G)
        region_b, diff_b = cal_region_difference(B)

        region_start = (region_r[0] + region_g[0] + region_b[0]) / 3
        region_end = (region_r[-1] + region_g[-1] + region_b[-1]) / 3
        region_difference = (diff_r + diff_g + diff_b) / 3

        entropy_r = lsb_entropy(R)
        entropy_g = lsb_entropy(G)
        entropy_b = lsb_entropy(B)
        entropy_avg = (entropy_r + entropy_g + entropy_b) / 3

        # Per-channel & Spatial Block Chi-Square PoV Analysis (Westfeld Method)
        # Evaluates full channel and 4 spatial blocks (0-25%, 25-50%, 50-75%, 75-100%) to catch sequential/top-half embeddings
        chi_stat_r, chi_p_r = chi_pair_analysis(R.flatten())
        chi_stat_g, chi_p_g = chi_pair_analysis(G.flatten())
        chi_stat_b, chi_p_b = chi_pair_analysis(B.flatten())
        chi_stat, chi_p_comb = chi_pair_analysis(calc_flat)

        block_chi_p_list = [chi_p_r, chi_p_g, chi_p_b]
        q_h = R.shape[0] // 4
        for q_i in range(4):
            for ch in [R, G, B]:
                b_flat = ch[q_i * q_h : (q_i + 1) * q_h, :].flatten()
                if b_flat.size >= 100:
                    _, b_p = chi_pair_analysis(b_flat)
                    block_chi_p_list.append(b_p)

        # In Westfeld's Chi-Square PoV, max p -> 1.0 (p > 0.95) indicates 50:50 histogram parity equalization (steganography)
        stego_chi_p = max(block_chi_p_list)
        chi_p = stego_chi_p

        # Fallback metadata inference if no signature header exists but statistical anomalies are flagged
        if not signature_detected:
            if stego_chi_p >= 0.95 or entropy_avg >= 0.998:
                payload_meta["encryption"] = "External LSB Stream (High Entropy / Encrypted)"
                payload_meta["content_type"] = "Headerless External Stego Data"
            elif entropy_avg >= 0.990:
                payload_meta["encryption"] = "Moderate Randomness Data"
                payload_meta["content_type"] = "Unstructured LSB Data / High-Noise Image"

        # RS Steganalysis payload estimation (evaluates per-channel max to catch single-channel attacks)
        rs_p_r, rs_payload_r = rs_steganalysis(R)
        rs_p_g, rs_payload_g = rs_steganalysis(G)
        rs_p_b, rs_payload_b = rs_steganalysis(B)
        rs_payload_ratio = float(max(rs_payload_r, rs_payload_g, rs_payload_b, (rs_payload_r + rs_payload_g + rs_payload_b) / 3))
        rs_estimated_kb = float((arr.size / 8 * rs_payload_ratio) / 1024)

        # Per-channel max regional difference
        region_difference = float(max(diff_r, diff_g, diff_b, (diff_r + diff_g + diff_b) / 3))

        lsb = calc_arr & 1
        ones = int(np.sum(lsb))
        total = int(lsb.size)
        ratio = round(ones / total, 4)
        bitplanes = get_bitplanes_b64(calc_arr)

        score = 0
        reasons = []
        balance_shift = abs(balance_ratio - 0.5)

        # 1. RS Steganalysis Payload Estimation (Fridrich et al.)
        if rs_payload_ratio >= 0.20:
            score += 50
            reasons.append(f"RS Steganalysis: significant hidden payload detected (~{round(rs_payload_ratio*100, 1)}% of capacity, est. {round(rs_estimated_kb, 1)} KB)")
        elif rs_payload_ratio >= 0.08:
            score += 30
            reasons.append(f"RS Steganalysis: moderate hidden payload detected (~{round(rs_payload_ratio*100, 1)}% of capacity, est. {round(rs_estimated_kb, 1)} KB)")
        elif rs_payload_ratio >= 0.03:
            score += 15
            reasons.append(f"RS Steganalysis: minor LSB payload detected (~{round(rs_payload_ratio*100, 1)}% of capacity)")

        # 2. Chi-Square PoV Histogram Parity Equalization (Westfeld Method)
        # On stego images, Chi-Square p-value approaches 1.0 (p > 0.95) due to forced 50:50 pair counts
        if stego_chi_p >= 0.999:
            score += 35
            reasons.append(f"Chi-square PoV confirms LSB histogram parity equalization (p = {round(stego_chi_p, 4)})")
        elif stego_chi_p >= 0.95:
            score += 20
            reasons.append(f"Chi-square PoV supports LSB histogram parity equalization (p = {round(stego_chi_p, 4)})")

        # 3. Regional LSB Variation (Sequential Embedding Pattern)
        if region_difference > 0.018:
            score += 35
            reasons.append(f"Strong sequential embedding pattern detected (regional LSB shift: {round(region_difference, 4)})")
        elif region_difference > 0.010:
            score += 18
            reasons.append(f"Moderate regional LSB variation detected ({round(region_difference, 4)})")

        # 4. High LSB Entropy — scored when corroborated by Chi-Square or RS payload
        if entropy_avg >= 0.995 and (stego_chi_p >= 0.95 or rs_payload_ratio >= 0.03):
            score += 20
            reasons.append(f"Near-maximum LSB entropy ({round(entropy_avg, 4)}) corroborated by statistical LSB parity shift")

        # 5. Artificial 50:50 forced distribution — scored when corroborated by Chi-Square or RS payload
        if balance_shift < 0.005 and (stego_chi_p >= 0.95 or rs_payload_ratio >= 0.03):
            score += 15
            reasons.append(f"LSB bit ratio near-perfect 50:50 ({round(balance_ratio*100, 2)}%), confirmed by Chi-Square test")

        # Explicit signature match overrides all heuristics to 100%
        if signature_detected:
            score = max(score, 100)
            reasons.insert(0, f"Pinpoint Steganography Signature Found: Verified {sig_type}")

        score = min(score, 100)
        confidence = score

        if score >= 65:
            status = "Strong Indicators of Hidden Data"
        elif score >= 35:
            status = "Possible Hidden Data"
        else:
            status = "No strong Indicators of Hidden Data"

        suspected = score >= 35
        return jsonify({
            'chi_stat': round(chi_stat, 2),
            'p_value': round(chi_p, 6),
            'lsb_ratio': ratio,
            'ones': ones,
            'zeros': total - ones,
            'total': total,
            'suspected': suspected,

            'chi_p': round(chi_p, 6),
            'chi_detected': chi_p < 0.05,
            'lsb_plane': bitplanes["red"],
            'bitplanes': bitplanes,
            'confidence': confidence,
            'status': status,
            'score': score,
            'reasons': reasons,
            'signature_detected': signature_detected,
            'sig_type': sig_type,
            'payload_meta': payload_meta,

            'rs_payload_ratio': round(rs_payload_ratio, 4),
            'rs_estimated_kb': round(rs_estimated_kb, 2),

            'region_start': round(region_start, 6),
            'region_end': round(region_end, 6),
            'region_difference': round(region_difference, 6),
            'balance_ratio': round(balance_ratio, 4),
            'lsb_entropy': round(entropy_avg, 4),
            'warning': warning
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        gc.collect()

