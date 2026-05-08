# codex-sound-notify

Codex işlem bitince veya onay beklediğinde kendi seçtiğiniz sesi çaldırır.

[English README](README.md)

[Changelog](CHANGELOG.md)

## Seviye 1: Tek Dosya İle Kurulum

Windows kullanıcıları:

```text
Install-Windows.cmd
```

Bu dosyaya çift tıklayın. Script önce Python'un hazır olup olmadığını kontrol eder. Python yoksa veya sürümü eskiyse otomatik kurulum teklif eder, sonra işlem sonu ve onay isteği ses dosyalarını sorar. Boş bırakırsanız repo içindeki örnek Pixabay sesi kullanılır. MP3 veya WAV dosyası yolu verebilirsiniz.

macOS kullanıcıları:

```text
Install-macOS.command
```

Linux kullanıcıları:

```text
Install-Linux.sh
```

## Script Ne Yapar?

- Codex home klasörünü `CODEX_HOME`, mevcut `config.toml` veya platform kullanıcı home bilgisi üzerinden bulur.
- `codex-notify.py` dosyasını bulunan Codex home klasörüne kurar.
- Python hazır değilse kurulum için yönlendirir veya otomatik kurulum teklif eder.
- Seçtiğiniz sesleri `<codex-home>/music/codex-notify-done.*` ve `<codex-home>/music/codex-notify-approval.*` olarak kopyalar.
- `<codex-home>/config.toml` dosyasını yedekler.
- Codex config içine işlem bitiş bildirimi ve onay isteği hook ayarlarını ekler veya günceller.
- Kurulu Codex sürümündeki hook feature anahtarını algılar (`hooks` Codex 0.129+ için, `codex_hooks` eski 0.128 dönemi sürümler için).
- Kurulum metinlerini varsayılan olarak İngilizce kullanır; yalnızca Türkçe locale algılanırsa Türkçe açılır.
- Kurulum sonunda sesi test eder.
- Kurulu script yolunu ve Python başlatıcısını bulunan hedefe göre yazar; makineye özel sabit Python yolu kullanmaz.

Oluşan config, mevcut platformda PATH içinde bulunan ilk uygun komutu kullanır:

- Windows: `pyw.exe -3`, `pythonw.exe`, `py.exe -3`, sonra `python.exe`
- macOS/Linux: `python3`, sonra `python`

Windows için oluşan config şu şekilde olabilir:

```toml
notify = ["pyw.exe", "-3", "C:\\Users\\<user>\\.codex\\codex-notify.py"]

[tui]
notifications = false

[features]
hooks = true

[[hooks.PermissionRequest]]
[[hooks.PermissionRequest.hooks]]
type = "command"
command = "pyw.exe -3 C:\\Users\\<user>\\.codex\\codex-notify.py approval"
timeout = 5
```

macOS/Linux için şu şekilde olabilir:

```toml
notify = ["python3", "/Users/<user>/.codex/codex-notify.py"]

[tui]
notifications = false

[features]
hooks = true

[[hooks.PermissionRequest]]
[[hooks.PermissionRequest.hooks]]
type = "command"
command = "python3 /Users/<user>/.codex/codex-notify.py approval"
timeout = 5
```

Eski Codex sürümleri bunun yerine `codex_hooks = true` kullanır. Installer kurulu CLI'yi otomatik algılar ve Codex 0.128 üzerinde kurulmuş sistemler 0.129'a geçince eski anahtarı temizleyerek sorunsuz günceller.

Codex 0.129+ yeni kurulan hook'ları bir kez incelemenizi isteyebilir. Codex `1 hook needs review before it can run` derse Codex içinde `/hooks` açıp `codex-notify.py` komutunu onaylayın.

## Seviye 2: Manuel Kullanım

```powershell
python app\install.py --sound C:\path\to\notification.mp3
python app\install.py --done-sound C:\path\to\done.wav --approval-sound C:\path\to\approval.wav
python app\install.py --codex-home C:\Users\you\.codex
python app\install.py --hooks-feature-key codex_hooks
python app\install.py --language en
```

Dil seçimi varsayılan olarak `auto` çalışır. Auto, OS veya environment locale değeri `tr` ile başlıyorsa Türkçe; diğer tüm locale değerlerinde İngilizce kullanır. Dili `--language en`, `--language tr` veya `CODEX_NOTIFY_LANG=en` ile elle sabitleyebilirsiniz.

Test:

```powershell
python app\codex-notify.py done --test --sound app\music\universfield-new-notification-017-352293.wav
python app\codex-notify.py approval --test --sound app\music\universfield-new-notification-017-352293.wav
```

## Ses Desteği

- Windows: MP3, WAV, AIFF, M4A. Ek paket gerekmez.
- macOS: `afplay` tarafından desteklenen formatlar.
- Linux: WAV için `paplay` veya `aplay`; MP3 için `ffplay`, `mpv`, `cvlc` veya `mpg123`.

## Örnek Ses

Örnek ses Pixabay üzerinden alınmıştır: `New Notification 017` by Universfield.

Pixabay notification araması: https://pixabay.com/sound-effects/search/notification/

Varlık sayfası: https://pixabay.com/es/sound-effects/new-notification-017-352293/
