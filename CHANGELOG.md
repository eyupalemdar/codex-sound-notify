# Changelog

All notable changes to this project are documented here.

## Unreleased

### Added

- Added Codex 0.129+ compatibility for the hooks feature flag rename from `[features].codex_hooks` to `[features].hooks`.
- Added automatic migration for existing Codex 0.128-era installs so rerunning the installer replaces stale hook feature keys while preserving older Codex compatibility.
- Added `--hooks-feature-key {auto,hooks,codex_hooks}` for manual override when the installed Codex CLI cannot be detected correctly.
- Added `--language {auto,en,tr}` and `CODEX_NOTIFY_LANG` support. Auto defaults to English except on Turkish locales.

### Changed

- Updated README examples to use the canonical Codex 0.129+ `[features].hooks = true` setting.
- Installer output now reports the selected hooks feature key.
- Localized the Windows, macOS, Linux, and Python installer prompts so non-Turkish systems no longer see Turkish by default.

### Fixed

- Fixed Python installer language auto-detection on Windows so a non-Turkish `LANG` environment value does not mask a Turkish OS locale.
- Made the post-install Codex hook review instructions explicit and localized.
