#!/usr/bin/env python3
"""Install codex-notify.py into the detected Codex home and update config.toml."""

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


def toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def toml_array(values: list[str]) -> str:
    return "[" + ", ".join(toml_string(value) for value in values) + "]"


def first_available_command(candidates: list[list[str]]) -> list[str]:
    for command in candidates:
        if shutil.which(command[0]):
            return command

    return candidates[-1]


def python_command_for_notify(installed_script: Path) -> list[str]:
    if platform.system().lower() == "windows":
        launcher = first_available_command(
            [
                ["pyw.exe", "-3"],
                ["pythonw.exe"],
                ["py.exe", "-3"],
                ["python.exe"],
            ]
        )
        return launcher + [str(installed_script)]

    launcher = first_available_command([["python3"], ["python"]])
    return launcher + [str(installed_script)]


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


def move_common_codex_root_keys_out_of_tui(text: str) -> str:
    tui_match = re.search(r"(?m)^\[tui\]\s*$", text)
    if not tui_match:
        return text

    next_table = re.search(r"(?m)^\[[^\]]+\]\s*$", text[tui_match.end() :])
    section_end = len(text) if not next_table else tui_match.end() + next_table.start()
    section = text[tui_match.end() : section_end]
    root_keys = {
        "model",
        "model_reasoning_effort",
        "windows_wsl_setup_acknowledged",
        "personality",
        "plan_mode_reasoning_effort",
    }

    kept_lines: list[str] = []
    moved_lines: list[str] = []
    for line in section.splitlines(keepends=True):
        match = re.match(r"^([A-Za-z0-9_-]+)\s*=", line)
        if match and match.group(1) in root_keys:
            moved_lines.append(line)
        else:
            kept_lines.append(line)

    if not moved_lines:
        return text

    without_moved = text[: tui_match.end()] + "".join(kept_lines) + text[section_end:]
    root_block = "".join(moved_lines).rstrip()
    first_table = re.search(r"(?m)^\[", without_moved)

    if not first_table:
        return without_moved.rstrip() + "\n\n" + root_block + ("\n" if text.endswith("\n") else "")

    root_prefix = without_moved[: first_table.start()].rstrip()
    table_suffix = without_moved[first_table.start() :].lstrip("\r\n")
    parts = [part for part in (root_prefix, root_block, table_suffix.rstrip()) if part]
    return "\n\n".join(parts) + ("\n" if text.endswith("\n") else "")


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
        while index < len(lines):
            stripped = lines[index].strip()
            if stripped == "[[hooks.PermissionRequest]]":
                break
            if stripped.startswith("[") and stripped != "[[hooks.PermissionRequest.hooks]]":
                break
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
    existing = config_path.read_text(encoding="utf-8-sig") if config_path.exists() else ""
    backup_path = backup_config(config_path)

    updated = set_top_level_notify(existing, notify_command)
    updated = move_common_codex_root_keys_out_of_tui(updated)
    updated = set_table_key(updated, "features", "codex_hooks", "true")
    updated = append_permission_request_hook(updated, shell_command_for_hook(notify_command, "approval"))
    updated = set_tui_notifications_false(updated)

    if updated and not updated.endswith("\n"):
        updated += "\n"

    config_path.write_text(updated, encoding="utf-8")
    return backup_path


def validate_sound_path(sound_path: Path) -> Path:
    resolved = sound_path.expanduser().resolve()
    if not resolved.is_file():
        raise ValueError(f"Sound file not found: {resolved}")

    if resolved.suffix.lower() not in SUPPORTED_SOUND_EXTENSIONS:
        extensions = ", ".join(sorted(SUPPORTED_SOUND_EXTENSIONS))
        raise ValueError(f"Unsupported sound extension: {resolved.suffix}. Use one of: {extensions}")

    return resolved


