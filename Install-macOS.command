#!/bin/sh
cd "$(dirname "$0")" || exit 1

echo "Codex Notify Music - macOS Installer"
echo

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
  echo "Python 3.10 veya daha yeni bir surum bulunamadi."
  echo "Bu kurulum icin Python 3.10 veya daha yeni bir surum gerekir."
  echo

  if command -v brew >/dev/null 2>&1; then
    printf "Python'u Homebrew ile otomatik kurmak ister misiniz? [E/H]: "
    read answer
    case "$answer" in
      E|e|EVET|evet|Y|y|YES|yes)
        brew install python
        return $?
        ;;
    esac
  else
    echo "Homebrew bulunamadi; otomatik kurulum yapilamiyor."
  fi

  echo "Python 3 kurun: https://www.python.org/downloads/"
  if command -v open >/dev/null 2>&1; then
    printf "Indirme sayfasini acmak ister misiniz? [E/H]: "
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

"$PYTHON_CMD" app/install.py --interactive

echo
echo "Kapatmak icin Enter'a basin."
read _
