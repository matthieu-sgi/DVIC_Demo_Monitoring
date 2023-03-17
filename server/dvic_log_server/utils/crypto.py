from pathlib import Path
from typing import Union
import random
import string
import base64
import os
from abc import ABC, abstractmethod

from ecdsa import SigningKey, VerifyingKey
import ecdsa
# private_key = SigningKey.generate() # uses NIST192p
# signature = private_key.sign(b"Educative authorizes this shot")
# print(signature)
# public_key = private_key.verifying_key
# print("Verified:", public_key.verify(signature, b"Educative authorizes this shot"))

UUID_LEN = 36
SALT_LEN = 16
CUTOFF   = SALT_LEN + UUID_LEN

class CryptPhonebook(ABC):
     @abstractmethod
     def get_public_key(self, uid: str) -> str: ...

     @abstractmethod
     def get_client_salt(self, uid: str) -> str: ...

     @abstractmethod
     def set_client_salt(self, uid: str, salt: str) -> None: ...

class CryptClient():
    def __init__(self, public_key: Union[Path, bytes] = None, private_key: Union[Path, str] = None) -> None:
        self.private_key = None; self.public_key = None

        if public_key is not None:
            self.public_key: VerifyingKey = VerifyingKey.from_pem(self._read_key(public_key))
        if private_key is not None:
            self.private_key: SigningKey = SigningKey.from_pem(self._read_key(private_key))
    
        if self.public_key is None and self.private_key is None:
            raise Exception("No public or private key provided")


    def _read_key(self, k):
        if type(k) == str:
            if k.startswith('-----BEGIN'): return k
            if os.path.isfile(k):
                with open(k, 'r') as fh: return fh.read()
        if type(k) == Path:
            if k.exists() and k.is_file():
                with open(k, 'r') as fh: return fh.read()
        raise Exception("Cannot load private key")

    @staticmethod
    def get_salt() -> str:
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k = SALT_LEN))
    
    def sign(self, msg: str) -> str:
        return base64.b64encode(self.private_key.sign(msg.encode())).decode()

    # def encrypt_for(self, to: crypto.PKey, msg: str) -> str:
    #     return base64.b64encode(to.to_cryptography_key().encrypt(msg.encode(), padding.PKCS1v15())).decode()

    # def decrypt(self, msg: str) -> str:
    #     return self.private_key.to_cryptography_key().decrypt(base64.b64decode(msg), padding.PKCS1v15()).decode()

    def verify(self, key: VerifyingKey, plaintext: str, signature: str) -> bool:
        try: return key.verify(base64.b64decode(signature), plaintext.encode())
        except ecdsa.keys.BadSignatureError: return False

    def craft_initial_token(self, uid: str, salt: str):
        # salt = CryptClient.get_salt()
        plaintext = f'{uid}{salt}'
        signature = client.encode_b64_for_url(self.sign(plaintext))
        return f'{plaintext}{signature}'
    
    def verify_initial_packet(self, pck: str, phone_book: CryptPhonebook) -> tuple[str, bool]:
        plaintext, signature = pck[:CUTOFF], pck[CUTOFF:]
        uid = plaintext[:UUID_LEN]
        key = VerifyingKey.from_pem(self._read_key(phone_book.get_public_key(uid)))

        return uid, self.verify(key, plaintext, self.decode_b64_from_url(signature))
    
    def encode_b64_for_url(self, b64: str):
        # '+/=' > '*_-'
        return b64.replace('+', '*').replace('/', '_').replace('=', '-')
    
    def decode_b64_from_url(self, eb64: str):
        return eb64.replace('*', '+').replace('_', '/').replace('-', '=')

if __name__ == '__main__':
    import uuid
    #! fixme: cannot crete salt on client side because of replay attacks
    client = CryptClient(private_key='./testing/client1.private')
    u = 'e118857e-3732-4e58-aa9c-56685c6a6492' # str(uuid.uuid4())
    pck = client.craft_initial_token(u, CryptClient.get_salt())
    print(pck)
    server = CryptClient(private_key='./testing/api.private')

    print(server.verify_initial_packet(pck, './testing/client1.public'))
