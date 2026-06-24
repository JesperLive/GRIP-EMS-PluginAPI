# Getting started

This page takes you from an empty folder to a plugin that listens to EMS and reads its state. It assumes you've written a WoW addon before — you know what a `.toc` is and how `SavedVariables` work.

## 1. Declare EMS as a dependency

Your plugin is its own addon. In its `.toc`, make GRIP-EMS a hard dependency:

```
## Interface: 120007
## Title: My EMS Plugin
## Author: You
## Version: 1.0.0
## Dependencies: GRIP-EMS

MyPlugin.lua
```

`## Dependencies: GRIP-EMS` does two things. WoW refuses to load your plugin when EMS is absent or disabled, and it guarantees EMS loads first — so by the time your files run, `GRIPEMS.API` already exists. If you'd rather your plugin load on its own and just do less when EMS is missing, use `## OptionalDeps: GRIP-EMS` instead and null-check the API.

## 2. Grab the API and check the version

The entry point is `GRIPEMS.API` (the global alias `_G.GRIPEMS_API` points at the same table). Before you call anything, run the handshake:

```lua
local API = GRIPEMS and GRIPEMS.API
if not API then
    return  -- EMS not loaded; nothing to extend
end

local ok, reason = API:RequireVersion(1)
if not ok then
    print("My EMS Plugin needs a newer GRIP-EMS:", reason)
    return
end
```

`RequireVersion(n)` returns `true` when the running `API_VERSION` is at least `n`. On a build that's too old it returns `false` plus a reason string you can show the user. Pass the lowest version that has the features you use.

## 3. Register on readiness, not at file scope

Even though EMS loads first, register your hooks from an init point rather than at file scope. Use `PLAYER_LOGIN` for events and registries, and the `GEMS_UI_READY` event for anything that touches the UI (host frames and the main window are built by then):

```lua
local f = CreateFrame("Frame")
f:RegisterEvent("PLAYER_LOGIN")
f:SetScript("OnEvent", function()
    local API = GRIPEMS and GRIPEMS.API
    if not API or not API:RequireVersion(1) then
        return
    end
    MyPlugin_Init(API)
end)
```

## 4. A plugin that does something

Listen for a sequence being created and read back its details:

```lua
function MyPlugin_Init(API)
    API:On("SEQUENCE_CREATED", function(name, data)
        local info = API:GetSequenceInfo(name)
        if info then
            print(("EMS sequence %q has %d step(s) on the %s strategy")
                :format(name, info.activeStepCount, tostring(info.stepFunction)))
        end
    end)
end
```

That's a complete plugin. It declares the dependency, checks the version, waits for login, subscribes to an event, and reads state through a Tier 2 accessor. Nothing it does can change how EMS runs.

## 5. Where to go next

- [Security model](concepts/security-model.md) — the boundary you're working inside, and why it exists.
- [Tier 1 - Events](api/events.md) and the [event catalog](reference/event-catalog.md) — everything you can subscribe to.
- [Tier 2 - Data](api/data.md) — the read-only accessors.
- [Tier 3 - UI and layout](api/ui-layout.md) — replace the window layout with your own.
- [Tier 4 - Registries](api/registries.md) — add variables, conditions, and step functions.

## A note on failure

Every callback you hand EMS — event handlers, provider methods, layout-provider hooks — runs inside `pcall`. If your code throws, EMS logs it against your plugin and disables that one feature. It does not crash the addon. You'll find your errors in the EMS debug log, not in a `lua error` popup for the user, so turn debug on while you develop.
