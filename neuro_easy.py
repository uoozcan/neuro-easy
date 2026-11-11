"""Local launcher for independent MELD Graph and SWANe workflows (Python 3.10+)."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'local'
CONFIG = STATE / 'config.json'
SWANE_VERSION = '0.2.1.1'


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def run(command, cwd=None, capture=False):
    command = list(map(str, command))
    print('+', ' '.join(command), flush=True)
    logs = STATE / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    log = logs / (dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.log')
    with log.open('w') as output:
        output.write(json.dumps({'argv': command, 'cwd': str(cwd or ROOT), 'utc': now()}) + '\n')
        output.flush()
        if capture:
            result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
            output.write(result.stdout + result.stderr)
            if result.returncode:
                raise subprocess.CalledProcessError(result.returncode, command,
                                                    result.stdout, result.stderr)
            return result
        process = subprocess.Popen(command, cwd=cwd, text=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            for line in process.stdout:
                print(line, end='', flush=True)
                output.write(line)
                output.flush()
            code = process.wait()
        except KeyboardInterrupt:
            os.killpg(process.pid, signal.SIGINT)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            raise
        finally:
            process.stdout.close()
        if code:
            raise subprocess.CalledProcessError(code, command)
        return subprocess.CompletedProcess(command, code)


def linux():
    if platform.system() != 'Linux':
        raise ValueError('Run this command inside Ubuntu / WSL Ubuntu.')


def load(required=True):
    if not CONFIG.is_file():
        if required:
            raise ValueError('Run configure --meld-release PATH first. See README.md.')
        return {'swane_version': SWANE_VERSION}
    return json.loads(CONFIG.read_text())


def configure(args):
    config = load(required=False)
    if args.swane_version:
        if not re.fullmatch(r'[0-9]+(?:\.[0-9]+){1,3}', args.swane_version):
            raise ValueError('Provide an exact numeric SWANe release version.')
        config['swane_version'] = args.swane_version
    if args.meld_release:
        release = Path(args.meld_release).expanduser().resolve()
        if not (release / 'compose.yml').is_file():
            raise ValueError('Expected the official extracted MELD release with compose.yml.')
        if config.get('meld_release') != str(release):
            config.pop('meld_image_digest', None)
        config['meld_release'] = str(release)
    if args.data:
        data = Path(args.data).expanduser().resolve()
        data.mkdir(parents=True, exist_ok=True)
        config['data'] = str(data)
    if args.fsl_dir:
        fsl = Path(args.fsl_dir).expanduser().resolve()
        if not (fsl / 'etc/fslversion').is_file():
            raise ValueError('FSL directory must contain etc/fslversion.')
        config['fsl_dir'] = str(fsl)
    if args.freesurfer_dir:
        home = Path(args.freesurfer_dir).expanduser().resolve()
        if not (home / 'SetUpFreeSurfer.sh').is_file():
            raise ValueError('FreeSurfer directory must contain its official SetUpFreeSurfer.sh.')
        config['freesurfer_dir'] = str(home)
    if 'meld_release' in config and 'data' not in config:
        data = STATE / 'meld-data'
        data.mkdir(parents=True, exist_ok=True)
        config['data'] = str(data)
    save(CONFIG, config)
    print('Configuration saved locally. SWANe and MELD are configured independently.')


def runtime_environment(config, include_freesurfer=False):
    if include_freesurfer and config.get('freesurfer_dir'):
        home = Path(config['freesurfer_dir'])
        if not (home / 'SetUpFreeSurfer.sh').is_file():
            raise ValueError('Configured FreeSurfer setup is absent; check --freesurfer-dir.')
        environment = dict(os.environ, FREESURFER_HOME=str(home))
        # Structural setup must not create/modify a MATLAB startup file.
        environment.setdefault('NO_FSFAST', '1')
        fsl_home = Path(config.get('fsl_dir', STATE / 'fsl-env'))
        if (fsl_home / 'etc/fslversion').is_file():
            environment['FSLDIR'] = str(fsl_home)
        licence = Path(config.get('meld_release', STATE / 'meld-release')) / 'license.txt'
        if licence.is_file():
            environment.setdefault('FS_LICENSE', str(licence))
        subjects = STATE / 'swane-freesurfer-subjects'
        subjects.mkdir(parents=True, exist_ok=True)
        environment.setdefault('SUBJECTS_DIR', str(subjects))
        # Read the vendor setup in a child shell; never edit the user's shell profile.
        result = subprocess.run(
            ['bash', '-c', 'source "$FREESURFER_HOME/SetUpFreeSurfer.sh" >&2 && env -0'],
            env=environment, capture_output=True)
        if result.returncode:
            raise ValueError('Official FreeSurfer environment setup failed; inspect it in a dedicated terminal.')
        os.environ.update(os.fsdecode(item).split('=', 1) for item in result.stdout.split(b'\0')
                          if b'=' in item)
    tools = STATE / 'tools/docker'
    if (tools / 'docker').is_file():
        os.environ['PATH'] = str(tools) + os.pathsep + os.environ.get('PATH', '')
        os.environ.setdefault('DOCKER_CONFIG', str(STATE / 'docker-config'))
        os.environ.setdefault('DOCKER_HOST', 'unix://' + str(STATE / 'docker.sock'))
    fsl = Path(config.get('fsl_dir', STATE / 'fsl-env'))
    if (fsl / 'etc/fslversion').is_file():
        os.environ['FSLDIR'] = str(fsl)
        os.environ['FSLOUTPUTTYPE'] = 'NIFTI_GZ'
        # FSL wrappers keep its Python out of the SWANe interpreter's PATH.
        os.environ['PATH'] = str(fsl / 'share/fsl/bin') + os.pathsep + os.environ.get('PATH', '')
    if swane_python().is_file():
        os.environ['PATH'] = str(swane_python().parent) + os.pathsep + os.environ.get('PATH', '')


def compose(config):
    if not config.get('meld_release') or not config.get('data'):
        raise ValueError('Configure --meld-release PATH --data PATH before MELD actions.')
    release = Path(config['meld_release'])
    os.environ['DOCKER_USER'] = f'{os.getuid()}:{os.getgid()}'
    base = ['docker', 'compose', '--project-directory', str(release),
            '-f', str(release / 'compose.yml')]
    # Normalize using Compose itself so relative secrets/mounts resolve upstream.
    model = json.loads(run(base + ['config', '--format', 'json'], capture=True).stdout)
    service = model['services']['meld_graph']
    service.pop('gpus', None)
    reservations = service.get('deploy', {}).get('resources', {}).get('reservations', {})
    reservations.pop('devices', None)
    volumes = [v for v in service.get('volumes', []) if v.get('target') != '/data']
    volumes.append({'type': 'bind', 'source': config['data'], 'target': '/data'})
    service['volumes'] = volumes
    if config.get('meld_image_digest'):
        service['image'] = config['meld_image_digest']
    # Keep this invocation's mount/image snapshot stable during long analyses.
    path = STATE / 'runs' / uuid.uuid4().hex / 'compose.cpu.json'
    save(path, model)
    # A single normalized file avoids sequence merging retaining a GPU request.
    return ['docker', 'compose', '--project-directory', str(release), '-f', str(path)]


def license_syntax(name, content):
    # Syntax only: personal registration and an operational upstream check are still required.
    if not content.strip():
        raise ValueError(f'{name} is empty. Obtain your personal licence from upstream.')
    if name == 'meld_license.txt':
        match = re.search(r'License\s*ID[:\s]*([0-9]+)', content, re.IGNORECASE)
        if not match or len(match.group(1)) != 6:
            raise ValueError('meld_license.txt does not contain the six-digit License ID required by this MELD release.')
    elif name == 'license.txt':
        tokens = ' '.join(line for line in content.splitlines()
                          if not line.lstrip().startswith('#')).split()
        if len(tokens) < 4 or '@' not in tokens[0] or not tokens[1].isdigit():
            raise ValueError('license.txt does not have the expected FreeSurfer licence structure.')


def licenses(config):
    for name in ('license.txt', 'meld_license.txt'):
        p = Path(config['meld_release']) / name
        if not p.is_file():
            raise ValueError(f'Obtain your own {name} and place it in the MELD release folder.')
        if p.stat().st_size > 1024 * 1024:
            raise ValueError(f'{name} is unexpectedly large; choose the licence text file.')
        license_syntax(name, p.read_text())


def import_licenses(args, config):
    import uuid
    if not config.get('meld_release'):
        raise ValueError('Configure the MELD release folder first.')
    candidates = [('license.txt', args.freesurfer), ('meld_license.txt', args.meld)]
    candidates = [(name, Path(path).expanduser().resolve()) for name, path in candidates if path]
    if not candidates:
        raise ValueError('Provide --freesurfer PATH and/or --meld PATH; never paste licence contents.')
    prepared = []
    for name, source in candidates:
        if not source.is_file() or source.stat().st_size > 1024 * 1024:
            raise ValueError(f'Choose the personal licence text file for {name}.')
        content = source.read_text(encoding='utf-8-sig').encode('utf-8')
        license_syntax(name, content.decode('utf-8'))
        destination = Path(config['meld_release']) / name
        if destination.is_symlink():
            raise ValueError(f'Refusing to replace a symbolic link named {name}.')
        prepared.append((name, destination, content))
    # Validate every supplied file before modifying any installed licence.
    for name, destination, content in prepared:
        if destination.exists() and destination.read_bytes() != content:
            backups = STATE / 'license-backups'
            backups.mkdir(parents=True, exist_ok=True)
            backup = backups / (uuid.uuid4().hex + '-' + name)
            fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(destination.read_bytes())
        temporary = destination.with_name('.neuro-easy-' + uuid.uuid4().hex + '.tmp')
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(destination)
        print(f'Installed personal {name} locally; contents were not logged.')
    print('File syntax checked only. Run MELD preparation and upstream verification next.')


def license_status(config):
    report = {'scope': 'File syntax only; does not establish licence validity or analysis success.',
              'files': {}, 'registration': {
                  'freesurfer': 'https://surfer.nmr.mgh.harvard.edu/registration.html',
                  'meld': 'https://docs.google.com/forms/d/e/1FAIpQLSdocMWtxbmh9T7Sv8NT4f0Kpev-tmRI-kngDhUeBF9VcZXcfg/viewform'}}
    for name in ('license.txt', 'meld_license.txt'):
        p = Path(config.get('meld_release', STATE / 'meld-release')) / name
        if not p.is_file():
            report['files'][name] = 'MISSING'
            continue
        try:
            if p.stat().st_size > 1024 * 1024:
                raise ValueError('Unexpected file size.')
            license_syntax(name, p.read_text(encoding='utf-8-sig'))
            report['files'][name] = 'SYNTAX_OK'
        except (ValueError, OSError):
            report['files'][name] = 'INVALID_OR_UNREADABLE'
    save(STATE / 'license-status.json', report)
    print(json.dumps(report, indent=2))
    return 0 if all(v == 'SYNTAX_OK' for v in report['files'].values()) else 2


def disk_info(path):
    path = Path(path)
    while not path.exists() and path != path.parent:
        path = path.parent
    return {'path': str(path), 'free_gib': round(shutil.disk_usage(path).free / 2**30, 1)}


def require_space(path, minimum):
    info = disk_info(path)
    if info['free_gib'] < minimum:
        raise ValueError(f"Need {minimum} GiB free at {info['path']}; found {info['free_gib']} GiB.")
    return info


def probe(command):
    try:
        p = subprocess.run(command, capture_output=True, text=True, timeout=30)
        return p.returncode == 0, p.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return False, ''


def swane_python():
    return STATE / 'swane-env' / 'bin' / 'python'


def dependency_report():
    if not swane_python().is_file():
        return {'error': 'Run install-swane first.'}
    script = """
