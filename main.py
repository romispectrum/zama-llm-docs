#!/usr/bin/env python3
"""
Download a docs/ folder from a GitHub 'tree' URL (if needed) and build a single zama-llm.txt by
concatenating all content under docs/.
- Downloads only when the local root folder doesn't exist (or is empty).
- Works with URLs like: https://github.com/<owner>/<repo>/tree/<branch>/<subpath>
  (default: https://github.com/zama-ai/fhevm/tree/main/docs)
- Includes .md, .mdx, and .txt files
- Orders files deterministically (A–Z)
- Adds a Table of Contents with anchor links
- Inserts section headers and a horizontal rule between files
"""

from __future__ import annotations
import argparse
import io
import os
import re
import sys
import zipfile
import urllib.request
from pathlib import Path
from typing import Iterable, List, Tuple

DEFAULT_INCLUDE_EXTS = {".md", ".mdx", ".txt"}
DEFAULT_EXCLUDE_DIRS = {".git", ".gitbook", "node_modules", ".DS_Store", "__pycache__"}

DEFAULT_GITHUB_TREE_URL = "https://github.com/zama-ai/fhevm/tree/main/docs"

# ---------------------------
# GitHub download helpers
# ---------------------------

_TREE_URL_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/tree/(?P<branch>[^/]+)(?:/(?P<subpath>.*))?$"
)

def parse_github_tree_url(url: str) -> Tuple[str, str, str, str]:
    """
    Parse a GitHub 'tree' URL into (owner, repo, branch, subpath).
    Raises ValueError if malformed.
    """
    m = _TREE_URL_RE.match(url.strip())
    if not m:
        raise ValueError(f"Not a valid GitHub tree URL: {url}")
    owner = m.group("owner")
    repo = m.group("repo")
    branch = m.group("branch")
    subpath = (m.group("subpath") or "").strip("/")
    return owner, repo, branch, subpath

def download_and_extract_subdir_from_zip(zip_url: str, zip_root_prefix: str, subdir: str, dest: Path) -> None:
    """
    Download a repo ZIP and extract only files under subdir into dest.
    zip_root_prefix is usually '{repo}-{branch}/'.
    """
    dest.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(zip_url) as resp:
        data = resp.read()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        # Normalize prefixes (ensure trailing slashes)
        zip_root_prefix = zip_root_prefix.rstrip("/") + "/"
        subdir_prefix = (zip_root_prefix + subdir.strip("/")).rstrip("/") + "/"

        members = [zi for zi in zf.infolist()
                   if not zi.is_dir() and zi.filename.startswith(subdir_prefix)]
        if not members:
            raise FileNotFoundError(
                f"Subdirectory '{subdir}' not found in archive at {zip_url}"
            )

        for zi in members:
            rel = Path(zi.filename[len(subdir_prefix):])  # path relative to subdir
            out_path = dest / rel
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(zi) as src, open(out_path, "wb") as dst:
                dst.write(src.read())

def ensure_docs_present_from_github(root: Path, github_tree_url: str) -> None:
    """
    If 'root' doesn't exist or is empty, fetch it from the provided GitHub tree URL.
    """
    needs_download = (not root.exists()) or (root.is_dir() and not any(root.iterdir()))
    if not needs_download:
        return

    owner, repo, branch, subpath = parse_github_tree_url(github_tree_url)
    if not subpath:
        # If no subpath given, assume whole repo and use 'docs' by default
        subpath = "docs"

    # codeload URL for the branch ZIP
    zip_url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{branch}"
    zip_root_prefix = f"{repo}-{branch}"

    print(f"Downloading '{subpath}/' from {owner}/{repo}@{branch} ...")
    download_and_extract_subdir_from_zip(zip_url, zip_root_prefix, subpath, root)
    print(f"Downloaded {subpath}/ to {root}")

# ---------------------------
# Build helpers (unchanged logic)
# ---------------------------

