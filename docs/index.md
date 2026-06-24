# GRIP-EMS Plugin API

Write plugins for **GRIP - Enhanced Macro Sequencer** without touching its source.

GRIP-EMS exposes one blessed entry point: a frozen, versioned table at `GRIPEMS.API` (also `_G.GRIPEMS_API`). Through it your addon can listen to what EMS is doing, read its state, drop in a new UI layout, and register your own variables, conditions, and step functions. Everything on the surface either reads state or registers a contribution that EMS validates and owns. No call you make changes how rotations execute, how keys bind, who signed a sequence, what gets transmitted, or what gets saved.

That line is deliberate. WoW runs every addon in one shared Lua state, so a true sandbox is impossible — the API holds because it never hands you a write path into the parts that matter, and it wraps everything you give it in `pcall` so a bug in your plugin breaks your plugin, not the addon. The [security model](concepts/security-model.md) page explains the reasoning.

## Start here

- [Getting started](getting-started.md) — the TOC dependency, the handshake, and a plugin that does something in about twenty lines.
- [Security model](concepts/security-model.md) — what the boundary is and why it's drawn where it is.
- [API reference](api/index.md) — every method, by tier.

## The tiers at a glance

| Tier | Surface | You use it to |
|---|---|---|
| 0 | Discovery | Check the API version before you call anything. |
| 1 | Events | Subscribe to lifecycle and UI signals. EMS fires, you react. |
| 2 | Data | Read sequence summaries, the active context, allowlisted settings. |
| 3 | UI + Preview | Mount panels into host frames, register a layout provider, drive the preview. |
| 4 | Registries | Add variables, conditions, and step functions EMS validates and owns. |
| 5 | Theme | Register your frames so they inherit the active EMS skin. |

## Two rules that save you time

Register on readiness, not at file scope. EMS builds `GRIPEMS.API` during its own load, so wait for `PLAYER_LOGIN` (or the `GEMS_UI_READY` event for UI work) before you call anything.

Treat `_G.GRIPEMS` as off-limits. The internal table is reachable — WoW can't stop that — but it is unsupported and changes without notice. If you find yourself reaching into it, something is missing from the public API. Open an issue instead of building on internals.
