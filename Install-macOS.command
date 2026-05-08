#!/bin/sh
cd "$(dirname "$0")" || exit 1

echo "Codex Notify Music - macOS Installer"
echo

detect_language() {
  case "${CODEX_NOTIFY_LANG:-${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}}" in
    tr*|TR*|turkish*|Turkish*) echo "tr" ;;
    *) echo "en" ;;
  esac
}

INSTALL_LANG="$(detect_language)"

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    if python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
      PYTHON_CMD="python3"
      return 0
    fi
  fi

  if command -v python >/dev/null 2>&1; then
    if python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
      PYTHON_CMD="python"
      return 0
    fi
  fi

  return 1
}

install_python() {
  if [ "$INSTALL_LANG" = "tr" ]; then
    echo "Python 3.10 veya daha yeni bir surum bulunamadi."
    echo "Bu kurulum icin Python 3.10 veya daha yeni bir surum gerekir."
    brew_prompt="Python'u Homebrew ile otomatik kurmak ister misiniz? [E/H]: "
    no_brew="Homebrew bulunamadi; otomatik kurulum yapilamiyor."
    manual_python="Python 3 kurun: https://www.python.org/downloads/"
    open_prompt="Indirme sayfasini acmak ister misiniz? [E/H]: "
  else
    echo "Python 3.10 or newer was not found."
    echo "This installer requires Python 3.10 or newer."
    brew_prompt="Install Python automatically with Homebrew? [Y/N]: "
    no_brew="Homebrew was not found; automatic installation is unavailable."
    manual_python="Install Python 3: https://www.python.org/downloads/"
    open_prompt="Open the download page? [Y/N]: "
  fi
  echo

  if command -v brew >/dev/null 2>&1; then
    printf "%s" "$brew_prompt"
    read answer
    case "$answer" in
      E|e|EVET|evet|Y|y|YES|yes)
        brew install python
        return $?
        ;;
    esac
  else
    echo "$no_brew"
  fi

  echo "$manual_python"
  if command -v open >/dev/null 2>&1; then
    printf "%s" "$open_prompt"
    read open_answer
    case "$open_answer" in
      E|e|EVET|evet|Y|y|YES|yes) open "https://www.python.org/downloads/" ;;
    esac
  fi
  return 1
}

if ! find_python; then
  install_python || exit 1
  find_python || exit 1
fi

"$PYTHON_CMD" app/install.py --interactive --language "$INSTALL_LANG"

echo
if [ "$INSTALL_LANG" = "tr" ]; then
  echo "Kapatmak icin Enter'a basin."
else
  echo "Press Enter to close."
fi
read _
