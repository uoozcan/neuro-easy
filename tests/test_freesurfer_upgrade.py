"""Real filesystem safety tests; no system package or network operations."""
import importlib.util
import os
import json
import subprocess
from unittest.mock import patch
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('fs_upgrade', Path(__file__).parents[1]/'tools/upgrade_freesurfer_810.py')
upgrade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upgrade)


class UpgradePreservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old = self.root/'old'
        (self.old/'bin').mkdir(parents=True)
        (self.old/'bin/tool').write_bytes(b'original executable fixture')
        (self.old/'bin/alias').symlink_to('tool')
        self.backup = self.root/'preserved'

    def tearDown(self):
        self.temp.cleanup()

    def test_restore_after_dpkg_unlinks_original_files(self):
        upgrade.preserve_tree(self.old,self.backup)
        inode = (self.old/'bin/tool').stat().st_ino
        (self.old/'bin/tool').unlink()
        (self.old/'bin/alias').unlink()
        upgrade.restore_tree(self.backup,self.old)
        self.assertEqual((self.old/'bin/tool').stat().st_ino,inode)
        self.assertEqual((self.old/'bin/tool').read_bytes(),b'original executable fixture')
        self.assertEqual(os.readlink(self.old/'bin/alias'),'tool')

    def test_preservation_rejects_existing_destination(self):
        self.backup.mkdir()
        with self.assertRaisesRegex(ValueError,'Existing preservation'):
            upgrade.preserve_tree(self.old,self.backup)

    def test_restore_does_not_overwrite_conflicting_files(self):
        upgrade.preserve_tree(self.old,self.backup)
        (self.old/'bin/tool').unlink()
        (self.old/'bin/tool').write_bytes(b'new unexpected file')
        with self.assertRaisesRegex(ValueError,'Conflicting file'):
            upgrade.restore_tree(self.backup,self.old)
        self.assertEqual((self.old/'bin/tool').read_bytes(),b'new unexpected file')

    def test_restore_does_not_follow_new_directory_symlink(self):
        upgrade.preserve_tree(self.old,self.backup)
        (self.old/'bin/tool').unlink()
        (self.old/'bin/alias').unlink()
        (self.old/'bin').rmdir()
        outside=self.root/'outside';outside.mkdir()
        (self.old/'bin').symlink_to(outside,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'Unexpected directory symlink'):
            upgrade.restore_tree(self.backup,self.old)
        self.assertFalse((outside/'tool').exists())

    def upgrade_patches(self):
        (self.old/'SetUpFreeSurfer.sh').write_text('# fixture only')
        package=self.root/'fixture.deb';package.write_bytes(b'offline fixture')
        return package, [
            patch.object(upgrade,'OLD',self.old),
            patch.object(upgrade,'NEW',self.root/'new'),
            patch.object(upgrade.launcher,'STATE',self.root/'state'),
            patch.object(upgrade.vendor,'profile',return_value=('20.04',None)),
            patch.object(upgrade.vendor,'installed_package',return_value='install ok installed 7.4.1'),
            patch.object(upgrade.os,'geteuid',return_value=0),
            patch.object(upgrade.launcher,'require_space'),
        ]

    def test_corrupted_package_does_not_touch_installation(self):
        package,patches=self.upgrade_patches()
        for item in patches:item.start()
        try:
            with patch.object(upgrade.vendor,'checksums',return_value=('wrong','sha')), patch.object(upgrade.launcher,'run') as runner:
                with self.assertRaisesRegex(ValueError,'checksum mismatch'):
                    upgrade.main(['--package',str(package),'--host-storage',str(self.root),'--accept-freesurfer-license'])
                runner.assert_not_called()
            self.assertFalse((self.root/'state/freesurfer-741-preserved').exists())
            self.assertEqual((self.old/'bin/tool').read_bytes(),b'original executable fixture')
        finally:
            for item in reversed(patches):item.stop()

    def test_failed_apt_restores_missing_old_paths(self):
        package,patches=self.upgrade_patches()
        for item in patches:item.start()
        try:
            def fake_apt(command):
                if '--simulate' not in command:
                    (self.old/'bin/tool').unlink()
                    raise subprocess.CalledProcessError(100,command)
                return subprocess.CompletedProcess(command,0)
            expected=upgrade.PROFILES['20.04'][1]
            with patch.object(upgrade.vendor,'checksums',return_value=(expected,'sha')), patch.object(upgrade.vendor,'validate_package'), patch.object(upgrade.launcher,'run',side_effect=fake_apt):
                with self.assertRaises(subprocess.CalledProcessError):
                    upgrade.main(['--package',str(package),'--host-storage',str(self.root),'--accept-freesurfer-license'])
            self.assertEqual((self.old/'bin/tool').read_bytes(),b'original executable fixture')
            result=json.loads((self.root/'state/freesurfer-810-upgrade.json').read_text())
            self.assertEqual(result['status'],'FAILED')
            self.assertTrue(result['old_files_restored'])
        finally:
            for item in reversed(patches):item.stop()


if __name__=='__main__':
    unittest.main()
