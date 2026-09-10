import argparse
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the deterministic coding-RL verifier.")
    parser.add_argument("--target", default="/workspace", help="Path to candidate repository")
    args = parser.parse_args()

    verifier_dir = Path(__file__).resolve().parent
    env = os.environ.copy()
    env["TARGET_REPO"] = str(Path(args.target).resolve())
    command = [
    sys.executable,
    "-m",
    "pytest",
    "-q",
    "-p",
    "no:cacheprovider",
    str(verifier_dir),
    ]
    return subprocess.run(command, env=env, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
