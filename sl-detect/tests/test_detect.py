#!/usr/bin/env python3
"""
Unit tests for sl-detect.

Stdlib `unittest` only — no pytest, no third-party deps, so this runs on the
minimal live ISO. From the repo root:

    python3 -m unittest discover -s sl-detect/tests -v
    # or
    python3 sl-detect/tests/test_detect.py
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import detect  # noqa: E402

T = detect.DEFAULTS


class RecommendEnv(unittest.TestCase):
    def test_imedia_s2883_reference(self):
        # Bay Trail: no Wayland, 3727 MB, x86_64  -> forced XFCE
        self.assertEqual(
            detect.recommend_env(False, 3727, "x86_64", T), "xfce-themed"
        )

    def test_full_when_wayland_and_4gb(self):
        self.assertEqual(
            detect.recommend_env(True, 4096, "x86_64", T), "hyprland-astal-full"
        )

    def test_lite_when_wayland_and_2gb(self):
        self.assertEqual(
            detect.recommend_env(True, 3000, "x86_64", T), "hyprland-astal-lite"
        )

    def test_xfce_when_wayland_but_low_ram(self):
        self.assertEqual(
            detect.recommend_env(True, 1500, "x86_64", T), "xfce-themed"
        )

    def test_openbox_when_under_1gb(self):
        self.assertEqual(
            detect.recommend_env(True, 768, "x86_64", T), "openbox-minimal"
        )

    def test_arm32_always_openbox(self):
        self.assertEqual(
            detect.recommend_env(True, 8192, "arm32", T), "openbox-minimal"
        )

    def test_no_wayland_beats_high_ram(self):
        self.assertEqual(
            detect.recommend_env(False, 16000, "x86_64", T), "xfce-themed"
        )

    def test_ram_unknown_zero_does_not_force_openbox(self):
        # ram_mb == 0 means "couldn't read it"; must not drop to openbox.
        self.assertEqual(
            detect.recommend_env(False, 0, "x86_64", T), "xfce-themed"
        )


class RecommendFs(unittest.TestCase):
    def test_hdd_is_ext4(self):
        self.assertEqual(detect.recommend_fs("hdd", 3727, T), "ext4")

    def test_ssd_low_ram_is_ext4(self):
        self.assertEqual(detect.recommend_fs("ssd", 1800, T), "ext4")

    def test_ssd_with_4gb_is_btrfs(self):
        self.assertEqual(detect.recommend_fs("ssd", 8192, T), "btrfs")

    def test_emmc_is_f2fs(self):
        self.assertEqual(detect.recommend_fs("emmc", 4096, T), "f2fs")


class RecommendKernel(unittest.TestCase):
    def test_hdd_forces_lts(self):
        self.assertEqual(detect.recommend_kernel("hdd", 2022, T), "linux-lts")

    def test_old_cpu_on_ssd_is_lts(self):
        self.assertEqual(detect.recommend_kernel("ssd", 2013, T), "linux-lts")

    def test_modern_cpu_on_ssd_is_zen(self):
        self.assertEqual(detect.recommend_kernel("ssd", 2022, T), "linux-zen")

    def test_unknown_cpu_year_on_ssd_is_zen(self):
        self.assertEqual(detect.recommend_kernel("ssd", None, T), "linux-zen")


class IoScheduler(unittest.TestCase):
    def test_hdd_bfq(self):
        self.assertEqual(detect.recommend_io_scheduler("hdd"), "bfq")

    def test_ssd_none(self):
        self.assertEqual(detect.recommend_io_scheduler("ssd"), "none")


class GpuRules(unittest.TestCase):
    def setUp(self):
        self.rules = detect.load_gpu_rules()

    def _classify(self, description):
        import re
        for pattern, family, driver, wl in self.rules:
            if re.search(pattern, description, re.I):
                return family, driver, wl
        return "unknown", "modesetting", False

    def test_bay_trail_no_wayland(self):
        fam, drv, wl = self._classify(
            "Intel Corporation Atom Processor Z36xxx/Z37xxx Series Graphics"
        )
        self.assertEqual(fam, "intel_bay_trail")
        self.assertEqual(drv, "i915")
        self.assertFalse(wl)

    def test_rtx_wayland_ok(self):
        fam, drv, wl = self._classify("NVIDIA Corporation GeForce RTX 3060 Ti")
        self.assertEqual(drv, "nvidia")
        self.assertTrue(wl)

    def test_kepler_falls_back(self):
        fam, drv, wl = self._classify("NVIDIA Corporation GK107 GeForce GTX 650")
        self.assertEqual(drv, "nouveau")
        self.assertFalse(wl)

    def test_amd_rdna_wayland_ok(self):
        fam, drv, wl = self._classify("AMD Radeon RX 6700 XT")
        self.assertEqual(drv, "amdgpu")
        self.assertTrue(wl)

    def test_old_radeon_hd_no_wayland(self):
        fam, drv, wl = self._classify("AMD Radeon HD 6450")
        self.assertEqual(drv, "radeon")
        self.assertFalse(wl)

    def test_old_gma_no_wayland(self):
        fam, drv, wl = self._classify(
            "Intel Corporation Mobile 945GM/GMS, 943/940GML Express "
            "Integrated Graphics Controller"
        )
        self.assertEqual(fam, "intel_gma")
        self.assertFalse(wl)

    def test_arc_wayland_ok(self):
        fam, drv, wl = self._classify("Intel Corporation DG2 [Arc A770]")
        self.assertEqual(fam, "intel_arc")
        self.assertTrue(wl)


class PcPrincipalReference(unittest.TestCase):
    """Ryzen 5 5600 + RTX 3070 Ti, 32 GB, SATA SSD — the current dev machine.

    The high-end counterpart of the iMedia S2883 reference: values are the
    real `sl-detect --json` output from that hardware.
    """

    def test_gpu_is_turing_plus_with_wayland(self):
        orig = detect._pci_display_devices
        try:
            detect._pci_display_devices = lambda: [
                "NVIDIA Corporation GA104 [GeForce RTX 3070 Ti]"
            ]
            gpu = detect.detect_gpu()
        finally:
            detect._pci_display_devices = orig
        self.assertEqual(gpu["family"], "nvidia_turing_plus")
        self.assertEqual(gpu["driver"], "nvidia")
        self.assertTrue(gpu["wayland_ok"])

    def test_cpu_year_beats_generic_ryzen_hint(self):
        # "5600 = 2022" must win over the catch-all "ryzen = 2019".
        orig = detect._cpu_model
        try:
            detect._cpu_model = lambda: "AMD Ryzen 5 5600 6-Core Processor"
            self.assertEqual(detect.detect_cpu_year(), 2022)
        finally:
            detect._cpu_model = orig

    def test_recommendations(self):
        self.assertEqual(
            detect.recommend_env(True, 32006, "x86_64", T), "hyprland-astal-full"
        )
        self.assertEqual(detect.recommend_fs("ssd", 32006, T), "btrfs")
        self.assertEqual(detect.recommend_kernel("ssd", 2022, T), "linux-zen")
        self.assertEqual(detect.recommend_io_scheduler("ssd"), "none")


class SocGpuRules(unittest.TestCase):
    """ARM SoC GPUs, matched against /proc/device-tree/compatible."""

    def setUp(self):
        self.rules = detect.load_soc_gpu_rules()

    def _classify(self, compatible):
        import re
        for pattern, family, driver, wl, label in self.rules:
            if re.search(pattern, compatible, re.I):
                return family, driver, wl, label
        return "unknown", "modesetting", False, "unknown"

    def test_raspberry_pi_4(self):
        fam, drv, wl, _ = self._classify(
            "raspberrypi,4-model-b brcm,bcm2711"
        )
        self.assertEqual(fam, "videocore_vc6")
        self.assertEqual(drv, "v3d")
        self.assertTrue(wl)

    def test_raspberry_pi_5(self):
        fam, drv, wl, _ = self._classify(
            "raspberrypi,5-model-b brcm,bcm2712"
        )
        self.assertEqual(fam, "videocore_vc7")
        self.assertTrue(wl)

    def test_raspberry_pi_3_too_weak(self):
        fam, drv, wl, _ = self._classify(
            "raspberrypi,3-model-b brcm,bcm2837"
        )
        self.assertEqual(fam, "videocore_vc4")
        self.assertFalse(wl)

    def test_rk3588_wayland_ok(self):
        fam, drv, wl, _ = self._classify("rockchip,rk3588")
        self.assertEqual(fam, "mali_valhall_g610")
        self.assertEqual(drv, "panfrost")
        self.assertTrue(wl)

    def test_pinebook_pro_rk3399(self):
        fam, drv, wl, _ = self._classify("pine64,pinebook-pro rockchip,rk3399")
        self.assertEqual(fam, "mali_midgard_t860")
        self.assertTrue(wl)

    def test_unmatched_soc_falls_through(self):
        fam, drv, wl, _ = self._classify("some,unknown-soc")
        self.assertEqual(fam, "unknown")
        self.assertFalse(wl)


class DeviceTreeGpu(unittest.TestCase):
    """detect_gpu() must fall back to the device-tree path when lspci finds
    nothing — the situation on every real ARM SBC."""

    def setUp(self):
        self._orig_pci = detect._pci_display_devices
        self._orig_read = detect._read
        detect._pci_display_devices = lambda: []

    def tearDown(self):
        detect._pci_display_devices = self._orig_pci
        detect._read = self._orig_read

    def test_rpi4_detected_without_pci(self):
        detect._read = lambda path: (
            "raspberrypi,4-model-b\x00brcm,bcm2711"
            if path == "/proc/device-tree/compatible" else ""
        )
        gpu = detect.detect_gpu()
        self.assertEqual(gpu["family"], "videocore_vc6")
        self.assertTrue(gpu["wayland_ok"])

    def test_no_devicetree_and_no_pci_is_unknown(self):
        detect._read = lambda path: ""
        gpu = detect.detect_gpu()
        self.assertEqual(gpu["family"], "unknown")
        self.assertFalse(gpu["wayland_ok"])


class ThresholdLoading(unittest.TestCase):
    def test_defaults_present(self):
        vals = detect.load_thresholds()
        for key in ("FULL_RAM_MB", "LITE_RAM_MB", "XFCE_RAM_MB", "LTS_CPU_YEAR"):
            self.assertIn(key, vals)
            self.assertIsInstance(vals[key], int)

    def test_kernel_year_map_parsed(self):
        pairs = dict(detect.load_kernel_year_map())
        self.assertEqual(pairs.get("j1900"), 2013)
        self.assertNotIn("lts_cpu_year", pairs)  # threshold line excluded


class Arch(unittest.TestCase):
    def test_maps_known_machines(self):
        cases = {
            "x86_64": "x86_64", "amd64": "x86_64",
            "aarch64": "arm64", "arm64": "arm64",
            "armv7l": "arm32", "armv6l": "arm32",
        }
        orig = detect.platform.machine
        try:
            for raw, expected in cases.items():
                detect.platform.machine = lambda r=raw: r
                self.assertEqual(detect.detect_arch(), expected)
        finally:
            detect.platform.machine = orig


class StorageType(unittest.TestCase):
    def test_explicit_device_classes(self):
        self.assertEqual(detect.detect_storage_type("mmcblk0"), "emmc")
        self.assertEqual(detect.detect_storage_type("nvme0n1"), "ssd")


class SmokeReport(unittest.TestCase):
    def test_build_report_shape(self):
        r = detect.build_report()
        self.assertIn(r["recommend"]["env"], {
            "hyprland-astal-full", "hyprland-astal-lite",
            "xfce-themed", "openbox-minimal",
        })
        self.assertIn(r["recommend"]["fs"], {"btrfs", "ext4", "xfs", "f2fs"})
        self.assertIn(r["recommend"]["kernel"], {"linux-lts", "linux-zen"})
        self.assertIsInstance(r["ram_mb"], int)
        # format_report must not raise on real hardware output
        self.assertIn("sl-detect", detect.format_report(r))


if __name__ == "__main__":
    unittest.main(verbosity=2)
