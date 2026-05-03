#!/bin/sh
cd "$(dirname "$0")" || exit 1

echo "Codex Notify Music - Linux Installer"
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
  printf "Python'u paket yoneticisi ile otomatik kurmak ister misiniz? [E/H]: "
  read answer
  case "$answer" in
    E|e|EVET|evet|Y|y|YES|yes) ;;
    *) return 1 ;;
  esac

  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y python3
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y python3
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -S --needed python
  elif command -v zypper >/dev/null 2>&1; then
    sudo zypper install -y python3
  else
    echo "Desteklenen paket yoneticisi bulunamadi."
    echo "Python 3 kurun: https://www.python.org/downloads/"
    return 1
  fi
}

if ! find_python; then
  install_python || exit 1
  find_python || exit 1
fi

"$PYTHON_CMD" app/install.py --interactive
