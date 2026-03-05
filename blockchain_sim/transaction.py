# -*- coding: utf-8 -*-
"""
Transaction: representasi transaksi blockchain dengan ECC signing/verification.
"""

import hashlib
import time
from typing import Optional


class Transaction:
    """
    Struktur transaksi blockchain:
    - sender: alamat pengirim (hex public key)
    - receiver: alamat penerima (hex public key)
    - amount: jumlah transfer
    - timestamp: waktu transaksi
    - signature: tanda tangan ECDSA (bytes)
    - public_key: public key pengirim (VerifyingKey)
    """

    def __init__(
        self,
        sender: str,
        receiver: str,
        amount: float,
        timestamp: Optional[float] = None,
    ):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = timestamp or time.time()
        self.signature: Optional[bytes] = None
        self.public_key = None  # VerifyingKey (set saat sign)

    def to_dict(self) -> dict:
        """Konversi transaksi ke dictionary (tanpa signature)."""
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "timestamp": self.timestamp,
        }

    def to_hash(self) -> str:
        """SHA-256 hash dari data transaksi (tanpa signature)."""
        data = f"{self.sender}{self.receiver}{self.amount}{self.timestamp}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def to_bytes(self) -> bytes:
        """Data transaksi sebagai bytes (untuk signing)."""
        data = f"{self.sender}{self.receiver}{self.amount}{self.timestamp}"
        return data.encode("utf-8")

    def sign(self, signing_key) -> None:
        """
        Tanda tangani transaksi dengan private key (SigningKey).
        Menyimpan signature dan public_key pada objek ini.
        """
        from ecc_engine import sign_data
        self.signature = sign_data(signing_key, self.to_bytes())
        self.public_key = signing_key.get_verifying_key()

    def verify(self) -> bool:
        """
        Verifikasi tanda tangan transaksi.
        Returns True jika valid, False jika tidak.
        """
        if self.signature is None or self.public_key is None:
            return False
        from ecc_engine import verify_signature
        return verify_signature(self.public_key, self.to_bytes(), self.signature)

    def __repr__(self) -> str:
        return (
            f"Transaction(sender={self.sender[:8]}..., "
            f"receiver={self.receiver[:8]}..., "
            f"amount={self.amount}, "
            f"signed={self.signature is not None})"
        )
