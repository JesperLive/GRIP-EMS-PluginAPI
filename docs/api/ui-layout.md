# Tier 3 — UI and layout

Replacing the EMS window with a layout of your own takes four pieces, all on `GRIPEMS.API.UI`:

- a **layout provider** that positions EMS's host frames and owns the chrome,
- **`MountPanel`** to pull EMS's built-in panels — the sequence list, the editor, and the rest — into those hosts,
- **`SetClassicChrome(false)`** to hide the default two-panel chrome so yours shows instead,
- **`RegisterView` / `SetActiveView`** for navigation between screens.

A provider on its own gets you seven empty host frames and nothing to put in them. That was the limit of the first version of this API, and it's why a real reskin used to mean editing EMS's source. The panel-mount, chrome, and view methods close that gap: you position the hosts, mount the built-in content into them, hide the classic chrome, and drive your own nav.

EMS keeps its built-in `"classic"` provider — the two-panel window you see by default — and never removes it, so a user can always switch back.

One thing never moves: EMS's single in-window secure button (the Simplified Mode run button) stays parented to the window root, outside every host, so a layout can't taint it. Two panel ids, `vehiclePet` and `metadata`, are reserved with nothing to mount yet. Everything else is yours to place.

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

## Mount a built-in panel

`API.UI:MountPanel(panelId, host)` pulls one of EMS's built-in panels out of the classic chrome and into a host you control. This is what fills your layout with EMS's real content instead of leaving you to rebuild the sequence list and editor yourself.

```lua
local ok, reason = API.UI:MountPanel("editor", API.UI:GetHost("editorHost"))
```

Content panels reparent their content root into the host and pin it to fill. The mountable content panels:

| Panel id | What it is |
|---|---|
| `sequenceList` | the sequence list |
| `editor` | the sequence editor body |
| `variables` | the variables panel |
| `conditions` | the conditions panel |
| `macros` | the macros panel |
| `source` | the raw source view |

A few ids behave differently:

- `preview` hands off to the [Preview facade](preview.md), the same as `API.Preview:MountSidebar(host)`.
- `options`, `import`, `export`, and `about` are dialog-class. They open their existing standalone window and ignore the `host` argument.
- `vehiclePet` and `metadata` are reserved — known ids, but no panel is built for them yet, so mounting one returns `false`.

Returns `true`, or `false` plus a reason for an unknown id, a reserved id, or a non-table host on a content panel.

!!! note "Mount order doesn't matter"
    If you call `MountPanel` before the panel has been built (it's lazy, like the window), EMS records your host as a pending mount and applies it the moment the panel comes up. So you can mount from `OnInitPanels` without checking whether a given panel exists yet.

Disable un-mounts every panel your plugin mounted, returning each to the parent it had before — part of the [reversibility](../concepts/reversibility.md) guarantee.

## Hide the classic chrome

`API.UI:SetClassicChrome(enabled)` shows or hides the default two-panel chrome — the left panel, the divider, the right panel, and the title bar — so your layout presents its own instead of sitting on top of EMS's.

```lua
API.UI:SetClassicChrome(false)  -- hide the classic chrome
API.UI:SetClassicChrome(true)   -- show it again
```

`false` hides; `true` (or `nil`) shows. The frames are only toggled, never reparented or destroyed, and their children hide and show with them. Returns `false` with a reason only when the window isn't built yet. If your plugin hid the chrome, disable shows it again for you.

## Views and navigation

Classic EMS has no nav region — it's one window with two panels. A modern layout usually wants named screens (Sequences, Editor, Variables, and so on) with a way to switch between them. Views are that: you register the screens your layout offers, then tell EMS which one is active.

### `API.UI:RegisterView(id, def)`

```lua
local ok, reason = API.UI:RegisterView("sequences", { id = "sequences", name = "Sequences" })
```

Registers a named view. `def` needs an `id` that matches the registry id and a `name`. A duplicate id is rejected. Classic registers no views; the registry is empty until your provider fills it.

### `API.UI:SetActiveView(id)`

```lua
API.UI:SetActiveView("sequences")
```

Makes `id` the active view and fires `GEMS_UI_NAV_CHANGED` with the id, so the rest of your UI (and any listener) can react. Rejects an unknown id. The active view is in-memory only — your provider rebuilds it each load, so it isn't persisted.

### `API.UI:GetActiveView()`

```lua
local id = API.UI:GetActiveView()  -- nil under classic (no active view)
```

Returns the active view id, or `nil` when none is set, which is the classic default.

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
