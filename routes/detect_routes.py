import numpy as np
from flask import Blueprint, request, jsonify
from PIL import Image, ImageOps
from core.steganalysis import (
    probe_signature, chi_pair_analysis, lsb_balance, lsb_entropy,
    cal_region_difference, rs_steganalysis, get_bitplanes_b64
)

detect_bp = Blueprint('detect_bp', __name__)

ALLOWED_FORMATS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'tif'}

@detect_bp.route('/detect', methods=['POST'])
def detect():
    try:
        file = request.files['image']

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

        # 1. Direct Signature Probing
        signature_detected, sig_type = probe_signature(flat)

        # 2. Multi-Metric Statistical Steganalysis
        R, G, B = arr[:,:,0], arr[:,:,1], arr[:,:,2]

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

        chi_stat, chi_p = chi_pair_analysis(flat)

        # RS Steganalysis payload estimation
        rs_p_r, rs_payload_r = rs_steganalysis(R)
        rs_p_g, rs_payload_g = rs_steganalysis(G)
        rs_p_b, rs_payload_b = rs_steganalysis(B)
        rs_payload_ratio = float((rs_payload_r + rs_payload_g + rs_payload_b) / 3)
        rs_estimated_kb = float((arr.size / 8 * rs_payload_ratio) / 1024)

        lsb = arr & 1
        ones = int(np.sum(lsb))
        total = int(lsb.size)
        ratio = round(ones / total, 4)
        bitplanes = get_bitplanes_b64(arr)

        score = 0
        reasons = []
        balance_shift = abs(balance_ratio - 0.5)

        # NOTE ON AI-GENERATED IMAGES:
        # AI/neural images (Midjourney, DALL-E, Stable Diffusion) and high-quality DSLR photos
        # naturally produce near-maximum LSB entropy (~0.999) and near-50:50 bit ratios because
        # their pixel values are computed, not captured with sensor noise. This is NOT steganography.
        # RS Steganalysis and Regional Variation are the only reliable primary signals —
        # entropy and chi-square alone are NOT sufficient to flag an image.

        # 1. RS Steganalysis Payload Estimation (Fridrich et al.) — primary signal, highest weight
        if rs_payload_ratio >= 0.20:
            score += 50
            reasons.append(f"RS Steganalysis: significant hidden payload detected (~{round(rs_payload_ratio*100, 1)}% of capacity, est. {round(rs_estimated_kb, 1)} KB)")
        elif rs_payload_ratio >= 0.08:
            score += 30
            reasons.append(f"RS Steganalysis: moderate hidden payload detected (~{round(rs_payload_ratio*100, 1)}% of capacity, est. {round(rs_estimated_kb, 1)} KB)")
        elif rs_payload_ratio >= 0.03:
            score += 12
            reasons.append(f"RS Steganalysis: minor LSB payload detected (~{round(rs_payload_ratio*100, 1)}% of capacity)")

        # 2. Regional LSB Variation (Sequential Embedding Pattern) — primary corroborating signal
        # Natural photos and AI images have smooth region transitions; embedding creates sharp jumps
        if region_difference > 0.018:
            score += 35
            reasons.append(f"Strong sequential embedding pattern detected (regional LSB shift: {round(region_difference, 4)})")
        elif region_difference > 0.010:
            score += 18
            reasons.append(f"Moderate regional LSB variation detected ({round(region_difference, 4)})")

        # 3. Chi-Square PoV — only meaningful when combined with RS or Regional signal
        # On its own, chi-square is unreliable for AI images; award points only if RS also fired
        if chi_p < 0.001 and rs_payload_ratio >= 0.03:
            score += 20
            reasons.append(f"Chi-square PoV confirms statistical LSB alteration (p < 0.001)")
        elif chi_p < 0.01 and rs_payload_ratio >= 0.08:
            score += 10
            reasons.append(f"Chi-square PoV supports statistical LSB alteration (p = {round(chi_p, 4)})")

        # 4. High LSB Entropy — only scored when RS also indicates payload
        # AI and DSLR images naturally reach entropy ~0.999; this signal alone means nothing
        if entropy_avg >= 0.9995 and rs_payload_ratio >= 0.05:
            score += 15
            reasons.append(f"Near-maximum LSB entropy ({round(entropy_avg, 4)}) consistent with encrypted payload")

        # 5. Artificial 50:50 forced distribution — only meaningful with RS corroboration
        if balance_shift < 0.003 and rs_payload_ratio >= 0.08:
            score += 10
            reasons.append(f"LSB bit ratio near-perfect 50:50 ({round(balance_ratio*100, 2)}%), consistent with encrypted embedding")

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
