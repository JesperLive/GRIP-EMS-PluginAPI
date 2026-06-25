# Guide: a layout provider

This is the big one — replacing the EMS window with a layout of your own. EMS gives you seven empty host frames on the main window and a slot to register a provider that positions them. A provider alone just gets you empty frames, though: a real reskin also pulls EMS's built-in panels (the sequence list, the editor) into your hosts, hides the classic chrome, and drives its own nav. The built-in "classic" provider draws the default two-panel window and never goes away, so the user can always switch back.

Read the [Tier 3 - UI and layout](../api/ui-layout.md) reference alongside this; the guide is the walkthrough, the reference is the contract.

## The shape of a provider

A provider is a table with an `id`, a `name`, and optional lifecycle callbacks. EMS calls the callbacks as plain functions with the arguments shown — not method-style, so there's no `self`.

```lua
local provider = {
    id = "acme_modern",
    name = "Acme Modern",

    OnInitPanels = function(mainFrame, hosts)
        -- Build and parent your chrome into the hosts here.
    end,
    OnApplyLayout = function(context)
        -- Reposition on a layout pass (also when the window resizes).
    end,
    OnMinimize = function(mainFrame) end,
    OnRestore = function(mainFrame) end,
}
```

Every callback is optional but must be a function if present. There's also `OnRegister(self)` (runs once at registration) and `OnInitMainFrame(mainFrame, hosts)` (runs before `OnInitPanels`).

## Position content into hosts

The seven hosts are plain frames, created empty and hidden. In `OnInitPanels`, position the ones you need, show them, and parent your widgets into them:

```lua
OnInitPanels = function(mainFrame, hosts)
    local nav = hosts.navHost
    nav:ClearAllPoints()
    nav:SetPoint("TOPLEFT", mainFrame, "TOPLEFT", 0, -40)
    nav:SetPoint("BOTTOMLEFT", mainFrame, "BOTTOMLEFT", 0, 0)
    nav:SetWidth(160)
    nav:Show()
    -- build your nav buttons, parent them to nav ...
end,
```

The host names and their intended roles are in the [reference](../api/ui-layout.md#host-frames): `navHost`, `listHost`, `metadataHost`, `editorHost`, `configHost`, `globalViewHost`, `iconFooterHost`.

## Pull in EMS's panels

Your own widgets are half of it. The other half is EMS's real content — the sequence list, the editor, the variables and conditions panels. `MountPanel` reparents a built-in panel into one of your hosts so you don't rebuild it:

```lua
OnInitPanels = function(mainFrame, hosts)
    local API = GRIPEMS.API
    API.UI:SetClassicChrome(false)                      -- hide the two-panel chrome
    API.UI:MountPanel("sequenceList", hosts.listHost)   -- EMS's list, in your host
    API.UI:MountPanel("editor", hosts.editorHost)       -- EMS's editor, in your host
end,
```

`SetClassicChrome(false)` hides the classic left panel, divider, right panel, and title bar so yours shows instead. `MountPanel` takes a content panel id — `sequenceList`, `editor`, `variables`, `conditions`, `macros`, or `source` — and pins it to fill the host. The dialog panels (`options`, `import`, `export`, `about`) open their own window; `preview` goes through the [Preview facade](../api/preview.md); `vehiclePet` and `metadata` are reserved. The full list and rules are in the [reference](../api/ui-layout.md#mount-a-built-in-panel).

For named screens and a nav rail, register views and switch between them:

```lua
API.UI:RegisterView("sequences", { id = "sequences", name = "Sequences" })
API.UI:RegisterView("editor", { id = "editor", name = "Editor" })
API.UI:SetActiveView("sequences")   -- fires GEMS_UI_NAV_CHANGED
```

All of it is reversible. When the user disables your plugin, EMS un-mounts the panels back where they were, shows the classic chrome again, and drops your views — see [reversibility](../concepts/reversibility.md).

## The one hard safety rule

!!! danger "Never put a secure frame under a host"
    Hosts are non-secure and a provider may reparent them. If a `SecureActionButtonTemplate` (or any secure frame) ends up under a host, reparenting it taints the secure execution path. Keep any secure frames your plugin creates outside the hosts. EMS already keeps its own secure button off the hosts for exactly this reason.

## Register and let the user opt in

```lua
GRIPEMS.API.UI:RegisterLayoutProvider("acme_modern", provider)
-- when the user chooses your layout (a setting, a button -- not automatically):
GRIPEMS.API.UI:SetActiveLayoutProvider("acme_modern")
```

`SetActiveLayoutProvider` persists the choice to the `uiLayout` setting. Don't call it on load — that would override the user's choice. Wait for them to pick your layout.

## Take over the first paint (load order)

EMS resolves the active provider when it builds the window, which is the first time the user opens it. So to own the first paint, be registered and active before that:

- Register at `PLAYER_LOGIN`.
- Because `SetActiveLayoutProvider` writes `uiLayout`, once the user has opted in, the next time the window builds EMS resolves your provider on its own.

If the window is already open when you register, EMS won't rebuild it under the user. Apply on the next `GEMS_UI_LAYOUT_APPLY`, or let it take effect on `/reload`.

## Mount the preview and match the theme

Use the [Preview facade](../api/preview.md) to put the rotation preview where your layout wants it, typically from `OnApplyLayout`:

```lua
OnApplyLayout = function(context)
    local API = GRIPEMS.API
    API.Preview:MountSidebar(API.UI:GetHost("configHost"))
    API.Preview:Update()
end,
```

Register your frames with the theme so they match the active skin:

```lua
GRIPEMS.API.UI:RegisterPanelFrame(myNavFrame, "panel", "panel.acmeNav")
```

## Failure is contained

If your `OnInitPanels` throws, EMS logs it and falls back to the classic layout, so a bug gives the user the stock window rather than an empty one. Develop with debug on so you see the fallback reason.
