"""Install or update Personal HR OS in a private project folder."""

import argparse
import fcntl
import hashlib
import json
import os
import re
from pathlib import Path
import stat
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
DISTRIBUTION = ROOT / "distribution"
ORIGINAL_PACKAGES = ("skillos-blake1", "employee-lifecycle-record-preparation")
RECEIPT = Path(".personal-hr-os-release.json")
MANAGED_ROOT_FILES = {"AGENTS.md", "LICENSE", "NOTICE.md", "README.md", "Role Index.md", "Skill Index.md"}
MANAGED_FOLDERS = {("Context", "Guides"), ("Skills", "_Drafts"), ("Work", "Templates")}


def managed(rel):
    return str(rel) in MANAGED_ROOT_FILES or rel.parts[:2] in MANAGED_FOLDERS


def skill_packages(files):
    return sorted(rel.parts[2] for rel in files if rel.parts[:2] == ("Skills", "_Drafts")
                  and len(rel.parts) == 4 and rel.name == "SKILL.md")


def digest(contents):
    return hashlib.sha256(contents).hexdigest()


def release_hashes(files):
    return {str(rel): digest(data) for rel, data in files.items() if managed(rel)}


def receipt(hashes, edition):
    info = {"product": "Personal HR OS", "format": 1, "edition": edition, "files": hashes}
    return (json.dumps(info, indent=2, sort_keys=True) + "\n").encode("utf-8")


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
    for package in ORIGINAL_PACKAGES:
        if Path("Skills", "_Drafts", package, "SKILL.md") not in payload:
            raise ValueError(f"Missing Draft package: {package}")
    directories = {Path("Skills/Active"), Path("Work/Records"), Path("_Archive")}
    if set(map(Path, manifest["empty_directories"])) != directories:
        raise ValueError("The blank starter directories do not match this install edition.")
    return payload, directories, manifest["edition"]


def choose_destination(argument, updating):
    supplied = Path(argument).expanduser()
    # Retain the final component so that dangling links are treated as occupied.
    dest = supplied.parent.resolve(strict=True) / supplied.name
    if updating:
        if dest.is_symlink() or not dest.is_dir():
            raise ValueError("Choose the existing installed private folder itself.")
        if ROOT.is_relative_to(dest) or (dest / "distribution/lifecycle-files.json").exists():
            raise ValueError("Choose the installed private workspace, outside the release checkout.")
    elif dest.exists() or dest.is_symlink():
        raise ValueError(f"Destination already exists: {dest}. Choose a new folder name.")
    if dest.is_relative_to(ROOT):
        raise ValueError("Choose a private destination outside this distribution folder.")
    if not dest.parent.is_dir():
        raise ValueError("The parent folder must exist.")
    return dest


def install(destination, files, empty_directories, edition):
    # Reserve the destination exclusively. Concurrent launches cannot adopt the same path.
    destination.mkdir(mode=0o700)
    created = [destination]
    try:
        data = dict(files)
        data[Path(".gitignore")] = b"*\n"
        data[RECEIPT] = receipt(release_hashes(files), edition)
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
        for package in skill_packages(files):
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


def check_parents(workspace, rel):
    """Never traverse an alias into a private folder or another project."""
    parent = workspace
    for part in rel.parts[:-1]:
        parent /= part
        if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
            raise ValueError(f"Expected a real workspace directory at {parent}.")


def regular_contents(workspace, rel):
    check_parents(workspace, rel)
    path = workspace / rel
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(mode):
        raise ValueError(f"Expected a regular file at {rel}. Update stopped.")
    return path.read_bytes()


def edition_number(edition):
    match = re.fullmatch(r"Personal HR OS · Employee Lifecycle Preview (\d+(?:\.\d+)+)", edition)
    return tuple(map(int, match[1].split("."))) if match else None


