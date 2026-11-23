"""Build ZFundPilot's frontend from a Git commit and archive the result."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent
HISTORY = ROOT / "data" / "build-history"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def build(ref):
    commit = git("rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}").decode().strip()
    mirror = subprocess.run(
        ["git", "merge-base", commit, "refs/remotes/origin/main"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    node = shutil.which("node")
    npm = shutil.which("npm.cmd")
    if not node or not npm:
        raise SystemExit("Node.js and npm.cmd must be on PATH.")

    started = datetime.now(timezone.utc)
    build_id = f"{started:%Y%m%dT%H%M%S%fZ}-{commit[:12]}"
    inputs = ("frontend/package-lock.json", "pyproject.toml", "requirements.txt")
    input_hashes = {
        name: hashlib.sha256(git("show", f"{commit}:{name}")).hexdigest()
        for name in inputs
    }
    python_packages = json.loads(subprocess.check_output(
        [sys.executable, "-m", "pip", "list", "--format=json", "--disable-pip-version-check"],
        cwd=ROOT,
    ))
    steps = [
        ["ci", "--include=dev", "--no-audit", "--no-fund"],
        ["test"],
        ["run", "build"],
    ]

    HISTORY.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pending-", dir=HISTORY) as temp:
        work = Path(temp)
        source = work / "source.zip"
        git("archive", "--format=zip", "--output", str(source), commit, "frontend")
        with ZipFile(source) as archive:
            archive.extractall(work)
        frontend = work / "frontend"
        node_version = subprocess.check_output([node, "--version"], cwd=frontend, text=True).strip()
        npm_version = subprocess.check_output([npm, "--version"], cwd=frontend, text=True).strip()
        for args in steps:
            subprocess.run([npm, *args], cwd=frontend, check=True)

        output = work / "output"
        output.mkdir()
        dist = frontend / "dist"
        if not (dist / "index.html").is_file():
            raise SystemExit("Build did not produce dist/index.html.")
        bundle = Path(shutil.make_archive(str(output / "frontend-dist"), "zip", root_dir=dist))
        with bundle.open("rb") as stream:
            bundle_sha = hashlib.file_digest(stream, "sha256").hexdigest()
        manifest = {
            "schema_version": 1,
            "started_at_utc": started.isoformat(),
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_commit": commit,
            "source_ref_requested": ref,
            "build_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "upstream_common_ancestor": mirror.stdout.strip() if mirror.returncode == 0 else None,
            "upstream_reference": "refs/remotes/origin/main",
            "frontend_version": json.loads((frontend / "package.json").read_text(encoding="utf-8"))["version"],
            "input_sha256": input_hashes,
            "platform": platform.platform(),
            "node": node_version,
            "npm": npm_version,
            "python_runtime": platform.python_version(),
            "python_environment_packages": [
                {"name": package["name"], "version": package["version"]}
                for package in python_packages
            ],
            "steps": [["npm", *args] for args in steps],
            "artifact": {"file": bundle.name, "sha256": bundle_sha},
        }
        (output / "build.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        destination = HISTORY / build_id
        output.rename(destination)
    print(f"Build archived at {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="HEAD", help="Git commit, tag, or branch to build (default: HEAD)")
    build(parser.parse_args().ref)
