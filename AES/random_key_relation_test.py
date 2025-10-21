# Search for triples (i,j,k) where one of 8 relations equals a constant (same constant across all trials).
# Relations: various combinations of S() applied to a,b,c and XORed; we accept a triple if for all trials
# the relation value is the same constant (byte 0..255). We'll report that constant.
#
# Defaults: R=10 (rounds 0..10 => 176 bytes), trials=10 random master keys.
# Outputs: printed list in k_r[i] format with relation and constant, a DataFrame displayed, and master keys used.
from typing import List, Tuple
import secrets
import pandas as pd
from itertools import combinations
import time

# AES S-box
SBOX = [
    0x63,
    0x7C,
    0x77,
    0x7B,
    0xF2,
    0x6B,
    0x6F,
    0xC5,
    0x30,
    0x01,
    0x67,
    0x2B,
    0xFE,
    0xD7,
    0xAB,
    0x76,
    0xCA,
    0x82,
    0xC9,
    0x7D,
    0xFA,
    0x59,
    0x47,
    0xF0,
    0xAD,
    0xD4,
    0xA2,
    0xAF,
    0x9C,
    0xA4,
    0x72,
    0xC0,
    0xB7,
    0xFD,
    0x93,
    0x26,
    0x36,
    0x3F,
    0xF7,
    0xCC,
    0x34,
    0xA5,
    0xE5,
    0xF1,
    0x71,
    0xD8,
    0x31,
    0x15,
    0x04,
    0xC7,
    0x23,
    0xC3,
    0x18,
    0x96,
    0x05,
    0x9A,
    0x07,
    0x12,
    0x80,
    0xE2,
    0xEB,
    0x27,
    0xB2,
    0x75,
    0x09,
    0x83,
    0x2C,
    0x1A,
    0x1B,
    0x6E,
    0x5A,
    0xA0,
    0x52,
    0x3B,
    0xD6,
    0xB3,
    0x29,
    0xE3,
    0x2F,
    0x84,
    0x53,
    0xD1,
    0x00,
    0xED,
    0x20,
    0xFC,
    0xB1,
    0x5B,
    0x6A,
    0xCB,
    0xBE,
    0x39,
    0x4A,
    0x4C,
    0x58,
    0xCF,
    0xD0,
    0xEF,
    0xAA,
    0xFB,
    0x43,
    0x4D,
    0x33,
    0x85,
    0x45,
    0xF9,
    0x02,
    0x7F,
    0x50,
    0x3C,
    0x9F,
    0xA8,
    0x51,
    0xA3,
    0x40,
    0x8F,
    0x92,
    0x9D,
    0x38,
    0xF5,
    0xBC,
    0xB6,
    0xDA,
    0x21,
    0x10,
    0xFF,
    0xF3,
    0xD2,
    0xCD,
    0x0C,
    0x13,
    0xEC,
    0x5F,
    0x97,
    0x44,
    0x17,
    0xC4,
    0xA7,
    0x7E,
    0x3D,
    0x64,
    0x5D,
    0x19,
    0x73,
    0x60,
    0x81,
    0x4F,
    0xDC,
    0x22,
    0x2A,
    0x90,
    0x88,
    0x46,
    0xEE,
    0xB8,
    0x14,
    0xDE,
    0x5E,
    0x0B,
    0xDB,
    0xE0,
    0x32,
    0x3A,
    0x0A,
    0x49,
    0x06,
    0x24,
    0x5C,
    0xC2,
    0xD3,
    0xAC,
    0x62,
    0x91,
    0x95,
    0xE4,
    0x79,
    0xE7,
    0xC8,
    0x37,
    0x6D,
    0x8D,
    0xD5,
    0x4E,
    0xA9,
    0x6C,
    0x56,
    0xF4,
    0xEA,
    0x65,
    0x7A,
    0xAE,
    0x08,
    0xBA,
    0x78,
    0x25,
    0x2E,
    0x1C,
    0xA6,
    0xB4,
    0xC6,
    0xE8,
    0xDD,
    0x74,
    0x1F,
    0x4B,
    0xBD,
    0x8B,
    0x8A,
    0x70,
    0x3E,
    0xB5,
    0x66,
    0x48,
    0x03,
    0xF6,
    0x0E,
    0x61,
    0x35,
    0x57,
    0xB9,
    0x86,
    0xC1,
    0x1D,
    0x9E,
    0xE1,
    0xF8,
    0x98,
    0x11,
    0x69,
    0xD9,
    0x8E,
    0x94,
    0x9B,
    0x1E,
    0x87,
    0xE9,
    0xCE,
    0x55,
    0x28,
    0xDF,
    0x8C,
    0xA1,
    0x89,
    0x0D,
    0xBF,
    0xE6,
    0x42,
    0x68,
    0x41,
    0x99,
    0x2D,
    0x0F,
    0xB0,
    0x54,
    0xBB,
    0x16,
]

