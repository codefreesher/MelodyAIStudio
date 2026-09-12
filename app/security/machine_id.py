"""Stable hashed machine identity; raw identifiers are never persisted."""

import hashlib
import platform
import re
from pathlib import Path


def normalize_machine_id(value: str) -> str:
    compact = value.strip().upper().replace("-", "")
    if not re.fullmatch(r"[0-9A-F]{32}", compact):
        raise ValueError("Machine ID phải gồm 32 ký tự hex.")
    return "-".join(compact[index : index + 4] for index in range(0, 32, 4))


def get_machine_id() -> str:
    sources: list[str] = [platform.system().lower()]
    if platform.system() == "Windows":
        import winreg

        for key, names in (
            (r"SOFTWARE\Microsoft\Cryptography", ("MachineGuid",)),
            (
                r"HARDWARE\DESCRIPTION\System\BIOS",
                ("SystemManufacturer", "SystemProductName", "BaseBoardProduct"),
            ),
        ):
            try:
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE, key, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY
                ) as registry:
                    for name in names:
                        try:
                            value = str(winreg.QueryValueEx(registry, name)[0]).strip().lower()
                            if value:
                                sources.append(f"{name.lower()}={value}")
                        except OSError:
                            continue
            except OSError:
                continue
    else:
        for name in ("/etc/machine-id", "/sys/class/dmi/id/product_uuid", "/sys/class/dmi/id/board_name"):
            try:
                value = Path(name).read_text().strip().lower()
                if value:
                    sources.append(f"{Path(name).name}={value}")
            except OSError:
                continue
    if len(sources) == 1:
        # Do not silently bind a license to an unstable MAC or random identifier.
        raise RuntimeError("Không đọc được định danh máy ổn định trên hệ thống này.")
    digest = hashlib.sha256(("melodyai-machine-v1|" + "|".join(sources)).encode()).hexdigest()[:32]
    return normalize_machine_id(digest)
