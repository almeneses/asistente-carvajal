"""Genera el hash PBKDF2 para AUTH_USERS."""

from __future__ import annotations

import argparse
import getpass

from assistant.auth import hash_password


def main() -> int:
    parser = argparse.ArgumentParser(description="Hash de contraseña para AUTH_USERS.")
    parser.add_argument("--user", help="Usuario (solo informativo).")
    parser.add_argument("--password", help="Contraseña; si se omite se pide por consola.")
    args = parser.parse_args()
    password = args.password or getpass.getpass("Contraseña: ")
    if len(password) < 12:
        print("La contraseña debe tener al menos 12 caracteres.")
        return 1
    print(hash_password(password))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
