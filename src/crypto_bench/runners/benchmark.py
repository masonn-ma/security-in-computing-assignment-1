import csv, json, os, random, time, uuid
from datetime import datetime, timezone
from pathlib import Path
from ..data_generation import payload
from ..timing import measure
from ..environment import metadata, preflight
from ..export import export_workbook
from ..algorithms.symmetric import SymmetricAdapter
from ..algorithms.asymmetric import x25519_exchange, ffdh_exchange, ml_kem_exchange
from ..algorithms.hashing import digest

FIELDS = ["category","algorithm","operation","payload_size_bytes","trial",
          "execution_time_ns","execution_time_ms","baseline_rss_mib",
          "peak_rss_mib","incremental_peak_rss_mib","overhead_bytes","batch_count"]

def _prepared(cat, name, op, data, adapter):
    """Prepare all inputs before timing, including decrypt ciphertext."""
    if cat == "symmetric":
        if op == "encrypt":
            nonce = os.urandom(adapter.nonce_size)
            return lambda: adapter.encrypt(data, nonce)
        nonce, ciphertext = adapter.encrypt(data)
        return lambda: adapter.decrypt(nonce, ciphertext)
    if cat == "hashing":
        return lambda: digest(name, data)
    return lambda: _exchange(name)

def _exchange(name):
    if name == "x25519":
        secret, info = x25519_exchange()
    elif name == "ffdh-group14":
        secret, info = ffdh_exchange()
    else:
        secret, info = ml_kem_exchange()
        if not info["matches"]:
            raise ValueError("ML-KEM shared secrets differ")
    return secret, info["public_bytes"]

def _overhead(cat, result, adapter=None):
    if cat == "asymmetric":
        return result[1]
    if cat == "symmetric":
        return (len(result[0]) + 16) if isinstance(result, tuple) else (adapter.nonce_size + 16)
    return len(result)

def run(cfg, category="all", algorithm=None, operation=None, payload_size=None,
        allow_unconstrained=False):
    run_id = uuid.uuid4().hex[:12]
    root = Path(cfg["output_dir"]) / run_id
    root.mkdir(parents=True, exist_ok=False)
    raw = root / "raw_measurements.csv"
    rows = []
    env = preflight(cfg, allow_unconstrained)
    meta = metadata(cfg, env)
    meta.update({"run_id": run_id, "started_at": datetime.now(timezone.utc).isoformat(),
                 "status": "running", "selected_filters": {
                     "category": category, "algorithm": algorithm,
                     "operation": operation, "payload_size_bytes": payload_size}})
    (root / "metadata.json").write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    if cfg.get("pre_run_idle_seconds", 0):
        time.sleep(cfg["pre_run_idle_seconds"])

    def save(row):
        rows.append(row)
        with raw.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    try:
        categories = [category] if category != "all" else ["symmetric", "asymmetric", "hashing"]
        rng = random.Random(cfg["random_seed"])
        for cat in categories:
            names = [n for n in cfg["algorithms"][cat] if not algorithm or n == algorithm]
            sizes = [None] if cat == "asymmetric" else ([payload_size] if payload_size else cfg["payload_sizes"])
            ops = ["encrypt", "decrypt"] if cat == "symmetric" else ["digest"] if cat == "hashing" else ["exchange"]
            if operation:
                ops = [operation]
            for size in sizes:
                for op in ops:
                    data = payload(size, cfg["random_seed"]) if size else None
                    adapters = {n: SymmetricAdapter(n) for n in names} if cat == "symmetric" else {}
                    # Interleave candidates in each trial round, while retaining serial execution.
                    for name in names:
                        for _ in range(cfg["warmup_trials"]):
                            fn = _prepared(cat, name, op, data, adapters.get(name))
                            fn()
                    for trial in range(1, cfg["measured_trials"] + 1):
                        order = list(names)
                        rng.shuffle(order)
                        for name in order:
                            fn = _prepared(cat, name, op, data, adapters.get(name))
                            result, ns, base, peak = measure(fn)
                            save({"category": cat, "algorithm": name, "operation": op,
                                  "payload_size_bytes": size, "trial": trial,
                                  "execution_time_ns": ns, "execution_time_ms": ns / 1e6,
                                  "baseline_rss_mib": base / 2**20, "peak_rss_mib": peak / 2**20,
                                  "incremental_peak_rss_mib": (peak - base) / 2**20,
                                  "overhead_bytes": _overhead(cat, result, adapters.get(name)), "batch_count": 1})
        meta["status"] = "complete"
        meta["completed_at"] = datetime.now(timezone.utc).isoformat()
        export_workbook(raw, metadata=meta)
    except Exception as exc:
        meta.update({"status": "incomplete", "completed_at": datetime.now(timezone.utc).isoformat(),
                     "error": f"{type(exc).__name__}: {exc}"})
    finally:
        (root / "metadata.json").write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    return root, meta["status"]
