#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
candidates=("${NEURO_PYTHON:-}" "$PWD/local/swane-env/bin/python" python3 python3.12 python3.11 python3.10 "$HOME/miniconda3/bin/python" "$HOME/miniforge3/bin/python")
python=""
for candidate in "${candidates[@]}"; do
  if [[ -n "$candidate" ]] && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    python="$candidate"; break
  fi
done
if [[ -z "$python" ]]; then
  echo 'Python >=3.10 is required. Install a separate supported Python, then set NEURO_PYTHON=/path/to/python.'
  exit 2
fi
if [[ $# -gt 0 ]]; then exec "$python" neuro_easy.py "$@"; fi
echo 'Neuro Easy: MELD Graph and SWANe'
select choice in 'Check this computer' 'Install SWANe Python package' 'Install FSL for T1 reference' 'Check SWANe package' 'Check SWANe dependencies' 'Open SWANe' 'Run SWANe T1 reference' 'Install MELD image' 'Prepare MELD model/test data' 'Run MELD verification' 'Run MELD subject' 'Quit'; do
  case "$REPLY" in
    1) "$python" neuro_easy.py doctor ;;
    2) "$python" neuro_easy.py install-swane ;;
    3) echo 'Read https://fsl.fmrib.ox.ac.uk/fsl/docs/license.html'
       read -r -p 'Type ACCEPT if you personally accept this licence: ' acceptance
       if [[ "$acceptance" == ACCEPT ]]; then
         "$python" neuro_easy.py install-fsl --accept-fsl-license
       else echo 'FSL licence not accepted; installation skipped.'; fi ;;
    4) "$python" neuro_easy.py swane-smoke ;;
    5) "$python" neuro_easy.py swane-dependencies ;;
    6) "$python" neuro_easy.py open-swane ;;
    7) read -r -p 'DICOM series directory: ' dicom
       read -r -p 'Local output directory: ' output
       "$python" neuro_easy.py validate-swane-t1 --dicom "$dicom" --output "$output" ;;
    8) "$python" neuro_easy.py install-meld ;;
    9) "$python" neuro_easy.py prepare-meld ;;
    10) "$python" neuro_easy.py test-meld ;;
    11) read -r -p 'Subject ID: ' subject; "$python" neuro_easy.py run-meld --subject "$subject" ;;
    12) exit 0 ;;
    *) echo 'Choose a number from 1 to 12.'; continue ;;
  esac || echo 'Step failed. Read the error above and local/logs before continuing.'
done
