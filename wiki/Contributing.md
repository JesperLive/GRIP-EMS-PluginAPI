# Contributing

Two surfaces, two ways to help.

## The wiki (this)

Edit freely. Fix a typo, add a [FAQ](FAQ) answer, list your plugin in the [showcase](Plugin-Showcase), or write up a pattern you worked out. No review step — just keep it accurate and plain. If something here contradicts the docs site, the docs site is authoritative; fix the wiki to match.

## The docs site

The reference and guides live in the repo under `docs/` and are built with MkDocs Material. To change them:

1. Fork the repo and edit the Markdown under `docs/`.
2. Build locally to check it: `pip install -r requirements.txt` then `mkdocs serve`.
3. Open a pull request.

Because the docs site is versioned with the repo, changes there are reviewed — that's what keeps the reference trustworthy.

## Reporting an API gap

If you need something the public API doesn't expose — a value, an event, a hook — open an [issue](https://github.com/JesperLive/GRIP-EMS-PluginAPI/issues) describing the goal, not just the missing call. The boundary around execution, binding, identity, transmission, secure CVars, and persistence is firm (see the [lock list](https://JesperLive.github.io/GRIP-EMS-PluginAPI/reference/lock-list/)), but the read-only and event surface around it can grow when there's a real need.

## Writing style

Plain and direct. Say what a thing does; skip the adjectives. Short sentences, real examples, code where it helps. These are developer docs — accuracy beats polish.
