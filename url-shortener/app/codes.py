import secrets

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def generate_code(length: int) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))
