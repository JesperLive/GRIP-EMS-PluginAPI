"""Tests for the changelog-driven announcement trigger.

The failure these guard against is not "the parser crashed". It is "the parser
quietly announced the wrong set", which on this pipeline means either spamming
the plugin-dev role with years of backfilled history or silently announcing
nothing at all. Both look like a healthy green run from the outside, so the
assertions below are about the SET and the ORDER, not just the parse.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import announce_pending
import changelog_releases


SAMPLE = """# API changelog

Newest first. A release that isn't listed didn't change the API surface.

!!! warning "One release `API_VERSION` won't tell you about"

    From EMS 2.4.0, `API_VERSION` bumps on any addition.

## EMS 2.4.0 — 2026-08-14

### Added

- **[`API:GetActiveSequence()`](../api/data.md#apigetactivesequence)** — the name.

## EMS 2.3.15 — 2026-07-29

### Fixed

- **[`API:GetSequenceInfo(name)`](../api/data.md#apigetsequenceinfoname)** stopped raising.

## EMS 2.3.7 — 2026-07-11

### Changed

- **`SEQUENCE_STEP_ADVANCED` now reports the expanded `numSteps`.**

    !!! danger "This one can break a working plugin"

        If you compensated for the old mismatch, you are double counting now.

## Getting notified

Watch the repo, or sit in the Discord thread.

## Something missing?

Tell me and I'll fix the page.
"""


def sections(text=SAMPLE):
    return changelog_releases.parse_changelog(text)


def test_prose_headings_never_become_releases():
    # "Getting notified" and "Something missing?" are ## headings too. Turning
    # either into a release would cut a junk tag AND ping the role for it.
    tags = [s["tag"] for s in sections()]
    assert tags == ["v2.3.7", "v2.3.15", "v2.4.0"]


def test_oldest_first():
    # The thread should read in shipping order, not reverse-chronological like
    # the page it came from.
    versions = [s["version"] for s in sections()]
    assert versions == sorted(versions, key=changelog_releases.parse_version)


def test_floor_excludes_already_announced_history():
    kept = [
        s
        for s in sections()
        if changelog_releases.parse_version(s["version"])
        >= changelog_releases.parse_version("2.3.8")
    ]
    assert [s["tag"] for s in kept] == ["v2.3.15", "v2.4.0"]


def test_relative_links_become_absolute():
    body = [s for s in sections() if s["version"] == "2.4.0"][0]["body"]
    assert "../api/data.md" not in body
    assert "https://jesperlive.github.io/GRIP-EMS-PluginAPI/api/data/#apigetactivesequence" in body


def test_admonition_markers_are_flattened():
    # Raw "!!! danger" renders as literal noise in Discord, and the indented
    # body under it renders as a code block.
    body = [s for s in sections() if s["version"] == "2.3.7"][0]["body"]
    assert "!!!" not in body
    assert "**This one can break a working plugin**" in body
    assert "\n        If you compensated" not in body


def test_trailing_prose_does_not_leak_into_the_last_release():
    body = [s for s in sections() if s["version"] == "2.3.7"][0]["body"]
    assert "Watch the repo" not in body
    assert "Tell me and I'll fix the page" not in body


def test_intro_admonition_above_the_first_section_is_not_a_release():
    # The page opens with a warning admonition before any "## EMS" heading.
    assert all(s["version"] != "0.0.0" for s in sections())
    assert len(sections()) == 3


def test_pending_skips_versions_that_already_have_a_release(monkeypatch):
    monkeypatch.setattr(
        announce_pending, "release_exists", lambda tag, repo: tag == "v2.3.15"
    )
    kept = [
        s
        for s in sections()
        if changelog_releases.parse_version(s["version"])
        >= changelog_releases.parse_version("2.3.8")
    ]
    pending = [s for s in kept if not announce_pending.release_exists(s["tag"], "r")]
    assert [s["tag"] for s in pending] == ["v2.4.0"]


def test_real_changelog_yields_exactly_the_two_missed_releases():
    """The instance that motivated the whole pipeline.

    EMS 2.3.15 and 2.4.0 both moved the plugin surface and neither reached the
    thread. If this ever returns a different set, the announcement scope has
    drifted and someone is about to be over- or under-notified.
    """
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "docs",
        "reference",
        "changelog.md",
    )
    if not os.path.exists(path):
        pytest.skip("changelog not present in this checkout")
    with open(path, encoding="utf-8") as fh:
        parsed = changelog_releases.parse_changelog(fh.read())
    kept = [
        s
        for s in parsed
        if changelog_releases.parse_version(s["version"])
        >= changelog_releases.parse_version("2.3.8")
    ]
    assert [s["tag"] for s in kept] == ["v2.3.15", "v2.4.0"]


def test_body_is_json_safe_for_the_webhook():
    for section in sections():
        json.dumps({"content": section["body"]})
