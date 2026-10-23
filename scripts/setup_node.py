"""Optional Windows bootstrap: install verified official Node LTS under .tools/."""
import hashlib
import io
import json
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile


def main():
    releases = json.load(urlopen("https://nodejs.org/dist/index.json", timeout=30))
    release = next(item for item in releases if item["lts"] and "win-x64-zip" in item["files"])
    version = release["version"]
    filename = f"node-{version}-win-x64.zip"
    base = f"https://nodejs.org/dist/{version}/"
    sums = urlopen(base + "SHASUMS256.txt", timeout=30).read().decode()
    expected = next(line.split()[0] for line in sums.splitlines() if line.split()[-1] == filename)
    data = urlopen(base + filename, timeout=60).read()
    if hashlib.sha256(data).hexdigest() != expected:
        raise SystemExit("Node download checksum mismatch.")
    target = Path(__file__).resolve().parents[1] / ".tools"
    target.mkdir(exist_ok=True)
    with ZipFile(io.BytesIO(data)) as archive:
        archive.extractall(target)
    print(f"Verified Node {version} installed in .tools/node-{version}-win-x64")


if __name__ == "__main__":
    main()
