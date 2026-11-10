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
            (self.release / name).write_text('test fixture only')
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
            generated = json.loads((self.state / 'compose.cpu.json').read_text())
            service = generated['services']['meld_graph']
            self.assertEqual(service['image'], self.config['meld_image_digest'])
            self.assertEqual(service['volumes'][0]['source'], self.config['data'])
            self.assertNotIn('devices', service['deploy']['resources']['reservations'])
            self.assertEqual(generated['secrets'], model['secrets'])

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
            self.assertEqual(runner.call_args.args[0][-2:], ['-id', 'sub-001'])
            runner.reset_mock()
            self.assertEqual(n.main(['run-meld', '--subject', 'sub-001; echo bad']), 1)
            runner.assert_not_called()

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


if __name__ == '__main__':
    unittest.main()
