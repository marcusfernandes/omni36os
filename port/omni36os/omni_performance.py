#!/usr/bin/env python3
"""Apply conservative, reversible CPU/GPU profiles while a port is running."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
CONFIG = Path(os.environ.get("OMNI_PERF_CONFIG", BASE / "performance-profiles.json"))
STATE = Path(os.environ.get("OMNI_PERF_STATE", "/run/omni36os-performance.json"))
CPU = Path(os.environ.get("OMNI_PERF_CPU", "/sys/devices/system/cpu/cpufreq/policy0"))
GPU = Path(os.environ.get("OMNI_PERF_GPU", "/sys/class/devfreq/ff400000.gpu"))
DMC = Path(os.environ.get("OMNI_PERF_DMC", "/sys/class/devfreq/dmc"))
SHM = Path(os.environ.get("OMNI_PERF_SHM", "/dev/shm"))
CPU_SAFE_MAX = 1_296_000
GPU_SAFE_MAX = 520_000_000


def read(path: Path) -> str | None:
    try:
        return path.read_text().strip()
    except OSError:
        return None


def write(path: Path, value: str) -> None:
    try:
        path.write_text(value + "\n")
    except PermissionError:
        result = subprocess.run(
            ["sudo", "-n", "tee", str(path)], input=value + "\n",
            text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        if result.returncode:
            raise RuntimeError(f"cannot write {path}")


def frequencies(path: Path) -> list[int]:
    raw = read(path)
    if not raw:
        return []
    return sorted({int(value) for value in re.findall(r"\d+", raw)})


def at_or_below(available: list[int], requested: int, safe_max: int) -> int | None:
    ceiling = min(requested, safe_max)
    choices = [value for value in available if value <= ceiling]
    return max(choices) if choices else None


def load_profiles() -> dict:
    try:
        data = json.loads(CONFIG.read_text())
    except FileNotFoundError:
        return {"disabled": True, "default": "native", "profiles": {"native": {}}, "ports": {}}
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("profiles"), dict)
        or not isinstance(data.get("ports", {}), dict)
    ):
        raise ValueError(f"invalid profile configuration: {CONFIG}")
    return data


def normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def choose_profile(target: str, data: dict, requested: str | None = None) -> tuple[str, dict]:
    name = requested or os.environ.get("OMNI_PERF_PROFILE")
    if not name:
        ports = data.get("ports", {})
        key = normalize(Path(target).stem)
        name = next((profile for port, profile in ports.items() if normalize(port) == key), None)
    name = name or data.get("default", "safe")
    profile = data["profiles"].get(name)
    if not isinstance(profile, dict):
        raise ValueError(f"unknown performance profile: {name}")
    return name, profile


def snapshot() -> dict:
    state = {}
    paths = {
        "cpu_governor": CPU / "scaling_governor",
        "cpu_min": CPU / "scaling_min_freq",
        "cpu_max": CPU / "scaling_max_freq",
        "gpu_governor": GPU / "governor",
        "gpu_min": GPU / "min_freq",
        "gpu_max": GPU / "max_freq",
        "dmc_governor": DMC / "governor",
    }
    for key, path in paths.items():
        value = read(path)
        if value is not None:
            state[key] = value
    return state


def apply(target: str, requested: str | None = None) -> None:
    if STATE.exists():
        restore()
    data = load_profiles()
    if data.get("disabled"):
        print("profile=disabled")
        return
    name, profile = choose_profile(target, data, requested)
    before = snapshot()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"profile": name, "before": before}, sort_keys=True) + "\n")

    cpu_limit = min(int(profile.get("cpu_max_mhz", CPU_SAFE_MAX // 1000)) * 1000, CPU_SAFE_MAX)
    gpu_limit = min(int(profile.get("gpu_max_mhz", GPU_SAFE_MAX // 1_000_000)) * 1_000_000, GPU_SAFE_MAX)
    cpu_step = at_or_below(frequencies(CPU / "scaling_available_frequencies"), cpu_limit, CPU_SAFE_MAX)
    gpu_step = at_or_below(frequencies(GPU / "available_frequencies"), gpu_limit, GPU_SAFE_MAX)

    if cpu_step is not None:
        write(CPU / "scaling_max_freq", str(cpu_step))
    if profile.get("cpu_governor", "performance") in (read(CPU / "scaling_available_governors") or "").split():
        write(CPU / "scaling_governor", profile["cpu_governor"])
    if gpu_step is not None:
        write(GPU / "max_freq", str(gpu_step))
    if profile.get("gpu_governor", "performance") in (read(GPU / "available_governors") or "").split():
        write(GPU / "governor", profile["gpu_governor"])
    if "performance" in (read(DMC / "available_governors") or "").split():
        write(DMC / "governor", "performance")

    scaling = profile.get("scaling")
    if isinstance(scaling, dict) and scaling.get("enabled"):
        mode = scaling.get("mode", "cas")
        sharpness = scaling.get("sharpness", 0.6)
        pacing = "1" if scaling.get("pacing") else "0"
        target_fps = str(scaling.get("target_fps", 60))
        if SHM.exists():
            write(SHM / "omni36os-scaler-mode", str(mode))
            write(SHM / "omni36os-scaler-sharpness", str(sharpness))
            write(SHM / "omni36os-scaler-pacing", pacing)
            write(SHM / "omni36os-scaler-target-fps", target_fps)
    else:
        for f in ("omni36os-scaler-mode", "omni36os-scaler-sharpness", "omni36os-scaler-pacing", "omni36os-scaler-target-fps"):
            (SHM / f).unlink(missing_ok=True)

    print(f"profile={name} cpu_max={cpu_step or 'unchanged'} gpu_max={gpu_step or 'unchanged'}")


def restore() -> None:
    if not STATE.exists():
        return
    data = json.loads(STATE.read_text())
    before = data.get("before", {})
    ordered = (
        ("cpu_max", CPU / "scaling_max_freq"),
        ("cpu_min", CPU / "scaling_min_freq"),
        ("cpu_governor", CPU / "scaling_governor"),
        ("gpu_max", GPU / "max_freq"),
        ("gpu_min", GPU / "min_freq"),
        ("gpu_governor", GPU / "governor"),
        ("dmc_governor", DMC / "governor"),
    )
    for key, path in ordered:
        if key in before:
            write(path, before[key])
    for f in ("omni36os-scaler-mode", "omni36os-scaler-sharpness", "omni36os-scaler-pacing", "omni36os-scaler-target-fps"):
        (SHM / f).unlink(missing_ok=True)
    STATE.unlink(missing_ok=True)


def main(argv: list[str]) -> int:
    try:
        if len(argv) < 2 or argv[1] not in ("begin", "end"):
            print("usage: omni_performance.py begin TARGET [PROFILE] | end", file=sys.stderr)
            return 2
        if argv[1] == "end":
            restore()
        else:
            apply(argv[2] if len(argv) > 2 else "port", argv[3] if len(argv) > 3 else None)
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        print(f"omni_performance: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
