import os
import json
import hashlib
import hmac

MAGIC_STGO = b'STGO'
MAGIC_PWS1 = b'PWS1'

def derive_key(password: str, salt: bytes, dklen: int = 32) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200000, dklen)

def keystream_from_key(key: bytes, salt: bytes, length: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < length:
        ctr = counter.to_bytes(4, 'big')
        block = hmac.new(key, salt + ctr, hashlib.sha256).digest()
        out.extend(block)
        counter += 1
    return bytes(out[:length])

def encode_payload(payload_obj: dict, password: str = "") -> bytes:
    raw = json.dumps(payload_obj, separators=(",", ":")).encode("utf-8")
    if password:
        salt = os.urandom(16)
        key = derive_key(password, salt)
        mac = hmac.new(key, raw, hashlib.sha256).digest()
        to_encrypt = mac + raw
        ks = keystream_from_key(key, salt, len(to_encrypt))
        ciphertext = bytes(t ^ ks[i] for i, t in enumerate(to_encrypt))
        return MAGIC_PWS1 + salt + ciphertext
    return MAGIC_STGO + raw

def decode_payload(payload: bytes, password: str = "") -> dict:
    if payload.startswith(MAGIC_PWS1):
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
    elif payload.startswith(MAGIC_STGO):
        raw = payload[4:]
    else:
        raw = payload

    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        raise ValueError("INVALID_PAYLOAD")
