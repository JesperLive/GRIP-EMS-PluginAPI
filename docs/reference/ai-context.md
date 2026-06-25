# AI context pack

Writing an EMS plugin with an AI assistant? Paste this whole page into the chat before you ask for code. It's the entire public API on one page. An assistant that hasn't seen it guesses at method names and gets them wrong; one that has it writes against the real surface.

This page is condensed from the rest of these docs and tracks them. The fuller versions are linked from the [API reference](../api/index.md). To paste a clean copy, grab the [raw markdown](https://raw.githubusercontent.com/JesperLive/GRIP-EMS-PluginAPI/main/docs/reference/ai-context.md).

## How to use it

1. Paste everything below the line into your assistant.
2. Describe the plugin you want, concretely.
3. Check the result against this page: every `GRIPEMS.API:...` call it writes must appear below. If a method isn't here, it doesn't exist, and the assistant invented it. Tell it so and have it redo that part.

The [AI-assisted plugin guide](../guides/ai-assisted.md) has example prompts and the full check-it loop.

---

## GRIP-EMS plugin API, condensed

EMS (GRIP - Enhanced Macro Sequencer) is a World of Warcraft Retail addon. A plugin is its own addon that extends EMS through one frozen table, `GRIPEMS.API` (global alias `_G.GRIPEMS_API`). You never edit EMS and never reach into `_G.GRIPEMS`. Everything a plugin contributes through its handle is reverted the moment the user disables it, so the addon returns to stock.

API_VERSION: 2. Documented against GRIP-EMS 2.2.0 on WoW Retail 12.0.7.

### Hard rules (follow every one)

1. The plugin is a separate addon. Its `.toc` has `## Dependencies: GRIP-EMS`, so WoW loads EMS first and refuses to load the plugin without it.
2. Do setup from `PLAYER_LOGIN`; do UI setup after the `GEMS_UI_READY` event. Never at file scope.
3. Handshake before any other call: null-check `GRIPEMS.API`, then `API:RequireVersion(n)`.
4. To contribute anything that should vanish on disable, call `API:RegisterPlugin(id, meta)` and work through the handle it returns.
5. Use only methods on this page. Never read or write `_G.GRIPEMS`.
6. A variable provider's `Resolve` and a condition's `Evaluate` return a plain, non-secret scalar (string, number, or boolean). Never a table, a function, or a 12.0 secret value such as `UnitHealth("player")`.
7. Registering or changing returns `ok` first: `true`, or `false` plus a reason. Read accessors return the value or `nil` and never raise. Call with the colon: `API:Method()`.

### Plugin skeleton (the correct shape)

```lua
-- MyPlugin.toc
-- ## Interface: 120007
-- ## Title: My EMS Plugin
-- ## Author: You
-- ## Version: 1.0.0
-- ## Dependencies: GRIP-EMS
-- MyPlugin.lua

local f = CreateFrame("Frame")
f:RegisterEvent("PLAYER_LOGIN")
f:SetScript("OnEvent", function()
    local API = GRIPEMS and GRIPEMS.API
    if not API then return end                    -- EMS not loaded
    if not API:RequireVersion(2) then return end  -- needs v2 for the handle

    local handle = API:RegisterPlugin("myplugin", {
        name = "My EMS Plugin",
        version = "1.0.0",
        OnEnable = function(h)
            -- register providers, author sequences, mount panels here
        end,
        OnDisable = function(h)
            -- only cleanup EMS can't do; it reverts your contributions for you
        end,
    })
    if not handle then return end
end)
```

### Tier 0 - discovery

- `GRIPEMS.API.API_VERSION` -> integer (2)
- `GRIPEMS.API.EMS_VERSION` -> string ("2.2.0"); for logs only, don't gate features on it
- `GRIPEMS.API:RequireVersion(n)` -> true, or false + reason
- `GRIPEMS.API:GetCapabilities()` -> array of capability id strings
- `GRIPEMS.API:RegisterPlugin(id, meta)` -> handle, or nil + reason
    - `meta = { name = string, version = string, OnEnable = function(handle), OnDisable = function(handle) }`
    - `id` is your namespace for everything you contribute; a duplicate id is rejected, never overwritten.

Capability ids: `events`, `data`, `sequences`, `ui`, `preview`, `variables`, `conditions`, `stepfunctions`, `plugins`, `authoring`, `panels`, `views`, `settings`, `cvars`. Check `GetCapabilities()` before using a tier if you want to degrade on an older EMS.

### Tier 1 - events (listen only)

- `GRIPEMS.API:On(event, handler)` -> handle string, or false + reason. The handler gets the payload args only, not the event name. It runs inside `pcall`.
- `GRIPEMS.API:Off(handle)` -> nothing
- `GRIPEMS.API:ListEvents()` -> array of the subscribable names

`On` rejects any name not in this set. Payloads that carry a table hand you a deep-copied, read-only snapshot.

| Event | Payload |
|---|---|
| `SEQUENCE_CREATED` | `(name, data)` |
| `SEQUENCE_DELETED` | `(name)` |
| `SEQUENCE_IMPORTED` | `(results)` |
| `SEQUENCE_UPDATED` | `(name, data)` |
| `SEQUENCE_STEP_ADVANCED` | `(seqName, step, numSteps)` |
| `KEYBIND_CHANGED` | `(seqName, key)` - both may be nil on a bulk/clear change |
| `CONTEXT_CHANGED` | `(newContext, oldContext)` |
| `LOADOUT_CHANGED` | `(newID, newName, oldID, oldName)` |
| `SETTING_CHANGED` | `(key, value)` |
| `PLUGIN_REGISTERED` | `(name, version)` |
| `PLUGIN_SEQUENCES_LOADED` | none |
| `GEMS_UI_READY` | none - do UI setup on this one |
| `GEMS_UI_LAYOUT_APPLY` | none |
| `GEMS_UI_NAV_CHANGED` | `(viewId)` |
| `GEMS_EDITOR_TAB_CHANGED` | `(tabName)` |
| `GEMS_SEQUENCE_SELECTED` | `(name)` |
| `GEMS_PREVIEW_MODE_CHANGED` | `(mode)` |
| `GEMS_PREVIEW_UPDATE` | none |

`PLUGIN_ENABLED` and `PLUGIN_DISABLED` are not public; use your `OnEnable` / `OnDisable` callbacks instead.

### Tier 2 - data (read-only; you get copies and scalars)

- `GRIPEMS.API:GetSequenceList()` -> array of `{ name, stepCount, currentStep, stepFunction }`
- `GRIPEMS.API:GetSequenceInfo(name)` -> table or nil. Fields: `name, stepFunction, versionCount, defaultVersion, activeVersionIndex, activeStepCount, contextVersionCount, classID, specID, author, description, privacyMode, version, createdAt, updatedAt, disabled, keybind, variableDeps`
- `GRIPEMS.API:GetCurrentContext()` -> string ("none", "Raid", "Arena", ...)
- `GRIPEMS.API:GetSetting(key)` -> value or nil. Allowlist: `uiLayout` (string|nil), `debug` (boolean). For any other setting, listen to `SETTING_CHANGED`.
- `GRIPEMS.API:GetRegisteredPlugins()` -> array of `{ name, version, loaded, sequenceCount }`

### Tier 3 - UI and layout (`GRIPEMS.API.UI`)

- `:RegisterLayoutProvider(id, provider)` -> ok
- `:SetActiveLayoutProvider(id)` -> ok. Persists `uiLayout`; call only when the user opts in, not on load.
- `:GetActiveLayoutProvider()` -> id string
- `:GetHost(name)` -> frame or nil. Hosts: `navHost, listHost, metadataHost, editorHost, configHost, globalViewHost, iconFooterHost`
- `:MountPanel(panelId, host)` -> ok. Content panels: `sequenceList, editor, variables, conditions, macros, source`. `preview` goes through the Preview facade instead. `options, import, export, about` are dialogs and ignore the host. `vehiclePet, metadata` are reserved and return false.
- `:SetClassicChrome(enabled)` -> ok. `false` hides the default two-panel chrome so yours shows.
- `:RegisterView(id, def)` -> ok. `def = { id, name }`
- `:SetActiveView(id)` -> ok. Fires `GEMS_UI_NAV_CHANGED`.
- `:GetActiveView()` -> id or nil

Layout provider table. EMS calls the callbacks as plain functions (no `self`):

```lua
local provider = {
    id = "acme_modern",          -- must equal the id you register under
    name = "Acme Modern",
    OnRegister      = function(self) end,
    OnInitMainFrame = function(mainFrame, hosts) end,  -- before panels
    OnInitPanels    = function(mainFrame, hosts) end,  -- build chrome into hosts here
    OnApplyLayout   = function(context) end,           -- reposition on a layout pass
    OnMinimize      = function(mainFrame) end,
    OnRestore       = function(mainFrame) end,
}
```

SAFETY: hosts are plain, non-secure, reparentable frames. Never place a secure frame or `SecureActionButtonTemplate` under a host; reparenting it taints the secure execution path. Keep any secure frames your plugin makes outside the hosts.

### Tier 3 - preview (`GRIPEMS.API.Preview`)

- `:GetMode()` -> "icons" | "text" | "compiled"
- `:SetMode(mode)` -> ok (one of the three modes)
- `:Update(version)` -> true (the `version` arg is optional/advisory)
- `:Hide()` -> nothing
- `:MountSidebar(host)` -> ok
- `:MountIconFooter(host)` -> ok

### Tier 4 - registries

- `GRIPEMS.API:RegisterVariableProvider(id, spec)` -> ok
    - `spec = { id, name, Resolve = function(self, varName) ... end, OnRegister? }`
    - `Resolve` returns a plain non-secret scalar for names it owns, `nil` otherwise. Runs at compile time; keep it pure and cheap.
- `GRIPEMS.API:RegisterCondition(id, spec)` -> ok
    - `spec = { id, name, Evaluate = function(self) ... end, OnRegister? }` ; `Evaluate` returns a boolean.
- `GRIPEMS.API:EvaluateCondition(id)` -> clean boolean (users call this inside a variable body)
- `GRIPEMS.API:RegisterStepFunction(id, spec)` -> ok
    - `spec = { id, name, Expand = function(self, resolvedStepTexts) ... end, OnRegister? }` ; `Expand` returns an array of macrotext strings in execution order. Pure.
- `GRIPEMS.API:RegisterSequences(name, version, seqNames, seqTable)` -> ok (ships a static set; a user sequence wins on a name clash)

Reversible forms on the handle take the spec alone (id read from `spec.id`): `handle:RegisterVariableProvider(spec)`, `handle:RegisterCondition(spec)`, `handle:RegisterStepFunction(spec)`, `handle:RegisterLayoutProvider(provider)`.

### Tier 5 - authoring (handle methods only; owner-scoped; reverted on disable)

- `handle:CreateSequence(name, data)` -> ok (re-applying a name you own is a safe upsert)
- `handle:UpdateSequence(name, data)` -> ok
- `handle:DeleteSequence(name)` -> ok
- `handle:SelectSequence(name)` -> ok (UI; fires `GEMS_SEQUENCE_SELECTED`)
- `handle:OpenEditor(name)` -> ok (UI)
- `handle:RegisterSetting(def)` -> ok. `def = { key, type, name, desc, ... }` (e.g. `min, max, step` for a `"range"`)
- `handle:OverrideSetting(key, value)` -> ok
- `handle:RevertSetting(key)` -> ok
- `handle:RequestCVarProfile(profileKey)` -> ok (routed through the EMS CVar manager; no direct secure-CVar write)
- `handle:RevertCVarProfile()` -> ok
- `handle:RegisterImportProvider(spec)` -> ok. `spec = { id, name, Parse = function(self, text) ... end, Detect? }`
- `handle:RegisterExportProvider(spec)` -> ok. `spec = { id, name, Serialize = function(self, seq) ... end }`
- `handle:GetId()` -> your plugin id

Ownership is strict: a plugin may create, edit, or delete only sequences it owns. A user's sequence and another plugin's objects are rejected.

### Tier 5 - theme (`GRIPEMS.API.UI`)

- `:RegisterPanelFrame(frame, category, class)` -> makes your frame inherit the active EMS skin. Example: `("panel", "panel.acmeNav")`. Appearance only, no structural authority. Namespace `class` to your plugin.

### The lock list (no public write path, ever)

Rotation execution; secure buttons and the keybind matrix; authorship and signing; peer-to-peer transmission; direct secure-CVar writes; raw persistence; taint-laundering and secret values. The rule: if a call would change which spell fires, how a key binds, who authored a sequence, what is transmitted, or what is saved, it does not exist on the public API. You can read derived state (active version index, context, summaries); you cannot write any of these.

### Secret values

WoW 12.0 tags some values (a unit's health, for example) as secret so they can't cross into protected code. A variable provider that returns one has it rejected and the variable resolves to nothing; a condition that returns one evaluates to `false`. Return computed or non-secret values (counts, settings, group size, derived numbers).
