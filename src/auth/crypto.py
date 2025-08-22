# src/auth/crypto.py
# --- agent_meta ---
# role: auth-crypto
# owner: @backend
# contract: Хеширование паролей (scrypt) и проверка
# last_reviewed: 2025-08-21
# interfaces:
#   - hash_password(password: str) -> str
#   - verify_password(password: str, stored: str) -> bool
# --- /agent_meta ---

import base64
import hashlib
import os
import secrets
from typing import Tuple


# Параметры scrypt для надежного хеширования паролей
# Эти значения выбраны для баланса между безопасностью и производительностью
_SCRYPT_N = 2 ** 14  # 16384 - CPU/memory cost parameter (чем больше, тем медленнее)
_SCRYPT_R = 8        # Block size parameter
_SCRYPT_P = 1        # Parallelization parameter
_KEY_LEN = 32        # Длина выходного ключа в байтах (256 бит)
_SALT_LEN = 16       # Длина соли в байтах (128 бит)


def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("utf-8").rstrip("=")


def _b64d(s: str) -> bytes:
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def hash_password(password: str) -> str:
    """Хеширование пароля с использованием scrypt алгоритма.
    
    scrypt является криптографически стойкой функцией для хеширования паролей,
    устойчивой к brute-force атакам благодаря высокому потреблению CPU/памяти.
    
    Returns:
        Строка формата: scrypt$N$r$p$salt$hash
    """
    # Генерируем криптографически стойкую случайную соль
    salt = os.urandom(_SALT_LEN)
    
    # Выполняем scrypt хеширование с заданными параметрами
    dk = hashlib.scrypt(
        password=password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_KEY_LEN,
    )
    
    # Формируем строку с параметрами для возможности последующей верификации
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${_b64e(salt)}${_b64e(dk)}"


def _parse(stored: str) -> Tuple[int, int, int, bytes, bytes]:
    algo, n, r, p, salt_b64, hash_b64 = stored.split("$")
    if algo != "scrypt":
        raise ValueError("Unsupported hash format")
    return int(n), int(r), int(p), _b64d(salt_b64), _b64d(hash_b64)


def verify_password(password: str, stored: str) -> bool:
    try:
        n, r, p, salt, ref = _parse(stored)
        dk = hashlib.scrypt(
            password=password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            dklen=len(ref),
        )
        return secrets.compare_digest(dk, ref)
    except Exception:
        return False

