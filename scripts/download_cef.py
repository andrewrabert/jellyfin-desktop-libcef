#!/usr/bin/env python3
"""Download CEF distribution for prebuild pipeline."""

import argparse
import json
import pathlib
import platform
import sys
import tarfile
import urllib.request
import zipfile

CEF_INDEX_URL = "https://cef-builds.spotifycdn.com/index.json"
CEF_DOWNLOAD_BASE = "https://cef-builds.spotifycdn.com"

PLATFORM_MAP = {
    "linux64": ("Linux", "x86_64"),
    "linuxarm64": ("Linux", "aarch64"),
    "macosx64": ("Darwin", "x86_64"),
    "macosarm64": ("Darwin", "arm64"),
    "windows64": ("Windows", "AMD64"),
    "windowsarm64": ("Windows", "ARM64"),
}


def get_platform_id():
    """Auto-detect platform."""
    system = platform.system()
    machine = platform.machine()
    for plat_id, (s, m) in PLATFORM_MAP.items():
        if s == system and m == machine:
            return plat_id
    raise RuntimeError(f"Unsupported: {system} {machine}")


def fetch_index():
    """Fetch CEF builds index."""
    print("Fetching CEF index...")
    with urllib.request.urlopen(CEF_INDEX_URL) as resp:
        return json.load(resp)


def find_latest_stable(index, platform_id):
    """Find latest stable CEF for platform."""
    versions = index.get(platform_id, {}).get("versions", [])
    stable = [v for v in versions if v.get("channel") == "stable"]
    if not stable:
        raise RuntimeError(f"No stable version for {platform_id}")
    stable.sort(key=lambda v: int(v.get("chromium_version", "0").split(".")[0]), reverse=True)
    return stable[0]


def get_minimal_dist(version_data):
    """Get minimal distribution file info."""
    for f in version_data.get("files", []):
        if f.get("type") == "minimal":
            return f
    for f in version_data.get("files", []):
        if f.get("type") == "standard":
            return f
    raise RuntimeError("No distribution found")


def download_file(url, dest):
    """Download with progress."""
    print(f"Downloading {url}")
    def progress(block, block_size, total):
        if total > 0:
            pct = min(100, block * block_size * 100 // total)
            sys.stdout.write(f"\r  {pct}%")
            sys.stdout.flush()
    urllib.request.urlretrieve(url, dest, reporthook=progress)
    print()


def extract(archive_path, dest_dir):
    """Extract tar.bz2 or zip."""
    print(f"Extracting to {dest_dir}")
    if archive_path.suffix == ".bz2" or ".tar" in archive_path.name:
        with tarfile.open(archive_path, "r:bz2") as tar:
            tar.extractall(dest_dir)
    else:
        with zipfile.ZipFile(archive_path) as zf:
            zf.extractall(dest_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", help="Target platform (auto-detect if omitted)")
    parser.add_argument("--output-dir", type=pathlib.Path, default=pathlib.Path("cef_download"))
    parser.add_argument("--version", help="CEF version (latest stable if omitted)")
    parser.add_argument("--info-only", action="store_true", help="Print version info and exit")
    args = parser.parse_args()

    platform_id = args.platform or get_platform_id()
    index = fetch_index()
    version_data = find_latest_stable(index, platform_id)
    cef_version = version_data.get("cef_version", "unknown")
    file_info = get_minimal_dist(version_data)
    filename = file_info["name"]
    sha1 = file_info.get("sha1", "")
    url = f"{CEF_DOWNLOAD_BASE}/{filename}"

    if args.info_only:
        print(json.dumps({"cef_version": cef_version, "url": url, "sha1": sha1}, indent=2))
        return

    args.output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = args.output_dir / filename

    if not archive_path.exists():
        download_file(url, archive_path)
    else:
        print(f"Using cached {archive_path}")

    # Extract
    extract(archive_path, args.output_dir)

    # Find extracted dir (cef_binary_*_<platform>_minimal)
    extracted = list(args.output_dir.glob("cef_binary_*"))
    if extracted:
        print(f"CEF ready at: {extracted[0]}")
        # Write version for later use
        (args.output_dir / "CEF_VERSION").write_text(cef_version)


if __name__ == "__main__":
    main()
