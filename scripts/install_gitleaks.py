"""Install a checksum-verified scanner; no global executable changes."""

import hashlib
import io
import platform
import tarfile
import urllib.request
from pathlib import Path

VERSION = "8.30.1"
HASHES = {
    ("Linux", "x86_64"): (
        "linux_x64",
        "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb",
    ),
    ("Linux", "aarch64"): (
        "linux_arm64",
        "e4a487ee7ccd7d3a7f7ec08657610aa3606637dab924210b3aee62570fb4b080",
    ),
    ("Darwin", "x86_64"): (
        "darwin_x64",
        "dfe101a4db2255fc85120ac7f3d25e4342c3c20cf749f2c20a18081af1952709",
    ),
    ("Darwin", "arm64"): (
        "darwin_arm64",
        "b40ab0ae55c505963e365f271a8d3846efbc170aa17f2607f13df610a9aeb6a5",
    ),
}
target = Path(".tools/gitleaks")
if target.exists():
    raise SystemExit(0)
key = (platform.system(), platform.machine())
if key not in HASHES:
    raise SystemExit("Make setup supports Linux/macOS; use Linux CI or WSL for scanner setup.")
name, expected = HASHES[key]
url = f"https://github.com/gitleaks/gitleaks/releases/download/v{VERSION}/gitleaks_{VERSION}_{name}.tar.gz"
with urllib.request.urlopen(url, timeout=60) as response:
    raw = response.read(25 * 1024 * 1024 + 1)
if hashlib.sha256(raw).hexdigest() != expected:
    raise SystemExit("Scanner archive checksum mismatch")
with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
    member = archive.extractfile("gitleaks")
    if member is None:
        raise SystemExit("Scanner missing from archive")
    binary = member.read()
target.parent.mkdir(exist_ok=True)
target.write_bytes(binary)
target.chmod(0o755)
