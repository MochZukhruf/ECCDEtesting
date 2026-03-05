# -*- coding: utf-8 -*-
"""
ECC Engine: operasi kriptografi pada curve NIST (secp192r1, secp224r1, secp256r1).
Mendukung key generation, transaction signing, dan signature verification.
"""

import hashlib
from typing import List, Optional, Tuple

from ecdsa import NIST192p, NIST224p, NIST256p, SigningKey, VerifyingKey, BadSignatureError
from ecdsa.ellipticcurve import Point

# Mapping nama curve -> class curve (hanya 3 kurva jurnal)
_CURVE_MAP = {
    "secp192r1": NIST192p,
    "secp224r1": NIST224p,
    "secp256r1": NIST256p,
}


def get_curve(curve_name: str):
    """Ambil class curve dari nama (secp192r1, secp224r1, secp256r1)."""
    c = _CURVE_MAP.get(curve_name)
    if c is None:
        raise ValueError(f"Curve tidak didukung: {curve_name}. Gunakan: {list(_CURVE_MAP.keys())}")
    return c


def get_curve_order(curve_name: str) -> int:
    """Order curve (n) untuk validasi scalar."""
    return get_curve(curve_name).order


def get_curve_bit_size(curve_name: str) -> int:
    """Bit size curve (192, 224, 256)."""
    bits = {"secp192r1": 192, "secp224r1": 224, "secp256r1": 256}
    return bits.get(curve_name, 0)


def scalar_multiply(curve_name: str, scalar: int, point: Optional[Point] = None) -> Point:
    """
    Scalar multiplication: scalar * G (atau scalar * point jika point diberikan).
    scalar harus dalam range [1, n-1] dengan n = order curve.
    """
    curve = get_curve(curve_name)
    generator = curve.generator
    order = curve.order
    scalar = int(scalar) % order
    if scalar == 0:
        scalar = 1
    base = point if point is not None else generator
    return scalar * base


def generate_key_pair(curve_name: str, entropy: Optional[bytes] = None) -> Tuple[SigningKey, VerifyingKey]:
    """Generate key pair (private key = scalar) untuk curve."""
    curve = get_curve(curve_name)
    if entropy is not None:
        sk = SigningKey.from_string(entropy[:curve.baselen], curve=curve)
    else:
        sk = SigningKey.generate(curve=curve)
    vk = sk.get_verifying_key()
    return sk, vk


def generate_key_pair_from_scalar(curve_name: str, scalar: int) -> Tuple[SigningKey, VerifyingKey]:
    """
    Generate key pair deterministik dari scalar.
    Scalar dikonversi ke bytes dan dipakai sebagai private key.
    """
    curve = get_curve(curve_name)
    order = curve.order
    scalar = scalar % order
    if scalar == 0:
        scalar = 1
    scalar_bytes = scalar.to_bytes(curve.baselen, byteorder="big")
    sk = SigningKey.from_string(scalar_bytes, curve=curve)
    vk = sk.get_verifying_key()
    return sk, vk


def sign_data(signing_key: SigningKey, data: bytes) -> bytes:
    """
    Sign data menggunakan private key (ECDSA).
    Data di-hash dengan SHA-256 sebelum signing.
    Returns signature bytes.
    """
    return signing_key.sign(data, hashfunc=hashlib.sha256)


def verify_signature(verifying_key: VerifyingKey, data: bytes, signature: bytes) -> bool:
    """
    Verifikasi signature menggunakan public key.
    Returns True jika valid, False jika tidak.
    """
    try:
        verifying_key.verify(signature, data, hashfunc=hashlib.sha256)
        return True
    except BadSignatureError:
        return False


def run_batch_scalar_multiplication(
    curve_name: str,
    scalars: List[int],
    use_parallel: bool = False,
    num_workers: int = 1,
) -> List[Point]:
    """
    Jalankan banyak operasi scalar multiplication (batch).
    Return list titik hasil.
    """
    results: List[Point] = []

    if use_parallel and num_workers > 1:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        import multiprocessing
        workers = min(num_workers, len(scalars), multiprocessing.cpu_count() or 1)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(_worker_scalar_multiply, curve_name, s) for s in scalars]
            for f in as_completed(futures):
                try:
                    results.append(f.result())
                except Exception as e:
                    raise RuntimeError(f"ECC batch error: {e}") from e
    else:
        for s in scalars:
            results.append(_worker_scalar_multiply(curve_name, s))

    return results


def _worker_scalar_multiply(curve_name: str, scalar: int) -> Point:
    """Worker untuk batch scalar multiplication."""
    curve = get_curve(curve_name)
    order = curve.order
    k = int(scalar) % order
    if k == 0:
        k = 1
    return k * curve.generator