import json
from swane.utils.DependencyManager import DependencyManager
result = {}
for name in ('dcm2niix', 'fsl', 'freesurfer', 'graphviz'):
    value = getattr(DependencyManager, 'check_' + name)()
    result[name] = {'state': value.state.name, 'detail': value.label}
print(json.dumps(result))
"""
    result = run([swane_python(), '-c', script], capture=True)
    # Nipype may emit informational messages before the final JSON line.
    report = json.loads(result.stdout.strip().splitlines()[-1])
    missing = [tool for tool in ('dc', 'bc', 'bet', 'robustfov', 'fslmaths',
               'fslorient', 'fslswapdim') if not shutil.which(tool)]
    report['t1_runtime'] = {'state': 'MISSING' if missing else 'DETECTED',
                            'missing_commands': missing,
                            'detail': 'Install bc and dc with apt; install the partial FSL environment.'}
    return report


def ram_gib():
    p = Path('/proc/meminfo')
    if p.exists():
        return round(int(re.search(r'MemTotal:\s+(\d+)', p.read_text())[1]) / 2**20, 1)
    return 0


def docker_storage():
    ok, value = probe(['docker', 'info', '--format', '{{.DockerRootDir}}'])
    if not ok or not value or not Path(value).is_dir():
        raise ValueError('Cannot check Docker storage locally. Run docker info and check space on its daemon host.')
    return Path(value)


def doctor(args):
    config = load(required=False)
    runtime_environment(config, include_freesurfer=args.scope in ('swane-gui', 'swane-analysis', 'all'))
    checks = {'linux': platform.system() == 'Linux',
              'python_3_10_plus': sys.version_info >= (3, 10),
              'machine': platform.machine(), 'ram_gib': ram_gib(),
              'display_available': bool(os.getenv('DISPLAY') or os.getenv('WAYLAND_DISPLAY')),
              'environment_disk': disk_info(STATE),
              'data_disk': disk_info(config.get('data', STATE)),
              'swane_package': probe([str(swane_python()), '-c', 'import swane'])[0],
              'docker_daemon': probe(['docker', 'info'])[0],
              'compose_plugin': probe(['docker', 'compose', 'version'])[0],
              'meld_configured': bool(config.get('meld_release')),
              'full_analysis_test': 'NOT RUN by doctor'}
    if 'microsoft' in platform.release().lower():
        checks['wsl_host_disks'] = {str(p): disk_info(p) for p in (Path('/mnt/c'), Path('/mnt/d')) if p.is_dir()}
        checks['wsl_storage_note'] = 'Check the Windows drive containing ext4.vhdx as well as virtual Linux space.'
    try:
        licenses(config)
        checks['meld_licenses'] = True
    except (KeyError, ValueError):
        checks['meld_licenses'] = False
    if checks['docker_daemon']:
        try:
            checks['docker_disk'] = disk_info(docker_storage())
        except ValueError as e:
            checks['docker_disk'] = {'error': str(e)}
    checks['environment_space_ready'] = checks['environment_disk']['free_gib'] >= 5
    checks['venv_available'] = probe([sys.executable, '-c', 'import venv, ensurepip'])[0]
    checks['docker_space_ready'] = checks.get('docker_disk', {}).get('free_gib', 0) >= 30
    checks['meld_data_space_ready'] = checks['data_disk']['free_gib'] >= 10
    checks['meld_amd64'] = platform.machine() == 'x86_64'
    required = ['linux', 'python_3_10_plus']
    scope = args.scope
    if scope == 'swane-install':
        required += ['venv_available', 'environment_space_ready']
    if scope in ('swane-gui', 'swane-analysis', 'all'):
        required += ['swane_package', 'display_available']
    if scope in ('swane-analysis', 'all'):
        try:
            checks['swane_dependencies'] = dependency_report()
            checks['swane_t1_dependencies'] = all(
                checks['swane_dependencies'].get(k, {}).get('state') == 'DETECTED'
                for k in ('dcm2niix', 'fsl', 't1_runtime'))
        except (ValueError, OSError, subprocess.CalledProcessError) as e:
            checks['swane_dependencies'] = {'error': str(e)}
            checks['swane_t1_dependencies'] = False
        required += ['swane_t1_dependencies']
    if scope in ('meld-install', 'meld-run', 'all'):
        required += ['docker_daemon', 'compose_plugin', 'meld_configured', 'docker_space_ready',
                     'meld_data_space_ready', 'meld_amd64']
    if scope in ('meld-run', 'all'):
        checks['meld_recommended_ram'] = checks['ram_gib'] >= 24
        checks['meld_pinned'] = bool(config.get('meld_image_digest'))
        required += ['meld_licenses', 'meld_recommended_ram', 'meld_pinned']
    checks['requested_scope'] = scope
    checks['missing'] = [key for key in required if not checks[key]]
    save(STATE / ('doctor-' + scope + '.json'), checks)
    print(json.dumps(checks, indent=2))
    return 2 if checks['missing'] else 0


def action(args):
    linux()
    config = load(required=False)
    if args.command == 'run-meld' and args.data:
        config = dict(config, data=str(Path(args.data).expanduser().resolve()))
    runtime_environment(config, include_freesurfer=args.command in ('open-swane', 'swane-dependencies'))
    if args.command == 'license-status':
        return license_status(config)
    elif args.command == 'import-licenses':
        import_licenses(args, config)
    elif args.command == 'install-freesurfer':
        command = [sys.executable, ROOT / 'tools/install_freesurfer.py']
        if args.plan:
            command += ['--plan']
        if args.download_only:
            command += ['--download-only']
        if args.accept_freesurfer_license:
            command += ['--accept-freesurfer-license']
        if args.host_storage:
            command += ['--host-storage', args.host_storage]
        # Preserve the controlling terminal for apt's sudo authentication.
        subprocess.run(list(map(str, command)), check=True)
    elif args.command == 'install-fsl':
        command = [sys.executable, ROOT / 'tools/install_fsl.py']
        if args.conda:
            command += ['--conda', args.conda]
        if args.accept_fsl_license:
            command += ['--accept-fsl-license']
        if args.locked:
            command += ['--locked']
        run(command)
    elif args.command == 'validate-swane-t1':
        run([swane_python(), ROOT / 'tools/validate_swane_t1.py',
             '--dicom', args.dicom, '--output', args.output])
    elif args.command == 'install-swane':
        if sys.version_info < (3, 10):
            raise ValueError('Use Python >=3.10, or bash start.sh to find an existing supported interpreter.')
        require_space(STATE, 5)
        STATE.mkdir(parents=True, exist_ok=True)
        if not swane_python().is_file():
            run([sys.executable, '-m', 'venv', STATE / 'swane-env'])
        run([swane_python(), '-m', 'pip', 'install', 'pip==26.3'])
        requirements = [f"swane=={config.get('swane_version', SWANE_VERSION)}",
                        'dcm2niix==1.0.20250506']
        if args.locked:
            if sys.version_info[:2] != (3, 11) or config.get('swane_version', SWANE_VERSION) != SWANE_VERSION:
                raise ValueError('--locked requires Python 3.11 and SWANe 0.2.1.1.')
            requirements = ['-r', ROOT / 'requirements-swane-py311.lock']
        run([swane_python(), '-m', 'pip', 'install', '--report',
             STATE / 'swane-install-report.json'] + requirements)
        result = run([swane_python(), '-m', 'pip', 'freeze'], capture=True)
        (STATE / 'swane-installed.txt').write_text(result.stdout)
        run([swane_python(), '-m', 'pip', 'check'])
        print('Python packages installed. Use swane-dependencies, then open-swane.')
    elif args.command == 'swane-smoke':
        run([swane_python(), '-m', 'pip', 'check'])
        run([swane_python(), '-c', 'import swane; print(swane.__file__)'])
        print('Package checks passed. GUI and scientific workflows require separate checks.')
    elif args.command == 'swane-dependencies':
        report = dependency_report()
        save(STATE / 'swane-dependencies.json', report)
        print(json.dumps(report, indent=2))
        if not all(report.get(k, {}).get('state') == 'DETECTED' for k in ('dcm2niix', 'fsl', 't1_runtime')):
            return 2
    elif args.command == 'open-swane':
        if not (os.getenv('DISPLAY') or os.getenv('WAYLAND_DISPLAY')):
            raise ValueError('No GUI display detected. Use Ubuntu desktop or configure WSLg.')
        os.environ.setdefault('QT_QPA_PLATFORM', 'xcb')
        run([swane_python(), '-m', 'swane'])
    else:
        if not config.get('meld_release'):
            raise ValueError('Run configure --meld-release PATH --data PATH first.')
        if args.command not in ('install-meld', 'meld-config') and not config.get('meld_image_digest'):
            raise ValueError('Run install-meld first to record the container digest.')
        if args.command not in ('install-meld', 'meld-config'):
            licenses(config)
        if args.command in ('test-meld', 'run-meld') and ram_gib() < 24:
            raise ValueError('MELD recommends >=24 GiB RAM; this host has less. Use a suitably resourced host.')
        base = compose(config)
        if args.command == 'meld-config':
            result = run(base + ['config', '--format', 'json'], capture=True)
            print(result.stdout)
        elif args.command == 'install-meld':
            storage = docker_storage()
            require_space(storage, 30)
            require_space(config['data'], 10)
            model = json.loads(run(base + ['config', '--format', 'json'], capture=True).stdout)
            image = model['services']['meld_graph']['image']
            run(base + ['pull', 'meld_graph'])
            inspected = json.loads(run(['docker', 'image', 'inspect', image], capture=True).stdout)[0]
            digests = inspected.get('RepoDigests', [])
            if not digests:
                raise ValueError('Cannot record an immutable registry digest; setup stopped.')
            repository = image.split('@')[0].rsplit(':', 1)[0]
            matches = [d for d in digests if d.split('@')[0] == repository]
            if not matches:
                raise ValueError('No registry digest matches the selected image repository.')
            latest = load(required=False)
            if latest.get('meld_release') != config['meld_release']:
                raise ValueError('MELD release changed during download. Rerun install-meld for the current configuration.')
            latest['meld_image_digest'] = matches[0]
            save(CONFIG, latest)
            save(STATE / 'meld-image.json', {k: inspected.get(k) for k in
                 ('Id', 'RepoDigests', 'Architecture', 'Os', 'Size', 'Config')})
            print('MELD image installed and pinned. Licences are required before preparation.')
        elif args.command == 'prepare-meld':
            require_space(config['data'], 10)
            run(base + ['run', '--rm', 'meld_graph', 'python',
                        'scripts/new_patient_pipeline/prepare_classifier.py'])
        elif args.command == 'test-meld':
            run(base + ['run', '--rm', 'meld_graph', 'pytest', '-ra', '-s'])
        elif args.command == 'run-meld':
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', args.subject):
                raise ValueError('Subject ID must use letters, numbers, underscores or hyphens.')
            if not 1 <= args.threads <= 64:
                raise ValueError('--threads must be between 1 and 64.')
            helper = ROOT / 'tools/check_meld_case.py'
            checked = base + ['run', '--rm', '-v', str(helper) + ':/opt/neuro_easy/check_meld_case.py:ro',
                              'meld_graph', 'python', '/opt/neuro_easy/check_meld_case.py']
            run(checked + ['pre', args.subject, config['meld_image_digest']])
            run(base + ['run', '--rm', '-e', 'OMP_NUM_THREADS=' + str(args.threads),
                        '-e', 'MKL_NUM_THREADS=' + str(args.threads),
                        '-e', 'OPENBLAS_NUM_THREADS=' + str(args.threads),
                        'meld_graph', 'python', 'scripts/new_patient_pipeline/new_pt_pipeline.py',
                        '--threads', str(args.threads), '-id', args.subject])
            run(checked + ['post', args.subject, config['meld_image_digest']])
            print('Structural outputs checked. Inspect reconstruction and report visually before acceptance.')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('configure')
    p.add_argument('--meld-release')
    p.add_argument('--data')
    p.add_argument('--swane-version')
    p.add_argument('--fsl-dir')
    p.add_argument('--freesurfer-dir')
    p = sub.add_parser('doctor')
    p.add_argument('--for', dest='scope', choices=('computer', 'swane-install', 'swane-gui',
                   'swane-analysis', 'meld-install', 'meld-run', 'all'), default='all')
    p = sub.add_parser('install-swane')
    p.add_argument('--locked', action='store_true')
    p = sub.add_parser('import-licenses')
    p.add_argument('--freesurfer')
    p.add_argument('--meld')
    for name in ('license-status', 'swane-smoke', 'swane-dependencies', 'open-swane',
                 'meld-config', 'install-meld', 'prepare-meld', 'test-meld'):
        sub.add_parser(name)
    p = sub.add_parser('install-freesurfer')
    p.add_argument('--plan', action='store_true')
    p.add_argument('--download-only', action='store_true')
    p.add_argument('--accept-freesurfer-license', action='store_true')
    p.add_argument('--host-storage')
    p = sub.add_parser('install-fsl')
    p.add_argument('--conda')
    p.add_argument('--accept-fsl-license', action='store_true')
    p.add_argument('--locked', action='store_true')
    p = sub.add_parser('validate-swane-t1')
    p.add_argument('--dicom', required=True)
    p.add_argument('--output', required=True)
    p = sub.add_parser('run-meld')
    p.add_argument('--subject', required=True)
    p.add_argument('--threads', type=int, default=4)
    p.add_argument('--data', help='Per-run MELD data directory; does not change saved configuration.')
    args = parser.parse_args(argv)
    record = {'command': args.command, 'status': 'RUNNING', 'utc': now(),
              'scope': 'launcher action; see command logs for acceptance evidence'}
    save(STATE / 'last-action.json', record)
    if args.command == 'test-meld':
        save(STATE / 'meld-test.json', record)
    if args.command == 'run-meld' and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', args.subject):
        record.update(subject=args.subject, data=args.data,
                      data_source='override' if args.data else 'saved configuration', threads=args.threads,
                      scope='raw-MRI pipeline and structural output checks; visual QC required separately')
        save(STATE / ('meld-run-' + args.subject + '.json'), record)
    try:
        if args.command == 'configure':
            configure(args)
            code = 0
        elif args.command == 'doctor':
            code = doctor(args)
        else:
            code = action(args)
    except KeyboardInterrupt:
        print('Interrupted. Logs are in local/logs; rerun the failed action to resume.', file=sys.stderr)
        code = 130
        record['status'] = 'INTERRUPTED'
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr, file=sys.stderr)
        code = error.returncode if isinstance(error, subprocess.CalledProcessError) else 1
        code = code if code > 0 else 128 - code
    record.update({'status': record.get('status') if record.get('status') == 'INTERRUPTED'
                   else ('PASSED' if code == 0 else 'FAILED'), 'exit_code': code, 'finished_utc': now()})
    save(STATE / 'last-action.json', record)
    if args.command == 'test-meld':
        record.update({'scope': 'upstream MELD pytest only; inspect skips and raw-MRI coverage',
                       'image': load(required=False).get('meld_image_digest', 'UNPINNED')})
        save(STATE / 'meld-test.json', record)
    if args.command == 'run-meld' and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', args.subject):
        save(STATE / ('meld-run-' + args.subject + '.json'), record)
    return code


if __name__ == '__main__':
    sys.exit(main())
