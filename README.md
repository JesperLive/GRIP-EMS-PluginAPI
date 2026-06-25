# GRIP-EMS Plugin API

Developer documentation for writing plugins for **GRIP - Enhanced Macro Sequencer**, a World of Warcraft Retail addon.

GRIP-EMS exposes a frozen, versioned Lua table — `GRIPEMS.API` — that lets your addon extend it without editing its files. You can listen to events, read sequence and context state, and register your own variables, conditions, and step functions. v2 adds owner-scoped authoring: a plugin can create its own sequences, override settings, request CVar profiles, and rehome EMS's panels into a UI layout of its own, up to a full overhaul — and everything it does is reverted when it's disabled. Through all of it the locked core holds: nothing you call changes how EMS runs rotations, binds keys, signs sequences, or saves data. Extend the addon, don't reach into it.

- **Docs site:** https://JesperLive.github.io/GRIP-EMS-PluginAPI
- **Wiki:** https://github.com/JesperLive/GRIP-EMS-PluginAPI/wiki
- **The addon:** search "GRIP - Enhanced Macro Sequencer" on CurseForge, Wago, or WoWInterface.

## Quick start

Add EMS as a hard dependency in your `.toc`, then register once EMS is loaded:

```lua
-- YourPlugin.toc
-- ## Dependencies: GRIP-EMS

local API = GRIPEMS and GRIPEMS.API
if not API then return end                 -- EMS not present
if not API:RequireVersion(1) then return end  -- EMS too old

API:On("SEQUENCE_CREATED", function(name, data)
    print("EMS created a sequence:", name)
end)
```

## What the API gives you

- Tier 0 — a version handshake, then `RegisterPlugin` to get your owning handle.
- Tier 1 — a listen-only event bus (EMS fires, you react).
- Tier 2 — read-only accessors for sequences, the active context, and a few settings.
- Tier 3 — host frames, a layout provider, panel mounting, views, and a preview facade.
- Tier 4 — registries for your own variables, conditions, and step functions.
- Tier 5 — authoring (owned sequences, settings, CVar profiles) and theme integration.

Everything a plugin registers or authors through its handle is reverted when the plugin is disabled — the reversibility page on the docs site covers it.

## Building with an AI assistant

An AI assistant writes correct plugins when it has the API in front of it. Paste the [AI context pack](https://JesperLive.github.io/GRIP-EMS-PluginAPI/reference/ai-context/) into the chat, then follow the [AI-assisted guide](https://JesperLive.github.io/GRIP-EMS-PluginAPI/guides/ai-assisted/) and check what it gives you against the pack.

## Versioning

`GRIPEMS.API.API_VERSION` is an integer; it goes up when the surface gains a level worth gating on (v1 → v2 added the handle and the authoring tier). Call `GRIPEMS.API:RequireVersion(n)` in your init and bail out cleanly if it returns false.

## Status

API_VERSION 2. Documented against GRIP-EMS 2.2.0 on WoW Retail 12.0.7 (Midnight).

## License

Documentation prose in this repo is © Sataana (MrSataana / JesperLive), all rights reserved. The example and snippet **code** is released under the MIT License (see `LICENSE`) so you can copy it straight into your own plugin.
