import os, platform, sys, subprocess
from importlib.metadata import version, PackageNotFoundError

def _read(path):
    try: return open(path, encoding="utf-8").read().strip()
    except OSError: return None

def limits():
    cpu, mem, swap = _read("/sys/fs/cgroup/cpu.max"), _read("/sys/fs/cgroup/memory.max"), _read("/sys/fs/cgroup/memory.swap.max")
    quota = None if not cpu or cpu.startswith("max") else float(cpu.split()[0]) / int(cpu.split()[1])
    return {"cpu_quota": quota, "memory_bytes": None if mem in (None, "max") else int(mem), "swap_bytes": None if swap in (None, "max") else int(swap)}

def preflight(cfg, allow_unconstrained=False):
    found = limits()
    expected = cfg["expected_limits"]
    ok = all(found[k] is not None and abs(found[k] - expected[k]) <= (0.01 if k == "cpu_quota" else 0) for k in expected)
    if not ok and not allow_unconstrained:
        raise RuntimeError(f"resource limits do not match profile: detected={found}, expected={expected}; use --allow-unconstrained only knowingly")
    return {"ok": ok, "unconstrained": not ok, "limits": found, "python": sys.version, "platform": platform.platform(), "architecture": platform.machine()}

def metadata(cfg, env):
    try: commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception: commit = None
    packages = {}
    for package in ("cryptography", "pqcrypto", "ascon", "PyYAML", "pandas", "scipy"):
        try: packages[package] = version(package)
        except PackageNotFoundError: packages[package] = None
    return {"config": cfg, "environment": env, "dependencies": packages,
            "ascon_source_revision": packages.get("ascon"), "git_commit": commit}
