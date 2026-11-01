import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shlex
import socket
import unittest
from unittest.mock import patch


class EnrollmentChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).with_name('enroll_seal_key.py')
        if not path.exists():
            cls.module = None
            return
        spec = importlib.util.spec_from_file_location('enroll_seal_key', path)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def module_required(self):
        self.assertIsNotNone(self.module, 'Enrollment helper is not implemented')
        return self.module

    def test_password_is_one_literal_shell_word(self):
        m = self.module_required()
        for secret in ['Example7', 'with spaces', "a'quote", '$(never-execute); echo danger', 'back`tick']:
            payload = json.loads(m.make_payload(secret, 'ssh-rsa AAAA test'))
            self.assertEqual(shlex.split(payload['password']), [secret])

    def test_rejects_echo_option_password_before_sending(self):
        m = self.module_required()
        with self.assertRaises(ValueError):
            m.make_payload('-n', 'ssh-rsa AAAA test')

    def test_rejects_key_with_shell_quote_or_multiple_lines(self):
        m = self.module_required()
        for key in ["ssh-rsa AAAA bad'quote", 'ssh-rsa AAAA\nssh-rsa BBBB', 'ssh-ed25519 AAAA test']:
            with self.assertRaises(ValueError):
                m.validate_key(key)

    def test_dry_run_does_not_connect_or_prompt(self):
        m = self.module_required()
        with patch.object(socket, 'create_connection', side_effect=AssertionError('network')), patch.object(m.getpass, 'getpass', side_effect=AssertionError('prompt')), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(m.main([]), 0)

    def test_open_ssh_port_stops_before_password_or_post(self):
        m = self.module_required()
        with patch.object(m, 'ssh_banner', return_value='SSH-2.0-OpenSSH_7.9'), patch.object(m, 'request', side_effect=AssertionError('request')), patch.object(m.getpass, 'getpass', side_effect=AssertionError('prompt')), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertNotEqual(m.main(['--send']), 0)

    def test_single_enrollment_keeps_password_out_of_output(self):
        m = self.module_required()
        observed = []
        def transport(host, pin, method, path, body=None):
            if method == 'POST':
                observed.append((path, json.loads(body)))
                return 200, b'OK'
            if path == '/currentsetting.htm':
                return 200, b'Model=RBR850\nFirmware=V7.2.8.8_5.1.24\n'
            return 200, b'{"seal_version":"v2.2.9.6-0-gc6614a48","api_versions":["1.0"]}'
        out = io.StringIO()
        with patch.object(m, 'ssh_banner', side_effect=[None, 'SSH-2.0-dropbear_2019.78']), patch.object(m, 'request', side_effect=transport), patch.object(m.sys.stdin, 'isatty', return_value=True), patch.object(m.getpass, 'getpass', return_value='PrivateExample7'), contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            self.assertEqual(m.main(['--send']), 0)
        self.assertEqual(len(observed), 1)
        self.assertEqual(observed[0][0], '/api/v1/enable_ssh')
        self.assertEqual(observed[0][1]['username'], 'admin')
        self.assertEqual(shlex.split(observed[0][1]['password']), ['PrivateExample7'])
        self.assertNotIn('PrivateExample7', out.getvalue())

    def test_banner_excludes_coalesced_binary_key_exchange(self):
        m = self.module_required()
        with patch.object(socket, 'create_connection') as connect:
            connect.return_value.__enter__.return_value.recv.return_value = b'SSH-2.0-dropbear\r\n\x00\x00\x01binary-kex'
            self.assertEqual(m.ssh_banner('192.168.1.1'), 'SSH-2.0-dropbear')


if __name__ == '__main__':
    unittest.main()
