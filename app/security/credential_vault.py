"""OS keyring first, encrypted local fallback for unavailable keyring backends."""

import hashlib
import os
import sys
from pathlib import Path

import keyring
from cryptography.fernet import Fernet


class CredentialVault:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.backend = None
        if sys.platform == "win32":
            from keyring.backends.Windows import WinVaultKeyring

            self.backend = WinVaultKeyring()

    def _name(self, provider: str) -> str:
        return hashlib.sha256(provider.encode()).hexdigest()

    def _cipher(self) -> Fernet:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / "vault.key"
        if not path.exists():
            try:
                descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(Fernet.generate_key())
            except FileExistsError:
                pass
        return Fernet(path.read_bytes())

    def set(self, provider: str, secret: str) -> None:
        try:
            if self.backend is None:
                raise keyring.errors.NoKeyringError()
            self.backend.set_password("MelodyAI", provider, secret)
            (self.root / self._name(provider)).unlink(missing_ok=True)
            return
        except keyring.errors.KeyringError:
            pass
        cipher = self._cipher()
        path = self.root / self._name(provider)
        path.write_bytes(cipher.encrypt(secret.encode()))
        path.chmod(0o600)

    def get(self, provider: str) -> str:
        path = self.root / self._name(provider)
        if path.exists():
            return self._cipher().decrypt(path.read_bytes()).decode()
        try:
            if self.backend is None:
                return ""
            return self.backend.get_password("MelodyAI", provider) or ""
        except keyring.errors.KeyringError:
            return ""

    def delete(self, provider: str) -> None:
        try:
            if self.backend is not None:
                self.backend.delete_password("MelodyAI", provider)
        except keyring.errors.KeyringError:
            pass
        (self.root / self._name(provider)).unlink(missing_ok=True)
