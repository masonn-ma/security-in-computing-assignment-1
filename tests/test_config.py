from crypto_bench.config import load_config

def test_default_config():
    cfg = load_config("configs/default.yaml")
    assert cfg["measured_trials"] > 0
    assert len(cfg["payload_sizes"]) == len(set(cfg["payload_sizes"]))
