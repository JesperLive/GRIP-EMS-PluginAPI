# Tier 2 — Data

Read-only accessors over EMS state. Each returns a copy or a scalar, so nothing you receive aliases live engine data. There are no setters here — you read state, you don't write it.

## `API:GetSequenceList()`

```lua
for _, s in ipairs(API:GetSequenceList()) do
    print(s.name, s.currentStep .. "/" .. s.stepCount, s.stepFunction)
end
```

Returns an array of summaries for the active sequences, sorted by name. Each entry:

| Field | Type | Meaning |
|---|---|---|
| `name` | string | sequence name |
| `stepCount` | number | steps in the active version |
| `currentStep` | number | step the sequence is currently on (1 when idle) |
| `stepFunction` | string | active version's step-function id (e.g. `"Sequential"`) |

This is the lightweight listing view. For richer per-sequence metadata, call `GetSequenceInfo`.

## `API:GetSequenceInfo(name)`

```lua
local info = API:GetSequenceInfo("My Rotation")
if info then
    print(info.versionCount, "version(s), active is", info.activeVersionIndex)
end
```

Returns a metadata snapshot for one sequence, or `nil` when no sequence by that name is active. Every field is a scalar copied out of the sequence data:

| Field | Type | Meaning |
|---|---|---|
| `name` | string | sequence name |
| `stepFunction` | string \| nil | active version's step-function id |
| `versionCount` | number | how many versions the sequence has |
| `defaultVersion` | number \| nil | the default version index |
| `activeVersionIndex` | number \| nil | version resolved under the current context |
| `activeStepCount` | number | steps in the active version |
| `classID` | number \| nil | class the sequence is tagged to, if any |

There's no separate "active version" accessor — `activeVersionIndex` already carries the index the current context resolves to.

## `API:GetCurrentContext()`

```lua
local ctx = API:GetCurrentContext()  -- "none", "Raid", "MythicPlusHigh", "Arena", ...
```

Returns the content context EMS has detected, as a string key. It's `"none"` outside any recognized context. The full set of keys is internal and can grow between patches, so treat unknown values as "some context I don't handle" rather than switching exhaustively on it.

Context isn't a public event — to react to a change, poll this on the lifecycle events you already handle, or read it when you need it.

## `API:GetSetting(key)`

```lua
local layout = API:GetSetting("uiLayout")  -- "classic" | "modern" | nil
```

Returns the value of an allowlisted setting, or `nil` for anything off the allowlist. The allowlist is deliberately small and scalar-valued:

| Key | Type | Meaning |
|---|---|---|
| `uiLayout` | string \| nil | active layout-provider id; `nil` before one is stored |
| `debug` | boolean | whether EMS debug logging is on |

There's no setter. If you need visibility into a setting that isn't allowlisted, subscribe to `SETTING_CHANGED` — it broadcasts every changed key and value, so you can watch for the one you care about.

## `API:GetRegisteredPlugins()`

```lua
for _, p in ipairs(API:GetRegisteredPlugins()) do
    print(p.name, p.version, p.loaded, p.sequenceCount)
end
```

Returns an array of records for plugins that have registered sequences through the addon registry:

| Field | Type | Meaning |
|---|---|---|
| `name` | string | plugin name |
| `version` | string | plugin version as registered |
| `loaded` | boolean | whether its sequences are loaded into the engine |
| `sequenceCount` | number | how many sequences it registered |
