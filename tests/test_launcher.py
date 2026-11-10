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
                        patch.object(n, 'CONFIG', self.state / 'config.json')]
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
        with patch.object(n.os, 'getuid', return_value=1000, create=True), patch.object(n.os, 'getgid', return_value=1000, create=True), patch.dict(n.os.environ):
            cmd = n.compose(self.config)
            self.assertIn(str(self.release / 'compose.yml'), cmd)
            service = json.loads((self.state / 'compose.local.json').read_text())['services']['meld_graph']
            self.assertEqual(service['image'], self.config['meld_image_digest'])
            self.assertEqual(service['volumes'][0]['source'], self.config['data'])

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


if __name__ == '__main__':
    unittest.main()
