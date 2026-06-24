# Tier 3 — Preview

The preview facade lets a layout provider drive and relocate the sequence preview without reaching into the editor's internals. It lives on `GRIPEMS.API.Preview`.

The classic layout never calls this facade, so the stock preview behaves exactly as before. It's here for a provider that wants the preview mounted somewhere other than where classic puts it. Every method is nil-safe: if the editor isn't built yet (or at all, in a foreground-only context), the method returns cleanly rather than erroring.

## `API.Preview:GetMode()`

```lua
local mode = API.Preview:GetMode()  -- "icons" | "text" | "compiled"
```

Returns the current preview mode, defaulting to `"icons"` when nothing is stored.

## `API.Preview:SetMode(mode)`

```lua
local ok, reason = API.Preview:SetMode("compiled")
```

Sets the preview mode. `mode` must be one of `"icons"`, `"text"`, or `"compiled"` — anything else returns `false` plus a reason. On success it persists the setting, re-renders the live preview if the editor is built, and fires `GEMS_PREVIEW_MODE_CHANGED` with the new mode. If no settings writer is available (a headless context), it returns `false` and does not fire the event.

## `API.Preview:Update(version)`

```lua
API.Preview:Update()
```

Re-renders the live preview and fires `GEMS_PREVIEW_UPDATE`. Always returns `true`. The `version` argument is accepted for forward compatibility but is currently advisory — classic derives the version from the selected sequence internally, so you can omit it.

## `API.Preview:Hide()`

```lua
API.Preview:Hide()
```

Hides the preview frame. A no-op when the editor isn't built. Returns nothing.

## `API.Preview:MountSidebar(host)`

```lua
local ok, reason = API.Preview:MountSidebar(API.UI:GetHost("configHost"))
```

Reparents the preview frame into one of your host frames and pins it to fill that host. `host` must be a frame table, or you get `false` plus a reason. EMS records your intended host even if the preview frame isn't built yet, so a later build can pick it up. Returns `false` with a reason when the editor or preview frame isn't available, or if the reparent fails.

## `API.Preview:MountIconFooter(host)`

```lua
local ok, reason = API.Preview:MountIconFooter(API.UI:GetHost("iconFooterHost"))
```

Reparents the preview icon strip into a host and pins it to fill it. Same return contract as `MountSidebar`.

!!! note "Sidebar and footer share a frame today"
    The icon strip currently lives inside the preview frame, so a true sidebar/footer split is a later increment. For now `MountIconFooter` relocates the icon scroll specifically, while `MountSidebar` relocates the whole preview frame. Mount the one that matches where you want the content; don't assume they're fully independent yet.

## Mounting from a provider

Call the mount methods from your layout provider's `OnInitPanels` or `OnApplyLayout`, after the hosts exist. A typical modern provider mounts the preview into its config column and re-drives `Update` when the selected sequence changes:

```lua
OnApplyLayout = function(context)
    local API = GRIPEMS.API
    API.Preview:MountSidebar(API.UI:GetHost("configHost"))
    API.Preview:Update()
end,
```
