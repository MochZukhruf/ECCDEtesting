# -*- coding: utf-8 -*-
"""
Node: simulasi node blockchain yang mengelola chain dan transaction pool.
"""

import time
from typing import List, Optional

from blockchain_sim.transaction import Transaction
from blockchain_sim.block import Block


class Node:
    """
    Simulasi node blockchain:
    - node_id: identifier node
    - blockchain: chain of blocks
    - pending_transactions: transaction pool (belum masuk blok)
    """

    # Jumlah transaksi per blok (bisa diatur)
    TRANSACTIONS_PER_BLOCK = 50

    def __init__(self, node_id: int):
        self.node_id = node_id
        self.blockchain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        # Buat genesis block
        self._create_genesis_block()

    def _create_genesis_block(self) -> None:
        """Buat blok genesis (blok pertama)."""
        genesis = Block(
            index=0,
            previous_hash="0" * 64,
            transactions=[],
            timestamp=time.time(),
            nonce=0,
        )
        self.blockchain.append(genesis)

    def add_transaction(self, tx: Transaction) -> None:
        """Tambahkan transaksi ke pool pending."""
        self.pending_transactions.append(tx)

    def add_transactions(self, txs: List[Transaction]) -> None:
        """Tambahkan banyak transaksi ke pool pending."""
        self.pending_transactions.extend(txs)

    def mine_block(self) -> Optional[Block]:
        """
        Buat blok baru dari pending transactions.
        Ambil hingga TRANSACTIONS_PER_BLOCK transaksi dari pool.
        Returns Block yang baru dibuat, atau None jika pool kosong.
        """
        if not self.pending_transactions:
            return None

        # Ambil transaksi dari pool
        batch = self.pending_transactions[:self.TRANSACTIONS_PER_BLOCK]
        self.pending_transactions = self.pending_transactions[self.TRANSACTIONS_PER_BLOCK:]

        previous_block = self.blockchain[-1]
        new_block = Block(
            index=len(self.blockchain),
            previous_hash=previous_block.hash,
            transactions=batch,
            timestamp=time.time(),
            nonce=0,
        )

        self.blockchain.append(new_block)
        return new_block

    def mine_all_pending(self) -> List[Block]:
        """Mine semua pending transactions menjadi blok-blok."""
        blocks = []
        while self.pending_transactions:
            block = self.mine_block()
            if block:
                blocks.append(block)
        return blocks

    def validate_chain(self) -> bool:
        """
        Validasi seluruh blockchain:
        1. Cek hash blok sesuai dengan compute_hash()
        2. Cek previous_hash sesuai dengan hash blok sebelumnya
        3. Cek semua signature transaksi valid
        """
        for i in range(1, len(self.blockchain)):
            current = self.blockchain[i]
            previous = self.blockchain[i - 1]

            # Cek hash
            if current.hash != current.compute_hash():
                return False

            # Cek previous_hash
            if current.previous_hash != previous.hash:
                return False

            # Cek Merkle root
            if current.merkle_root != current.compute_merkle_root():
                return False

            # Cek signature transaksi
            if not current.verify_transactions():
                return False

        return True

    def get_chain_info(self) -> dict:
        """Info ringkasan chain."""
        total_txs = sum(len(b.transactions) for b in self.blockchain)
        return {
            "node_id": self.node_id,
            "chain_length": len(self.blockchain),
            "total_transactions": total_txs,
            "latest_block_hash": self.blockchain[-1].hash if self.blockchain else None,
        }

    def __repr__(self) -> str:
        return (
            f"Node(id={self.node_id}, "
            f"blocks={len(self.blockchain)}, "
            f"pending={len(self.pending_transactions)})"
        )
