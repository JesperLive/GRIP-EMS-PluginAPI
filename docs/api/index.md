# API reference

Everything a plugin can call lives on `GRIPEMS.API` (alias `_G.GRIPEMS_API`), plus two frozen sub-tables, `GRIPEMS.API.UI` and `GRIPEMS.API.Preview`. This page is the map; each tier has its own page with full signatures and examples.

## Conventions

**Call style.** Use the colon: `GRIPEMS.API:GetSequenceList()`. Every method takes a leading `self` it ignores, so the colon form is what you want. Sub-table methods are the same: `GRIPEMS.API.UI:GetHost("editorHost")`.

**Return values.** Methods that register or change something return `ok` first — `true`, or `false` plus a reason string:

```lua
local ok, reason = GRIPEMS.API:RegisterCondition("acme_burst", spec)
if not ok then
    print("registration failed:", reason)
end
```

Read accessors return the value directly, or `nil` when there's nothing to return. They never raise.

**The table is frozen.** Assigning to `GRIPEMS.API` (or `.UI` / `.Preview`) throws. You call methods; you don't add or replace them.

## The surface, by tier

### Tier 0 — Discovery ([details](discovery.md))

| Member | Returns |
|---|---|
| `API.API_VERSION` | integer contract version |
| `API.EMS_VERSION` | running EMS version string |
| `API:RequireVersion(n)` | `true`, or `false` + reason |
| `API:GetCapabilities()` | fresh array of capability ids |

### Tier 1 — Events ([details](events.md))

| Method | Returns |
|---|---|
| `API:On(event, handler)` | handle string, or `false` + reason |
| `API:Off(handle)` | nothing |
| `API:ListEvents()` | fresh array of event names |

### Tier 2 — Data ([details](data.md))

| Method | Returns |
|---|---|
| `API:GetSequenceList()` | array of sequence summaries |
| `API:GetSequenceInfo(name)` | metadata table, or `nil` |
| `API:GetCurrentContext()` | context key string |
| `API:GetSetting(key)` | allowlisted value, or `nil` |
| `API:GetRegisteredPlugins()` | array of plugin records |

### Tier 3 — UI and layout ([details](ui-layout.md))

| Method | Returns |
|---|---|
| `API.UI:RegisterLayoutProvider(id, provider)` | `true`, or `false` + reason |
| `API.UI:SetActiveLayoutProvider(id)` | `true`, or `false` + reason |
| `API.UI:GetActiveLayoutProvider()` | provider id string |
| `API.UI:GetHost(name)` | host frame, or `nil` |
| `API.UI:RegisterPanelFrame(frame, category, class)` | nothing (Tier 5) |

### Tier 3 — Preview ([details](preview.md))

| Method | Returns |
|---|---|
| `API.Preview:GetMode()` | mode string |
| `API.Preview:SetMode(mode)` | `true`, or `false` + reason |
| `API.Preview:Update(version)` | `true` |
| `API.Preview:Hide()` | nothing |
| `API.Preview:MountSidebar(host)` | `true`, or `false` + reason |
| `API.Preview:MountIconFooter(host)` | `true`, or `false` + reason |

### Tier 4 — Registries ([details](registries.md))

| Method | Returns |
|---|---|
| `API:RegisterSequences(name, version, seqNames, seqTable)` | success boolean |
| `API:RegisterVariableProvider(id, spec)` | `true`, or `false` + reason |
| `API:RegisterCondition(id, spec)` | `true`, or `false` + reason |
| `API:EvaluateCondition(id)` | clean boolean |
| `API:RegisterStepFunction(id, spec)` | `true`, or `false` + reason |

### Tier 5 — Theme ([details](theme.md))

`API.UI:RegisterPanelFrame(frame, category, class)` registers your frame with the EMS theme so it inherits the active skin. It lives on the UI sub-table.
