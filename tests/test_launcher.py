import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('neuro_easy', Path(__file__).parents[1] / 'neuro_easy.py')
n = importlib.util.module_from_spec(spec)
spec.loader.exec_module(n)


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.state = root / 'local'
        self.state.mkdir()
        self.release = root / 'release with spaces'
        self.release.mkdir()
        (self.release / 'compose.yml').write_text('services: {}')
        for name in ('license.txt', 'meld_license.txt'):
            (self.release / name).write_text('fixture@example.invalid\n12345\nfixture-key-one\nfixture-key-two\n' if name == 'license.txt' else 'TEST FIXTURE ONLY\nLicense ID: 123456\n')
        self.patches = [patch.object(n, 'STATE', self.state),
                        patch.object(n, 'CONFIG', self.state / 'config.json'),
                        patch.object(n, 'ram_gib', return_value=32)]
        for p in self.patches:
            p.start()
        self.config = {'meld_release': str(self.release), 'data': str(root / 'data with spaces'),
                       'swane_version': '0.2.1.1', 'meld_image_digest': 'example/image@sha256:fixture'}
        n.CONFIG.write_text(json.dumps(self.config))

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_missing_release_rejected(self):
        self.assertEqual(n.main(['configure', '--meld-release', str(self.release / 'absent'), '--data', str(self.state)]), 1)

    def test_configure_round_trip_with_spaces(self):
        self.assertEqual(n.main(['configure', '--meld-release', str(self.release), '--data', self.config['data']]), 0)
        self.assertEqual(n.load()['data'], self.config['data'])

    def test_meld_license_status_does_not_source_host_freesurfer(self):
        self.config['freesurfer_dir'] = str(self.state / 'absent-host-freesurfer')
        n.CONFIG.write_text(json.dumps(self.config))
        with patch.object(n, 'linux'):
            self.assertEqual(n.main(['license-status']), 0)

    def test_empty_license_rejected(self):
        (self.release / 'license.txt').write_text('')
        with self.assertRaises(ValueError):
            n.licenses(self.config)

    def test_compose_uses_data_mount_and_digest(self):
        model = {'services': {'meld_graph': {'image': 'example/image:tag',
                 'volumes': [{'type': 'bind', 'source': 'old', 'target': '/data'}],
                 'deploy': {'resources': {'reservations': {'devices': [{'capabilities': ['gpu']}]}}}}},
                 'secrets': {'license.txt': {'file': str(self.release / 'license.txt')}}}
        with patch.object(n.os, 'getuid', return_value=1000, create=True), patch.object(n.os, 'getgid', return_value=1000, create=True), patch.dict(n.os.environ), patch.object(n, 'run', return_value=subprocess.CompletedProcess([], 0, json.dumps(model))):
            cmd = n.compose(self.config)
            self.assertNotIn(str(self.release / 'compose.yml'), cmd)
            generated = json.loads(Path(cmd[-1]).read_text())
            service = generated['services']['meld_graph']
            self.assertEqual(service['image'], self.config['meld_image_digest'])
            self.assertEqual(service['volumes'][0]['source'], self.config['data'])
            self.assertNotIn('devices', service['deploy']['resources']['reservations'])
            self.assertEqual(generated['secrets'], model['secrets'])

    def test_compose_snapshots_do_not_overwrite_active_data_mount(self):
        model = {'services': {'meld_graph': {'image': 'example/image:tag'}}}
        with patch.object(n.os, 'getuid', return_value=1000, create=True), patch.object(n.os, 'getgid', return_value=1000, create=True), patch.dict(n.os.environ), patch.object(n, 'run', return_value=subprocess.CompletedProcess([], 0, json.dumps(model))):
            first = Path(n.compose(self.config)[-1])
            second_config = dict(self.config, data='/different/input')
            second = Path(n.compose(second_config)[-1])
        self.assertNotEqual(first, second)
        self.assertEqual(json.loads(first.read_text())['services']['meld_graph']['volumes'][-1]['source'], self.config['data'])
        self.assertEqual(json.loads(second.read_text())['services']['meld_graph']['volumes'][-1]['source'], '/different/input')

    def test_non_linux_install_blocked(self):
        with patch.object(n.platform, 'system', return_value='Windows'), patch.object(n, 'run') as runner:
            self.assertEqual(n.main(['install-swane']), 1)
            runner.assert_not_called()

    def test_unpinned_meld_run_blocked(self):
        del self.config['meld_image_digest']
        n.CONFIG.write_text(json.dumps(self.config))
        with patch.object(n, 'linux'), patch.object(n, 'run') as runner:
            self.assertEqual(n.main(['prepare-meld']), 1)
            runner.assert_not_called()

    def test_failed_analysis_cannot_retain_previous_pass(self):
        report = self.state / 'meld-test.json'
        report.write_text('{"status":"PASSED"}')
        with patch.object(n, 'linux'), patch.object(n, 'compose', return_value=['docker', 'compose']), patch.object(n, 'run', side_effect=subprocess.CalledProcessError(1, 'fixture')):
            self.assertEqual(n.main(['test-meld']), 1)
        self.assertEqual(json.loads(report.read_text())['status'], 'FAILED')

    def test_subject_is_single_argument(self):
        with patch.object(n, 'linux'), patch.object(n, 'compose', return_value=['docker', 'compose']), patch.object(n, 'run') as runner:
            self.assertEqual(n.main(['run-meld', '--subject', 'sub-001']), 0)
            calls = [call.args[0] for call in runner.call_args_list]
            pipeline = next(call for call in calls if 'scripts/new_patient_pipeline/new_pt_pipeline.py' in call)
            self.assertEqual(pipeline[-2:], ['-id', 'sub-001'])
            self.assertEqual(calls[-1][-3], 'post')
            runner.reset_mock()
            self.assertEqual(n.main(['run-meld', '--subject', 'sub-001; echo bad']), 1)
            runner.assert_not_called()

    def test_meld_preflight_failure_stops_pipeline(self):
        with patch.object(n, 'linux'), patch.object(n, 'compose', return_value=['docker', 'compose']), patch.object(n, 'run', side_effect=subprocess.CalledProcessError(2, 'preflight')) as runner:
            self.assertEqual(n.main(['run-meld', '--subject', 'sub-001']), 2)
            self.assertEqual(runner.call_count, 1)

    def test_meld_postcheck_failure_cannot_pass(self):
        with patch.object(n, 'linux'), patch.object(n, 'compose', return_value=['docker', 'compose']), patch.object(n, 'run', side_effect=[None, None, subprocess.CalledProcessError(2, 'postcheck')]):
            self.assertEqual(n.main(['run-meld', '--subject', 'sub-001']), 2)
            self.assertEqual(json.loads((self.state / 'last-action.json').read_text())['status'], 'FAILED')

    def test_meld_data_override_does_not_change_configuration(self):
        with patch.object(n, 'linux'), patch.object(n, 'compose', return_value=['docker', 'compose']) as composer, patch.object(n, 'run'):
            target = str(self.state / 'separate-data')
            self.assertEqual(n.main(['run-meld', '--subject', 'sub-001', '--data', target]), 0)
            self.assertEqual(composer.call_args.args[0]['data'], target)
            self.assertEqual(n.load()['data'], self.config['data'])

    def test_swane_can_configure_without_meld(self):
        n.CONFIG.unlink()
        self.assertEqual(n.main(['configure', '--swane-version', '0.2.1.1']), 0)
        self.assertNotIn('meld_release', n.load())

    def test_swane_install_without_configuration(self):
        n.CONFIG.unlink()
        with patch.object(n, 'linux'), patch.object(n, 'run', return_value=subprocess.CompletedProcess([], 0, 'swane==0.2.1.1')), patch.object(n, 'require_space'):
            self.assertEqual(n.main(['install-swane']), 0)

    def test_reconfigure_same_release_preserves_digest(self):
        self.assertEqual(n.main(['configure', '--meld-release', str(self.release)]), 0)
        self.assertEqual(n.load()['meld_image_digest'], self.config['meld_image_digest'])

    def test_changed_release_clears_digest(self):
        other = self.release.parent / 'other'
        other.mkdir()
        (other / 'compose.yml').write_text('services: {}')
        self.assertEqual(n.main(['configure', '--meld-release', str(other)]), 0)
        self.assertNotIn('meld_image_digest', n.load())

    def test_subprocess_exit_code_preserved(self):
        with patch.object(n, 'action', side_effect=subprocess.CalledProcessError(17, 'fixture')):
            self.assertEqual(n.main(['swane-smoke']), 17)
        self.assertEqual(json.loads((self.state / 'last-action.json').read_text())['exit_code'], 17)

    def test_interrupt_clears_prior_meld_pass(self):
        (self.state / 'meld-test.json').write_text('{"status":"PASSED"}')
        with patch.object(n, 'action', side_effect=KeyboardInterrupt):
            self.assertEqual(n.main(['test-meld']), 130)
        self.assertEqual(json.loads((self.state / 'meld-test.json').read_text())['status'], 'INTERRUPTED')

    def test_missing_license_clears_prior_meld_pass(self):
        (self.state / 'meld-test.json').write_text('{"status":"PASSED"}')
        (self.release / 'license.txt').unlink()
        with patch.object(n, 'linux'):
            self.assertEqual(n.main(['test-meld']), 1)
        self.assertEqual(json.loads((self.state / 'meld-test.json').read_text())['status'], 'FAILED')

    def test_low_disk_blocks_large_download(self):
        with patch.object(n, 'disk_info', return_value={'path': '/fixture', 'free_gib': 1}):
            with self.assertRaises(ValueError):
                n.require_space('/fixture', 30)

    def test_swane_gui_doctor_independent_of_docker(self):
        import argparse
        def fake_probe(command):
            return (command[0] != 'docker', '')
        with patch.object(n, 'probe', side_effect=fake_probe), patch.object(n.platform, 'system', return_value='Linux'), patch.dict(n.os.environ, {'DISPLAY': ':0'}):
            self.assertEqual(n.doctor(argparse.Namespace(scope='swane-gui')), 0)
            self.assertEqual(n.doctor(argparse.Namespace(scope='meld-install')), 2)

    def test_swane_dependency_failure_is_nonzero(self):
        with patch.object(n, 'dependency_report', return_value={'fsl': {'state': 'MISSING'}}):
            self.assertEqual(n.main(['swane-dependencies']), 2)

    def validation_module(self):
        path = Path(__file__).parents[1] / 'tools/validate_swane_t1.py'
        spec = importlib.util.spec_from_file_location('validation_fixture', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_changed_mri_inputs_cannot_reuse_cached_outputs(self):
        validation = self.validation_module()
        dicom = Path(self.tmp.name) / 'dicom'
        dicom.mkdir()
        (dicom / 'fixture.dcm').write_bytes(b'offline fixture only')
        output = Path(self.tmp.name) / 'analysis'
        output.mkdir()
        (output / 'input-manifest.json').write_text('[]')
        with patch.object(validation, 'version', return_value='0.2.1.1'), patch.object(validation.sys, 'argv', ['validate', '--dicom', str(dicom), '--output', str(output)]):
            with self.assertRaises(SystemExit) as caught:
                validation.main()
        self.assertEqual(caught.exception.code, 2)
        self.assertFalse((output / 'validation.json').exists())

    def test_untracked_cached_analysis_is_rejected(self):
        validation = self.validation_module()
        dicom = Path(self.tmp.name) / 'dicom'
        dicom.mkdir()
        (dicom / 'fixture.dcm').write_bytes(b'offline fixture only')
        output = Path(self.tmp.name) / 'analysis'
        (output / 'work').mkdir(parents=True)
        with patch.object(validation, 'version', return_value='0.2.1.1'), patch.object(validation.sys, 'argv', ['validate', '--dicom', str(dicom), '--output', str(output)]):
            with self.assertRaises(SystemExit) as caught:
                validation.main()
        self.assertEqual(caught.exception.code, 2)

    def test_meld_pull_preserves_concurrent_swane_configuration(self):
        def fake_run(command, **kwargs):
            if 'pull' in command:
                latest = n.load()
                latest['fsl_dir'] = '/configured/while/pulling'
                n.CONFIG.write_text(json.dumps(latest))
                return subprocess.CompletedProcess(command, 0)
            if command[:3] == ['docker', 'image', 'inspect']:
                return subprocess.CompletedProcess(command, 0, json.dumps([{'RepoDigests': ['example/image@sha256:pinned']}]))
            return subprocess.CompletedProcess(command, 0, json.dumps({'services': {'meld_graph': {'image': 'example/image:tag'}}}))
        with patch.object(n, 'linux'), patch.object(n, 'compose', return_value=['docker', 'compose']), patch.object(n, 'docker_storage', return_value=self.state), patch.object(n, 'require_space'), patch.object(n, 'run', side_effect=fake_run):
            self.assertEqual(n.main(['install-meld']), 0)
        self.assertEqual(n.load()['fsl_dir'], '/configured/while/pulling')
        self.assertEqual(n.load()['meld_image_digest'], 'example/image@sha256:pinned')

    def test_malformed_meld_license_is_rejected_before_zero_exit_upstream(self):
        (self.release / 'meld_license.txt').write_text('License ID: 123')
        with patch.object(n, 'linux'), patch.object(n, 'run') as runner:
            self.assertEqual(n.main(['prepare-meld']), 1)
            runner.assert_not_called()

    def test_personal_license_import_is_private_and_contents_are_not_printed(self):
        import io
        source = Path(self.tmp.name) / 'personal licence.txt'
        source.write_text('person@example.invalid\n4321\nprivate-fixture-key-a\nprivate-fixture-key-b\n')
        output = io.StringIO()
        with patch.object(n, 'linux'), patch('sys.stdout', output):
            self.assertEqual(n.main(['import-licenses', '--freesurfer', str(source)]), 0)
        installed = self.release / 'license.txt'
        self.assertEqual(installed.read_bytes(), source.read_bytes())
        self.assertEqual(installed.stat().st_mode & 0o777, 0o600)
        self.assertNotIn('private-fixture', output.getvalue())
        self.assertNotIn('person@example', output.getvalue())

    def test_invalid_second_license_does_not_replace_first(self):
        first = Path(self.tmp.name) / 'fs.txt'
        first.write_text('person@example.invalid\n4321\na\nb\n')
        second = Path(self.tmp.name) / 'meld.txt'
        second.write_text('incorrect')
        original = (self.release / 'license.txt').read_bytes()
        with patch.object(n, 'linux'):
            self.assertEqual(n.main(['import-licenses', '--freesurfer', str(first), '--meld', str(second)]), 1)
        self.assertEqual((self.release / 'license.txt').read_bytes(), original)

    def test_replaced_license_has_private_backup(self):
        source = Path(self.tmp.name) / 'new meld.txt'
        source.write_text('TEST FIXTURE ONLY\nLicense ID: 654321\n')
        original = (self.release / 'meld_license.txt').read_bytes()
        with patch.object(n, 'linux'):
            self.assertEqual(n.main(['import-licenses', '--meld', str(source)]), 0)
        backups = list((self.state / 'license-backups').iterdir())
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), original)
        self.assertEqual(backups[0].stat().st_mode & 0o777, 0o600)

    def test_license_status_does_not_claim_operational_validity(self):
        with patch.object(n, 'linux'):
            self.assertEqual(n.main(['license-status']), 0)
        report = json.loads((self.state / 'license-status.json').read_text())
        self.assertEqual(report['files']['meld_license.txt'], 'SYNTAX_OK')
        self.assertIn('does not establish licence validity', report['scope'])


class FreeSurferInstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        path = Path(__file__).parents[1] / 'tools/install_freesurfer.py'
        spec = importlib.util.spec_from_file_location('freesurfer_installer_fixture', path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.root = Path(self.tmp.name)
        self.patches = [
            patch.object(self.module.launcher, 'STATE', self.root),
            patch.object(self.module, 'profile', return_value=('20.04', ('fixture.deb', 'expected-md5'))),
            patch.object(self.module.launcher, 'require_space'),
            patch.object(self.module, 'TARGET', self.root / 'system/freesurfer/7.4.1'),
            patch.object(self.module, 'installed_package', return_value=''),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_no_download_without_personal_acceptance(self):
        with patch.object(self.module.launcher, 'run') as runner:
            self.assertEqual(self.module.main([]), 2)
            runner.assert_not_called()

    def test_checksum_mismatch_prevents_package_installation(self):
        def fake_download(command):
            Path(command[command.index('--output') + 1]).write_bytes(b'corrupted fixture')
        with patch.object(self.module.launcher, 'run', side_effect=fake_download), patch.object(self.module, 'validate_package') as validator:
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                self.module.main(['--accept-freesurfer-license', '--host-storage', str(self.root)])
            validator.assert_not_called()

    def test_existing_installation_is_never_replaced(self):
        target = self.module.TARGET
        target.mkdir(parents=True)
        (target / 'existing').write_text('preserve')
        with patch.object(self.module.launcher, 'run') as runner:
            with self.assertRaisesRegex(ValueError, 'already exists'):
                self.module.main(['--accept-freesurfer-license', '--host-storage', str(self.root)])
            runner.assert_not_called()
        self.assertEqual((target / 'existing').read_text(), 'preserve')

    def test_wrong_package_identity_is_rejected(self):
        with patch.object(self.module.launcher, 'run',
                          return_value=subprocess.CompletedProcess([], 0, 'unrelated 7.4.1 amd64')):
            with self.assertRaisesRegex(ValueError, 'Unexpected FreeSurfer package'):
                self.module.validate_package(self.root / 'fixture.deb')

    def test_failed_apt_preserves_failure_and_does_not_record_installed(self):
        package = self.root / 'downloads/fixture.deb'
        package.parent.mkdir()
        package.write_bytes(b'fixture')
        failure = subprocess.CalledProcessError(100, ['apt-get'])
        with patch.object(self.module, 'checksums', return_value=('expected-md5', 'sha256-fixture')), \
                patch.object(self.module, 'validate_package'), \
                patch.object(self.module.launcher, 'run', side_effect=failure):
            with self.assertRaises(subprocess.CalledProcessError) as caught:
                self.module.main(['--accept-freesurfer-license', '--host-storage', str(self.root)])
        self.assertEqual(caught.exception.returncode, 100)
        record = json.loads((self.root / 'freesurfer-install.json').read_text())
        self.assertEqual(record['status'], 'PACKAGE_VERIFIED')

    def test_installed_package_is_not_replaced_even_if_directory_missing(self):
        with patch.object(self.module, 'installed_package', return_value='install ok installed 6.0.0'), \
                patch.object(self.module.launcher, 'run') as runner:
            with self.assertRaisesRegex(ValueError, 'already exists'):
                self.module.main(['--accept-freesurfer-license', '--host-storage', str(self.root)])
            runner.assert_not_called()


if __name__ == '__main__':
    unittest.main()
