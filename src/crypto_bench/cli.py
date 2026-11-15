import argparse, json
from pathlib import Path
from .config import load_config
from .environment import preflight
from .algorithms.symmetric import SymmetricAdapter
from .algorithms.asymmetric import x25519_exchange, ffdh_exchange, ml_kem_exchange
from .algorithms.hashing import digest
from .runners.benchmark import run
from .export import export_workbook
from .config import SYMMETRIC, ASYMMETRIC, HASHING

def _validate_filters(cfg, args):
    if args.algorithm:
        all_names = set().union(*[set(cfg["algorithms"][c]) for c in ("symmetric", "asymmetric", "hashing")])
        if args.algorithm not in all_names:
            raise ValueError(f"unknown algorithm: {args.algorithm}")
        if args.category != "all" and args.algorithm not in cfg["algorithms"][args.category]:
            raise ValueError(f"{args.algorithm} is not enabled for {args.category}")
    valid_ops = {"symmetric": {"encrypt", "decrypt"}, "hashing": {"digest"}, "asymmetric": {"exchange"}}
    if args.operation:
        cats = [args.category] if args.category != "all" else list(valid_ops)
        if not any(args.operation in valid_ops[c] for c in cats):
            raise ValueError(f"unsupported operation: {args.operation}")
        if args.category == "all" and not all(args.operation in valid_ops[c] for c in cats):
            raise ValueError("an operation filter with --category all must identify one category")
    if args.payload_size is not None and (args.payload_size <= 0 or args.payload_size not in cfg["payload_sizes"]):
        raise ValueError("payload size must be a configured positive payload size")

def main(argv=None):
    p = argparse.ArgumentParser(description="Serial IIoT cryptography benchmark")
    p.add_argument("--config", default="configs/default.yaml")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    pf = sub.add_parser("preflight"); pf.add_argument("--allow-unconstrained", action="store_true")
    r = sub.add_parser("run"); r.add_argument("--category", choices=["all","symmetric","asymmetric","hashing"], default="all"); r.add_argument("--algorithm"); r.add_argument("--operation"); r.add_argument("--payload-size", type=int); r.add_argument("--allow-unconstrained", action="store_true")
    ex = sub.add_parser("export"); ex.add_argument("--input", required=True)
    an = sub.add_parser("analyse"); an.add_argument("--input", required=True)
    args = p.parse_args(argv); cfg = load_config(args.config)
    if args.command == "validate":
        failures = []
        for n in sum((cfg["algorithms"][c] for c in ("symmetric", "asymmetric", "hashing")), []):
            try:
                if n in SYMMETRIC:
                    a = SymmetricAdapter(n); nonce, ct = a.encrypt(b"test"); assert a.decrypt(nonce, ct) == b"test"
                elif n == "x25519": assert x25519_exchange()[0]
                elif n == "ffdh-group14": assert ffdh_exchange()[0]
                elif n == "ml-kem-768": assert ml_kem_exchange()[0]
                else: assert len(digest(n, b"test")) == 32
                print(f"{n}: OK")
            except Exception as exc:
                failures.append(f"{n}: {type(exc).__name__}: {exc}")
        if failures:
            raise RuntimeError("algorithm validation failed:\n" + "\n".join(failures))
        return 0
    if args.command == "preflight":
        print(json.dumps(preflight(cfg, args.allow_unconstrained), indent=2)); return 0
    if args.command == "run":
        _validate_filters(cfg, args)
        root, status = run(cfg, args.category, args.algorithm, args.operation, args.payload_size, args.allow_unconstrained)
        print(f"{status}: {root}"); return 0 if status == "complete" else 1
    if args.command == "export":
        print(export_workbook(args.input)); return 0
    if args.command == "analyse":
        from .statistics import descriptive, anova
        import pandas as pd
        df = pd.read_csv(args.input); print(descriptive(df).to_string(index=False)); print(anova(df).to_string(index=False)); return 0

if __name__ == "__main__": raise SystemExit(main())
