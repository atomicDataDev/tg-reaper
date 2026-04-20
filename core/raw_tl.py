"""RAW TL objects for Login Email.
Registration in tlobjects during import."""

import struct
from telethon.tl import TLObject
from telethon.tl.alltlobjects import tlobjects as _tlobjects


class TLBytes(TLObject):
    @staticmethod
    def _serialize_bytes_to(data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        r = b''
        if len(data) < 254:
            r += bytes([len(data)])
            r += data
            padding = (len(r)) % 4
            if padding:
                r += b'\x00' * (4 - padding)
        else:
            r += b'\xfe'
            r += len(data).to_bytes(3, 'little')
            r += data
            padding = (len(r)) % 4
            if padding:
                r += b'\x00' * (4 - padding)
        return r


class RawEmailVerifyPurposeLoginChange(TLObject):
    CONSTRUCTOR_ID = 0x527d706a
    SUBCLASS_OF_ID = 0x1b2b1930

    def _bytes(self):
        return struct.pack('<I', 0x527d706a)

    @classmethod
    def from_reader(cls, reader):
        return cls()


class RawSendVerifyEmailCode(TLObject):
    CONSTRUCTOR_ID = 0x98e037bb
    SUBCLASS_OF_ID = 0xbf3bac0e

    def __init__(self, purpose, email):
        self.purpose = purpose
        self.email = email

    def _bytes(self):
        return (
            struct.pack('<I', 0x98e037bb)
            + self.purpose._bytes()
            + TLBytes._serialize_bytes_to(self.email)
        )

    @classmethod
    def from_reader(cls, reader):
        return cls(purpose=None, email='')


class RawEmailVerificationCode(TLObject):
    CONSTRUCTOR_ID = 0x922e55a9
    SUBCLASS_OF_ID = 0xb32e2e0a

    def __init__(self, code):
        self.code = code

    def _bytes(self):
        return (
            struct.pack('<I', 0x922e55a9)
            + TLBytes._serialize_bytes_to(self.code)
        )

    @classmethod
    def from_reader(cls, reader):
        return cls(code=reader.tgread_string())


class RawVerifyEmail(TLObject):
    CONSTRUCTOR_ID = 0x32da4f5c
    SUBCLASS_OF_ID = 0xbf3bac0e

    def __init__(self, purpose, verification):
        self.purpose = purpose
        self.verification = verification

    def _bytes(self):
        return (
            struct.pack('<I', 0x32da4f5c)
            + self.purpose._bytes()
            + self.verification._bytes()
        )

    @classmethod
    def from_reader(cls, reader):
        return cls(purpose=None, verification=None)


class RawSentEmailCode(TLObject):
    CONSTRUCTOR_ID = 0x811f854f

    def __init__(self, email_pattern='', length=0):
        self.email_pattern = email_pattern
        self.length = length

    def _bytes(self):
        return b''

    @classmethod
    def from_reader(cls, reader):
        return cls(
            email_pattern=reader.tgread_string(),
            length=reader.read_int(),
        )


class RawEmailVerified(TLObject):
    CONSTRUCTOR_ID = 0x2b96cd1b

    def __init__(self, email=''):
        self.email = email

    def _bytes(self):
        return b''

    @classmethod
    def from_reader(cls, reader):
        return cls(email=reader.tgread_string())


class RawEmailVerifiedLogin(TLObject):
    CONSTRUCTOR_ID = 0xe1bb0d61

    def __init__(self, email='', sent_code=None):
        self.email = email
        self.sent_code = sent_code

    def _bytes(self):
        return b''

    @classmethod
    def from_reader(cls, reader):
        return cls(
            email=reader.tgread_string(),
            sent_code=reader.tgread_object(),
        )


# Registration in the global TL table
for _c in [
    RawSentEmailCode, RawEmailVerified,
    RawEmailVerifiedLogin, RawEmailVerifyPurposeLoginChange,
    RawSendVerifyEmailCode, RawEmailVerificationCode,
    RawVerifyEmail,
]:
    _tlobjects[_c.CONSTRUCTOR_ID] = _c