"""Check every raw-data file listed in the experiment manifests against its SHA-256,
and the run counts against the expected key-set size.
Usage (from the archive root): python -I verify_package.py
Diagnostics files are read from data/E1_E5 (in this archive they are included)."""
import sys, json, hashlib, csv
from pathlib import Path
root = Path(__file__).parent
diag = Path(sys.argv[1]) if len(sys.argv) > 1 else None
ok = True
for folder in ("data/E1_E5", "data/E5b"):
    for m in sorted((root / folder).glob("*_manifest.json")):
        man = json.loads(m.read_text()); exp = man["exp"]
        for name, h in man["outputs"].items():
            p = root / folder / name
            if name.endswith("_diagnostics.npz") and diag is not None:
                p = diag / name
            got = hashlib.sha256(p.read_bytes()).hexdigest()
            good = got == h; ok &= good
            print(f"{exp}: {name} {'OK' if good else 'HASH MISMATCH'}")
        n = sum(1 for _ in csv.DictReader(open(root / folder / f"{exp}_runs.csv")))
        good = n == man["expected"] == man["completed"]; ok &= good
        print(f"{exp}: rows {n} / expected {man['expected']} {'OK' if good else 'MISMATCH'}; commit {man['commit'][:10]}; protocol {man['protocol_sha256'][:8]}")
print("ALL OK" if ok else "PROBLEMS FOUND"); sys.exit(0 if ok else 1)
