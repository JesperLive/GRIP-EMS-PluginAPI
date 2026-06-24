# Tier 3 — UI and layout

This is how a plugin replaces the EMS window layout with its own. EMS keeps a built-in "classic" layout provider (the two-panel window you see by default). You register your own provider, the user opts into it, and your provider positions the content into a set of host frames EMS creates for you.

These methods live on `GRIPEMS.API.UI`.

## Host frames

The main window (`GRIPEMS_MainFrame`) carries seven plain, empty, hidden host frames. The classic layout ignores them and drives its own two panels; your provider positions and shows the ones it needs and mounts content into them.

| Host | Intended for |
|---|---|
| `navHost` | a navigation rail / sidebar |
| `listHost` | the sequence list |
| `metadataHost` | per-sequence metadata |
| `editorHost` | the editor body |
| `configHost` | a config sidebar |
| `globalViewHost` | global / about-style views |
| `iconFooterHost` | the preview icon strip / footer |

These are intended roles, not enforcement — a host is just a `Frame`. Use the ones that fit your layout.

!!! warning "Hosts are non-secure — keep them that way"
    Host frames are plain `Frame` objects, and a provider may reparent them, so **no secure frame or secure button may ever live under a host.** EMS keeps its one in-window secure button (the Simplified Mode run button) on the window root, outside every host, exactly so a layout plugin can't taint it. If you create secure templates in your plugin, parent them outside the hosts. This is the single most important safety rule on this tier.

### `API.UI:GetHost(name)`

```lua
local editor = API.UI:GetHost("editorHost")
```

Returns the named host frame, or `nil` if the window hasn't been built yet (it's lazy-created the first time the user opens EMS). Resolve hosts inside your provider callbacks — by the time `OnInitPanels` runs, all seven exist.

## The layout provider

A provider is a table with an `id`, a `name`, and a set of optional lifecycle callbacks. EMS calls the callbacks as plain functions with the arguments shown — they are not method-style, so don't expect `self`.

```lua
local provider = {
    id = "acme_modern",          -- must equal the id you register under
    name = "Acme Modern",        -- shown to the user

    OnRegister = function(self) end,                 -- called once, at register time
    OnInitMainFrame = function(mainFrame, hosts) end, -- before panels are built
    OnInitPanels = function(mainFrame, hosts)         -- build your chrome into hosts
        local nav = hosts.navHost
        nav:ClearAllPoints()
        nav:SetPoint("TOPLEFT", mainFrame, "TOPLEFT", 0, -40)
        nav:SetPoint("BOTTOMLEFT", mainFrame, "BOTTOMLEFT", 0, 0)
        nav:SetWidth(160)
        nav:Show()
        -- ... build and parent your widgets into nav, hosts.editorHost, etc.
    end,
    OnApplyLayout = function(context) end,            -- reposition on a layout pass
    OnMinimize = function(mainFrame) end,             -- collapse to title bar
    OnRestore = function(mainFrame) end,              -- expand again
}
```

Every callback is optional, but each must be a function if present. The `id` and `name` are required and must be strings, and the `id` field inside the table must equal the id you register under.

### `API.UI:RegisterLayoutProvider(id, provider)`

```lua
local ok, reason = API.UI:RegisterLayoutProvider("acme_modern", provider)
```

Validates the provider against the contract above, stores it under `id`, and runs its `OnRegister`. Returns `true`, or `false` plus a reason — a malformed contract, a non-function callback, an `id` mismatch, or a duplicate id (it never overwrites an existing provider, including the built-in `"classic"`).

### `API.UI:SetActiveLayoutProvider(id)`

```lua
local ok, reason = API.UI:SetActiveLayoutProvider("acme_modern")
```

Makes `id` the active provider and persists it to the `uiLayout` setting. Returns `false` plus a reason for an unknown id. Call this when the user opts into your layout — not automatically on load, or you'll override their choice.

### `API.UI:GetActiveLayoutProvider()`

```lua
local id = API.UI:GetActiveLayoutProvider()  -- e.g. "classic"
```

Returns the active provider id. Falls back to the stored `uiLayout` setting, then to `"classic"`.

## Lifecycle and dispatch

The window is lazy-created the first time the user opens it. On that first open, EMS:

1. builds `GRIPEMS_MainFrame` and the seven hosts (empty, hidden),
2. resolves the active provider (default `"classic"`),
3. calls `OnInitMainFrame(mainFrame, hosts)`, then `OnInitPanels(mainFrame, hosts)`,
4. fires `GEMS_UI_READY`,
5. builds a read-only `context` and calls `OnApplyLayout(context)`, then fires `GEMS_UI_LAYOUT_APPLY`.

The minimize button routes through your `OnMinimize` / `OnRestore`. If your `OnInitPanels` throws, EMS logs it and falls back to the classic layout, so a broken provider degrades to the stock UI rather than an empty window.

### The `context` passed to `OnApplyLayout`

A read-only snapshot — scalars and `IsShown` booleans, no live frame handles:

| Field | Type | Meaning |
|---|---|---|
| `navId` | string \| nil | active nav region (`nil` under classic) |
| `editorTab` | any \| nil | the editor's active tab |
| `selectedSequence` | string \| nil | currently selected sequence |
| `panelVisibility.left` | boolean | is the left panel shown |
| `panelVisibility.right` | boolean | is the right panel shown |
| `previewMode` | string \| nil | current preview mode |
| `frameWidth` / `frameHeight` | number \| nil | current window size |

## Taking over the first paint (load order)

The active provider is resolved when the window is built, which is the first time the user opens it. So to own the first paint, your provider must be registered **and** active before that happens:

- Register at `PLAYER_LOGIN` (EMS has loaded; the window usually hasn't been opened yet).
- Persist the user's opt-in with `SetActiveLayoutProvider` — because it writes `uiLayout`, the next time the window builds, EMS resolves your provider on its own.

If you register after the window already exists this session, EMS won't rebuild it underneath the user. Apply your layout on the next `GEMS_UI_LAYOUT_APPLY`, or let it take effect when they reopen or `/reload`.

## Theme integration

`API.UI:RegisterPanelFrame(frame, category, class)` also lives on this sub-table. It's the Tier 5 hook for making your frames inherit the active EMS skin — see [Tier 5 - Theme](theme.md).
