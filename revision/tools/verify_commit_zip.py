"""Verify a ZIP of the revision commit against the reviewed revision tree.

Usage:
  python -I verify_commit_zip.py ZIP REVIEWED_TREE OUT_JSON
         [--expected-sha SHA] [--ls-tree LS_TREE_TXT]

Checks
  1. ZIP comment is a full 40-hex commit SHA ([0-9a-fA-F]{40}); if
     --expected-sha is given, it must equal the comment (case-insensitive).
     (The comment is archive metadata written by git archive / GitHub;
     it is not proof of commit identity on its own.)
  2. Content: SHA-256 of every file under src/ and revision/ in the ZIP equals
     the reviewed tree (no missing, extra or differing files).
  3. Repository binding (optional, recommended): with --ls-tree, the output of
     `git ls-tree -r <SHA>` from the repository. The git blob id of every
     in-scope ZIP file must equal the blob id recorded in that commit's tree,
     and the tree must contain no extra in-scope files. This ties the archive
     content to the commit object in the repository.
"""
import argparse, hashlib, json, re, sys, zipfile
from pathlib import Path

SCOPE = ("src/", "revision/")
HEX40 = re.compile(r"^[0-9a-fA-F]{40}$")


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def git_blob_id(b):
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("zip"); ap.add_argument("tree"); ap.add_argument("out")
    ap.add_argument("--expected-sha"); ap.add_argument("--ls-tree")
    a = ap.parse_args()

    z = zipfile.ZipFile(a.zip)
    comment = z.comment.decode(errors="replace").strip()
    names = [n for n in z.namelist() if not n.endswith("/")]
    root = names[0].split("/", 1)[0] + "/"
    zbytes = {n[len(root):]: z.read(n) for n in names
              if n.startswith(root) and n[len(root):].startswith(SCOPE)}
    tree = Path(a.tree)
    tfiles = {}
    for p in tree.rglob("*"):
        rel = p.relative_to(tree).as_posix()          # POSIX separators on every OS
        if p.is_file() and rel.startswith(SCOPE) and "__pycache__" not in p.parts:
            tfiles[rel] = sha256(p.read_bytes())
    zfiles = {k: sha256(v) for k, v in zbytes.items()}

    rep = dict(zip_sha256=sha256(Path(a.zip).read_bytes()), commit_from_zip_comment=comment)
    rep["sha_format_ok"] = bool(HEX40.match(comment))
    if a.expected_sha:
        rep["expected_sha"] = a.expected_sha
        rep["expected_sha_format_ok"] = bool(HEX40.match(a.expected_sha))
        rep["expected_sha_matches_comment"] = a.expected_sha.lower() == comment.lower()
    rep["missing_in_zip"] = sorted(set(tfiles) - set(zfiles))
    rep["extra_in_zip"] = sorted(set(zfiles) - set(tfiles))
    rep["differing"] = sorted(k for k in set(tfiles) & set(zfiles) if tfiles[k] != zfiles[k])
    rep["files_compared"] = len(set(tfiles) & set(zfiles))
    rep["content_ok"] = not (rep["missing_in_zip"] or rep["extra_in_zip"] or rep["differing"])

    if a.ls_tree:
        blobs = {}
        for line in Path(a.ls_tree).read_text().splitlines():
            meta, path = line.split("\t", 1)
            mode, typ, oid = meta.split()
            if typ == "blob" and path.startswith(SCOPE):
                blobs[path] = oid
        rb = dict(tree_files=len(blobs),
                  missing_in_commit=sorted(set(zbytes) - set(blobs)),
                  extra_in_commit=sorted(set(blobs) - set(zbytes)),
                  blob_mismatch=sorted(k for k in set(blobs) & set(zbytes) if git_blob_id(zbytes[k]) != blobs[k]))
        rb["ok"] = not (rb["missing_in_commit"] or rb["extra_in_commit"] or rb["blob_mismatch"])
        rep["repository_binding"] = rb

    rep["protocol_sha256"] = zfiles.get("revision/protocol/Deney_Protokolu_v1.0.1.md")
    checks = [rep["sha_format_ok"], rep["content_ok"]]
    if a.expected_sha:
        checks += [rep["expected_sha_format_ok"], rep["expected_sha_matches_comment"]]
    if a.ls_tree:
        checks.append(rep["repository_binding"]["ok"])
    rep["passed"] = all(checks)
    rep["note"] = ("The ZIP comment is archive metadata. Commit identity is established only with "
                   "--ls-tree output taken from the repository (or an equivalent repository check).")
    Path(a.out).write_text(json.dumps(rep, indent=2))
    print(json.dumps({k: v for k, v in rep.items() if k != "note"}, indent=2))
    sys.exit(0 if rep["passed"] else 1)


if __name__ == "__main__":
    main()
