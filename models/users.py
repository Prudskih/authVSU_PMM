from dataclasses import dataclass

@dataclass
class User:
    username: str
    password_hash: bytes
    role: str  # "user" или "admin"