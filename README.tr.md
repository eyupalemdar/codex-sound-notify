# codex-sound-notify

Codex işlem bitince veya onay beklediğinde kendi seçtiğiniz sesi çaldırır.

[English README](README.md)

## Seviye 1: Tek Dosya İle Kurulum

Windows kullanıcıları:

```text
Install-Windows.cmd
```

Bu dosyaya çift tıklayın. Script önce Python'un hazır olup olmadığını kontrol eder. Python yoksa veya sürümü eskiyse otomatik kurulum teklif eder, sonra size ses dosyası sorar. Boş bırakırsanız repo içindeki örnek Pixabay sesi kurulur. MP3 veya WAV dosyası yolu verebilirsiniz.

macOS kullanıcıları:

```text
Install-macOS.command
```

Linux kullanıcıları:

```text
Install-Linux.sh
```

## Script Ne Yapar?

- `~/.codex/codex-notify.py` dosyasını kurar.
- Python hazır değilse kurulum için yönlendirir veya otomatik kurulum teklif eder.
- Seçtiğiniz sesi `~/.codex/music/codex-notify.*` olarak kopyalar.
- `~/.codex/config.toml` dosyasını yedekler.
- Codex config içine işlem bitiş bildirimi ve onay isteği hook ayarlarını ekler veya günceller.
- Kurulum sonunda sesi test eder.
- Python başlatıcısını makineye özel tam yol olarak değil, PATH üzerinden çözülen komut olarak yazar.

Windows için oluşan config şu şekildedir:

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

## Seviye 2: Manuel Kullanım

```powershell
python app\install.py --sound C:\path\to\notification.mp3
python app\install.py --sound C:\path\to\notification.wav
```

Test:

```powershell
python app\codex-notify.py --test --sound app\music\universfield-new-notification-017-352293.wav
```

## Ses Desteği

- Windows: MP3, WAV, AIFF, M4A. Ek paket gerekmez.
- macOS: `afplay` tarafından desteklenen formatlar.
- Linux: WAV için `paplay` veya `aplay`; MP3 için `ffplay`, `mpv`, `cvlc` veya `mpg123`.

## Örnek Ses

Örnek ses Pixabay üzerinden alınmıştır: `New Notification 017` by Universfield.

Pixabay notification araması: https://pixabay.com/sound-effects/search/notification/

Varlık sayfası: https://pixabay.com/es/sound-effects/new-notification-017-352293/
