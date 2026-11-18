#!/usr/bin/env python3
"""
Unit tests for sl-ctl.

Stdlib `unittest` only, same as sl-detect. From the repo root:

    python3 -m unittest discover -s sl-ctl/tests -v
"""

import importlib.util
import json
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


class RestorePoints(unittest.TestCase):
    """ext4 restore points: roll back reinstalls the old versions from the cache."""

    def test_rollback_picks_cached_old_versions(self):
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            rdir, cache = tmp / "rp", tmp / "pkg"
            point = rdir / "20261114-120000"
            point.mkdir(parents=True)
            cache.mkdir()
            (point / "packages").write_text("bash 5.2-1\nmesa 1:25.0-1\nzlib 1.3-1\n")
            for f in ("mesa-1:25.0-1-x86_64.pkg.tar.zst", "mesa-1:25.0-1-x86_64.pkg.tar.zst.sig"):
                (cache / f).write_text("")
            now = "bash 5.2-1\nmesa 1:25.1-1\nzlib 1.3.1-1\nnewpkg 1-1\n"
            calls = []

            def fake_sh(cmd, **kw):
                calls.append(cmd)
                out = now if cmd[:2] == ["pacman", "-Q"] else ""
                return subprocess.CompletedProcess(cmd, 0, stdout=out)

            with mock.patch.object(sl_ctl, "RESTORE_DIR", rdir), \
                 mock.patch.object(sl_ctl, "PKG_CACHE", cache), \
                 mock.patch.object(sl_ctl, "_sh", side_effect=fake_sh), \
                 mock.patch("builtins.print"):
                self.assertEqual(sl_ctl._restore_rollback("1"), 0)
            upgrades = [c for c in calls if c[:2] == ["pacman", "-U"]]
            self.assertEqual(len(upgrades), 1)
            # only mesa has a cached copy; the .sig is never passed to pacman
            self.assertEqual([Path(x).name for x in upgrades[0][3:]], ["mesa-1:25.0-1-x86_64.pkg.tar.zst"])


if __name__ == "__main__":
    unittest.main(verbosity=2)


class PolkitAgentRepair(unittest.TestCase):
    """2026.11.14.2 shipped six desktops without a polkit agent; sl-ctl update fixes it."""

    def _run(self, installed):
        calls = []
        with mock.patch.object(sl_ctl, "_installed", side_effect=lambda p: p in installed), \
             mock.patch.object(sl_ctl, "_sh", side_effect=lambda cmd, **k: calls.append(cmd) or mock.Mock(returncode=0)), \
             mock.patch("builtins.print"):
            sl_ctl._ensure_polkit_agent()
        return calls

    def test_xfce_without_agent_gets_polkit_gnome(self):
        self.assertEqual(self._run({"xfce4-session"}),
                         [["pacman", "-S", "--needed", "--noconfirm", "polkit-gnome"]])

    def test_kde_gets_the_kde_agent(self):
        self.assertEqual(self._run({"plasma-workspace"})[0][-1], "polkit-kde-agent")

    def test_nothing_when_an_agent_exists_or_no_desktop(self):
        self.assertEqual(self._run({"xfce4-session", "polkit-gnome"}), [])
        self.assertEqual(self._run({"gnome-shell"}), [])
        self.assertEqual(self._run(set()), [])


class GpuDriverRepair(unittest.TestCase):
    """sl-detect recommended "nvidia" but nothing ever pacstrapped it — only
    lib32-nvidia-utils, with the Gaming flavor, on top of a base driver that
    didn't exist. sl-ctl update brings it to systems that already hit this."""

    def _run(self, driver, installed=frozenset()):
        calls = []

        def fake_sh(cmd, **k):
            if "--json" in cmd:
                return mock.Mock(stdout=json.dumps({"gpu": {"driver": driver}}))
            calls.append(cmd)
            return mock.Mock(returncode=0)

        with mock.patch.object(sl_ctl, "_installed", side_effect=lambda p: p in installed), \
             mock.patch.object(sl_ctl, "_sh", side_effect=fake_sh), \
             mock.patch("builtins.print"):
            sl_ctl._ensure_gpu_driver()
        return calls

    def test_nvidia_without_driver_gets_installed(self):
        self.assertEqual(self._run("nvidia"),
                         [["pacman", "-S", "--needed", "--noconfirm",
                           "nvidia-dkms", "nvidia-utils", "nvidia-settings"]])

    def test_nouveau_is_left_alone(self):
        self.assertEqual(self._run("nouveau"), [])

    def test_non_nvidia_gpu_is_left_alone(self):
        self.assertEqual(self._run("amdgpu"), [])

    def test_nothing_when_driver_already_installed(self):
        self.assertEqual(self._run("nvidia", installed={"nvidia-utils"}), [])
