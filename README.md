# codex-sound-notify

One-click sound notifications for Codex task completion and approval requests.

[Turkce README](README.tr.md)

## Level 1: One-Click Install

Windows users:

```text
Install-Windows.cmd
```

Double-click this file. The script first checks whether Python is ready. If Python is missing or too old, it offers to install it automatically, then asks for a sound file. Leave the sound path empty to use the included Pixabay example sound. You can also provide an MP3 or WAV file path.

macOS users:

```text
Install-macOS.command
```

Linux users:

```text
Install-Linux.sh
```

## What The Script Does

- Installs `~/.codex/codex-notify.py`.
- Guides Python setup or offers automatic installation if Python is not ready.
- Copies your selected sound to `~/.codex/music/codex-notify.*`.
- Backs up `~/.codex/config.toml`.
- Adds or updates Codex settings for task-complete notifications and approval-request hooks.
- Tests sound playback after installation.

On Windows, the generated config looks like this:

```toml
notify = ["pythonw.exe", "C:\\Users\\<user>\\.codex\\codex-notify.py"]

[tui]
notifications = false

[features]
codex_hooks = true

[[hooks.PermissionRequest]]
[[hooks.PermissionRequest.hooks]]
type = "command"
command = "pythonw.exe C:\\Users\\<user>\\.codex\\codex-notify.py approval"
timeout = 5
```

## Level 2: Manual Usage

```powershell
python app\install.py --sound C:\path\to\notification.mp3
python app\install.py --sound C:\path\to\notification.wav
```

Test:

```powershell
python app\codex-notify.py --test --sound app\music\universfield-new-notification-017-352293.wav
```

## Audio Support

- Windows: MP3, WAV, AIFF, M4A. No extra package required.
- macOS: formats supported by `afplay`.
- Linux: `paplay` or `aplay` for WAV; `ffplay`, `mpv`, `cvlc`, or `mpg123` for MP3.

## Example Sound

The included example sound is `New Notification 017` by Universfield from Pixabay.

Pixabay notification search: https://pixabay.com/sound-effects/search/notification/

Asset page: https://pixabay.com/es/sound-effects/new-notification-017-352293/
