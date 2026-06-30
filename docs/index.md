# GRIP-EMS Plugin API

Write plugins for **GRIP - Enhanced Macro Sequencer** without touching its source.

GRIP-EMS exposes one blessed entry point: a frozen, versioned table at `GRIPEMS.API` (also `_G.GRIPEMS_API`). Through it your addon can listen to what EMS is doing, read its state, and register your own variables, conditions, and step functions. The API goes further: a plugin can author content EMS owns — its own sequences, settings, and CVar profiles — and rehome EMS's built-in panels into a UI layout of its own, up to a full overhaul. Everything a plugin contributes is owned by its id and reverted the moment it's disabled, so a user can try an overhaul and get the stock addon back by turning it off. No call you make changes how rotations execute, how keys bind, who signed a sequence, what gets transmitted, or what gets saved.

That line is deliberate. WoW runs every addon in one shared Lua state, so a true sandbox is impossible — the API holds because it never hands you a write path into the parts that matter, and it wraps everything you give it in `pcall` so a bug in your plugin breaks your plugin, not the addon. The [security model](concepts/security-model.md) page explains the reasoning.

## Start here

- [Getting started](getting-started.md) — the TOC dependency, the handshake, and a plugin that does something in about twenty lines.
- [Security model](concepts/security-model.md) — what the boundary is and why it's drawn where it is.
- [Reversibility](concepts/reversibility.md) — why disabling a plugin always returns EMS to stock.
- [API reference](api/index.md) — every method, by tier.

## The tiers at a glance

| Tier | Surface | You use it to |
|---|---|---|
| 0 | Discovery + handshake | Check the API version, then register your plugin and take its handle. |
| 1 | Events | Subscribe to lifecycle and UI signals. EMS fires, you react. |
| 2 | Data | Read sequence summaries and per-step spell data, the active context, allowlisted settings, and a sequence's action-bar macro index. |
| 3 | UI + Preview | Mount EMS's built-in panels into your own hosts, register a layout provider and views, hide the classic chrome, drive the preview. |
| 4 | Registries | Add variables, conditions, and step functions EMS validates and owns. |
| 5 | Authoring + Theme | Author owned sequences, settings, CVar profiles, action-bar macros, and `/gems` subcommands; theme your frames to match. |

## Two rules that save you time

Register on readiness, not at file scope. EMS builds `GRIPEMS.API` during its own load, so wait for `PLAYER_LOGIN` (or the `GEMS_UI_READY` event for UI work) before you call anything.

Treat `_G.GRIPEMS` as off-limits. The internal table is reachable — WoW can't stop that — but it is unsupported and changes without notice. If you find yourself reaching into it, something is missing from the public API. Open an issue instead of building on internals.
