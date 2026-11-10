"""Local launcher for separate MELD Graph and SWANe workflows (Python 3.10+)."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'local'
CONFIG = STATE / 'config.json'


def run(command, cwd=None, capture=False):
    print('+', ' '.join(map(str, command)), flush=True)
    return subprocess.run(list(map(str, command)), cwd=cwd, check=True,
                          text=True, capture_output=capture)


def linux():
    if platform.system() != 'Linux':
        raise ValueError('Run this command inside Ubuntu / WSL Ubuntu.')


def load():
    if not CONFIG.is_file():
        raise ValueError('Run configure first. See README.md.')
    return json.loads(CONFIG.read_text())


def configure(args):
    release = Path(args.meld_release).expanduser().resolve()
    data = Path(args.data).expanduser().resolve()
    if not (release / 'compose.yml').is_file():
        raise ValueError('Expected the official extracted MELD release with compose.yml.')
    if not re.fullmatch(r'[0-9]+(?:\.[0-9]+){1,3}', args.swane_version):
        raise ValueError('Provide an exact numeric SWANe release version.')
    STATE.mkdir(exist_ok=True)
    data.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps({'meld_release': str(release), 'data': str(data),
                                 'swane_version': args.swane_version}, indent=2))
    print('Configuration saved locally. No application has been installed yet.')


def compose(config):
    release = Path(config['meld_release'])
    override = {'services': {'meld_graph': {'volumes': [
        {'type': 'bind', 'source': config['data'], 'target': '/data'}]}}}
    if config.get('meld_image_digest'):
        override['services']['meld_graph']['image'] = config['meld_image_digest']
    path = STATE / 'compose.local.json'
    path.write_text(json.dumps(override, indent=2))
    os.environ['DOCKER_USER'] = f'{os.getuid()}:{os.getgid()}'
    return ['docker', 'compose', '--project-directory', str(release), '-f',
            str(release / 'compose.yml'), '-f', str(path)]


def licenses(config):
    for name in ('license.txt', 'meld_license.txt'):
        p = Path(config['meld_release']) / name
        if not p.is_file() or not p.stat().st_size:
            raise ValueError(f'Obtain your own {name} and place it in the MELD release folder.')


def doctor(args):
    checks = {'linux': platform.system() == 'Linux',
              'python_3_10_plus': sys.version_info >= (3, 10),
              'machine': platform.machine(),
              'display_available': bool(os.getenv('DISPLAY') or os.getenv('WAYLAND_DISPLAY')),
              'docker_command': bool(shutil.which('docker')),
              'dcm2niix': bool(shutil.which('dcm2niix')),
              'free_gib_here': round(shutil.disk_usage(ROOT).free / 2**30, 1)}
    if platform.system() == 'Linux':
        mem = Path('/proc/meminfo')
        if mem.exists():
            checks['ram_gib'] = round(int(re.search(r'MemTotal:\s+(\d+)', mem.read_text())[1]) / 2**20, 1)
    for name, cmd in [('docker_daemon', ['docker', 'info']),
                      ('compose_plugin', ['docker', 'compose', 'version'])]:
        try:
            checks[name] = subprocess.run(cmd, capture_output=True, timeout=20).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            checks[name] = False
    checks['configured'] = CONFIG.exists()
    checks['full_analysis_test'] = 'NOT RUN by doctor'
    STATE.mkdir(exist_ok=True)
    (STATE / 'doctor.json').write_text(json.dumps(checks, indent=2))
    print(json.dumps(checks, indent=2))
    return 0 if all(checks[k] for k in ('linux', 'python_3_10_plus', 'docker_daemon', 'compose_plugin')) else 2


def swane_python():
    return STATE / 'swane-env' / 'bin' / 'python'


def action(args):
    linux()
    config = load()
    if args.command == 'install-swane':
        run([sys.executable, '-m', 'venv', STATE / 'swane-env'])
        run([swane_python(), '-m', 'pip', 'install', f"swane=={config['swane_version']}"])
        result = run([swane_python(), '-m', 'pip', 'freeze'], capture=True)
        (STATE / 'swane-installed.txt').write_text(result.stdout)
        print('Python package installed. External imaging tools and GUI still require verification.')
    elif args.command == 'swane-smoke':
        run([swane_python(), '-m', 'pip', 'check'])
        run([swane_python(), '-c', 'import swane; print(swane.__file__)'])
        print('Package checks passed. This does not test a SWANe analysis or GUI.')
    elif args.command == 'open-swane':
        if not (os.getenv('DISPLAY') or os.getenv('WAYLAND_DISPLAY')):
            raise ValueError('No GUI display detected. Use Ubuntu desktop or configure WSLg.')
        run([swane_python(), '-m', 'swane'])
    else:
        licenses(config)
        if args.command != 'install-meld' and not config.get('meld_image_digest'):
            raise ValueError('Run install-meld first to record the container digest.')
        base = compose(config)
        if args.command == 'install-meld':
            result = run(base + ['config', '--format', 'json'], capture=True)
            model = json.loads(result.stdout)
            service = model['services']['meld_graph']
            if service.get('deploy', {}).get('resources', {}).get('reservations', {}).get('devices') or service.get('gpus'):
                raise ValueError('For CPU mode remove the GPU reservation from your local release compose.yml as documented upstream.')
            image = service['image']
            run(base + ['pull', 'meld_graph'])
            digest = json.loads(run(['docker', 'image', 'inspect', image], capture=True).stdout)[0].get('RepoDigests', [])
            if not digest:
                raise ValueError('Cannot record an immutable registry digest; setup stopped.')
            config['meld_image_digest'] = digest[0]
            CONFIG.write_text(json.dumps(config, indent=2))
            print('MELD image installed and its digest recorded. Next run prepare-meld.')
        elif args.command == 'prepare-meld':
            run(base + ['run', '--rm', 'meld_graph', 'python',
                        'scripts/new_patient_pipeline/prepare_classifier.py'])
        elif args.command == 'test-meld':
            report = STATE / 'meld-test.json'
            # Clear previous success before executing a new test.
            report.write_text(json.dumps({'status': 'RUNNING', 'utc': dt.datetime.now(dt.timezone.utc).isoformat()}))
            try:
                run(base + ['run', '--rm', 'meld_graph', 'pytest', '-s'])
            except (subprocess.CalledProcessError, OSError):
                report.write_text(json.dumps({'status': 'FAILED'}))
                raise
            report.write_text(json.dumps({'status': 'PASSED', 'scope': 'upstream MELD pytest; not a SWANe test',
                                         'utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                                         'image': config.get('meld_image_digest', 'UNPINNED')}))
        elif args.command == 'run-meld':
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', args.subject):
                raise ValueError('Subject ID must use letters, numbers, underscores or hyphens.')
            run(base + ['run', '--rm', 'meld_graph', 'python',
                        'scripts/new_patient_pipeline/new_pt_pipeline.py', '-id', args.subject])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('configure')
    p.add_argument('--meld-release', required=True)
    p.add_argument('--data', required=True)
    p.add_argument('--swane-version', default='0.2.1.1')
    sub.add_parser('doctor')
    for name in ('install-swane', 'swane-smoke', 'open-swane', 'install-meld', 'prepare-meld', 'test-meld'):
        sub.add_parser(name)
    p = sub.add_parser('run-meld')
    p.add_argument('--subject', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'configure':
            configure(args)
        elif args.command == 'doctor':
            return doctor(args)
        else:
            action(args)
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
