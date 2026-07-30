import io
import base64
import numpy as np
from PIL import Image
from scipy.stats import chisquare
from core.security import MAGIC_STGO, MAGIC_PWS1

def probe_signature(flat: np.ndarray):
    # Check for known StegoScan payload headers (STGO / PWS1) in the initial bits
    signature_detected = False
    sig_type = ""
    if flat.size >= 32:
        len_bits = ''.join(str(flat[i] & 1) for i in range(32))
        try:
            p_len = int(len_bits, 2)
            if 0 < p_len <= flat.size - 32 and p_len % 8 == 0:
                p_bits = ''.join(str(flat[32 + i] & 1) for i in range(p_len))
                pb = bytearray()
                for b_i in range(0, len(p_bits), 8):
                    pb.append(int(p_bits[b_i:b_i+8], 2))
                pb = bytes(pb)
                if pb.startswith(MAGIC_STGO):
                    signature_detected = True
                    sig_type = "Unencrypted StegoScan Payload"
                elif pb.startswith(MAGIC_PWS1):
                    signature_detected = True
                    sig_type = "Password-Protected StegoScan Payload"
        except Exception:
            pass
    return signature_detected, sig_type

def chi_pair_analysis(flat: np.ndarray):
    # Chi-Square Pairs of Values (PoV) analysis for LSB embedding detection
    counts = np.bincount(flat, minlength=256).astype(float)
    obs, exp = [], []
    for i in range(0, 256, 2):
        total = counts[i] + counts[i + 1]
        if total > 0:
            obs.extend([counts[i], counts[i + 1]])
            exp.extend([total / 2, total / 2])
    obs = np.array(obs)
    exp = np.array(exp)
    if len(obs) == 0:
        return 0.0, 1.0
    stat, p = chisquare(obs, exp)
    return float(stat), float(p)

def lsb_balance(channel: np.ndarray):
    # Evaluate 0/1 bit ratio in LSB plane (random data approaches ~0.50)
    bits = channel & 1
    ones = np.sum(bits)
    total = bits.size
    ratio = ones / total
    return {"ratio": float(ratio), "ones": int(ones), "zeros": int(total - ones)}

def lsb_entropy(channel: np.ndarray):
    # Shannon entropy of LSB layer (max entropy = 1.0 bit/pixel)
    bits = (channel & 1).flatten()
    p1 = np.mean(bits)
    p0 = 1 - p1
    entropy = 0.0
    if p0 > 0:
        entropy -= p0 * np.log2(p0)
    if p1 > 0:
        entropy -= p1 * np.log2(p1)
    return float(entropy)

def region_lsb_statistics(channel: np.ndarray, parts=10):
    bits = (channel & 1).flatten()
    section = len(bits) // parts
    ratios = []
    for i in range(parts):
        start = i * section
        end = len(bits) if i == parts - 1 else (i + 1) * section
        region = bits[start:end]
        ratios.append(float(np.mean(region)))
    return ratios

def cal_region_difference(channel: np.ndarray):
    # Measures localized variance across 20 spatial image slices
    ratios = region_lsb_statistics(channel, parts=20)
    diffs = [abs(ratios[i] - ratios[i + 1]) for i in range(len(ratios) - 1)]
    avg_diff = float(np.mean(diffs)) if diffs else 0.0
    return ratios, avg_diff

def rs_steganalysis(channel: np.ndarray):
    # RS Steganalysis (Fridrich et al.) - dual quadratic curve solver for LSB estimate
    flat = channel.flatten().astype(np.int32)
    n = len(flat)
    if n < 100:
        return 0.0, 0.0

    num_groups = n // 4
    groups = flat[:num_groups * 4].reshape(-1, 4)

    def f(g):
        return np.abs(g[:, 1] - g[:, 0]) + np.abs(g[:, 2] - g[:, 1]) + np.abs(g[:, 3] - g[:, 2])

    def F1(x):
        return np.where(x % 2 == 0, x + 1, x - 1)

    def F_neg1(x):
        res = np.where(x % 2 == 1, x + 1, x - 1)
        return np.clip(res, 0, 255)

    def apply_mask(g, mask, fn_pos, fn_neg):
        res = g.copy()
        for i in range(4):
            if mask[i] == 1:
                res[:, i] = fn_pos(g[:, i])
            elif mask[i] == -1:
                res[:, i] = fn_neg(g[:, i])
        return res

    mask = [0, 1, 1, 0]
    neg_mask = [0, -1, -1, 0]

    f_orig = f(groups)

    g_M = apply_mask(groups, mask, F1, F_neg1)
    f_M = f(g_M)
    g_negM = apply_mask(groups, neg_mask, F1, F_neg1)
    f_negM = f(g_negM)

    R_M = np.mean(f_M > f_orig)
    S_M = np.mean(f_M < f_orig)
    R_negM = np.mean(f_negM > f_orig)
    S_negM = np.mean(f_negM < f_orig)

    groups_inv = F1(groups)
    f_orig_inv = f(groups_inv)

    g_M_inv = apply_mask(groups_inv, mask, F1, F_neg1)
    f_M_inv = f(g_M_inv)
    g_negM_inv = apply_mask(groups_inv, neg_mask, F1, F_neg1)
    f_negM_inv = f(g_negM_inv)

    R_M_inv = np.mean(f_M_inv > f_orig_inv)
    S_M_inv = np.mean(f_M_inv < f_orig_inv)
    R_negM_inv = np.mean(f_negM_inv > f_orig_inv)
    S_negM_inv = np.mean(f_negM_inv < f_orig_inv)

    d0 = R_M - S_M
    d1 = R_M_inv - S_M_inv
    d0_neg = R_negM - S_negM
    d1_neg = R_negM_inv - S_negM_inv

    a = 2 * (d1 + d0)
    b = (d0_neg - d1_neg) - d1 - 3 * d0
    c = d0 - d0_neg

    if abs(a) < 1e-10:
        p = 0.0 if abs(b) < 1e-10 else -c / b
    else:
        discriminant = b * b - 4 * a * c
        if discriminant < 0:
            p = 0.0
        else:
            root1 = (-b + np.sqrt(discriminant)) / (2 * a)
            root2 = (-b - np.sqrt(discriminant)) / (2 * a)
            valid_roots = [r for r in (root1, root2) if -0.1 <= r <= 0.6]
            p = min(valid_roots, key=abs) if valid_roots else 0.0

    p = float(np.clip(p, 0.0, 0.5))
    payload_ratio = float(np.clip(2 * p / (1 - 2 * p + 1e-6) if p < 0.45 else 1.0, 0.0, 1.0))
    return p, payload_ratio

def lsb_plane_b64(channel: np.ndarray):
    # Isolates bitplane 0 (LSB) into a visual B&W mask
    img = Image.fromarray(((channel & 1) * 255).astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()

def get_bitplanes_b64(arr: np.ndarray):
    # Generates LSB bitplane visualizations for R, G, B channels and combined RGB
    R, G, B = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    lsb_r = lsb_plane_b64(R)
    lsb_g = lsb_plane_b64(G)
    lsb_b = lsb_plane_b64(B)

    comb = np.zeros_like(arr)
    comb[:,:,0] = (R & 1) * 255
    comb[:,:,1] = (G & 1) * 255
    comb[:,:,2] = (B & 1) * 255
    img_comb = Image.fromarray(comb.astype(np.uint8))
    buf = io.BytesIO()
    img_comb.save(buf, format='PNG')
    lsb_comb = base64.b64encode(buf.getvalue()).decode()

    return {
        "red": lsb_r,
        "green": lsb_g,
        "blue": lsb_b,
        "combined": lsb_comb
    }
