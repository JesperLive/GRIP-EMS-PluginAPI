"""Tests for the changelog-driven announcement trigger.

Stdlib unittest only, no pytest: deploy-docs.yml runs these with
`python -m unittest discover` on a runner that installs nothing but
requirements.txt, so an `import pytest` here fails the whole docs deploy.

The failure these guard against is not "the parser crashed". It is "the parser
quietly announced the wrong set", which on this pipeline means either spamming
the plugin-dev role with years of backfilled history or silently announcing
nothing at all. Both look like a healthy green run from the outside, so the
assertions below are about the SET and the ORDER, not just the parse.
"""

import json
import os
import sys
import unittest
from unittest import mock

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


def _floor(version):
    return changelog_releases.parse_version(version)


class SectionSelection(unittest.TestCase):
    def test_prose_headings_never_become_releases(self):
        # "Getting notified" and "Something missing?" are ## headings too.
        # Turning either into a release would cut a junk tag AND ping the role.
        self.assertEqual([s["tag"] for s in sections()], ["v2.3.7", "v2.3.15", "v2.4.0"])

    def test_oldest_first(self):
        # The thread should read in shipping order, not reverse-chronological
        # like the page it came from.
        versions = [s["version"] for s in sections()]
        self.assertEqual(versions, sorted(versions, key=changelog_releases.parse_version))

    def test_floor_excludes_already_announced_history(self):
        kept = [s for s in sections() if _floor(s["version"]) >= _floor("2.3.8")]
        self.assertEqual([s["tag"] for s in kept], ["v2.3.15", "v2.4.0"])

    def test_intro_admonition_above_the_first_section_is_not_a_release(self):
        self.assertEqual(len(sections()), 3)


class BodyRewriting(unittest.TestCase):
    def test_relative_links_become_absolute(self):
        body = [s for s in sections() if s["version"] == "2.4.0"][0]["body"]
        self.assertNotIn("../api/data.md", body)
        self.assertIn(
            "https://jesperlive.github.io/GRIP-EMS-PluginAPI/api/data/#apigetactivesequence",
            body,
        )

    def test_admonition_markers_are_flattened(self):
        # Raw "!!! danger" renders as literal noise in Discord, and the indented
        # body under it renders as a code block.
        body = [s for s in sections() if s["version"] == "2.3.7"][0]["body"]
        self.assertNotIn("!!!", body)
        self.assertIn("**This one can break a working plugin**", body)
        self.assertNotIn("\n        If you compensated", body)

    def test_trailing_prose_does_not_leak_into_the_last_release(self):
        body = [s for s in sections() if s["version"] == "2.3.7"][0]["body"]
        self.assertNotIn("Watch the repo", body)
        self.assertNotIn("Tell me and I'll fix the page", body)

    def test_body_is_json_safe_for_the_webhook(self):
        for section in sections():
            json.dumps({"content": section["body"]})


class PendingSelection(unittest.TestCase):
    def test_pending_skips_versions_that_already_have_a_release(self):
        kept = [s for s in sections() if _floor(s["version"]) >= _floor("2.3.8")]
        with mock.patch.object(
            announce_pending, "release_exists", side_effect=lambda tag, repo: tag == "v2.3.15"
        ):
            pending = [s for s in kept if not announce_pending.release_exists(s["tag"], "r")]
        self.assertEqual([s["tag"] for s in pending], ["v2.4.0"])


class RealChangelog(unittest.TestCase):
    def test_real_changelog_yields_exactly_the_two_missed_releases(self):
        """The instance that motivated the whole pipeline.

        EMS 2.3.15 and 2.4.0 both moved the plugin surface and neither reached
        the thread. If this ever returns a different set, the announcement scope
        has drifted and someone is about to be over- or under-notified.
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
            self.skipTest("changelog not present in this checkout")
        with open(path, encoding="utf-8") as fh:
            parsed = changelog_releases.parse_changelog(fh.read())
        kept = [s for s in parsed if _floor(s["version"]) >= _floor("2.3.8")]
        self.assertEqual([s["tag"] for s in kept], ["v2.3.15", "v2.4.0"])


if __name__ == "__main__":
    unittest.main()
