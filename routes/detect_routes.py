import numpy as np
from flask import Blueprint, request, jsonify
from PIL import Image, ImageOps
from core.steganalysis import (
    probe_signature, chi_pair_analysis, lsb_balance, lsb_entropy,
    cal_region_difference, rs_steganalysis, get_bitplanes_b64
)

detect_bp = Blueprint('detect_bp', __name__)

@detect_bp.route('/detect', methods=['POST'])
def detect():
    try:
        file = request.files['image']
        img = Image.open(file)
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

        if region_difference > 0.015:
            score += 40
            reasons.append("Strong regional LSB variation detected")
        elif region_difference > 0.008:
            score += 15
            reasons.append("Moderate regional LSB variation detected")

        balance_shift = abs(balance_ratio - 0.5)
        if balance_shift > 0.025:
            score += 45
            reasons.append("Abnormal LSB distribution detected")
        elif balance_shift > 0.012:
            score += 20
            reasons.append("Minor LSB distribution shift detected")

        if entropy_avg < 0.998:
            score += 30
            reasons.append("Reduced LSB randomness detected")
        elif entropy_avg < 0.999:
            score += 10
            reasons.append("Slight randomness reduction detected")

        if chi_p < 0.05:
            score += 5
            reasons.append("Chi-square supports statistical alteration")

        # Explicit signature match overrides statistical heuristic to 100% confidence
        if signature_detected:
            score = max(score, 100)
            reasons.insert(0, f"Pinpoint Steganography Signature Found: Verified {sig_type}")

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
