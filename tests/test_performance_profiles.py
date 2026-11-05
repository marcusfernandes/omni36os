import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "port" / "omni36os" / "omni_performance.py"


class PerformanceProfilesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        cpu = root / "cpu"
        gpu = root / "gpu"
        cpu.mkdir()
        gpu.mkdir()
        self.cpu = cpu
        self.gpu = gpu
        dmc = root / "dmc"
        dmc.mkdir()
        shm = root / "shm"
        shm.mkdir()
        self.shm = shm
        (dmc / "governor").write_text("dmc_ondemand")
        (dmc / "available_governors").write_text("dmc_ondemand performance")
        self.state = root / "state.json"
        self.config = root / "profiles.json"
        self.config.write_text(json.dumps({
            "default": "safe",
            "profiles": {
                "safe": {
                    "cpu_governor": "performance", "cpu_max_mhz": 2000,
                    "gpu_governor": "performance", "gpu_max_mhz": 1000,
                },
                "eco": {
                    "cpu_governor": "powersave", "cpu_max_mhz": 1000,
                    "gpu_governor": "powersave", "gpu_max_mhz": 300,
                },
                "cas_scaled": {
                    "cpu_governor": "performance", "cpu_max_mhz": 1296,
                    "gpu_governor": "performance", "gpu_max_mhz": 520,
                    "scaling": {
                        "enabled": True, "mode": "cas", "sharpness": 0.75, "pacing": True, "target_fps": 60,
                    },
                },
            },
            "ports": {"daytona93": "eco", "heavy_game": "cas_scaled"},
        }))
        for path, value in {
            cpu / "scaling_governor": "ondemand", cpu / "scaling_min_freq": "600000",
            cpu / "scaling_max_freq": "1512000", cpu / "scaling_available_frequencies": "408000 600000 816000 1008000 1296000 1512000",
            cpu / "scaling_available_governors": "ondemand performance powersave",
            gpu / "governor": "simple_ondemand", gpu / "min_freq": "200000000",
            gpu / "max_freq": "600000000", gpu / "available_frequencies": "200000000 300000000 400000000 520000000 600000000",
            gpu / "available_governors": "simple_ondemand performance powersave",
        }.items():
            path.write_text(value)
        self.old_env = {key: os.environ.get(key) for key in
                        ("OMNI_PERF_CPU", "OMNI_PERF_GPU", "OMNI_PERF_DMC", "OMNI_PERF_SHM", "OMNI_PERF_CONFIG", "OMNI_PERF_STATE")}
        os.environ.update({"OMNI_PERF_CPU": str(cpu), "OMNI_PERF_GPU": str(gpu),
                           "OMNI_PERF_DMC": str(dmc), "OMNI_PERF_SHM": str(shm), "OMNI_PERF_CONFIG": str(self.config), "OMNI_PERF_STATE": str(self.state)})
        spec = importlib.util.spec_from_file_location("omni_performance_test", MODULE)
        self.perf = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.perf)
        self.addCleanup(self.restore_env)

    def restore_env(self):
        for key, value in self.old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_apply_caps_profile_to_hardware_safe_frequency_steps(self):
        self.perf.apply("daytona93.zip")
        self.assertEqual((self.cpu / "scaling_max_freq").read_text().strip(), "816000")
        self.assertEqual((self.gpu / "max_freq").read_text().strip(), "300000000")
        self.assertEqual((self.cpu / "scaling_governor").read_text().strip(), "powersave")
        state = json.loads(self.state.read_text())
        self.assertEqual(state["profile"], "eco")

    def test_restore_returns_original_governors_and_limits(self):
        original = {
            "cpu_governor": "ondemand", "cpu_min": "600000", "cpu_max": "1512000",
            "gpu_governor": "simple_ondemand", "gpu_min": "200000000", "gpu_max": "600000000",
            "dmc_governor": "dmc_ondemand",
        }
        self.perf.apply("daytona93.zip")
        self.perf.restore()
        paths = {
            "cpu_governor": self.cpu / "scaling_governor", "cpu_min": self.cpu / "scaling_min_freq",
            "cpu_max": self.cpu / "scaling_max_freq", "gpu_governor": self.gpu / "governor",
            "gpu_min": self.gpu / "min_freq", "gpu_max": self.gpu / "max_freq",
            "dmc_governor": self.perf.DMC / "governor",
        }
        self.assertEqual({key: path.read_text().strip() for key, path in paths.items()}, original)
        self.assertFalse(self.state.exists())

    def test_apply_failure_can_restore_partial_changes(self):
        original_max = (self.cpu / "scaling_max_freq").read_text()
        real_write = self.perf.write
        writes = 0

        def fail_after_cpu_limit(path, value):
            nonlocal writes
            writes += 1
            if writes == 2:
                raise RuntimeError("simulated sysfs write failure")
            real_write(path, value)

        self.perf.write = fail_after_cpu_limit
        with self.assertRaises(RuntimeError):
            self.perf.apply("daytona93.zip")
        self.perf.write = real_write
        self.perf.restore()
        self.assertEqual((self.cpu / "scaling_max_freq").read_text().strip(), original_max.strip())

    def test_profile_selection_and_unknown_profile(self):
        self.assertEqual(self.perf.choose_profile("unknown", json.loads(self.config.read_text()))[0], "safe")
        with self.assertRaises(ValueError):
            self.perf.choose_profile("unknown", json.loads(self.config.read_text()), "missing")

    def test_missing_sysfs_is_safe(self):
        self.perf.CPU = Path(self.tmp.name) / "missing-cpu"
        self.perf.GPU = Path(self.tmp.name) / "missing-gpu"
        self.perf.apply("unknown")
        self.perf.restore()

    def test_scaling_configuration_applied_and_restored(self):
        self.perf.apply("heavy_game.zip")
        self.assertEqual((self.shm / "omni36os-scaler-mode").read_text().strip(), "cas")
        self.assertEqual((self.shm / "omni36os-scaler-sharpness").read_text().strip(), "0.75")
        self.assertEqual((self.shm / "omni36os-scaler-pacing").read_text().strip(), "1")
        self.assertEqual((self.shm / "omni36os-scaler-target-fps").read_text().strip(), "60")
        self.perf.restore()
        self.assertFalse((self.shm / "omni36os-scaler-mode").exists())
        self.assertFalse((self.shm / "omni36os-scaler-sharpness").exists())
        self.assertFalse((self.shm / "omni36os-scaler-pacing").exists())
        self.assertFalse((self.shm / "omni36os-scaler-target-fps").exists())


if __name__ == "__main__":
    unittest.main()
