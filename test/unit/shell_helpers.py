"""Bridge native Python and the POSIX shells used by the shell fixtures."""

import os
from pathlib import Path
import shutil
import subprocess


def shell_executable(name: str = "bash") -> str:
    """Resolve on PATH before Windows CreateProcess can select System32's WSL launcher."""
    executable = shutil.which(name)
    if executable is None:
        raise FileNotFoundError(f"{name} is required for shell tests")
    return executable


def shell_path(path: str | Path, shell: str = "bash") -> str:
    """Return the path spelling the selected shell uses for filesystem operations."""
    if os.name != "nt":
        return str(path)
    return subprocess.run(
        [shell_executable(shell), "-c", 'cygpath -u -- "$1"', "path", str(path)],
        capture_output=True, encoding="utf-8", check=True, timeout=30,
    ).stdout.rstrip("\r\n")


def native_path(path: str, shell: str = "bash") -> Path:
    """Convert shell output before native Python interprets drive and mount prefixes."""
    if not path:
        raise ValueError("cannot convert an empty shell path")
    if os.name == "nt":
        path = subprocess.run(
            [shell_executable(shell), "-c", 'cygpath -w -- "$1"', "path", path],
            capture_output=True, encoding="utf-8", check=True, timeout=30,
        ).stdout.rstrip("\r\n")
    return Path(path)


def platform_environment() -> dict[str, str]:
    """Keep Windows process-startup variables without leaking tools into an isolated PATH."""
    return {
        name: os.environ[name]
        for name in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP")
        if name in os.environ
    }
