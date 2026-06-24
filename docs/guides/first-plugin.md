# Guide: your first plugin

This walks through the complete example at [`examples/MyFirstPlugin`](https://github.com/JesperLive/GRIP-EMS-PluginAPI/tree/main/examples/MyFirstPlugin). It's a real, installable plugin that touches every common part of the API. Copy the folder, rename it, and change things as you read.

## The TOC

```
## Interface: 120007
## Title: My First EMS Plugin
## Author: You
## Version: 1.0.0
## Dependencies: GRIP-EMS

MyFirstPlugin.lua
```

`## Dependencies: GRIP-EMS` is the line that matters. WoW won't load the plugin without EMS, and it loads EMS first, so `GRIPEMS.API` exists by the time your file runs.

## Register on login

```lua
local f = CreateFrame("Frame")
f:RegisterEvent("PLAYER_LOGIN")
f:SetScript("OnEvent", function()
    Init()
end)
```

Do your setup from `PLAYER_LOGIN`, not at file scope. It's the point where EMS is fully built.

## The handshake

```lua
local API = GRIPEMS and GRIPEMS.API
if not API then return end

local ok, reason = API:RequireVersion(1)
if not ok then
    print("needs a newer GRIP-EMS: " .. tostring(reason))
    return
end
```

Null-check the API, then check the version. Pass the lowest `API_VERSION` you depend on.

## Check a capability before you use it

```lua
local function HasCapability(API, cap)
    for _, c in ipairs(API:GetCapabilities()) do
        if c == cap then return true end
    end
    return false
end
```

This lets the plugin degrade on an older EMS that doesn't have a tier, instead of erroring. The example guards its variable provider with `HasCapability(API, "variables")`.

## Listen for an event

```lua
API:On("SEQUENCE_CREATED", function(name)
    print("saw a new sequence: " .. tostring(name))
end)
```

`SEQUENCE_CREATED` hands your handler `(name, data)` — the name first. `On` returns a handle you can keep and pass to `Off` later if you ever need to unsubscribe. The full list of events is the [event catalog](../reference/event-catalog.md).

## Add a variable

```lua
API:RegisterVariableProvider("myfirst_groupsize", {
    id = "myfirst_groupsize",
    name = "My First Plugin: group size",
    Resolve = function(_, varName)
        if varName == "myfirst_groupsize" then
            return GetNumGroupMembers()
        end
        return nil
    end,
})
```

Now a user can drop `~myfirst_groupsize~` into a sequence and it resolves to the current group size. Return `nil` for names that aren't yours, and only ever return a plain non-secret scalar — see the [variable provider guide](variable-provider.md) for the why.

## Add a condition

```lua
API:RegisterCondition("myfirst_in_group", {
    id = "myfirst_in_group",
    name = "My First Plugin: in a group",
    Evaluate = function() return IsInGroup() end,
})
```

A user branches on it inside a variable body:

```lua
GRIPEMS.API:EvaluateCondition("myfirst_in_group") and "Battle Shout" or "Heroic Strike"
```

## Read state behind a slash command

```lua
SLASH_MYFIRSTPLUGIN1 = "/myfirst"
SlashCmdList["MYFIRSTPLUGIN"] = function()
    local list = API:GetSequenceList()
    print(("%d active sequence(s), context = %s"):format(#list, tostring(API:GetCurrentContext())))
end
```

`GetSequenceList` and `GetCurrentContext` are read-only Tier 2 accessors — see [Tier 2 - Data](../api/data.md).

## That's the whole shape

Dependency, login, handshake, capability check, events, registries, data reads. From here, pick the tier you want to go deeper on — [registries](../api/registries.md) for content, [UI and layout](../api/ui-layout.md) to replace the window layout.
