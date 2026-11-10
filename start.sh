#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
echo 'Neuro Easy: MELD Graph and SWANe'
select choice in 'Check this computer' 'Install SWANe Python package' 'Check SWANe package' 'Open SWANe' 'Install MELD image' 'Prepare MELD model/test data' 'Run MELD verification' 'Quit'; do
  case "$REPLY" in
    1) python3 neuro_easy.py doctor ;;
    2) python3 neuro_easy.py install-swane ;;
    3) python3 neuro_easy.py swane-smoke ;;
    4) python3 neuro_easy.py open-swane ;;
    5) python3 neuro_easy.py install-meld ;;
    6) python3 neuro_easy.py prepare-meld ;;
    7) python3 neuro_easy.py test-meld ;;
    8) exit 0 ;;
    *) echo 'Choose a number from 1 to 8.'; continue ;;
  esac || echo 'Step failed. Read the error above before continuing.'
done