RCON = [
    0x00000000,
    0x01000000,
    0x02000000,
    0x04000000,
    0x08000000,
    0x10000000,
    0x20000000,
    0x40000000,
    0x80000000,
    0x1B000000,
    0x36000000,
]


def bytes_to_word(b: bytes) -> int:
    return (b[0] << 24) | (b[1] << 16) | (b[2] << 8) | b[3]


def word_to_bytes(w: int) -> bytes:
    return bytes([(w >> 24) & 0xFF, (w >> 16) & 0xFF, (w >> 8) & 0xFF, w & 0xFF])


def sub_word(w: int) -> int:
    b = word_to_bytes(w)
    return bytes_to_word(bytes([SBOX[b[0]], SBOX[b[1]], SBOX[b[2]], SBOX[b[3]]]))


def rot_word(w: int) -> int:
    b = word_to_bytes(w)
    return bytes_to_word(bytes([b[1], b[2], b[3], b[0]]))


def expand_key_aes128(master_key: bytes) -> List[int]:
    if not isinstance(master_key, (bytes, bytearray)) or len(master_key) != 16:
        raise ValueError("master_key must be 16 bytes")
    Nk = 4
    Nb = 4
    Nr = 10
    w = [0] * (Nb * (Nr + 1))
    for i in range(Nk):
        w[i] = bytes_to_word(master_key[4 * i : 4 * i + 4])
    for i in range(Nk, Nb * (Nr + 1)):
        temp = w[i - 1]
        if i % Nk == 0:
            temp = sub_word(rot_word(temp)) ^ RCON[i // Nk]
        w[i] = w[i - Nk] ^ temp
    return w


def round_keys_bytes_from_words(words: List[int], R: int) -> bytes:
    if R < 0:
        raise ValueError("R must be >= 0")
    if R > 10:
        R = 10
    parts = [word_to_bytes(words[r * 4 + c]) for r in range(0, R + 1) for c in range(4)]
    return b"".join(parts)


def find_triple_constant_relations(R: int = 10, trials: int = 10):
    if R < 0:
        raise ValueError("R must be >= 0")
    if R > 10:
        R = 10
    n_bytes = 16 * (R + 1)
    # generate expanded bytes for each trial
    expanded_list = []
    master_keys = []
    for t in range(trials):
        mk = secrets.token_bytes(16)
        master_keys.append(mk)
        words = expand_key_aes128(mk)
        expanded_list.append(round_keys_bytes_from_words(words, R))
    matches = []
    total_checked = 0
    t0 = time.time()
    # iterate triples
    for i, j, k in combinations(range(n_bytes), 3):
        total_checked += 1
        # compute value for each trial for each relation, check if all equal
        # relation 1: a ^ b ^ c == const
        vals = [
            (expanded_list[t][i] ^ expanded_list[t][j] ^ expanded_list[t][k])
            for t in range(trials)
        ]
        if all(v == vals[0] for v in vals):
            matches.append(
                {
                    "pos_i": i,
                    "pos_j": j,
                    "pos_k": k,
                    "relation": "a^b^c",
                    "constant": vals[0],
                }
            )
        # relation 2: S(a)^b^c == const
        vals = [
            (SBOX[expanded_list[t][i]] ^ expanded_list[t][j] ^ expanded_list[t][k])
            for t in range(trials)
        ]
        if all(v == vals[0] for v in vals):
            matches.append(
                {
                    "pos_i": i,
                    "pos_j": j,
                    "pos_k": k,
                    "relation": "S(a)^b^c",
                    "constant": vals[0],
                }
            )
        # relation 3: a^S(b)^c
        vals = [
            (expanded_list[t][i] ^ SBOX[expanded_list[t][j]] ^ expanded_list[t][k])
            for t in range(trials)
        ]
        if all(v == vals[0] for v in vals):
            matches.append(
                {
                    "pos_i": i,
                    "pos_j": j,
                    "pos_k": k,
                    "relation": "a^S(b)^c",
                    "constant": vals[0],
                }
            )
        # relation 4: a^b^S(c)
        vals = [
            (expanded_list[t][i] ^ expanded_list[t][j] ^ SBOX[expanded_list[t][k]])
            for t in range(trials)
        ]
        if all(v == vals[0] for v in vals):
            matches.append(
                {
                    "pos_i": i,
                    "pos_j": j,
                    "pos_k": k,
                    "relation": "a^b^S(c)",
                    "constant": vals[0],
                }
            )
        # relation 5: S(a^b)^c
        vals = [
            (SBOX[expanded_list[t][i] ^ expanded_list[t][j]] ^ expanded_list[t][k])
            for t in range(trials)
        ]
        if all(v == vals[0] for v in vals):
            matches.append(
                {
                    "pos_i": i,
                    "pos_j": j,
                    "pos_k": k,
                    "relation": "S(a^b)^c",
                    "constant": vals[0],
                }
            )
        # relation 6: S(a^c)^b
        vals = [
            (SBOX[expanded_list[t][i] ^ expanded_list[t][k]] ^ expanded_list[t][j])
            for t in range(trials)
        ]
        if all(v == vals[0] for v in vals):
            matches.append(
                {
                    "pos_i": i,
                    "pos_j": j,
                    "pos_k": k,
                    "relation": "S(a^c)^b",
                    "constant": vals[0],
                }
            )
        # relation 7: a^S(b^c)
        vals = [
            (expanded_list[t][i] ^ SBOX[expanded_list[t][j] ^ expanded_list[t][k]])
            for t in range(trials)
        ]
        if all(v == vals[0] for v in vals):
            matches.append(
                {
                    "pos_i": i,
                    "pos_j": j,
                    "pos_k": k,
                    "relation": "a^S(b^c)",
                    "constant": vals[0],
                }
            )
        # relation 8: S(a)^S(b)^c
        vals = [
            (
                SBOX[expanded_list[t][i]]
                ^ SBOX[expanded_list[t][j]]
                ^ expanded_list[t][k]
            )
            for t in range(trials)
        ]
        if all(v == vals[0] for v in vals):
            matches.append(
                {
                    "pos_i": i,
                    "pos_j": j,
                    "pos_k": k,
                    "relation": "S(a)^S(b)^c",
                    "constant": vals[0],
                }
            )
        # relation 9: a^S(b)^S(c)
        vals = [
            (
                expanded_list[t][i]
                ^ SBOX[expanded_list[t][j]]
                ^ SBOX[expanded_list[t][k]]
            )
            for t in range(trials)
        ]
        if all(v == vals[0] for v in vals):
            matches.append(
                {
                    "pos_i": i,
                    "pos_j": j,
                    "pos_k": k,
                    "relation": "a^S(b)^S(c)",
                    "constant": vals[0],
                }
            )
        # relation 10: S(a)^b^S(c)
        vals = [
            (
                SBOX[expanded_list[t][i]]
                ^ expanded_list[t][j]
                ^ SBOX[expanded_list[t][k]]
            )
            for t in range(trials)
        ]
        if all(v == vals[0] for v in vals):
            matches.append(
                {
                    "pos_i": i,
                    "pos_j": j,
                    "pos_k": k,
                    "relation": "S(a)^b^S(c)",
                    "constant": vals[0],
                }
            )
        # relation 11: S(S(a)^b)^c
        vals = [
            (
                SBOX[SBOX[expanded_list[t][i]] ^ expanded_list[t][j]]
                ^ expanded_list[t][k]
            )
            for t in range(trials)
        ]
        if all(v == vals[0] for v in vals):
            matches.append(
                {
                    "pos_i": i,
                    "pos_j": j,
                    "pos_k": k,
                    "relation": "S(S(a)^b)^c",
                    "constant": vals[0],
                }
            )
        # relation 12: S(a^S(b))^c
        vals = [
            (
                SBOX[expanded_list[t][i] ^ SBOX[expanded_list[t][j]]]
                ^ expanded_list[t][k]
            )
            for t in range(trials)
        ]
        if all(v == vals[0] for v in vals):
            matches.append(
                {
                    "pos_i": i,
                    "pos_j": j,
                    "pos_k": k,
                    "relation": "S(a^S(b))^c",
                    "constant": vals[0],
                }
            )
        # relation 13: S(S(a)^c)^b
        vals = [
            (
                SBOX[SBOX[expanded_list[t][i]] ^ expanded_list[t][k]]
                ^ expanded_list[t][j]
            )
            for t in range(trials)
        ]
        if all(v == vals[0] for v in vals):
            matches.append(
                {
                    "pos_i": i,
                    "pos_j": j,
                    "pos_k": k,
                    "relation": "S(S(a)^c)^b",
                    "constant": vals[0],
                }
            )
        # relation 14: S(a^S(c))^b
        vals = [
            (
                SBOX[expanded_list[t][i] ^ SBOX[expanded_list[t][k]]]
                ^ expanded_list[t][j]
            )
            for t in range(trials)
        ]
        if all(v == vals[0] for v in vals):
            matches.append(
                {
                    "pos_i": i,
                    "pos_j": j,
                    "pos_k": k,
                    "relation": "S(a^S(c))^b",
                    "constant": vals[0],
                }
            )
        # relation 15: a^S(S(b)^c)
        vals = [
            (
                expanded_list[t][i]
                ^ SBOX[SBOX[expanded_list[t][j]] ^ expanded_list[t][k]]
            )
            for t in range(trials)
        ]
        if all(v == vals[0] for v in vals):
            matches.append(
                {
                    "pos_i": i,
                    "pos_j": j,
                    "pos_k": k,
                    "relation": "a^S(S(b)^c)",
                    "constant": vals[0],
                }
            )
        # relation 16: a^S(b^S(c))
        vals = [
            (
                expanded_list[t][i]
                ^ SBOX[expanded_list[t][j] ^ SBOX[expanded_list[t][k]]]
            )
            for t in range(trials)
        ]
        if all(v == vals[0] for v in vals):
            matches.append(
                {
                    "pos_i": i,
                    "pos_j": j,
                    "pos_k": k,
                    "relation": "a^S(b^S(c))",
                    "constant": vals[0],
                }
            )
        # relation 17: S(a)^S(b)^S(c)
        vals = [
            (
                SBOX[expanded_list[t][i]]
                ^ SBOX[expanded_list[t][j]]
                ^ SBOX[expanded_list[t][k]]
            )
            for t in range(trials)
        ]
        if all(v == vals[0] for v in vals):
            matches.append(
                {
                    "pos_i": i,
                    "pos_j": j,
                    "pos_k": k,
                    "relation": "S(a)^S(b)^S(c)",
                    "constant": vals[0],
                }
            )
        if total_checked % 100000 == 0:
            elapsed = time.time() - t0
            print(
                f"Checked {total_checked} triples, elapsed {elapsed:.1f}s, matches so far: {len(matches)}"
            )
    # format positions into k_r[i] notation for printing
    lines = []
    rows = []
    for rec in matches:
        i = rec["pos_i"]
        j = rec["pos_j"]
        k = rec["pos_k"]
        r_i, idx_i = divmod(i, 16)
        r_j, idx_j = divmod(j, 16)
        r_k, idx_k = divmod(k, 16)
        const_hex = hex(rec["constant"])
        lines.append(
            f"k_{r_i}[{idx_i}], k_{r_j}[{idx_j}], k_{r_k}[{idx_k}]    relation: {rec['relation']} == {const_hex}"
        )
        rows.append(
            {
                "r_i": r_i,
                "idx_i": idx_i,
                "r_j": r_j,
                "idx_j": idx_j,
                "r_k": r_k,
                "idx_k": idx_k,
                "relation": rec["relation"],
                "constant_hex": const_hex,
            }
        )
    print(f"Found {len(lines)} matching triples. Listing them:\n")
    for line in lines:
        print(line)


if __name__ == "__main__":
    # Run with R=10, trials=10
    find_triple_constant_relations(R=10, trials=10)
