#!/usr/bin/env python3
"""
Unit tests for sl-ctl.

Stdlib `unittest` only, same as sl-detect. From the repo root:

    python3 -m unittest discover -s sl-ctl/tests -v
"""

import importlib.util
import os
import pwd
import unittest
from pathlib import Path
from unittest import mock

# sl-ctl.py has a hyphen in its name, so it can't be a plain `import`.
_spec = importlib.util.spec_from_file_location(
    "sl_ctl", Path(__file__).resolve().parents[1] / "sl-ctl.py"
)
sl_ctl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sl_ctl)

ME = pwd.getpwuid(os.getuid())
HINTS = ("SUDO_USER", "DOAS_USER", "PKEXEC_UID", "SUDO_UID")


class InvokingUser(unittest.TestCase):
    def _resolve(self, env, loginuid="4294967295"):
        clean = {k: v for k, v in os.environ.items() if k not in HINTS}
        clean.update(env)
        with mock.patch.dict(os.environ, clean, clear=True), \
             mock.patch.object(sl_ctl.Path, "read_text", return_value=loginuid):
            return sl_ctl._invoking_user()

    @unittest.skipIf(ME.pw_uid == 0, "needs a non-root account to resolve")
    def test_sudo_user(self):
        self.assertEqual(self._resolve({"SUDO_USER": ME.pw_name}), ME.pw_name)

    @unittest.skipIf(ME.pw_uid == 0, "needs a non-root account to resolve")
    def test_pkexec_has_no_sudo_user(self):
        # The sl-welcome path: pkexec sets PKEXEC_UID, never SUDO_USER.
        self.assertEqual(self._resolve({"PKEXEC_UID": str(ME.pw_uid)}), ME.pw_name)

    @unittest.skipIf(ME.pw_uid == 0, "needs a non-root account to resolve")
    def test_loginuid_when_env_is_empty(self):
        # `su -` / root shell: no env hint at all, only the audit loginuid.
        self.assertEqual(self._resolve({}, loginuid=str(ME.pw_uid)), ME.pw_name)

    def test_never_returns_root(self):
        self.assertIsNone(self._resolve({"SUDO_USER": "root", "PKEXEC_UID": "0"}))

    def test_unknown_user_is_ignored(self):
        self.assertIsNone(self._resolve({"SUDO_USER": "sl-no-such-user"}))

    def test_nothing_to_go_on(self):
        # Was: silently ran paru as "nobody".
        self.assertIsNone(self._resolve({}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
