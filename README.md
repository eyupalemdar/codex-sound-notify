# codex-sound-notify

One-click sound notifications for Codex task completion and approval requests.

[Turkce README](README.tr.md)

## Level 1: One-Click Install

Windows users:

```text
Install-Windows.cmd
```

Double-click this file. The script first checks whether Python is ready. If Python is missing or too old, it offers to install it automatically, then asks for task-complete and approval-request sound files. Leave the paths empty to use the included Pixabay example sound. You can also provide MP3 or WAV file paths.

macOS users:

```text
Install-macOS.command
```

Linux users:

```text
Install-Linux.sh
```

## What The Script Does

- Finds the Codex home directory from `CODEX_HOME`, an existing `config.toml`, or the platform user home.
- Installs `codex-notify.py` into that Codex home directory.
- Guides Python setup or offers automatic installation if Python is not ready.
- Copies your selected sounds to `<codex-home>/music/codex-notify-done.*` and `<codex-home>/music/codex-notify-approval.*`.
- Backs up `<codex-home>/config.toml`.
- Adds or updates Codex settings for task-complete notifications and approval-request hooks.
- Tests sound playback after installation.
- Writes the installed script path and Python launcher from the detected target, not from a hard-coded machine path.

The generated config uses the first available PATH command for the current platform:

- Windows: `pyw.exe -3`, `pythonw.exe`, `py.exe -3`, then `python.exe`
- macOS/Linux: `python3`, then `python`

On Windows, the generated config may look like this:

```toml
notify = ["pyw.exe", "-3", "C:\\Users\\<user>\\.codex\\codex-notify.py"]

[tui]
notifications = false

[features]
codex_hooks = true

[[hooks.PermissionRequest]]
[[hooks.PermissionRequest.hooks]]
type = "command"
command = "pyw.exe -3 C:\\Users\\<user>\\.codex\\codex-notify.py approval"
timeout = 5
```

On macOS/Linux, it may look like this:

```toml
notify = ["python3", "/Users/<user>/.codex/codex-notify.py"]

[tui]
notifications = false

[features]
codex_hooks = true

[[hooks.PermissionRequest]]
[[hooks.PermissionRequest.hooks]]
type = "command"
command = "python3 /Users/<user>/.codex/codex-notify.py approval"
timeout = 5
```

## Level 2: Manual Usage

```powershell
python app\install.py --sound C:\path\to\notification.mp3
python app\install.py --done-sound C:\path\to\done.wav --approval-sound C:\path\to\approval.wav
python app\install.py --codex-home C:\Users\you\.codex
```

Test:

```powershell
python app\codex-notify.py done --test --sound app\music\universfield-new-notification-017-352293.wav
python app\codex-notify.py approval --test --sound app\music\universfield-new-notification-017-352293.wav
```

## Audio Support

- Windows: MP3, WAV, AIFF, M4A. No extra package required.
- macOS: formats supported by `afplay`.
- Linux: `paplay` or `aplay` for WAV; `ffplay`, `mpv`, `cvlc`, or `mpg123` for MP3.

## Example Sound

The included example sound is `New Notification 017` by Universfield from Pixabay.

Pixabay notification search: https://pixabay.com/sound-effects/search/notification/

Asset page: https://pixabay.com/es/sound-effects/new-notification-017-352293/
