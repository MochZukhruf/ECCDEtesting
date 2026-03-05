# -*- coding: utf-8 -*-
"""
Block: representasi blok blockchain dengan Merkle tree.
"""

import hashlib
import time
from typing import List, Optional

from blockchain_sim.transaction import Transaction


class Block:
    """
    Struktur blok blockchain:
    - index: nomor urut blok
    - previous_hash: hash blok sebelumnya
    - timestamp: waktu pembuatan blok
    - merkle_root: akar Merkle tree dari transaksi
    - transactions: daftar transaksi dalam blok
    - nonce: nilai nonce (untuk simulasi mining)
    - hash: hash blok ini
    """

    def __init__(
        self,
        index: int,
        previous_hash: str,
        transactions: List[Transaction],
        timestamp: Optional[float] = None,
        nonce: int = 0,
    ):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp or time.time()
        self.transactions = transactions
        self.nonce = nonce
        self.merkle_root = self.compute_merkle_root()
        self.hash = self.compute_hash()

    @staticmethod
    def compute_merkle_root_from_hashes(hashes: List[str]) -> str:
        """
        Hitung Merkle root dari list hash transaksi.
        Binary Merkle tree: pasangkan hash, hash gabungannya,
        ulangi sampai tinggal satu.
        """
        if not hashes:
            return hashlib.sha256(b"empty").hexdigest()
        if len(hashes) == 1:
            return hashes[0]

        # Jika ganjil, duplikasi hash terakhir
        current_level = list(hashes)
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                combined = hashlib.sha256(
                    (left + right).encode("utf-8")
                ).hexdigest()
                next_level.append(combined)
            current_level = next_level

        return current_level[0]

    def compute_merkle_root(self) -> str:
        """Hitung Merkle root dari transaksi dalam blok."""
        tx_hashes = [tx.to_hash() for tx in self.transactions]
        return self.compute_merkle_root_from_hashes(tx_hashes)

    def compute_hash(self) -> str:
        """Hitung hash blok (SHA-256)."""
        block_data = (
            f"{self.index}"
            f"{self.previous_hash}"
            f"{self.timestamp}"
            f"{self.merkle_root}"
            f"{self.nonce}"
        )
        return hashlib.sha256(block_data.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        """Konversi blok ke dictionary."""
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce,
            "hash": self.hash,
            "num_transactions": len(self.transactions),
        }

    def verify_transactions(self) -> bool:
        """Verifikasi semua signature transaksi dalam blok."""
        return all(tx.verify() for tx in self.transactions)

    def __repr__(self) -> str:
        return (
            f"Block(index={self.index}, "
            f"hash={self.hash[:16]}..., "
            f"txs={len(self.transactions)})"
        )
