#!/usr/bin/env python3
"""Regression net for notify_discord.build_content.

Stdlib unittest, no dependencies -- runs in CI next to the deploy job.

The thing under test is a truncation calculation against a hard external limit.
Discord REJECTS a webhook message over 2000 characters rather than trimming it,
so an off-by-one here means the announcement silently never posts. That failure
would surface as "the bot is broken" weeks later, which is exactly the situation
this whole notification system exists to avoid.

    python3 -m unittest discover -s .github/scripts -p "test_*.py"
"""

import unittest

from notify_discord import CONTENT_LIMIT, USER_AGENT, build_content, build_request

ROLE = "1519784464983523452"
DOCS = "https://jesperlive.github.io/GRIP-EMS-PluginAPI/reference/changelog/"
URL = "https://github.com/JesperLive/GRIP-EMS-PluginAPI/releases/tag/api-2.3.7"


def content(body, name="API changelog - EMS 2.3.7"):
    return build_content(name=name, body=body, url=URL, role_id=ROLE, docs_url=DOCS)


class BuildContent(unittest.TestCase):
    def test_short_body_passes_through_intact(self):
        c = content("Added API:GetAuthoredSteps(name).")
        self.assertIn("Added API:GetAuthoredSteps(name).", c)
        self.assertLessEqual(len(c), CONTENT_LIMIT)

    def test_role_mention_is_well_formed(self):
        # A stray space here renders as literal text and pings nobody.
        self.assertIn("<@&%s>" % ROLE, content("x"))

    def test_oversized_body_is_trimmed_to_the_limit(self):
        c = content("A" * 5000)
        self.assertLessEqual(len(c), CONTENT_LIMIT)
        self.assertIn("(truncated)", c)

    def test_oversized_body_keeps_both_links(self):
        # Non-vacuity: trimming the wrong end would drop these and the reader
        # would have no way to find the actual changelog.
        c = content("A" * 5000)
        self.assertIn(DOCS, c)
        self.assertIn(URL, c)

    def test_body_at_exactly_the_boundary_does_not_overflow(self):
        # Walk the boundary rather than trusting one sample.
        for n in range(1900, 2101):
            self.assertLessEqual(len(content("A" * n)), CONTENT_LIMIT, "body of %d overflowed" % n)

    def test_empty_body_still_announces(self):
        c = content("")
        self.assertIn(DOCS, c)
        self.assertLessEqual(len(c), CONTENT_LIMIT)

    def test_missing_name_falls_back_without_crashing(self):
        c = build_content(name="new release", body="", url=URL, role_id=ROLE, docs_url=DOCS)
        self.assertIn("new release", c)


class BuildRequest(unittest.TestCase):
    """Transport-layer tests.

    These exist because of a real escape. The first version of this script
    shipped with 7 green tests and still failed against live Discord: urllib's
    default "Python-urllib/3.x" User-Agent is blocked at Cloudflare with
    403 / error 1010. Every test stopped at build_content, so nothing noticed.
    Caught only by posting for real. These pin the transport so it cannot
    regress silently again.
    """

    def req(self):
        return build_request("https://discord.com/api/webhooks/1/t?thread_id=2&wait=true", {"content": "x"})

    def test_sends_a_custom_user_agent(self):
        ua = self.req().get_header("User-agent")
        self.assertIsNotNone(ua, "no User-Agent header -- Cloudflare will 403 this")
        self.assertEqual(ua, USER_AGENT)

    def test_user_agent_is_not_the_urllib_default(self):
        # The exact string Cloudflare rejects.
        self.assertNotIn("Python-urllib", self.req().get_header("User-agent"))

    def test_posts_json(self):
        r = self.req()
        self.assertEqual(r.get_method(), "POST")
        self.assertEqual(r.get_header("Content-type"), "application/json")

    def test_body_is_encoded_json(self):
        import json as _j

        self.assertEqual(_j.loads(self.req().data.decode("utf-8")), {"content": "x"})


if __name__ == "__main__":
    unittest.main()
