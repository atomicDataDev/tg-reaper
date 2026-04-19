"""
Secret chat manager: creation, encryption, TTL, typing.
"""

import os
import random
import struct
import hashlib
import asyncio

from telethon import TelegramClient, events
from telethon.tl.functions.messages import (
    GetDhConfigRequest,
    RequestEncryptionRequest,
    SendEncryptedServiceRequest,
    DiscardEncryptionRequest,
    SetEncryptedTypingRequest,
)
from telethon.tl.types import (
    InputUser,
    InputEncryptedChat,
    EncryptedChat,
    EncryptedChatDiscarded,
    UpdateEncryption,
)

from crypto.aes_ige import aes_ige_encrypt
from crypto.mtproto import calc_key_iv_v2
from ui import print_error, print_success, print_warning, print_dim


class SecretChatManager:
    LAYER = 73

    def __init__(self, client: TelegramClient):
        self.client = client
        self._dh_config = None
        self.chats = {}

    # ----------------------------------------------------------
    # DH configuraion
    # ----------------------------------------------------------

    async def _get_dh_config(self):
        # Gets Diffie-Hellman configuration from server
        if self._dh_config is None:
            cfg = await self.client(
                GetDhConfigRequest(version=0, random_length=256)
            )
            if not hasattr(cfg, "p") or not cfg.p:
                raise RuntimeError(
                    "Не удалось получить DH конфигурацию "
                    "(DhConfigNotModified без кеша)"
                )
            self._dh_config = cfg
        return self._dh_config

    # ----------------------------------------------------------
    # Secret chat creation
    # ----------------------------------------------------------

    async def create(self, target_user) -> dict | None:
        """
        Makes a secret chat request
        Returns dict with chat data or None on Error
        """
        try:
            if isinstance(target_user, str):
                user = await self.client.get_entity(target_user)
            else:
                user = target_user

            cfg = await self._get_dh_config()

            p = int.from_bytes(cfg.p, "big")
            g = cfg.g
            a = int.from_bytes(os.urandom(256), "big")
            g_a = pow(g, a, p)
            g_a_len = (p.bit_length() + 7) // 8
            g_a_bytes = g_a.to_bytes(g_a_len, "big")

            result = await self.client(
                RequestEncryptionRequest(
                    user_id=InputUser(
                        user_id=user.id,
                        access_hash=user.access_hash,
                    ),
                    random_id=random.randint(0, 0x7FFFFFFF),
                    g_a=g_a_bytes,
                )
            )

            chat_id = result.id
            data = {
                "id": chat_id,
                "access_hash": getattr(result, "access_hash", 0),
                "a": a,
                "p": p,
                "g": g,
                "state": "waiting",
                "auth_key": None,
                "key_fp": None,
                "out_seq": 0,
                "in_seq": 0,
            }
            self.chats[chat_id] = data
            return data

        except Exception as e:
            print_error(
                f"Ошибка создания секретного чата: "
                f"{type(e).__name__}: {e}"
            )
            return None

    # ----------------------------------------------------------
    # Acception await
    # ----------------------------------------------------------

    async def wait_accept(
        self, chat_id: int, timeout: float = 60.0
    ) -> bool:
        """
        Awaits secret chat acception.
        Returns True/False
        """
        data = self.chats.get(chat_id)
        if not data:
            return False

        done = asyncio.Event()

        async def _handler(update):
            if not isinstance(update, UpdateEncryption):
                return
            enc = update.chat
            if not hasattr(enc, "id") or enc.id != chat_id:
                return

            if isinstance(enc, EncryptedChat):
                # Peer acepted - calculating mutual key
                g_b = int.from_bytes(enc.g_a_or_b, "big")
                auth_key_int = pow(g_b, data["a"], data["p"])
                auth_key = auth_key_int.to_bytes(256, "big")
                fp = struct.unpack(
                    "<q", hashlib.sha1(auth_key).digest()[-8:]
                )[0]

                data["auth_key"] = auth_key
                data["key_fp"] = fp
                data["access_hash"] = enc.access_hash
                data["state"] = "ready"
                done.set()

            elif isinstance(enc, EncryptedChatDiscarded):
                data["state"] = "discarded"
                done.set()

        self.client.add_event_handler(_handler, events.Raw)
        try:
            await asyncio.wait_for(done.wait(), timeout=timeout)
            return data["state"] == "ready"
        except asyncio.TimeoutError:
            return False
        finally:
            self.client.remove_event_handler(_handler)

    # ----------------------------------------------------------
    # TL-serialization
    # ----------------------------------------------------------

    @staticmethod
    def _tl_bytes(raw: bytes) -> bytes:
        """Serializes bytes in TL-format."""
        n = len(raw)
        if n < 254:
            hdr = bytes([n])
        else:
            hdr = b"\xfe" + struct.pack("<I", n)[:3]
        total = hdr + raw
        pad = (4 - len(total) % 4) % 4
        return total + b"\x00" * pad

    def _next_out_seq(self, data: dict, content: bool) -> int:
        # Calculates next out_seq_no
        raw = data["out_seq"]
        seq = raw * 2 + (1 if content else 0)
        if content:
            data["out_seq"] = raw + 1
        return seq

    # ----------------------------------------------------------
    # TL-object building SetTTL
    # ----------------------------------------------------------

    def _build_set_ttl_tl(
        self, data: dict, ttl_seconds: int
    ) -> bytes:
        # Builds TL-serialized object DecryptedMessageActionSetMessageTTL
        # DecryptedMessageActionSetMessageTTL#a1733aec
        action = struct.pack("<I", 0xA1733AEC)
        action += struct.pack("<i", ttl_seconds)

        # DecryptedMessageService#73164160
        svc = struct.pack("<I", 0x73164160)
        svc += struct.pack("<q", random.randint(0, 2**63 - 1))
        svc += action

        # DecryptedMessageLayer#1be31789
        layer = struct.pack("<I", 0x1BE31789)
        layer += self._tl_bytes(os.urandom(15))
        layer += struct.pack("<i", self.LAYER)
        layer += struct.pack("<i", data["in_seq"] * 2)
        layer += struct.pack(
            "<i", self._next_out_seq(data, content=True)
        )
        layer += svc

        return layer

    # ----------------------------------------------------------
    # Encryption
    # ----------------------------------------------------------

    def _encrypt(self, data: dict, plaintext: bytes) -> bytes:
        # Encrypts data for secret chat (MTProto v2)
        auth_key = data["auth_key"]

        # Length prefix
        prefixed = struct.pack("<I", len(plaintext)) + plaintext

        # Padding until divisible by 16
        remainder = len(prefixed) % 16
        pad_needed = (16 - remainder) % 16
        if pad_needed < 12:
            pad_needed += 16
        padded = prefixed + os.urandom(pad_needed)

        # msg_key = sha256(auth_key[88:120] + padded)[8:24]
        msg_key = hashlib.sha256(
            auth_key[88:120] + padded
        ).digest()[8:24]

        # Calculating AES key & IV
        aes_key, aes_iv = calc_key_iv_v2(
            auth_key, msg_key, is_outgoing=True
        )

        # Encrypt AES-IGE
        encrypted = aes_ige_encrypt(padded, aes_key, aes_iv)

        # key_fingerprint (8 bytes) + msg_key (16 bytes) + encrypted
        return (
            struct.pack("<q", data["key_fp"])
            + msg_key
            + encrypted
        )

    # ----------------------------------------------------------
    # TTL setting
    # ----------------------------------------------------------

    async def set_ttl(self, chat_id: int, ttl: int) -> bool:
        #Sets TTL in secret chat and sends service message to targer
        data = self.chats.get(chat_id)
        if not data or data["state"] != "ready":
            print_error(f"Чат {chat_id} не готов для установки TTL")
            return False

        try:
            # Building TL-объект
            tl_blob = self._build_set_ttl_tl(data, ttl)

            # Encrypt
            encrypted = self._encrypt(data, tl_blob)

            # Sending
            peer = InputEncryptedChat(
                chat_id=chat_id,
                access_hash=data["access_hash"],
            )
            await self.client(
                SendEncryptedServiceRequest(
                    peer=peer,
                    random_id=random.randint(0, 2**63 - 1),
                    data=encrypted,
                )
            )

            label = f"{ttl} сек" if ttl > 0 else "выключено"
            print_success(f"TTL установлен: {label}")
            return True

        except Exception as e:
            print_error(
                f"Ошибка установки TTL: "
                f"{type(e).__name__}: {e}"
            )
            return False

    # ----------------------------------------------------------
    # Text input indicator
    # ----------------------------------------------------------

    async def send_typing(self, chat_id: int) -> bool:
        # Makes indicaion of input in chat
        data = self.chats.get(chat_id)
        if not data:
            return False
        try:
            peer = InputEncryptedChat(
                chat_id=chat_id,
                access_hash=data["access_hash"],
            )
            await self.client(
                SetEncryptedTypingRequest(peer=peer, typing=True)
            )
            return True
        except Exception as e:
            print_dim(f"Typing не отправлен: {type(e).__name__}")
            return False

    # ----------------------------------------------------------
    # Secret chat closer
    # ----------------------------------------------------------

    async def discard(self, chat_id: int) -> bool:

        # Closes Secret chat for both sides

        try:
            await self.client(
                DiscardEncryptionRequest(chat_id=chat_id)
            )
            if chat_id in self.chats:
                self.chats[chat_id]["state"] = "discarded"
            return True
        except Exception as e:
            print_error(f"Ошибка закрытия секретного чата: {e}")
            return False