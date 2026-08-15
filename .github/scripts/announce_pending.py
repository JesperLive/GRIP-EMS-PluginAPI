#!/usr/bin/env python3
"""Cut a release for every changelog section that has not been announced yet.

Kept as a script rather than shell inside the workflow YAML for the same reason
notify_discord.py is: the interesting logic (which versions are pending, in what
order) is then testable without pushing a commit or cutting a release.

    DRY_RUN=1 python3 announce_pending.py docs/reference/changelog.md --floor 2.3.8

Idempotence comes from asking GitHub what already exists rather than tracking
state in the repo. An unrelated edit to an old changelog section therefore
re-runs the whole thing and announces nothing, which is the property that lets
this hang off "changelog.md changed" instead of a hand-maintained marker.
"""

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import changelog_releases  # noqa: E402
import notify_discord  # noqa: E402


def release_exists(tag, repo):
    """True when a release already exists for this tag.

    `gh release view` exits non-zero when the release is absent, which is the
    whole check. stdout/stderr are swallowed so a missing release does not look
    like a failure in the log.
    """
    probe = subprocess.run(
        ["gh", "release", "view", tag, "--repo", repo],
        capture_output=True,
        text=True,
    )
    return probe.returncode == 0


def create_release(section, repo, body_path):
    with open(body_path, "w", encoding="utf-8") as fh:
        fh.write(section["body"])
    subprocess.run(
        [
            "gh",
            "release",
            "create",
            section["tag"],
            "--title",
            section["name"],
            "--notes-file",
            body_path,
            "--repo",
            repo,
        ],
        check=True,
    )


def announce(section, repo):
    """Post one section, reusing the message builder notify_discord already has."""
    content = notify_discord.build_content(
        name=section["name"],
        body=section["body"],
        url="https://github.com/%s/releases/tag/%s" % (repo, section["tag"]),
        role_id=notify_discord.env("ROLE_ID"),
        docs_url=notify_discord.env("DOCS_URL"),
    )
    payload = {
        "content": content,
        "allowed_mentions": {"parse": [], "roles": [notify_discord.env("ROLE_ID")]},
    }
    if os.environ.get("DRY_RUN"):
        print(json.dumps(payload, indent=2))
        return 0

    url = "%s?thread_id=%s&wait=true" % (
        notify_discord.env("WEBHOOK_URL"),
        notify_discord.env("THREAD_ID"),
    )
    req = notify_discord.build_request(url, payload)
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print("Announced %s (HTTP %d, %d chars)." % (section["tag"], resp.status, len(content)))
    except urllib.error.HTTPError as e:
        # Never echo the URL -- it embeds the webhook token.
        sys.stderr.write(
            "Discord rejected %s: HTTP %d\n%s\n"
            % (section["tag"], e.code, e.read().decode("utf-8", "replace"))
        )
        return 1
    except urllib.error.URLError as e:
        sys.stderr.write("Could not reach Discord for %s: %s\n" % (section["tag"], e.reason))
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("changelog")
    ap.add_argument("--floor", default="2.3.8")
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    ap.add_argument("--body-path", default="body.md")
    args = ap.parse_args()

    with open(args.changelog, encoding="utf-8") as fh:
        sections = changelog_releases.parse_changelog(fh.read())

    floor = changelog_releases.parse_version(args.floor)
    sections = [
        s for s in sections if changelog_releases.parse_version(s["version"]) >= floor
    ]

    dry = bool(os.environ.get("DRY_RUN"))
    pending = [
        s for s in sections if dry or not release_exists(s["tag"], args.repo)
    ]

    if not pending:
        print("Nothing to announce; every changelog section at or above %s has a release." % args.floor)
        return 0

    print("Pending: %s" % ", ".join(s["tag"] for s in pending))

    failures = 0
    # Oldest first so the thread reads in shipping order.
    for section in pending:
        if not dry:
            create_release(section, args.repo, args.body_path)
        failures += announce(section, args.repo)

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
