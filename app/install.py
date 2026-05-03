#!/usr/bin/env python3
"""Install codex-notify.py into CODEX_HOME and update config.toml."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_SOUND = PROJECT_ROOT / "music" / "universfield-new-notification-017-352293.wav"
NOTIFY_SCRIPT = PROJECT_ROOT / "codex-notify.py"
SUPPORTED_SOUND_EXTENSIONS = {".wav", ".mp3", ".aiff", ".aif", ".m4a"}


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def toml_array(values: list[str]) -> str:
    return "[" + ", ".join(toml_string(value) for value in values) + "]"


def python_command_for_notify(installed_script: Path) -> list[str]:
    if platform.system().lower() == "windows":
        return ["pythonw.exe", str(installed_script)]

    return ["python3", str(installed_script)]


def shell_command_for_hook(command: list[str], mode: str) -> str:
    values = command + [mode]
    if platform.system().lower() == "windows":
        return subprocess.list2cmdline(values)
    return shlex.join(values)


def backup_config(config_path: Path) -> Path | None:
    if not config_path.exists():
        return None

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = config_path.with_name(f"{config_path.name}.bak-{stamp}")
    shutil.copy2(config_path, backup_path)
    return backup_path


def set_top_level_notify(text: str, notify_command: list[str]) -> str:
    notify_line = f"notify = {toml_array(notify_command)}"
    pattern = re.compile(r"(?m)^notify\s*=\s*\[.*?\]\s*$")
    if pattern.search(text):
        return pattern.sub(lambda _: notify_line, text, count=1)

    prefix = notify_line + "\n"
    return prefix + ("\n" if text and not text.startswith("\n") else "") + text


def set_tui_notifications_false(text: str) -> str:
    tui_match = re.search(r"(?m)^\[tui\]\s*$", text)
    if not tui_match:
        separator = "" if text.endswith("\n") or not text else "\n"
        return f"{text}{separator}\n[tui]\nnotifications = false\n"

    next_table = re.search(r"(?m)^\[[^\]]+\]\s*$", text[tui_match.end() :])
    section_end = len(text) if not next_table else tui_match.end() + next_table.start()
    section = text[tui_match.end() : section_end]

    if re.search(r"(?m)^notifications\s*=", section):
        section = re.sub(r"(?m)^notifications\s*=.*$", "notifications = false", section, count=1)
    else:
        insertion = "\nnotifications = false"
        section = insertion + section if section.startswith("\n") else insertion + "\n" + section

    return text[: tui_match.end()] + section + text[section_end:]


def set_table_key(text: str, table_name: str, key: str, value: str) -> str:
    table_header = f"[{table_name}]"
    table_match = re.search(rf"(?m)^\[{re.escape(table_name)}\]\s*$", text)
    key_line = f"{key} = {value}"

    if not table_match:
        separator = "" if text.endswith("\n") or not text else "\n"
        return f"{text}{separator}\n{table_header}\n{key_line}\n"

    next_table = re.search(r"(?m)^\[[^\]]+\]\s*$", text[table_match.end() :])
    section_end = len(text) if not next_table else table_match.end() + next_table.start()
    section = text[table_match.end() : section_end]

    if re.search(rf"(?m)^{re.escape(key)}\s*=", section):
        section = re.sub(rf"(?m)^{re.escape(key)}\s*=.*$", key_line, section, count=1)
    else:
        insertion = f"\n{key_line}"
        section = insertion + section if section.startswith("\n") else insertion + "\n" + section

    return text[: table_match.end()] + section + text[section_end:]


def remove_existing_codex_notify_permission_hooks(text: str) -> str:
    lines = text.splitlines(keepends=True)
    output: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        if line.strip() != "[[hooks.PermissionRequest]]":
            output.append(line)
            index += 1
            continue

        block_start = index
        index += 1
        while index < len(lines) and lines[index].strip() != "[[hooks.PermissionRequest]]":
            index += 1

        block = lines[block_start:index]
        if "codex-notify.py" not in "".join(block):
            output.extend(block)

    return "".join(output)


def append_permission_request_hook(text: str, hook_command: str) -> str:
    text = remove_existing_codex_notify_permission_hooks(text).rstrip()
    hook_block = "\n\n".join(
        (
            "[[hooks.PermissionRequest]]",
            "[[hooks.PermissionRequest.hooks]]\n"
            'type = "command"\n'
            f"command = {toml_string(hook_command)}\n"
            "timeout = 5",
        )
    )
    return f"{text}\n\n{hook_block}\n" if text else f"{hook_block}\n"


def update_config(config_path: Path, notify_command: list[str]) -> Path | None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    existing = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    backup_path = backup_config(config_path)

    updated = set_top_level_notify(existing, notify_command)
    updated = set_table_key(updated, "features", "codex_hooks", "true")
    updated = append_permission_request_hook(updated, shell_command_for_hook(notify_command, "approval"))
    updated = set_tui_notifications_false(updated)

    if updated and not updated.endswith("\n"):
        updated += "\n"

    config_path.write_text(updated, encoding="utf-8")
    return backup_path


def install_files(sound_path: Path) -> tuple[Path, Path]:
    home = codex_home()
    music_dir = home / "music"
    home.mkdir(parents=True, exist_ok=True)
    music_dir.mkdir(parents=True, exist_ok=True)

    installed_script = home / "codex-notify.py"
    installed_sound = music_dir / f"codex-notify{sound_path.suffix.lower()}"

    shutil.copy2(NOTIFY_SCRIPT, installed_script)
    shutil.copy2(sound_path, installed_sound)
    return installed_script, installed_sound


def test_sound(installed_script: Path, installed_sound: Path) -> int:
    command = [sys.executable, str(installed_script), "--test", "--sound", str(installed_sound)]
    return subprocess.run(command, check=False).returncode


def prompt_sound_path(default_sound: Path) -> Path:
    print()
    print("Codex Notify Music kurulumu")
    print("---------------------------")
    print("Bildirim sesi olarak MP3 veya WAV dosyasi kullanabilirsiniz.")
    print("Bos birakirsaniz repo icindeki ornek Pixabay sesi kurulur.")
    print()

    raw_value = input("Ses dosyasi yolu (bos = ornek ses): ").strip().strip('"')
    if not raw_value:
        return default_sound

    return Path(raw_value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Codex notification sound support.")
    parser.add_argument("--sound", type=Path, default=DEFAULT_SOUND, help="Sound file to install.")
    parser.add_argument("--interactive", action="store_true", help="Ask the user for setup choices.")
    parser.add_argument("--no-config", action="store_true", help="Copy files but do not update ~/.codex/config.toml.")
    parser.add_argument("--no-test", action="store_true", help="Skip test playback after installation.")
    args = parser.parse_args()

    if args.interactive:
        args.sound = prompt_sound_path(DEFAULT_SOUND)

    sound_path = args.sound.expanduser().resolve()
    if not sound_path.is_file():
        print(f"Sound file not found: {sound_path}", file=sys.stderr)
        return 1

    if sound_path.suffix.lower() not in SUPPORTED_SOUND_EXTENSIONS:
        print(f"Unsupported sound extension: {sound_path.suffix}", file=sys.stderr)
        print("Use one of: .wav, .mp3, .aiff, .aif, .m4a", file=sys.stderr)
        return 1

    if not NOTIFY_SCRIPT.is_file():
        print(f"Missing installer dependency: {NOTIFY_SCRIPT}", file=sys.stderr)
        return 1

    installed_script, installed_sound = install_files(sound_path)
    print()
    print(f"Installed script: {installed_script}")
    print(f"Installed sound:  {installed_sound}")

    if not args.no_config:
        config_path = codex_home() / "config.toml"
        notify_command = python_command_for_notify(installed_script)
        backup_path = update_config(config_path, notify_command)
        print(f"Updated config:   {config_path}")
        if backup_path:
            print(f"Backup config:    {backup_path}")

    if not args.no_test:
        print()
        print("Testing sound playback...")
        result = test_sound(installed_script, installed_sound)
        if result != 0:
            print("Test playback failed. Install completed, but your platform may need an audio player.", file=sys.stderr)
            return result
        print("Sound test completed.")

    print()
    print("Done. Restart Codex for the config change to take effect.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
