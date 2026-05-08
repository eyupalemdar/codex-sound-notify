#!/usr/bin/env python3
"""Install codex-notify.py into the detected Codex home and update config.toml."""

from __future__ import annotations

import argparse
import datetime as dt
import locale
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
HOOK_FEATURE_KEYS = ("hooks", "codex_hooks")
LANGUAGE_CHOICES = ("auto", "en", "tr")
MESSAGES = {
    "en": {
        "sound_prompt": "{label} sound file path (empty = default): ",
        "interactive_title": "Codex Notify Music setup",
        "interactive_intro": "You can use separate MP3 or WAV files for task completion and approval requests.",
        "interactive_default": "Leave empty to use the included Pixabay example sound.",
        "done_label": "Task complete",
        "approval_label": "Approval request",
        "restart_notice": "Done. Restart Codex for the config change to take effect.",
        "hook_review_notice": (
            "Codex 0.129+ requires manual hook review. In Codex, open /hooks, select "
            "PermissionRequest, press Enter, then press t to trust the codex-notify hook."
        ),
    },
    "tr": {
        "sound_prompt": "{label} ses dosyasi yolu (bos = varsayilan): ",
        "interactive_title": "Codex Notify Music kurulumu",
        "interactive_intro": "Islem sonu ve onay istegi icin ayri MP3 veya WAV dosyasi kullanabilirsiniz.",
        "interactive_default": "Bos birakirsaniz repo icindeki ornek Pixabay sesi kullanilir.",
        "done_label": "Islem sonu",
        "approval_label": "Onay istegi",
        "restart_notice": "Tamamlandi. Config degisikliginin etkili olmasi icin Codex'i yeniden baslatin.",
        "hook_review_notice": (
            "Codex 0.129+ hook icin manuel inceleme ister. Codex icinde /hooks acin, "
            "PermissionRequest satirini secip Enter'a basin, sonra codex-notify hook'una guvenmek icin t tusuna basin."
        ),
    },
}


def is_turkish_language(value: str | None) -> bool:
    normalized = (value or "").strip().lower()
    return normalized.startswith("tr") or normalized.startswith("turkish")


def detect_language() -> str:
    override = os.environ.get("CODEX_NOTIFY_LANG")
    if override:
        return "tr" if is_turkish_language(override) else "en"

    for env_name in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        value = os.environ.get(env_name)
        if value and is_turkish_language(value):
            return "tr"

    locale_names = [locale.getlocale()[0]]
    if hasattr(locale, "LC_MESSAGES"):
        try:
            locale_names.append(locale.getlocale(locale.LC_MESSAGES)[0])
        except (TypeError, ValueError):
            pass

    if any(is_turkish_language(name) for name in locale_names):
        return "tr"

    return "en"


def resolve_language(language: str) -> str:
    return detect_language() if language == "auto" else language


def message(language: str, key: str, **kwargs: str) -> str:
    return MESSAGES[language][key].format(**kwargs)


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


def parse_version_tuple(text: str) -> tuple[int, ...] | None:
    match = re.search(r"\d+(?:\.\d+)+", text)
    if not match:
        return None

    return tuple(int(part) for part in match.group(0).split("."))


def is_new_hooks_feature_version(version: tuple[int, ...]) -> bool:
    padded = version + (0,) * (3 - len(version))
    major, minor, patch = padded[:3]

    # Codex renamed [features].codex_hooks to [features].hooks in 0.129.0.
    if major == 0:
        return (minor, patch) >= (129, 0)
    return major >= 1


def existing_hooks_feature_key(text: str) -> str | None:
    for key in HOOK_FEATURE_KEYS:
        if re.search(rf"(?m)^{re.escape(key)}\s*=", text):
            return key

    return None


