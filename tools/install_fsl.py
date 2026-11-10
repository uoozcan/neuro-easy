"""Install only the FSL components used by SWANe's T1 reference workflow."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'local'
MANIFEST = 'https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/releases/manifest.json'
CHANNEL = 'https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/public/'
RELEASE = '6.0.7.8'
PACKAGES = ('fsl-bet2', 'fsl-flirt', 'fsl-avwutils', 'fsl-data_standard', 'python')
LICENCE = 'https://fsl.fmrib.ox.ac.uk/fsl/docs/license.html'


def read(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read().decode()


def finish(prefix):
    records = [json.loads(p.read_text()) for p in (prefix / 'conda-meta').glob('*.json')]
    tools = sorted({Path(f).name for r in records if r['name'].startswith('fsl-')
                    for f in r.get('files', []) if f.startswith('bin/')
                    and (prefix / f).is_file() and os.access(prefix / f, os.X_OK)})
    env = dict(os.environ, FSLDIR=str(prefix), PREFIX=str(prefix), FSL_CREATE_WRAPPER_SCRIPTS='1')
    subprocess.run([str(prefix / 'bin/createFSLWrapper')] + tools, env=env, check=True)
    required = ('bet', 'robustfov', 'fslmaths', 'fslorient', 'fslswapdim')
    missing = [tool for tool in required if not (prefix / 'share/fsl/bin' / tool).is_file()]
    if missing:
        raise RuntimeError('Missing FSL wrappers: ' + ', '.join(missing))
    (prefix / 'etc/fslversion').write_text(RELEASE + '\n')
    print('Partial FSL ' + RELEASE + ' installation configured for SWANe T1 reference preprocessing.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--conda', default=shutil.which('conda') or str(Path.home() / 'miniconda3/bin/conda'))
    parser.add_argument('--accept-fsl-license', action='store_true')
    parser.add_argument('--finish-existing', action='store_true',
                        help='Finish a completed installation without solving/downloading again.')
    args = parser.parse_args()
    if not args.accept_fsl_license:
        print('Read and accept the FSL licence yourself: ' + LICENCE)
        print('Then rerun with --accept-fsl-license. No licence is accepted automatically.')
        return 2
    if not Path(args.conda).is_file():
        parser.error('Provide --conda /path/to/conda. Install Miniforge from its official source if needed.')
    missing = [tool for tool in ('bc', 'dc', 'tcsh') if not shutil.which(tool)]
    if missing:
        raise RuntimeError('Install Ubuntu prerequisites first: sudo apt install bc dc tcsh')
    STATE.mkdir(exist_ok=True)
    if shutil.disk_usage(STATE).free < 5 * 2**30:
        raise RuntimeError('Need at least 5 GiB free for this partial FSL installation.')
    prefix = STATE / 'fsl-env'
    marker = STATE / 'fsl-provenance.json'
    if not args.finish_existing:
        manifest = json.loads(read(MANIFEST))
        build = next(b for b in manifest['versions'][RELEASE] if b['platform'] == 'linux-64')
        environment = read(build['environment'])
        found = dict(re.findall(r'^\s*-\s*([A-Za-z0-9_.-]+)\s+(\S+)\s*$', environment, re.MULTILINE))
        specs = [name + '=' + found[name] for name in PACKAGES] + ['fsl-installer=3.21.0']
        specfile = STATE / 'fsl-specs.txt'
        specfile.write_text('\n'.join(specs) + '\n')
        if prefix.exists() and not marker.is_file():
            raise RuntimeError('Existing fsl-env is not marked as ours. Inspect it before continuing.')
        marker.write_text(json.dumps({'release': RELEASE, 'environment': build['environment'],
                         'manifest_sha256': hashlib.sha256(environment.encode()).hexdigest(),
                         'specs': specs, 'scope': 'T1 reference components only',
                         'licence': LICENCE, 'licence_accepted': True}, indent=2))
        command = 'install' if (prefix / 'conda-meta/history').is_file() else 'create'
        subprocess.run([args.conda, command, '-y', '--solver', 'libmamba', '-p', str(prefix),
                        '--override-channels', '--strict-channel-priority', '-c', CHANNEL,
                        '-c', 'conda-forge', '--file', str(specfile)], check=True)
    elif not marker.is_file() or not (prefix / 'conda-meta/history').is_file():
        raise RuntimeError('No completed project FSL installation is available to finish.')
    finish(prefix)
    result = subprocess.run([args.conda, 'list', '-p', str(prefix), '--explicit'],
                            check=True, text=True, capture_output=True)
    (STATE / 'fsl-explicit.txt').write_text(result.stdout)
    return 0


if __name__ == '__main__':
    sys.exit(main())
