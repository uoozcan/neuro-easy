"""Install the official Ubuntu FreeSurfer 7.4.1 package; MELD retains bundled 7.2.0."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import neuro_easy as launcher

VERSION = '7.4.1'
TARGET = Path('/usr/local/freesurfer/7.4.1')
LICENCE_URL = 'https://surfer.nmr.mgh.harvard.edu/registration.html'
PROFILES = {
    '20.04': ('freesurfer_ubuntu20-7.4.1_amd64.deb', '3f488ddc5c1a19fe23bb9cbe2c9f457f'),
    '22.04': ('freesurfer_ubuntu22-7.4.1_amd64.deb', 'bfe85dd76677cfb7ca2b247b9ac6148e'),
}


def profile():
    values = {}
    for line in Path('/etc/os-release').read_text().splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            values[key] = value.strip('"')
    if platform.system() != 'Linux' or platform.machine() != 'x86_64' or values.get('ID') != 'ubuntu':
        raise ValueError('This installer supports Ubuntu Linux x86_64 only.')
    if values.get('VERSION_ID') not in PROFILES:
        raise ValueError('Use a supported upstream FreeSurfer build; this profile covers Ubuntu 20.04/22.04.')
    return values['VERSION_ID'], PROFILES[values['VERSION_ID']]


def checksums(path):
    md5 = hashlib.md5(usedforsecurity=False)
    sha256 = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            md5.update(chunk)
            sha256.update(chunk)
    return md5.hexdigest(), sha256.hexdigest()


def installed_package():
    result = subprocess.run(
        ['dpkg-query', '-W', '-f=${Status} ${Version}', 'freesurfer'],
        text=True, capture_output=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else ''


def validate_package(path):
    result = launcher.run(['dpkg-deb', '--show', '--showformat=${Package} ${Version} ${Architecture}', path],
                          capture=True)
    if result.stdout.strip() != 'freesurfer 7.4.1 amd64':
        raise ValueError('Unexpected FreeSurfer package name, version or architecture.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', action='store_true', help='Print package/storage plan; download nothing.')
    parser.add_argument('--download-only', action='store_true', help='Verify the package without installing it.')
    parser.add_argument('--accept-freesurfer-license', action='store_true')
    parser.add_argument('--host-storage', type=Path, help='Windows drive mount backing WSL, e.g. /mnt/c.')
    args = parser.parse_args(argv)
    release, (filename, expected_md5) = profile()
    state = launcher.STATE
    url = 'https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/' + VERSION + '/' + filename
    plan = {'version': VERSION, 'ubuntu': release, 'url': url, 'upstream_md5': expected_md5,
            'target': str(TARGET), 'method': 'official DEB with apt-get; sudo required',
            'minimum_free_gib': 40, 'disk': launcher.disk_info(state),
            'system_disk': launcher.disk_info(TARGET),
            'licence': LICENCE_URL, 'operational_license_file_required': True,
            'scope': 'Standalone SWANe/classic FreeSurfer; never substituted into MELD.'}
    if args.host_storage:
        plan['host_disk'] = launcher.disk_info(args.host_storage)
    if args.plan:
        print(json.dumps(plan, indent=2))
        return 0
    if not args.accept_freesurfer_license:
        print('Personally read/accept the FreeSurfer licence before downloading: ' + LICENCE_URL,
              file=sys.stderr)
        return 2
    if 'microsoft' in platform.release().lower() and not args.host_storage:
        raise ValueError('For WSL, provide --host-storage for the Windows drive containing ext4.vhdx.')
    launcher.require_space(state, 40)
    launcher.require_space(TARGET, 40)
    if args.host_storage:
        launcher.require_space(args.host_storage, 40)
    package_state = installed_package()
    if TARGET.exists() or 'install ok installed' in package_state:
        raise ValueError('FreeSurfer already exists. Inspect the recorded installation; existing software will not be replaced.')
    downloads = state / 'downloads'
    downloads.mkdir(parents=True, exist_ok=True)
    package = downloads / filename
    partial = package.with_suffix(package.suffix + '.part')
    if not package.is_file():
        launcher.run(['curl', '--fail', '--location', '--retry', '3', '--connect-timeout', '30',
                      '--continue-at', '-', '--output', partial, url])
        print('Verifying downloaded FreeSurfer package checksums; this may take several minutes.', flush=True)
        observed_md5, observed_sha256 = checksums(partial)
        if observed_md5 != expected_md5:
            raise ValueError('FreeSurfer package checksum mismatch. Installation was not started.')
        partial.replace(package)
    else:
        print('Verifying cached FreeSurfer package checksums; this may take several minutes.', flush=True)
        observed_md5, observed_sha256 = checksums(package)
        if observed_md5 != expected_md5:
            raise ValueError('FreeSurfer package checksum mismatch. Installation was not started.')
    validate_package(package)
    record = {**plan, 'package_sha256': observed_sha256, 'status': 'PACKAGE_VERIFIED',
              'acceptance': 'Package integrity only. Installation/licence/runtime checks remain required.'}
    launcher.save(state / 'freesurfer-install.json', record)
    if args.download_only:
        print('Official package verified; not installed.')
        return 0
    # Let Ubuntu resolve upstream dependencies. Refuse any package removals.
    launcher.run(['apt-get', '--simulate', '--no-remove', '--no-install-recommends', 'install', package])
    privilege = [] if os.geteuid() == 0 else ['sudo', '--']
    subprocess.run(list(map(str, privilege + ['apt-get', '--yes', '--no-remove', '--no-install-recommends',
                                             'install', package])), check=True)
    if installed_package() != 'install ok installed ' + VERSION or not (TARGET / 'SetUpFreeSurfer.sh').is_file():
        raise ValueError('Package installation did not produce the expected FreeSurfer version/setup.')
    launcher.save(state / 'freesurfer-install.json', {
        **record, 'status': 'PACKAGE_INSTALLED',
        'acceptance': 'Ubuntu package installed. Personal licence and operational validation remain required.'})
    print('Official Ubuntu package installed. Personal licence and operational validation remain required.')
    print('Standalone FREESURFER_HOME: ' + str(TARGET))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print('ERROR: ' + str(error), file=sys.stderr)
        sys.exit(error.returncode if isinstance(error, subprocess.CalledProcessError) else 1)
