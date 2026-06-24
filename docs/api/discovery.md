# Tier 0 — Discovery

The handshake. Call these before anything else so your plugin fails clearly against an EMS that's missing or too old, instead of erroring deep in a feature call.

## `API.API_VERSION`

An integer. The contract version of the API surface. It's bumped only when a change would break existing plugins — adding a method does not bump it. Compare against it through `RequireVersion` rather than reading it directly.

Current value: `1`.

## `API.EMS_VERSION`

A string, the running EMS version (for example `"2.1.29"`). Read once at load. Useful for logging and bug reports; don't gate features on it — gate on `API_VERSION`, which tracks the API, not the addon release.

## `API:RequireVersion(n)`

```lua
local ok, reason = API:RequireVersion(1)
```

Returns `true` when the running `API_VERSION` is at least `n`. Otherwise returns `false` and a reason string naming the running and required versions. Pass the lowest `API_VERSION` that has the features you depend on.

```lua
-- A plugin that needs a hypothetical v2 feature:
if not API:RequireVersion(2) then
    return  -- this EMS is v1; bail out quietly
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
