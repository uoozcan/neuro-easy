"""Prepare/install isolated FreeSurfer 7.4.1 for SWANe; MELD retains bundled 7.2.0."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import neuro_easy as launcher

VERSION = '7.4.1'
LICENCE_URL = 'https://surfer.nmr.mgh.harvard.edu/registration.html'
PROFILES = {
    '20.04': ('freesurfer-linux-ubuntu20_amd64-7.4.1.tar.gz', 'f735655a88b0a5e05bef4ab73d991e3d'),
    '22.04': ('freesurfer-linux-ubuntu22_amd64-7.4.1.tar.gz', '4275a307a1a91043587f659389b3e9a8'),
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


def extract(archive, destination):
    if not hasattr(tarfile, 'data_filter'):
        raise ValueError('Use an updated Python with tarfile.data_filter for safe extraction.')
    def only_freesurfer(member, target):
        if not PurePosixPath(member.name).parts or PurePosixPath(member.name).parts[0] != 'freesurfer':
            raise ValueError('Archive member is outside the expected freesurfer directory.')
        return tarfile.data_filter(member, target)
    with tarfile.open(archive, 'r:gz') as bundle:
        bundle.extractall(destination, filter=only_freesurfer)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', action='store_true', help='Print the selected package/storage plan; download nothing.')
    parser.add_argument('--accept-freesurfer-license', action='store_true')
    parser.add_argument('--host-storage', type=Path, help='Windows drive mount backing WSL, e.g. /mnt/c.')
    args = parser.parse_args(argv)
    release, (filename, expected_md5) = profile()
    state = launcher.STATE
    target = state / 'apps' / ('freesurfer-' + VERSION)
    url = 'https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/' + VERSION + '/' + filename
    plan = {'version': VERSION, 'ubuntu': release, 'url': url, 'upstream_md5': expected_md5,
            'target': str(target), 'minimum_free_gib': 40, 'disk': launcher.disk_info(state),
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
    if args.host_storage:
        launcher.require_space(args.host_storage, 40)
    if target.exists():
        raise ValueError('Target already exists. Inspect/resume the recorded installation; existing files will not be replaced.')
    downloads = state / 'downloads'
    downloads.mkdir(parents=True, exist_ok=True)
    archive = downloads / filename
    partial = archive.with_suffix(archive.suffix + '.part')
    if not archive.is_file():
        launcher.run(['curl', '--fail', '--location', '--retry', '3', '--connect-timeout', '30',
                      '--continue-at', '-', '--output', partial, url])
        observed_md5, observed_sha256 = checksums(partial)
        if observed_md5 != expected_md5:
            raise ValueError('FreeSurfer archive checksum mismatch. Extraction was not started.')
        partial.replace(archive)
    observed_md5, observed_sha256 = checksums(archive)
    if observed_md5 != expected_md5:
        raise ValueError('FreeSurfer archive checksum mismatch. Extraction was not started.')
    staging = target.with_name('.' + target.name + '.partial')
    marker = staging / '.neuro-easy-staging.json'
    if staging.exists() and (not marker.is_file() or
                             json.loads(marker.read_text()).get('archive_sha256') != observed_sha256):
        raise ValueError('Unrecognized staging directory. Inspect it before continuing.')
    staging.mkdir(parents=True, exist_ok=True)
    launcher.save(marker, {'archive_sha256': observed_sha256})
    extract(archive, staging)
    home = staging / 'freesurfer'
    if not (home / 'SetUpFreeSurfer.sh').is_file() or not (home / 'bin/recon-all').is_file():
        raise ValueError('Extracted archive is incomplete; required upstream files are absent.')
    home.rename(target)
    launcher.save(state / 'freesurfer-install.json', {
        **plan, 'archive_sha256': observed_sha256, 'status': 'UNPACKED',
        'acceptance': 'Files installed only. Licence, environment setup and operational checks remain required.'})
    print('Official files unpacked locally. Personal licence and operational validation remain required.')
    print('Standalone FREESURFER_HOME: ' + str(target))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError, tarfile.TarError) as error:
        print('ERROR: ' + str(error), file=sys.stderr)
        sys.exit(error.returncode if isinstance(error, subprocess.CalledProcessError) else 1)
