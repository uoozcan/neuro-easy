"""Explicit apt upgrade from 7.4.1 to 8.1.0, preserving old files as a fallback."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import neuro_easy as launcher
from tools import install_freesurfer as vendor

OLD = Path('/usr/local/freesurfer/7.4.1')
NEW = Path('/usr/local/freesurfer/8.1.0')
PROFILES = {
    '20.04': ('freesurfer_ubuntu20-8.1.0_amd64.deb', 'f7245f839d13ae64cfb406930f5adc82'),
    '22.04': ('freesurfer_ubuntu22-8.1.0_amd64.deb', '4da6856ed67b2528145d8e4ab48df461'),
}


def preserve_tree(source, backup):
    """Hard links retain original inodes when dpkg unlinks old-version paths."""
    if backup.exists() or backup.is_symlink():
        raise ValueError('Existing preservation tree must be inspected, not overwritten.')
    backup.parent.mkdir(parents=True, exist_ok=True)
    if source.stat().st_dev != backup.parent.stat().st_dev:
        raise ValueError('Preservation requires the same filesystem; no implicit large copy.')
    count = 0
    def link(src, dst):
        nonlocal count
        os.link(src, dst)
        count += 1
        if count % 5000 == 0:
            print('Preserved', count, 'files by hard link', flush=True)
    shutil.copytree(source, backup, symlinks=True, copy_function=link)
    return count


def restore_tree(backup, target):
    """Restore missing old paths; never overwrite an unexpected existing file."""
    if target.is_symlink():
        raise ValueError('Unexpected symlink at old installation root.')
    target.mkdir(parents=True, exist_ok=True)
    for folder, dirs, files in os.walk(backup, followlinks=False):
        relative = Path(folder).relative_to(backup)
        destination = target / relative
        if destination.is_symlink():
            raise ValueError('Unexpected directory symlink during restoration.')
        destination.mkdir(parents=True, exist_ok=True)
        for name in dirs + files:
            src, dst = Path(folder) / name, destination / name
            if src.is_symlink():
                if dst.is_symlink() and os.readlink(src) == os.readlink(dst):
                    continue
                if dst.exists() or dst.is_symlink():
                    raise ValueError('Conflicting path preserved: ' + str(dst))
                dst.symlink_to(os.readlink(src))
            elif src.is_file():
                if dst.exists() or dst.is_symlink():
                    if not dst.is_symlink() and os.path.samefile(src, dst):
                        continue
                    raise ValueError('Conflicting file preserved: ' + str(dst))
                os.link(src, dst)
        shutil.copystat(folder, destination, follow_symlinks=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', action='store_true')
    parser.add_argument('--package', type=Path)
    parser.add_argument('--host-storage', type=Path)
    parser.add_argument('--accept-freesurfer-license', action='store_true')
    args = parser.parse_args(argv)
    release, _ = vendor.profile()
    filename, expected = PROFILES[release]
    package = (args.package or launcher.STATE / 'downloads' / filename).resolve()
    backup = launcher.STATE / 'freesurfer-741-preserved'
    status_path = launcher.STATE / 'freesurfer-810-upgrade.json'
    record = {'from': '7.4.1', 'to': '8.1.0', 'ubuntu': release, 'package': str(package),
              'upstream_md5': expected, 'target': str(NEW), 'fallback': str(OLD),
              'preservation_tree': str(backup), 'method': 'official DEB via apt',
              'minimum_free_gib': 30, 'status': 'PLANNED',
              'scope': 'Package installation only; operational/scientific checks separate.'}
    if args.plan:
        record['disk'] = launcher.disk_info(NEW)
        if args.host_storage:
            record['host_disk'] = launcher.disk_info(args.host_storage)
        print(json.dumps(record, indent=2))
        return 0
    if not args.accept_freesurfer_license:
        raise ValueError('Personal FreeSurfer licence acceptance is required.')
    if os.geteuid() != 0:
        raise ValueError('Run this explicit system-package upgrade with sudo.')
    if vendor.installed_package() != 'install ok installed 7.4.1' or OLD.is_symlink() or not (OLD / 'SetUpFreeSurfer.sh').is_file():
        raise ValueError('This explicit upgrade requires the registered 7.4.1 installation.')
    if NEW.exists() or NEW.is_symlink() or backup.exists() or backup.is_symlink():
        raise ValueError('Existing target/preservation tree must be inspected before continuing.')
    if 'microsoft' in vendor.platform.release().lower() and not args.host_storage:
        raise ValueError('WSL requires --host-storage for the actual backing Windows drive.')
    if not package.is_file():
        raise ValueError('First download the official package; this command does not fetch software.')
    launcher.require_space(launcher.STATE, 30)
    launcher.require_space(NEW, 30)
    if args.host_storage:
        launcher.require_space(args.host_storage, 30)
    print('Verifying official 8.1.0 package; this may take several minutes.', flush=True)
    md5, sha = vendor.checksums(package)
    if md5 != expected:
        raise ValueError('Publisher checksum mismatch; no system change made.')
    vendor.validate_package(package, '8.1.0')
    launcher.run(['apt-get', '--simulate', '--no-remove', '--no-install-recommends', 'install', package])
    record.update(package_sha256=sha, status='PRESERVING_741')
    launcher.save(status_path, record)
    complete = False
    try:
        count = preserve_tree(OLD, backup)
        complete = True
        record.update(status='OLD_FILES_PRESERVED', preserved_files=count)
        launcher.save(status_path, record)
        launcher.run(['apt-get', '--yes', '--no-remove', '--no-install-recommends', 'install', package])
        if vendor.installed_package() != 'install ok installed 8.1.0' or not (NEW / 'SetUpFreeSurfer.sh').is_file():
            raise ValueError('Package did not produce the expected 8.1.0 installation.')
        record['status'] = 'PACKAGE_INSTALLED'
    except BaseException:
        record['status'] = 'FAILED'
        raise
    finally:
        try:
            if complete:
                restore_tree(backup, OLD)
                record['old_files_restored'] = True
        except BaseException:
            record['status'] = 'FAILED_RESTORATION_REQUIRED'
            raise
        finally:
            launcher.save(status_path, record)
    # Share the already installed same-release MCR; no new licence agreement or library exports.
    runtime = OLD / 'MCRv97'
    if (runtime / 'bin/glnxa64/libmwlaunchermain.so').is_file() and not (NEW / 'MCRv97').exists():
        (NEW / 'MCRv97').symlink_to(runtime, target_is_directory=True)
        record['runtime_link'] = str(runtime)
        launcher.save(status_path, record)
    print('8.1.0 package installed. 7.4.1 files retained as an unmanaged fallback.')
    print('Validate 8.1.0 before changing the SWANe configuration.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print('ERROR:', error, file=sys.stderr)
        sys.exit(error.returncode if isinstance(error, subprocess.CalledProcessError) else 1)
