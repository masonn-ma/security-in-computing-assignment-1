from pathlib import Path
import yaml

SYMMETRIC = {"aes-gcm", "chacha20-poly1305", "ascon-aead128"}
ASYMMETRIC = {"x25519", "ffdh-group14", "ml-kem-768"}
HASHING = {"sha256", "sha3-256", "ascon-hash256"}

def load_config(path="configs/default.yaml"):
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg.get("payload_sizes"), list) or not cfg["payload_sizes"]:
        raise ValueError("payload_sizes must be a non-empty list")
    sizes = cfg["payload_sizes"]
    if len(set(sizes)) != len(sizes) or any(not isinstance(x, int) or x <= 0 for x in sizes):
        raise ValueError("payload sizes must be unique positive integers")
    for key in ("warmup_trials", "measured_trials"):
        if not isinstance(cfg.get(key), int) or cfg[key] <= 0:
            raise ValueError(f"{key} must be positive")
    selected = set(sum((cfg["algorithms"][k] for k in ("symmetric", "asymmetric", "hashing")), []))
    allowed = SYMMETRIC | ASYMMETRIC | HASHING
    if not selected <= allowed:
        raise ValueError(f"unsupported algorithms: {selected - allowed}")
    if not isinstance(cfg.get("anova_alpha"), (int, float)) or not 0 < cfg["anova_alpha"] < 1:
        raise ValueError("anova_alpha must be between zero and one")
    cfg["_path"] = str(Path(path))
    return cfg
