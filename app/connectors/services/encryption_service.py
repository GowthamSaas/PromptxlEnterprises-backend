from cryptography.fernet import Fernet

from app.config import settings


class EncryptionService:

    def __init__(self):

        self.cipher = Fernet(
            settings.ENCRYPTION_KEY.encode()
        )

    # ----------------------------------
    # Encrypt
    # ----------------------------------

    def encrypt_token(self, token: str) -> str:

        encrypted = self.cipher.encrypt(
            token.encode()
        )

        return encrypted.decode()

    # ----------------------------------
    # Decrypt
    # ----------------------------------

    def decrypt_token(self, encrypted_token: str) -> str:

        decrypted = self.cipher.decrypt(
            encrypted_token.encode()
        )

        return decrypted.decode()


encryption_service = EncryptionService()