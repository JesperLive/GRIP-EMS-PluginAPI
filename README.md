# GRIP-EMS Plugin API

Developer documentation for writing plugins for **GRIP - Enhanced Macro Sequencer**, a World of Warcraft Retail addon.

GRIP-EMS exposes a frozen, versioned Lua table — `GRIPEMS.API` — that lets your addon extend it without editing its files. You can listen to events, read sequence and context state, register a custom UI layout, and add your own variables, conditions, and step functions. The API is additive: nothing you call changes how EMS runs rotations, binds keys, signs sequences, or saves data. That boundary is the whole point — extend the addon, don't reach into it.

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

- Tier 0 — a version handshake so you fail fast against an old EMS.
- Tier 1 — a listen-only event bus (EMS fires, you react).
- Tier 2 — read-only accessors for sequences, the active context, and a few settings.
- Tier 3 — UI host frames, a layout-provider slot, and a preview facade.
- Tier 4 — registries for your own variables, conditions, and step functions.
- Tier 5 — theme integration so your frames match the active EMS skin.

## Versioning

`GRIPEMS.API.API_VERSION` is an integer, bumped only on a breaking change. Call `GRIPEMS.API:RequireVersion(n)` in your init and bail out cleanly if it returns false.

## Status

API_VERSION 1. Documented against GRIP-EMS 2.1.29 on WoW Retail 12.0.7 (Midnight).

## License

Documentation prose in this repo is © Sataana (MrSataana / JesperLive), all rights reserved. The example and snippet **code** is released under the MIT License (see `LICENSE`) so you can copy it straight into your own plugin.