def previous_releases(saved, observed, edition):
    if saved is not None:
        info = json.loads(saved)
        if (not isinstance(info, dict) or info.get("format") != 1
                or info.get("product") != "Personal HR OS" or not isinstance(info.get("files"), dict)):
            raise ValueError("Unrecognised installation receipt. No update was applied.")
        if any(not isinstance(value, str) or len(value) != 64 for value in info["files"].values()):
            raise ValueError("Invalid release hashes in the installation receipt.")
        installed = info.get("edition")
        if not isinstance(installed, str):
            raise ValueError("The release receipt is missing its edition.")
        if installed != edition:
            current, target = edition_number(installed), edition_number(edition)
            if current is None or target is None or current > target:
                raise ValueError(f"Installed edition: {installed}. Use the latest release to update.")
        return [info["files"]]

    # The three pre-updater releases had no receipt. Compare only shipped files.
    catalog = json.loads((DISTRIBUTION / "update-bases.json").read_text(encoding="utf-8"))
    bases = [dict(catalog["base"], **overrides) for overrides in catalog["releases"].values()]
    scores = [sum(value == observed.get(name) for name, value in base.items()) for base in bases]
    return [base for base, score in zip(bases, scores) if score == max(scores)]


def skill_link(workspace, package):
    rel = Path(".agents", "skills", package)
    canonical = Path("Skills", "_Drafts", package)
    check_parents(workspace, rel)
    check_parents(workspace, canonical / "SKILL.md")
    target = os.path.relpath(workspace / canonical, (workspace / rel).parent)
    link = workspace / rel
    if link.is_symlink() and os.readlink(link) == target:
        return rel, target, True
    if link.is_symlink() or link.exists():
        raise ValueError(f"An existing item at {rel} differs from the project skill link.")
    return rel, target, False


