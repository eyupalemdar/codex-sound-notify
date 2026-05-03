#!/usr/bin/env python3
"""Play a custom sound when Codex invokes the notify command."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path


DEFAULT_SOUND_NAMES = (
    "codex-notify.wav",
    "codex-notify.mp3",
    "codex-notify.aiff",
    "codex-notify.aif",
    "codex-notify.m4a",
    "universfield-new-notification-017-352293.wav",
    "universfield-new-notification-017-352293.mp3",
)

MODE_SOUND_NAMES = {
    "approval": (
        "codex-notify-approval.wav",
        "codex-notify-approval.mp3",
        "codex-notify-approval.aiff",
        "codex-notify-approval.aif",
        "codex-notify-approval.m4a",
        "approval.wav",
        "approval.mp3",
        "approval.aiff",
        "approval.aif",
        "approval.m4a",
    ),
    "done": (
        "codex-notify-done.wav",
        "codex-notify-done.mp3",
        "codex-notify-done.aiff",
        "codex-notify-done.aif",
        "codex-notify-done.m4a",
        "done.wav",
        "done.mp3",
        "done.aiff",
        "done.aif",
        "done.m4a",
    ),
}


def unique_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    unique: list[Path] = []
    for path in paths:
        expanded = path.expanduser()
        key = os.path.normcase(str(expanded))
        if key in seen:
            continue
        seen.add(key)
        unique.append(expanded)
    return unique


def codex_home_candidates() -> list[Path]:
    candidates: list[Path] = []

    env_home = os.environ.get("CODEX_HOME")
    if env_home:
        candidates.append(Path(env_home))

    candidates.append(Path.home() / ".codex")

    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        candidates.append(Path(user_profile) / ".codex")

    home_drive = os.environ.get("HOMEDRIVE")
    home_path = os.environ.get("HOMEPATH")
    if home_drive and home_path:
        candidates.append(Path(home_drive + home_path) / ".codex")

    unix_home = os.environ.get("HOME")
    if unix_home:
        candidates.append(Path(unix_home) / ".codex")

    return unique_paths(candidates)


def find_codex_home() -> Path:
    env_home = os.environ.get("CODEX_HOME")
    if env_home:
        return Path(env_home).expanduser()

    candidates = codex_home_candidates()
    if not candidates:
        return Path.home() / ".codex"

    for candidate in candidates:
        if (candidate / "config.toml").is_file():
            return candidate

    for candidate in candidates:
        if candidate.is_dir():
            return candidate

    return candidates[0]


def default_sound_path(mode: str = "done") -> Path | None:
    music_dir = find_codex_home() / "music"
    names = MODE_SOUND_NAMES.get(mode, ()) + DEFAULT_SOUND_NAMES
    for name in names:
        candidate = music_dir / name
        if candidate.is_file():
            return candidate
    return None


def read_payload() -> dict:
    if sys.stdin.isatty():
        return {}

    try:
        data = sys.stdin.read().strip()
    except Exception:
        return {}

    if not data:
        return {}

    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        return {}

    return parsed if isinstance(parsed, dict) else {}


def play_windows(sound_path: Path) -> bool:
    alias = f"codex_notify_{uuid.uuid4().hex}"
    winmm = ctypes.windll.winmm

    def mci(command: str) -> tuple[bool, str]:
        buffer = ctypes.create_unicode_buffer(512)
        error = winmm.mciSendStringW(command, buffer, len(buffer), None)
        return error == 0, buffer.value

    opened, _ = mci(f'open "{sound_path}" alias {alias}')
    if not opened:
        return False

    try:
        played, _ = mci(f"play {alias} wait")
        return played
    finally:
        mci(f"close {alias}")


def run_player(command: list[str]) -> bool:
    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return False

    return completed.returncode == 0


def play_macos(sound_path: Path) -> bool:
    return run_player(["afplay", str(sound_path)])


def play_linux(sound_path: Path) -> bool:
    suffix = sound_path.suffix.lower()
    candidates: list[list[str]] = []

    if suffix == ".wav":
        candidates.extend((["paplay", str(sound_path)], ["aplay", str(sound_path)]))

    candidates.extend(
        (
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(sound_path)],
            ["mpv", "--no-video", "--really-quiet", str(sound_path)],
            ["cvlc", "--play-and-exit", "--intf", "dummy", str(sound_path)],
            ["mpg123", "-q", str(sound_path)],
        )
    )

    for command in candidates:
        if shutil.which(command[0]) and run_player(command):
            return True

    return False


def play_sound(sound_path: Path) -> bool:
    system = platform.system().lower()
    if system == "windows":
        return play_windows(sound_path)
    if system == "darwin":
        return play_macos(sound_path)
    if system == "linux":
        return play_linux(sound_path)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Play the configured Codex notification sound.")
    parser.add_argument("mode", nargs="?", default="done", choices=("done", "approval"), help="Notification mode.")
    parser.add_argument("--sound", type=Path, help="Sound file to play. Defaults to <codex-home>/music/codex-notify.*")
    parser.add_argument("--test", action="store_true", help="Print errors instead of failing silently.")
    args = parser.parse_args()

    read_payload()
    sound_path = args.sound.expanduser() if args.sound else default_sound_path(args.mode)

    if sound_path is None or not sound_path.is_file():
        if args.test:
            print("No notification sound found in the detected Codex home music directory.", file=sys.stderr)
        return 1 if args.test else 0

    ok = play_sound(sound_path.resolve())
    if not ok and args.test:
        print(f"Could not play sound: {sound_path}", file=sys.stderr)
        if platform.system().lower() == "linux":
            print("Install one of: paplay, aplay, ffplay, mpv, cvlc, mpg123.", file=sys.stderr)
        return 1

    time.sleep(0.05)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
