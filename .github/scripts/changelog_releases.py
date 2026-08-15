#!/usr/bin/env python3
"""Turn the API changelog into the set of releases that should exist.

The announcement pipeline used to hang off a manual `gh release create`. Nobody
knew that step existed, so EMS 2.3.15 and 2.4.0 both moved the plugin surface
and neither reached the #plugins thread -- a dev asked about it 2026-08-15,
four releases later. This script removes the human step: the changelog IS the
trigger, because writing the changelog is something that already happens.

Emits JSON on stdout:

    [{"version": "2.4.0", "tag": "v2.4.0", "name": "...", "body": "..."}, ...]

Oldest first, so a caller announcing several at once posts them in the order
they shipped.

The body is rewritten for Discord, not copied raw:

  * relative MkDocs links (../api/data.md#x) become absolute docs URLs, because
    a relative path in a Discord message is dead text.
  * MkDocs admonitions (!!! danger "Title") become bold text and lose their
    indentation, because the raw !!! syntax renders as literal noise.

Both conversions exist so plugin authors get the specific API detail in a
readable form, which is the entire point of announcing separately from the
player-facing EMS changelog.

    python3 changelog_releases.py docs/reference/changelog.md --floor 2.3.8
"""

import argparse
import json
import re
import sys

DOCS_BASE = "https://jesperlive.github.io/GRIP-EMS-PluginAPI"

# "## EMS 2.4.0" or "## EMS 2.4.0 - 2026-08-14" (em dash or hyphen).
# Any other "## ..." heading is prose ("Getting notified") and must not become
# a release -- hence the mandatory version group rather than a loose match.
SECTION_RE = re.compile(
    r"^##\s+EMS\s+(\d+\.\d+\.\d+)\s*(?:[—–-]\s*(\S+))?\s*$"
)

# [label](../api/data.md#anchor) -> absolute. Also handles a bare .md target.
REL_LINK_RE = re.compile(r"\]\(\.\./([A-Za-z0-9_\-/]+)\.md(#[A-Za-z0-9_\-]*)?\)")

# !!! danger "Title"  /  !!! warning "Title"  /  ??? note "Title"
ADMONITION_RE = re.compile(r'^(\s*)[!?]{3}\s+\w+(?:\s+"([^"]*)")?\s*$')


def parse_version(text):
    """'2.4.0' -> (2, 4, 0). Used for ordering and the floor comparison."""
    return tuple(int(part) for part in text.split("."))


def absolutize_links(text):
    """Rewrite relative MkDocs links to absolute docs URLs.

    'docs/api/data.md' publishes at '/api/data/', so the .md suffix is dropped
    and a trailing slash added before any anchor.
    """

    def repl(match):
        path, anchor = match.group(1), match.group(2) or ""
        return "](%s/%s/%s)" % (DOCS_BASE, path, anchor)

    return REL_LINK_RE.sub(repl, text)


def flatten_admonitions(text):
    """Convert MkDocs admonitions to plain bold + dedented body.

    An admonition body is indented 4 spaces under its marker. Left as-is,
    Discord renders it as a code block, which buries the warning that is
    usually the most important line in the entry.
    """
    out = []
    in_block = False
    indent = ""
    for line in text.splitlines():
        match = ADMONITION_RE.match(line)
        if match:
            indent = match.group(1)
            title = match.group(2)
            in_block = True
            if title:
                # Emitted at column 0 to match the dedented body below it. Keeping
                # the source indent here would leave the title sitting 4 spaces in
                # front of its own text in Discord.
                out.append("**%s**" % title)
            continue
        if in_block:
            if line.strip() == "":
                out.append("")
                continue
            stripped = line[len(indent) + 4 :] if line.startswith(indent + "    ") else line.lstrip()
            # A line that is no longer indented ends the block.
            if not line.startswith(indent + "    ") and line.strip():
                in_block = False
                out.append(line)
                continue
            out.append(stripped)
            continue
        out.append(line)
    return "\n".join(out)


def parse_changelog(text):
    """Split the changelog into [{version, tag, name, body}], oldest first."""
    lines = text.splitlines()
    starts = []
    for i, line in enumerate(lines):
        match = SECTION_RE.match(line)
        if match:
            starts.append((i, match.group(1), match.group(2)))

    sections = []
    for idx, (line_no, version, date) in enumerate(starts):
        # Body runs to the next "## " heading of ANY kind, so trailing prose
        # sections ("Getting notified") never leak into the last release body.
        end = len(lines)
        for j in range(line_no + 1, len(lines)):
            if lines[j].startswith("## "):
                end = j
                break
        body = "\n".join(lines[line_no + 1 : end]).strip()
        body = flatten_admonitions(absolutize_links(body))
        name = "EMS %s" % version
        if date:
            name = "%s (%s)" % (name, date)
        sections.append(
            {
                "version": version,
                "tag": "v%s" % version,
                "name": name,
                "body": body,
            }
        )

    sections.sort(key=lambda s: parse_version(s["version"]))
    return sections


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("changelog")
    ap.add_argument(
        "--floor",
        default="0.0.0",
        help="Ignore versions below this. Guards against the first run "
        "announcing the whole backfilled history at once.",
    )
    args = ap.parse_args()

    with open(args.changelog, encoding="utf-8") as fh:
        sections = parse_changelog(fh.read())

    floor = parse_version(args.floor)
    kept = [s for s in sections if parse_version(s["version"]) >= floor]
    json.dump(kept, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
