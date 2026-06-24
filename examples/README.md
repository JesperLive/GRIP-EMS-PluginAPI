# Examples

Copy-me starting points for your own plugin. The code here is under the MIT License (see the repo `LICENSE`), so take it, rename it, and build on it.

| Folder | What it shows |
|---|---|
| `MyFirstPlugin/` | A complete, working plugin: the TOC dependency, the version handshake, capability checks, event subscriptions, a Tier 2 data read behind a slash command, a variable provider, and a condition. |

## Using one

1. Copy the folder into your `World of Warcraft/_retail_/Interface/AddOns/` directory.
2. Rename the folder, the `.toc`, and the addon table to your own name.
3. Reload (`/reload`) with GRIP - Enhanced Macro Sequencer installed.

Each example is its own addon with a hard dependency on GRIP-EMS, so it won't load unless EMS is present. Read it top to bottom — the comments explain each API call as it happens, and the matching [guide](../docs/guides/first-plugin.md) walks through the same code.
