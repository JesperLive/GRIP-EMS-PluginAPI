# Guide: a layout provider

This is the big one — replacing the EMS window layout with your own. EMS gives you seven empty host frames on the main window and a slot to register a provider that positions content into them. The built-in "classic" provider draws the default two-panel window; yours can draw whatever you want.

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
