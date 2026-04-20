"""AES-IGE encryption/decryption."""


def aes_ige_encrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    """AES-256-IGE encryption."""
    if len(data) % 16 != 0:
        raise ValueError("Data length must be multiple of 16")
    if len(key) != 32:
        raise ValueError("Key must be 32 bytes")
    if len(iv) != 32:
        raise ValueError("IV must be 32 bytes")

    from cryptography.hazmat.primitives.ciphers import (
        Cipher, algorithms, modes as cmodes,
    )
    from cryptography.hazmat.backends import default_backend

    aes_ecb = Cipher(
        algorithms.AES(key), cmodes.ECB(), backend=default_backend()
    )
    enc = aes_ecb.encryptor()

    c_prev = bytearray(iv[0:16])
    p_prev = bytearray(iv[16:32])

    result = bytearray()
    for i in range(0, len(data), 16):
        p_i = data[i : i + 16]
        xored_in = bytes(a ^ b for a, b in zip(p_i, c_prev))
        aes_out = enc.update(xored_in)
        c_i = bytes(a ^ b for a, b in zip(aes_out, p_prev))
        result.extend(c_i)
        c_prev = bytearray(c_i)
        p_prev = bytearray(p_i)

    return bytes(result)


def aes_ige_decrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    """AES-256-IGE decryption."""
    if len(data) % 16 != 0:
        raise ValueError("Data length must be multiple of 16")
    if len(key) != 32:
        raise ValueError("Key must be 32 bytes")
    if len(iv) != 32:
        raise ValueError("IV must be 32 bytes")

    from cryptography.hazmat.primitives.ciphers import (
        Cipher, algorithms, modes as cmodes,
    )
    from cryptography.hazmat.backends import default_backend

    aes_ecb = Cipher(
        algorithms.AES(key), cmodes.ECB(), backend=default_backend()
    )
    dec = aes_ecb.decryptor()

    c_prev = bytearray(iv[0:16])
    p_prev = bytearray(iv[16:32])

    result = bytearray()
    for i in range(0, len(data), 16):
        c_i = data[i : i + 16]
        xored_in = bytes(a ^ b for a, b in zip(c_i, p_prev))
        aes_out = dec.update(xored_in)
        p_i = bytes(a ^ b for a, b in zip(aes_out, c_prev))
        result.extend(p_i)
        c_prev = bytearray(c_i)
        p_prev = bytearray(p_i)

    return bytes(result)