def install_files(codex_home: Path, done_sound_path: Path, approval_sound_path: Path) -> tuple[Path, Path, Path]:
    home = codex_home
    music_dir = home / "music"
    home.mkdir(parents=True, exist_ok=True)
    music_dir.mkdir(parents=True, exist_ok=True)

    installed_script = home / "codex-notify.py"
    installed_done_sound = music_dir / f"codex-notify-done{done_sound_path.suffix.lower()}"
    installed_approval_sound = music_dir / f"codex-notify-approval{approval_sound_path.suffix.lower()}"
    installed_default_sound = music_dir / f"codex-notify{done_sound_path.suffix.lower()}"

    shutil.copy2(NOTIFY_SCRIPT, installed_script)
    shutil.copy2(done_sound_path, installed_done_sound)
    shutil.copy2(approval_sound_path, installed_approval_sound)
    shutil.copy2(done_sound_path, installed_default_sound)
    return installed_script, installed_done_sound, installed_approval_sound


def test_sound(installed_script: Path, installed_sound: Path, mode: str) -> int:
    command = [sys.executable, str(installed_script), mode, "--test", "--sound", str(installed_sound)]
    return subprocess.run(command, check=False).returncode


def prompt_sound_path(label: str, default_sound: Path) -> Path:
    print()
    raw_value = input(f"{label} ses dosyasi yolu (bos = varsayilan): ").strip().strip('"')
    if not raw_value:
        return default_sound

    return Path(raw_value)


def prompt_sound_paths(default_sound: Path) -> tuple[Path, Path]:
    print()
    print("Codex Notify Music kurulumu")
    print("---------------------------")
    print("Islem sonu ve onay istegi icin ayri MP3 veya WAV dosyasi kullanabilirsiniz.")
    print("Bos birakirsaniz repo icindeki ornek Pixabay sesi kullanilir.")

    done_sound = prompt_sound_path("Islem sonu", default_sound)
    approval_sound = prompt_sound_path("Onay istegi", done_sound)
    return done_sound, approval_sound


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Codex notification sound support.")
    parser.add_argument("--sound", type=Path, help="Sound file to use for both notification modes.")
    parser.add_argument("--done-sound", type=Path, help="Sound file for task-complete notifications.")
    parser.add_argument("--approval-sound", type=Path, help="Sound file for approval-request notifications.")
    parser.add_argument("--interactive", action="store_true", help="Ask the user for setup choices.")
    parser.add_argument("--codex-home", type=Path, help="Override the detected Codex home directory.")
    parser.add_argument("--no-config", action="store_true", help="Copy files but do not update the detected config.toml.")
    parser.add_argument("--no-test", action="store_true", help="Skip test playback after installation.")
    args = parser.parse_args()

    if args.interactive:
        done_sound_path, approval_sound_path = prompt_sound_paths(DEFAULT_SOUND)
    else:
        shared_sound = args.sound or DEFAULT_SOUND
        done_sound_path = args.done_sound or shared_sound
        approval_sound_path = args.approval_sound or shared_sound

    try:
        done_sound_path = validate_sound_path(done_sound_path)
        approval_sound_path = validate_sound_path(approval_sound_path)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1

    if not NOTIFY_SCRIPT.is_file():
        print(f"Missing installer dependency: {NOTIFY_SCRIPT}", file=sys.stderr)
        return 1

    home = args.codex_home.expanduser() if args.codex_home else find_codex_home()
    installed_script, installed_done_sound, installed_approval_sound = install_files(
        home,
        done_sound_path,
        approval_sound_path,
    )
    print()
    print(f"Codex home:       {home}")
    print(f"Installed script: {installed_script}")
    print(f"Done sound:       {installed_done_sound}")
    print(f"Approval sound:   {installed_approval_sound}")

    if not args.no_config:
        config_path = home / "config.toml"
        notify_command = python_command_for_notify(installed_script)
        backup_path = update_config(config_path, notify_command)
        print(f"Updated config:   {config_path}")
        if backup_path:
            print(f"Backup config:    {backup_path}")

    if not args.no_test:
        print()
        print("Testing done sound playback...")
        result = test_sound(installed_script, installed_done_sound, "done")
        if result != 0:
            print("Done sound test failed. Install completed, but your platform may need an audio player.", file=sys.stderr)
            return result
        print("Done sound test completed.")

        print()
        print("Testing approval sound playback...")
        result = test_sound(installed_script, installed_approval_sound, "approval")
        if result != 0:
            print("Approval sound test failed. Install completed, but your platform may need an audio player.", file=sys.stderr)
            return result
        print("Approval sound test completed.")

    print()
    print("Done. Restart Codex for the config change to take effect.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
