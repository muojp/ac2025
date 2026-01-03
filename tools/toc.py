#!/usr/bin/env python3
"""
Generate TOC (Table of Contents) for README.md from git-indexed NN.md files
"""

import re
import subprocess
import sys
from pathlib import Path


def get_git_root():
    """Get the git repository root directory"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"Error finding git root: {e}", file=sys.stderr)
        sys.exit(1)


def get_git_indexed_md_files():
    """Get list of NN.md files that are checked into git"""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True,
            text=True,
            check=True
        )
        files = result.stdout.strip().split('\n')
        # Filter for NN.md pattern and sort
        md_files = [f for f in files if re.match(r'^\d{2}\.md$', f)]
        return sorted(md_files)
    except subprocess.CalledProcessError as e:
        print(f"Error running git ls-files: {e}", file=sys.stderr)
        sys.exit(1)


def extract_title(md_file):
    """Extract the first H1 title from markdown file"""
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('# '):
                    return line[2:].strip()
        return None
    except Exception as e:
        print(f"Error reading {md_file}: {e}", file=sys.stderr)
        return None


def generate_toc_entries(md_files):
    """Generate TOC entries from markdown files"""
    entries = []
    for md_file in md_files:
        title = extract_title(md_file)
        if title:
            # Extract day number (e.g., "01" from "01.md")
            day = md_file.replace('.md', '')
            entry = f"- 🎄{int(day)}日目🎄 [{title}](https://github.com/muojp/ac2025/blob/main/{md_file})"
            entries.append(entry)
    return entries


def update_readme(toc_entries):
    """Update README.md with new TOC entries"""
    readme_path = Path('README.md')

    # Create new README content
    header = "# 🎄「au Starlink DirectでDTC」アドベントカレンダー2025🎄\n\n"
    new_content = header + '\n'.join(toc_entries) + '\n'

    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ README.md updated with {len(toc_entries)} entries")
    except Exception as e:
        print(f"Error writing README.md: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    # Change to git repository root to ensure relative paths work
    git_root = get_git_root()
    import os
    os.chdir(git_root)

    # Get git-indexed NN.md files
    md_files = get_git_indexed_md_files()

    if not md_files:
        print("No NN.md files found in git index", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(md_files)} checked-in markdown files: {', '.join(md_files)}")

    # Generate TOC entries
    toc_entries = generate_toc_entries(md_files)

    if not toc_entries:
        print("No titles extracted from markdown files", file=sys.stderr)
        sys.exit(1)

    # Update README.md
    update_readme(toc_entries)


if __name__ == '__main__':
    main()
