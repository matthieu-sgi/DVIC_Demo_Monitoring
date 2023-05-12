from pathlib import Path
from typing import Union
import random
import string
import base64
import os
from abc import ABC, abstractmethod

from ecdsa import SigningKey, VerifyingKey
import ecdsa

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

     def is_secure_auth_enabled(self) -> bool: 
        return not bool(os.environ.get('DISABLE_CRYPTO'))

class CryptClient():
    def __init__(self, public_key: Union[Path, bytes] = None, private_key: Union[Path, str] = None) -> None:
        self.private_key = None; self.public_key = None

        if public_key is not None:
            self.public_key: VerifyingKey = VerifyingKey.from_pem(self._read_key(public_key))
        if private_key is not None:
            self.private_key: SigningKey = SigningKey.from_pem(self._read_key(private_key))
    
    @property
    def disabled(self):
        return self.public_key is None and self.private_key is None

    def _raise_if_disabled(self):
        if self.disabled: raise Exception("Crypto module disabled")

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
        self._raise_if_disabled()
        return base64.b64encode(self.private_key.sign(msg.encode())).decode()

    # def encrypt_for(self, to: crypto.PKey, msg: str) -> str:
    #     return base64.b64encode(to.to_cryptography_key().encrypt(msg.encode(), padding.PKCS1v15())).decode()

    # def decrypt(self, msg: str) -> str:
    #     return self.private_key.to_cryptography_key().decrypt(base64.b64decode(msg), padding.PKCS1v15()).decode()

    def verify(self, key: VerifyingKey, plaintext: str, signature: str) -> bool:
        self._raise_if_disabled()
        try: return key.verify(base64.b64decode(signature), plaintext.encode())
        except ecdsa.keys.BadSignatureError: return False

    def craft_initial_token(self, uid: str, salt: str):
        self._raise_if_disabled()
        plaintext = f'{uid}{salt}'
        signature = client.encode_b64_for_url(self.sign(plaintext))
        return f'{plaintext}{signature}'
    
    def verify_initial_packet(self, pck: str, phone_book: CryptPhonebook) -> tuple[str, bool]:
        plaintext, signature = pck[:CUTOFF], pck[CUTOFF:]
        uid = plaintext[:UUID_LEN]
        if not phone_book.is_secure_auth_enabled():
            return uid, True
        key = VerifyingKey.from_pem(self._read_key(phone_book.get_public_key(uid)))
        exst = plaintext[UUID_LEN:UUID_LEN+SALT_LEN]
        return uid, self.verify(key, plaintext, self.decode_b64_from_url(signature)) and exst == phone_book.get_client_salt(uid)
    
    def encode_b64_for_url(self, b64: str):
        # '+/=' > '*_-'
        return b64.replace('+', '*').replace('/', '_').replace('=', '-')
    
    def decode_b64_from_url(self, eb64: str):
        return eb64.replace('*', '+').replace('_', '/').replace('-', '=')

if __name__ == '__main__':
    import uuid
    #! fixme: cannot crete salt on client side because of replay attacks
    client = CryptClient(private_key='./testing/client1.private')
    s =  CryptClient.get_salt()
    u = 'e118857e-3732-4e58-aa9c-56685c6a6492' # str(uuid.uuid4())
    pck = client.craft_initial_token(u, s)
    print(f'uuid={u}')
    print(f'salt={s}')
    print(f'exst={pck[UUID_LEN:UUID_LEN+SALT_LEN]}')
    print(f'pck={pck}')


    server = CryptClient(private_key='./testing/api.private')

    class FS(CryptPhonebook):

        def is_secure_auth_enabled(self) -> bool:
            return True
        
        def get_client_salt(self, uid: str) -> str:
            return s
        
        def set_client_salt(self, uid: str, salt: str) -> None:
            pass

        def get_public_key(self, uid: str) -> str:
            return './testing/client1.public'

    print(server.verify_initial_packet(pck, FS()))
