import bcrypt

class PasswordService:
    def hash_password(self, password: str) -> bytes:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    def verify_password(self, plain: str, hashed: bytes) -> bool:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed)