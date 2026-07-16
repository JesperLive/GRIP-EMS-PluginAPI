#!/usr/bin/env python3
"""Post a GitHub release into the plugin-dev forum thread on Discord.

Reads the release JSON produced by `gh release view --json name,body,tagName,url`
and posts it through an incoming webhook. Everything variable arrives via env so
no release text is ever interpolated into a shell command.

Kept as a real file rather than an inline `run:` block so the truncation maths
below is testable without cutting a release:

    DRY_RUN=1 ROLE_ID=1 DOCS_URL=x THREAD_ID=1 WEBHOOK_URL=x \
        python3 notify_discord.py fixture.json
"""

import json
import os
import sys
import urllib.error
import urllib.request

# Discord hard-caps a webhook message at 2000 characters and rejects the whole
# request when it is over -- it does not truncate for you.
CONTENT_LIMIT = 2000

# Discord sits behind Cloudflare, which blocks urllib's default
# "Python-urllib/3.x" User-Agent outright: HTTP 403, Cloudflare error 1010
# ("banned based on your browser's signature"). Nothing about the payload is
# wrong when this fires, so it reads like a permissions problem and sends you
# hunting in the wrong place. Discord asks API clients to identify themselves;
# any honest descriptive UA clears it. Verified live 2026-07-16: default UA ->
# 403/1010, this UA -> 200.
USER_AGENT = "GRIP-EMS-PluginAPI-Announcer (https://github.com/JesperLive/GRIP-EMS-PluginAPI, 1.0)"


def env(name):
    """Read an env var, stripped.

    Stray whitespace is not cosmetic here: a trailing space inside the role
    mention ("<@&123 >") makes Discord render it as literal text instead of a
    ping, which fails silently -- the message posts, nobody gets notified.
    """
    return os.environ[name].strip()


def build_content(name, body, url, role_id, docs_url):
    """Assemble the message, trimming the BODY (never the header/footer).

    The tag, the changelog link, and the release link are the parts a reader
    cannot reconstruct themselves, so they are the parts that must survive.
    """
    header = "<@&%s> **GRIP-EMS Plugin API - %s**" % (role_id, name)
    footer = "Full changelog: %s\nRelease notes: %s" % (docs_url, url)
    body = (body or "").strip()

    fixed = len(header) + len(footer) + 4  # 4 = the two blank-line joins
    room = CONTENT_LIMIT - fixed

    if room <= 0:
        # Header + footer alone blow the cap. Drop the body rather than emit
        # something Discord will 400 on.
        return "%s\n\n%s" % (header, footer)

    if len(body) > room:
        ellipsis = "\n... (truncated)"
        body = body[: max(0, room - len(ellipsis))].rstrip() + ellipsis

    if not body:
        return "%s\n\n%s" % (header, footer)
    return "%s\n\n%s\n\n%s" % (header, body, footer)


def build_request(url, payload):
    """Build the POST request.

    Split out from main() so the headers are testable without a live webhook.
    The 7 tests that shipped alongside the first version of this script all
    passed while it was 403ing against the real Discord, because every one of
    them stopped at build_content and none touched the transport. That is the
    gap this function exists to close.
    """
    return urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage: notify_discord.py <release.json>\n")
        return 2

    with open(sys.argv[1], encoding="utf-8") as fh:
        rel = json.load(fh)

    name = rel.get("name") or rel.get("tagName") or "new release"
    content = build_content(
        name=name,
        body=rel.get("body") or "",
        url=rel.get("url") or "",
        role_id=env("ROLE_ID"),
        docs_url=env("DOCS_URL"),
    )

    payload = {
        "content": content,
        # Explicit allowlist: ping exactly the plugin-dev role and nothing else.
        # Without this, a stray @everyone in release notes would reach the whole
        # server.
        "allowed_mentions": {"parse": [], "roles": [env("ROLE_ID")]},
    }

    if os.environ.get("DRY_RUN"):
        print(json.dumps(payload, indent=2))
        return 0

    # A forum-channel webhook must name a thread or Discord rejects the post.
    url = "%s?thread_id=%s&wait=true" % (env("WEBHOOK_URL"), env("THREAD_ID"))
    req = build_request(url, payload)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print("Posted to Discord (HTTP %d), %d chars." % (resp.status, len(content)))
    except urllib.error.HTTPError as e:
        # Never echo the URL -- it embeds the webhook token.
        sys.stderr.write("Discord rejected the post: HTTP %d\n%s\n" % (e.code, e.read().decode("utf-8", "replace")))
        return 1
    except urllib.error.URLError as e:
        sys.stderr.write("Could not reach Discord: %s\n" % e.reason)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