def write_file(workspace, rel, previous, new):
    """Use a same-directory temporary and exclusive creation for new paths."""
    path = workspace / rel
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".hr-os-update-", delete=False) as out:
        temp = Path(out.name)
    try:
        temp.write_bytes(new)
        if regular_contents(workspace, rel) != previous:
            raise ValueError(f"{rel} changed during the update. Rerun after the edit is complete.")
        if previous is None:
            os.link(temp, path)
        else:
            os.chmod(temp, stat.S_IMODE(path.stat().st_mode))
            os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def update_workspace(workspace, files, edition):
    # The original installations have both discovery links. This also rejects
    # arbitrary folders that happen to contain a README or a Work directory.
    saved = regular_contents(workspace, RECEIPT)
    if saved is None:
        for package in ORIGINAL_PACKAGES:
            if not skill_link(workspace, package)[2]:
                raise ValueError(f"Cannot identify the private installation: missing {package} discovery link.")
    elif not (workspace / ".agents/skills").is_dir() or not (workspace / "Skills/_Drafts").is_dir():
        raise ValueError("The installed skill directory structure is missing. Check the workspace path.")
    incoming = release_hashes(files)
    observed = {name: regular_contents(workspace, Path(name)) for name in incoming}
    observed_hashes = {name: digest(data) if data is not None else None for name, data in observed.items()}
    bases = previous_releases(saved, observed_hashes, edition)
    changes = {}
    kept = []
    conflicts = []
    for name, wanted in incoming.items():
        current = observed_hashes[name]
        if current == wanted:
            continue
        old_hashes = {base.get(name) for base in bases}
        if old_hashes == {current}:
            rel = Path(name)
            changes[rel] = (observed[name], files[rel])
        elif old_hashes == {wanted}:
            kept.append(name)
        else:
            conflicts.append(name)

    links = []
    for package in skill_packages(files):
        rel, target, present = skill_link(workspace, package)
        package_dir = Path("Skills", "_Drafts", package)
        key = str(package_dir / "SKILL.md")
        previously_shipped = any(key in base for base in bases)
        if not previously_shipped and (workspace / package_dir).exists():
            # Avoid mixing a private skill of the same name with newly shipped files.
            # A retry can already contain a subset of the incoming package.
            allowed = {path for path in files if package_dir in path.parents}
            allowed.update(parent for path in tuple(allowed) for parent in path.parents)
            for item in (workspace / package_dir).rglob("*"):
                if item.relative_to(workspace) not in allowed:
                    conflicts.append(str(package_dir))
                    break
        if not present:
            if previously_shipped:
                kept.append(str(rel))
            else:
                links.append((rel, target))
    if conflicts:
        raise ValueError("Local choices overlap this release. No files changed. Review these paths, "
                         "keep a copy of any local version and resolve before retrying:\n  "
                         + "\n  ".join(conflicts))

    new_receipt = receipt(incoming, edition)
    # Preserve the selected legacy base across a power loss midway through migration.
    # A successful run commits the incoming hashes last.
    migration_receipt = None
    created_dirs, written, added_links = [], [], []
    try:
        if saved is None:
            legacy = receipt(bases[0], "Personal HR OS · Employee Lifecycle Preview 0.1")
            write_file(workspace, RECEIPT, None, legacy)
            migration_receipt = legacy
        parents = {parent for rel in changes for parent in rel.parents if parent != Path(".")}
        for rel in sorted(parents, key=lambda p: (len(p.parts), str(p))):
            check_parents(workspace, rel / "placeholder")
            if not (workspace / rel).exists():
                (workspace / rel).mkdir(mode=0o700)
                created_dirs.append(rel)
        for rel, (previous, new) in changes.items():
            write_file(workspace, rel, previous, new)
            written.append(rel)
        for rel, target in links:
            check_parents(workspace, rel)
            (workspace / rel).symlink_to(target, target_is_directory=True)
            added_links.append((rel, target))
        for rel in written:
            if regular_contents(workspace, rel) != changes[rel][1]:
                raise ValueError(f"Could not verify the saved release file {rel}.")
        for rel, target in added_links:
            if not (workspace / rel / "SKILL.md").is_file():
                raise ValueError(f"Could not verify the project skill at {rel}.")
        previous_receipt = migration_receipt if saved is None else saved
        if previous_receipt != new_receipt:
            write_file(workspace, RECEIPT, previous_receipt, new_receipt)
    except BaseException:
        # Roll back our changes only. An interrupted process can also rerun:
        # atomic writes already equal to the incoming version are accepted.
        for rel, target in reversed(added_links):
            path = workspace / rel
            if path.is_symlink() and os.readlink(path) == target:
                path.unlink()
        for rel in reversed(written):
            prior, new = changes[rel]
            if regular_contents(workspace, rel) == new:
                if prior is None:
                    (workspace / rel).unlink()
                else:
                    write_file(workspace, rel, new, prior)
        if migration_receipt is not None and regular_contents(workspace, RECEIPT) == migration_receipt:
            (workspace / RECEIPT).unlink()
        for rel in reversed(created_dirs):
            try:
                (workspace / rel).rmdir()
            except OSError:
                pass
        raise
    return len(written), len(added_links), kept


def update(destination, files, edition):
    # POSIX directory locks do not create a lock file or survive a crashed process.
    folder = os.open(destination, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        try:
            fcntl.flock(folder, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Another update is using this workspace. Retry when it finishes.") from None
        return update_workspace(destination, files, edition)
    finally:
        os.close(folder)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update", action="store_true", help="Update an existing private workspace in place.")
    parser.add_argument("workspace", help="Path of the private project folder")
    args = parser.parse_args()
    try:
        destination = choose_destination(args.workspace, args.update)
        payload, blank_dirs, edition = verified_source_files()
        os.umask(0o077)
        if args.update:
            count, links, kept = update(destination, payload, edition)
            print(f"Updated private workspace: {destination}\n{edition}\n"
                  f"{count} release files written; {links} skill links added.")
            if kept:
                print("Preserved local changes or deletions:\n  " + "\n  ".join(kept))
            return
        install(destination, payload, blank_dirs, edition)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"{'Update' if args.update else 'Setup'} stopped: {error}\n")
    print(f"Created Personal HR OS in {destination}\nVerified {len(payload)} preview files and "
          f"{len(skill_packages(payload))} project-level Draft skill links.\n"
          "Open this folder as a project in Codex, then start a fresh chat. "
          "See README.md for the fictional onboarding check.")


if __name__ == "__main__":
    main()