def detect_hooks_feature_key(existing_config: str = "") -> str:
    codex_command = shutil.which("codex")
    if not codex_command:
        return existing_hooks_feature_key(existing_config) or "hooks"

    try:
        result = subprocess.run(
            [codex_command, "features", "list"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        result = None

    if result and result.returncode == 0:
        feature_names = {
            line.split()[0]
            for line in result.stdout.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        if "hooks" in feature_names:
            return "hooks"
        if "codex_hooks" in feature_names:
            return "codex_hooks"

    try:
        result = subprocess.run(
            [codex_command, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        result = None

    if result and result.returncode == 0:
        version = parse_version_tuple(result.stdout)
        if version and not is_new_hooks_feature_version(version):
            return "codex_hooks"

    return existing_hooks_feature_key(existing_config) or "hooks"


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


def remove_table_key(text: str, table_name: str, key: str) -> str:
    table_match = re.search(rf"(?m)^\[{re.escape(table_name)}\]\s*$", text)
    if not table_match:
        return text

    next_table = re.search(r"(?m)^\[[^\]]+\]\s*$", text[table_match.end() :])
    section_end = len(text) if not next_table else table_match.end() + next_table.start()
    section = text[table_match.end() : section_end]
    section = re.sub(rf"(?m)^{re.escape(key)}\s*=.*(?:\r?\n)?", "", section)
    return text[: table_match.end()] + section + text[section_end:]


def set_hooks_feature_flag(text: str, hook_feature_key: str) -> str:
    for key in HOOK_FEATURE_KEYS:
        if key != hook_feature_key:
            text = remove_table_key(text, "features", key)

    return set_table_key(text, "features", hook_feature_key, "true")


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


def update_config(
    config_path: Path,
    notify_command: list[str],
    hook_feature_key: str | None = None,
) -> tuple[Path | None, str]:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    existing = config_path.read_text(encoding="utf-8-sig") if config_path.exists() else ""
    backup_path = backup_config(config_path)
    selected_hook_feature_key = hook_feature_key or detect_hooks_feature_key(existing)

    updated = set_top_level_notify(existing, notify_command)
    updated = move_common_codex_root_keys_out_of_tui(updated)
    updated = set_hooks_feature_flag(updated, selected_hook_feature_key)
    updated = append_permission_request_hook(updated, shell_command_for_hook(notify_command, "approval"))
    updated = set_tui_notifications_false(updated)

    if updated and not updated.endswith("\n"):
        updated += "\n"

    config_path.write_text(updated, encoding="utf-8")
    return backup_path, selected_hook_feature_key


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


def prompt_sound_path(label: str, default_sound: Path, language: str) -> Path:
    print()
    raw_value = input(message(language, "sound_prompt", label=label)).strip().strip('"')
    if not raw_value:
        return default_sound

    return Path(raw_value)


def prompt_sound_paths(default_sound: Path, language: str) -> tuple[Path, Path]:
    print()
    print(message(language, "interactive_title"))
    print("---------------------------")
    print(message(language, "interactive_intro"))
    print(message(language, "interactive_default"))

    done_sound = prompt_sound_path(message(language, "done_label"), default_sound, language)
    approval_sound = prompt_sound_path(message(language, "approval_label"), done_sound, language)
    return done_sound, approval_sound


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Codex notification sound support.")
    parser.add_argument("--sound", type=Path, help="Sound file to use for both notification modes.")
    parser.add_argument("--done-sound", type=Path, help="Sound file for task-complete notifications.")
    parser.add_argument("--approval-sound", type=Path, help="Sound file for approval-request notifications.")
    parser.add_argument("--interactive", action="store_true", help="Ask the user for setup choices.")
    parser.add_argument("--codex-home", type=Path, help="Override the detected Codex home directory.")
    parser.add_argument(
        "--language",
        choices=LANGUAGE_CHOICES,
        default="auto",
        help="Installer language. Auto uses Turkish only for Turkish locales; otherwise English.",
    )
    parser.add_argument(
        "--hooks-feature-key",
        choices=("auto",) + HOOK_FEATURE_KEYS,
        default="auto",
        help="Override the Codex hooks feature flag name. Auto uses the installed Codex CLI.",
    )
    parser.add_argument("--no-config", action="store_true", help="Copy files but do not update the detected config.toml.")
    parser.add_argument("--no-test", action="store_true", help="Skip test playback after installation.")
    args = parser.parse_args()
    language = resolve_language(args.language)

    if args.interactive:
        done_sound_path, approval_sound_path = prompt_sound_paths(DEFAULT_SOUND, language)
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
        hook_feature_key = None if args.hooks_feature_key == "auto" else args.hooks_feature_key
        backup_path, selected_hook_feature_key = update_config(config_path, notify_command, hook_feature_key)
        print(f"Updated config:   {config_path}")
        print(f"Hooks feature:    [features].{selected_hook_feature_key}")
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
    print(message(language, "restart_notice"))
    print(message(language, "hook_review_notice"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