def find_files(root: Path,
               include_exts: set[str],
               exclude_dirs: set[str]) -> List[Path]:
    out: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # prune excluded directories in-place
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix.lower() in include_exts:
                out.append(p)
    # sort deterministically by relative path
    out.sort(key=lambda p: p.relative_to(root).as_posix().lower())
    return out

def md_anchor_from_path(rel_path: Path) -> str:
    # GitHub-ish anchor: lowercase, spaces to '-', drop non-alnum except '-'
    import re as _re
    s = rel_path.as_posix().lower()
    s = _re.sub(r"[^\w\/\-\. ]", "", s)
    s = s.replace(" ", "-")
    return s

def make_toc(paths: Iterable[Path], root: Path) -> str:
    lines = ["## Table of Contents", ""]
    for p in paths:
        rel = p.relative_to(root)
        anchor = md_anchor_from_path(rel)
        lines.append(f"- [{rel.as_posix()}](#{anchor})")
    lines.append("")
    return "\n".join(lines)

def read_text_file(p: Path) -> str:
    # Try utf-8 first, fallback to latin-1 without crashing
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return p.read_text(encoding=enc)
        except Exception:
            continue
    # As last resort, read bytes and replace errors
    return p.read_bytes().decode("utf-8", errors="replace")

def build_document(root: Path, files: List[Path]) -> str:
    parts: List[str] = []
    # Header
    parts.append("# Zama FHEVM Combined Documentation\n")

    parts.append(make_toc(files, root))

    # Body
    for idx, p in enumerate(files, start=1):
        rel = p.relative_to(root)
        anchor = md_anchor_from_path(rel)
        parts.append(f"\n---\n")
        parts.append(f"## {rel.as_posix()}\n")
        parts.append(f"<a id=\"{anchor}\"></a>\n")

        text = read_text_file(p).rstrip()

        # If this is already Markdown (.md/.mdx/.txt), include as-is.
        # Add a tiny preface line showing the original path.
        parts.append(f"> _From `{rel.as_posix()}`_\n")
        parts.append("")
        parts.append(text)
        parts.append("")  # ensure trailing newline

    parts.append("\n---\n")
    return "\n".join(parts)

# ---------------------------
# CLI
# ---------------------------

def main():
    ap = argparse.ArgumentParser(description="Download docs/ from GitHub (if needed) and combine into zama-llm.txt markdown.")
    ap.add_argument("--root", "-r", type=Path, default=Path("docs"),
                    help="Root folder to scan or download into (default: ./docs)")
    ap.add_argument("--out", "-o", type=Path, default=Path("zama-llm.txt"),
                    help="Output markdown file (default: ./zama-llm.txt)")
    ap.add_argument("--github", type=str, default=DEFAULT_GITHUB_TREE_URL,
                    help="GitHub tree URL to fetch docs from if --root is missing/empty "
                         f"(default: {DEFAULT_GITHUB_TREE_URL})")
    ap.add_argument("--ext", action="append",
                    help="Additional file extension to include (can repeat), e.g. --ext .rst")
    ap.add_argument("--no-default-excludes", action="store_true",
                    help="Do not exclude common folders like .git, .gitbook, node_modules")
    args = ap.parse_args()

    root: Path = args.root
    out_path: Path = args.out

    # If root is missing/empty, try to fetch it from GitHub
    try:
        ensure_docs_present_from_github(root, args.github)
    except Exception as e:
        print(f"Warning: could not fetch from GitHub: {e}", file=sys.stderr)
        # Continue; we might already have a local root present

    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Root folder not found or not a directory: {root}")

    include_exts = set(DEFAULT_INCLUDE_EXTS)
    if args.ext:
        include_exts |= {e if e.startswith(".") else f".{e}" for e in args.ext}

    exclude_dirs = set() if args.no_default_excludes else set(DEFAULT_EXCLUDE_DIRS)

    files = find_files(root, include_exts, exclude_dirs)
    if not files:
        print("No input files found. Nothing to do.")
        return

    doc = build_document(root, files)
    out_path.write_text(doc, encoding="utf-8")
    print(f"Wrote {out_path.resolve()} with {len(files)} files combined.")

if __name__ == "__main__":
    main()
