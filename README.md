# codex-sound-notify

Codex islem bitince veya onay beklediginde kendi sectiginiz sesi caldirir.

## Seviye 1: Tek Dosya Ile Kurulum

Windows kullanicisi:

```text
Install-Windows.cmd
```

Bu dosyaya cift tiklayin. Script once Python'un hazir olup olmadigini kontrol eder. Python yoksa otomatik kurulum teklif eder, sonra size ses dosyasi sorar. Bos birakirsaniz repo icindeki ornek Pixabay sesi kurulur. MP3 veya WAV dosyasi yolu verebilirsiniz.

macOS kullanicisi:

```text
Install-macOS.command
```

Linux kullanicisi:

```text
Install-Linux.sh
```

## Script Ne Yapar?

- `~/.codex/codex-notify.py` dosyasini kurar.
- Python hazir degilse kurulum icin yonlendirir veya otomatik kurulum teklif eder.
- Sectiginiz sesi `~/.codex/music/codex-notify.*` olarak kopyalar.
- `~/.codex/config.toml` dosyasini yedekler.
- Codex config icine bitis bildirimi ve onay istegi hook ayarlarini ekler veya gunceller.
- Kurulum sonunda sesi test eder.

Windows icin olusan config su sekildedir:

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

## Seviye 2: Manuel Kullanim

```powershell
python app\install.py --sound C:\path\to\notification.mp3
python app\install.py --sound C:\path\to\notification.wav
```

Test:

```powershell
python app\codex-notify.py --test --sound app\music\universfield-new-notification-017-352293.wav
```

## Ses Destegi

- Windows: MP3, WAV, AIFF, M4A. Ek paket gerekmez.
- macOS: `afplay` tarafindan desteklenen formatlar.
- Linux: WAV icin `paplay` veya `aplay`; MP3 icin `ffplay`, `mpv`, `cvlc` veya `mpg123`.

## Ornek Ses

Ornek ses Pixabay uzerinden alinmistir: `New Notification 017` by Universfield.

Pixabay notification aramasi: https://pixabay.com/sound-effects/search/notification/

Varlik sayfasi: https://pixabay.com/es/sound-effects/new-notification-017-352293/
