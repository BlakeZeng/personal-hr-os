"""Set up a new private Personal HR OS project for a Codex file-practice trial."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
DISTRIBUTION = ROOT / "distribution"
DRAFT_PACKAGES = ("skillos-blake1", "employee-lifecycle-record-preparation")


def verified_source_files():
    """Load only the explicitly listed release files. Never import a local case."""
    manifest = json.loads((DISTRIBUTION / "lifecycle-files.json").read_text(encoding="utf-8"))
    payload = {}
    for name, expected_hash in manifest["files"].items():
        rel = Path(name)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"Invalid release path: {name}")
        source = ROOT / rel
        if not source.resolve(strict=True).is_relative_to(ROOT):
            raise ValueError(f"Source path leaves the release: {name}")
        data = source.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected_hash:
            raise ValueError(f"Release file changed: {name}. Use a clean release copy.")
        payload[rel] = data
    for package in DRAFT_PACKAGES:
        if Path("Skills", "_Drafts", package, "SKILL.md") not in payload:
            raise ValueError(f"Missing Draft package: {package}")
    directories = {Path("Skills/Active"), Path("Work/Records"), Path("_Archive")}
    if set(map(Path, manifest["empty_directories"])) != directories:
        raise ValueError("The blank starter directories do not match this install edition.")
    return payload, directories


def choose_destination(argument):
    supplied = Path(argument).expanduser()
    # Retain the final component so that dangling links are treated as occupied.
    dest = supplied.parent.resolve(strict=True) / supplied.name
    if dest.exists() or dest.is_symlink():
        raise ValueError(f"Destination already exists: {dest}. Choose a new folder name.")
    if dest.is_relative_to(ROOT):
        raise ValueError("Choose a private destination outside this distribution folder.")
    if not dest.parent.is_dir():
        raise ValueError("The parent folder must exist.")
    return dest


def install(destination, files, empty_directories):
    # Reserve the destination exclusively. Concurrent launches cannot adopt the same path.
    destination.mkdir(mode=0o700)
    created = [destination]
    try:
        data = dict(files)
        data[Path(".gitignore")] = b"*\n"
        directories = set(empty_directories) | {Path(".agents"), Path(".agents/skills")}
        for rel in data:
            directories.update(p for p in rel.parents if p != Path("."))
        for rel in sorted(directories, key=lambda p: (len(p.parts), str(p))):
            path = destination / rel
            path.mkdir(mode=0o700)
            created.append(path)
        for rel, contents in data.items():
            path = destination / rel
            with path.open("xb") as stream:
                created.append(path)
                stream.write(contents)
        for package in DRAFT_PACKAGES:
            link = destination / ".agents" / "skills" / package
            canonical = destination / "Skills" / "_Drafts" / package
            link.symlink_to(os.path.relpath(canonical, link.parent), target_is_directory=True)
            created.append(link)
            if not (link / "SKILL.md").samefile(canonical / "SKILL.md"):
                raise ValueError(f"Codex link verification failed: {package}")
        for rel, expected in data.items():
            if (destination / rel).read_bytes() != expected:
                raise ValueError(f"Saved file verification failed: {rel}")
    except BaseException:
        # Remove only our own created entries. Preserve files added by someone else.
        for path in reversed(created):
            try:
                if path.is_symlink() or path.is_file():
                    path.unlink()
                else:
                    path.rmdir()
            except OSError:
                pass
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", help="Path of a new private project folder")
    args = parser.parse_args()
    try:
        destination = choose_destination(args.workspace)
        payload, blank_dirs = verified_source_files()
        os.umask(0o077)
        install(destination, payload, blank_dirs)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Setup stopped: {error}\n")
    print(f"Created Personal HR OS in {destination}\nVerified {len(payload)} preview files and "
          f"{len(DRAFT_PACKAGES)} project-level Draft skill links.\n"
          "Open this folder as a project in Codex, then start a fresh chat. "
          "See README.md for the fictional onboarding check.")


if __name__ == "__main__":
    main()
