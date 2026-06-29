# Tier 0 — Discovery

The handshake. Call these before anything else so your plugin fails clearly against an EMS that's missing or too old, instead of erroring deep in a feature call.

## `API.API_VERSION`

An integer, the contract version of the API surface. It goes up when the surface gains a level worth gating on — v2 added the plugin handle, reversibility, panel mounting, views, and the authoring tier; v3 added the action-bar surface: per-step spell data, the sequence's own action-bar macro, and plugin `/gems` subcommands. A v1 plugin keeps working unchanged on a v3 build; the bump is what lets a newer plugin detect the surface it needs. Compare against it through `RequireVersion` rather than reading it directly.

Current value: `3`.

## `API.EMS_VERSION`

A string, the running EMS version (for example `"2.2.0"`). Read once at load. Useful for logging and bug reports; don't gate features on it — gate on `API_VERSION`, which tracks the API, not the addon release.

## `API:RequireVersion(n)`

```lua
local ok, reason = API:RequireVersion(1)
```

Returns `true` when the running `API_VERSION` is at least `n`. Otherwise returns `false` and a reason string naming the running and required versions. Pass the lowest `API_VERSION` that has the features you depend on.

```lua
-- A plugin that needs the v2 authoring surface (the handle, owned writes):
if not API:RequireVersion(2) then
    return  -- this EMS predates v2; bail out quietly
end
```

`n` must be a number. Anything else returns `false` with a reason.

## `API:GetCapabilities()`

```lua
local caps = API:GetCapabilities()  -- { "events", "data", "sequences", ... }
```

Returns a fresh array of capability-id strings this build supports. You get a new copy each call, so mutating it is harmless. Use it to feature-detect a tier before you use it, instead of assuming it's present:

```lua
local function has(cap)
    for _, c in ipairs(API:GetCapabilities()) do
        if c == cap then return true end
    end
    return false
end

if has("variables") then
    API:RegisterVariableProvider("acme_haste", spec)
end
```

The capability ids in this build:

| id | Tier | Covers |
|---|---|---|
| `events` | 1 | the listen-only event bus |
| `data` | 2 | read-only state accessors |
| `sequences` | 4 | `RegisterSequences` |
| `ui` | 3 | host frames + layout providers |
| `preview` | 3 | the preview facade |
| `variables` | 4 | `RegisterVariableProvider` |
| `conditions` | 4 | `RegisterCondition` / `EvaluateCondition` |
| `stepfunctions` | 4 | `RegisterStepFunction` |
| `plugins` | 0 | `RegisterPlugin` and the handle |
| `panels` | 3 | `MountPanel` |
| `views` | 3 | `RegisterView` / `SetActiveView` |
| `settings` | 5 | `RegisterSetting` / `OverrideSetting` |
| `cvars` | 5 | `RequestCVarProfile` |
| `authoring` | 5 | owned sequences, settings, and CVar profiles |
| `stepdata` | 2 | `GetSequenceSteps` |
| `macro` | 2 / 5 | `GetSequenceMacroIndex` and `handle:EnsureSequenceMacro` |
| `slash` | 5 | `handle:RegisterSlashCommand` |

The order in the array follows the source: `events`, `data`, `sequences`, `ui`, `preview`, `variables`, `conditions`, `stepfunctions`, `plugins`, `authoring`, `panels`, `views`, `settings`, `cvars`, `stepdata`, `macro`, `slash`. Don't depend on the order — check for the id you want.

## `API:RegisterPlugin(id, meta)`

The handshake ends here. Once the version checks out, register your plugin and take its handle — the table that owns everything your plugin contributes and the entry to most of the v2 surface.

```lua
local handle, reason = API:RegisterPlugin("acme_overhaul", {
    name = "Acme Overhaul",
    version = "1.0.0",
    OnEnable = function(h) MyPlugin_Build(h) end,
})
```

It has its own page, because the handle is where the rest of the API hangs off: [Plugins and the handle](plugins.md).
