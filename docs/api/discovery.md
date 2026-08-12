# Tier 0 — Discovery

The handshake. Call these before anything else so your plugin fails clearly against an EMS that's missing or too old, instead of erroring deep in a feature call.

## `API.API_VERSION`

An integer, the contract version of the API surface. It goes up when the surface gains something worth gating on — v2 added the plugin handle, reversibility, panel mounting, views, and the authoring tier; v3 added the action-bar surface: per-step spell data, the sequence's own action-bar macro, and plugin `/gems` subcommands; v4 adds `API:GetActiveSequence` and gives authored-step reads their own `authoredsteps` capability id. A v1 plugin keeps working unchanged on a v4 build; the bump is what lets a newer plugin detect the surface it needs. Compare against it through `RequireVersion` rather than reading it directly.

Current value: `4`.

It goes up on any addition to this surface, not only on a breaking change. One method predates that rule: `API:GetAuthoredSteps` arrived in EMS 2.3.7 while `API_VERSION` stayed at `3`, so on that one build a version check answers yes for a method that may not be there. A version check proves a *tier* is present — for `GetAuthoredSteps` specifically, or any time you still support 2.3.7, test for the method itself:

```lua
if API.GetAuthoredSteps then
    local steps = API:GetAuthoredSteps("My Rotation")
end
```

Reading a key the API does not have returns `nil` rather than raising, so the check is safe on any build. Note the dot on the check and the colon on the call.

## `API.EMS_VERSION`

A string, the running EMS version (for example `"2.4.0"`). Read once at load. Useful for logging and bug reports; don't gate features on it — gate on `API_VERSION`, which tracks the API, not the addon release, and presence-check any method that landed mid-version.

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

From v4 on, this is a real gate: the version goes up on any addition, so `RequireVersion` covers the methods too. The one exception is `GetAuthoredSteps` on EMS 2.3.7 — see `API_VERSION` above — which still needs its own presence check.

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
| `authoredsteps` | 2 | `GetAuthoredSteps` |

An id can be older than everything it covers. `stepdata` shipped with `GetSequenceSteps` and then silently grew to cover `GetAuthoredSteps` as well, which is what made it useless as a detector for the newer method. From v4 that is repaired: `GetAuthoredSteps` has its own `authoredsteps` id, so on a v4 build the id and the method agree. On EMS 2.3.7 neither `authoredsteps` nor a version bump is there to find, so the presence check above remains the only reliable test on that build. Capabilities gate the tier; presence-check the method.

The order in the array follows the source: `events`, `data`, `sequences`, `ui`, `preview`, `variables`, `conditions`, `stepfunctions`, `plugins`, `authoring`, `panels`, `views`, `settings`, `cvars`, `stepdata`, `macro`, `slash`, `authoredsteps`. Don't depend on the order — check for the id you want.

## `API:RegisterPlugin(id, meta)`

The handshake ends here. Once the version checks out, register your plugin and take its handle — the table that owns everything your plugin contributes and the entry to most of the surface.

```lua
local handle, reason = API:RegisterPlugin("acme_overhaul", {
    name = "Acme Overhaul",
    version = "1.0.0",
    OnEnable = function(h) MyPlugin_Build(h) end,
})
```

It has its own page, because the handle is where the rest of the API hangs off: [Plugins and the handle](plugins.md).
