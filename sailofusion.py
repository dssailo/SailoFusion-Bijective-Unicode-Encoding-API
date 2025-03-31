import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

# Precomputed GF(2^8) multiplication table (using prime polynomial x^8 + x^4 + x^3 + x^2 + 1)
GF256_PRIMES = [0x01, 0x03, 0x07, 0x0D, 0x11, 0x25, 0x3B, 0x43, 0x5F, 0x67, 0x89, 0xA1, 0xB3, 0xC5, 0xE7, 0xF1]

def gf256_multiply(a: int, b: int) -> int:
    """Galois Field (2^8) multiplication."""
    product = 0
    for _ in range(8):
        if b & 1:
            product ^= a
        a <<= 1
        if a & 0x100:
            a ^= 0x11D  # Reduction polynomial
        b >>= 1
    return product

def butterfly_shuffle(x: int) -> int:
    """Nonlinear bit permutation."""
    x = ((x & 0xF0) >> 4) | ((x & 0x0F) << 4)
    x = ((x & 0xCC) >> 2) | ((x & 0x33) << 2)
    x = ((x & 0xAA) >> 1) | ((x & 0x55) << 1)
    return x

def sailofusion_encode_byte(x: int, n: int) -> int:
    """Encodes a single byte using SailoFusion."""
    k = 3
    rotated = ((x << k) | (x >> (8 - k))) & 0xFF
    gf_product = gf256_multiply(rotated, GF256_PRIMES[n % 16])
    masked = gf_product ^ (0xFE >> int(n % np.pi))
    return butterfly_shuffle(masked)

def sailofusion_decode_byte(encoded_x: int, n: int) -> int:
    """Decodes a single byte (inverse of SailoFusion)."""
    x = butterfly_shuffle(encoded_x)
    masked = x ^ (0xFE >> int(n % np.pi))
    # Inverse GF(2^8) multiplication requires a precomputed inverse table
    inv_primes = [0x01, 0x8D, 0xF6, 0x6E, 0xEE, 0x4A, 0x9D, 0x5B, 0xE8, 0x4D, 0x97, 0x6B, 0xDC, 0x5D, 0x7F, 0x1F]
    gf_inv = inv_primes[n % 16]
    rotated = gf256_multiply(masked, gf_inv)
    return ((rotated >> k) | (rotated << (8 - k))) & 0xFF

# API Endpoints
@app.route('/encode', methods=['POST'])
def encode():
    data = request.json
    input_bytes = bytes.fromhex(data['hex']) if 'hex' in data else data['text'].encode('utf-8')
    encoded = [sailofusion_encode_byte(b, i) for i, b in enumerate(input_bytes)]
    return jsonify({'encoded_hex': bytes(encoded).hex()})

@app.route('/decode', methods=['POST'])
def decode():
    data = request.json
    encoded_bytes = bytes.fromhex(data['hex'])
    decoded = [sailofusion_decode_byte(b, i) for i, b in enumerate(encoded_bytes)]
    return jsonify({'decoded_text': bytes(decoded).decode('utf-8', errors='replace')})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
