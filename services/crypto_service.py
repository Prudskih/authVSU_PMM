# services/crypto_service.py
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import gzip
import os
from config import AES_KEY, RSA_PRIVATE_KEY, RSA_PUBLIC_KEY

class CryptoService:
    def __init__(self):
        self.aes_key = AES_KEY
        self.rsa_private = RSA_PRIVATE_KEY
        self.rsa_public = RSA_PUBLIC_KEY

    def encrypt_symmetric(self, data: bytes) -> bytes:
        """AES-GCM шифрование (автоматически генерирует IV)"""
        iv = os.urandom(12)
        cipher = Cipher(algorithms.AES(self.aes_key), modes.GCM(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        return iv + encryptor.tag + ciphertext  # IV + TAG + CIPHERTEXT

    def decrypt_symmetric(self, encrypted_data: bytes) -> bytes:
        """Расшифровка AES-GCM"""
        iv = encrypted_data[:12]
        tag = encrypted_data[12:28]
        ciphertext = encrypted_data[28:]
        cipher = Cipher(algorithms.AES(self.aes_key), modes.GCM(iv, tag))
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()

    def sign_data(self, data: bytes) -> bytes:
        """Электронная подпись (RSA-PSS)"""
        return self.rsa_private.sign(
            data,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )

    def verify_signature(self, data: bytes, signature: bytes) -> bool:
        """Проверка ЭП"""
        try:
            self.rsa_public.verify(
                signature,
                data,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    def compress(self, data: bytes) -> bytes:
        return gzip.compress(data)

    def decompress(self, compressed_data: bytes) -> bytes:
        return gzip.decompress(compressed_data)