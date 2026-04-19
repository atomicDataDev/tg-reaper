"""
MTProto v2 key/iv calculation
"""

import hashlib


def calc_key_iv_v2(
    auth_key: bytes, msg_key: bytes, is_outgoing: bool
) -> tuple[bytes, bytes]:
    # Calculates AES key & IV for MTProto v2
    x = 0 if is_outgoing else 8

    sha256_a = hashlib.sha256(msg_key + auth_key[x: x + 36]).digest()
    sha256_b = hashlib.sha256(auth_key[40 + x: 76 + x] + msg_key).digest()

    aes_key = sha256_a[0:8] + sha256_b[8:24] + sha256_a[24:32]
    aes_iv = sha256_b[0:8] + sha256_a[8:24] + sha256_b[24:32]
    return aes_key, aes_iv