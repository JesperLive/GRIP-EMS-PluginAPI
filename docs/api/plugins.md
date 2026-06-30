# Plugins and the handle

Tier 0 ends here. After the version handshake you register your plugin and get back a *handle* — a frozen table that owns everything your plugin contributes. Register through the handle and EMS can undo all of it when the plugin is disabled. That reversal is the main thing the handle adds; the [reversibility](../concepts/reversibility.md) page covers what it guarantees.

You don't have to use a handle. The bare `GRIPEMS.API:Register*` calls still work and still validate. But a contribution made that way is anonymous — EMS has no owner to attribute it to, so it isn't tracked and isn't reverted. If your plugin can be turned off, register through the handle.

## `API:RegisterPlugin(id, meta)`

```lua
local handle, reason = GRIPEMS.API:RegisterPlugin("acme_overhaul", {
    name = "Acme Overhaul",
    version = "1.0.0",
    OnEnable = function(h) MyPlugin_Build(h) end,
    OnDisable = function(h) MyPlugin_Teardown() end,
})
if not handle then
    print("RegisterPlugin failed:", reason)
    return
end
```

`id` is the namespace for everything the plugin contributes — every sequence, view, setting, and registry entry is owned by it. It must be a non-empty string. A duplicate id is rejected (it never overwrites a registered plugin), so a second call with the same id returns `nil` plus a reason.

`meta` is optional. Its fields:

| Field | Type | Meaning |
|---|---|---|
| `name` | string | human label, shown in the EMS plugins list |
| `version` | string | your plugin version |
| `OnEnable` | function | `OnEnable(handle)` — runs when the plugin is enabled |
| `OnDisable` | function | `OnDisable(handle)` — runs when the plugin is disabled |

The return is a frozen handle, or `nil` plus a reason. The handle is a read-only proxy, the same shape as `GRIPEMS.API`: you call its methods, you can't add to it or rewrite them, and it carries your id internally where no caller can read or change it.

## The handle

`handle:GetId()` returns your plugin id. Every other method registers or authors something owned by the plugin:

- registry contributions — `RegisterVariableProvider`, `RegisterCondition`, `RegisterStepFunction`, `RegisterLayoutProvider`, `RegisterImportProvider`, `RegisterExportProvider` (the [registries](registries.md) contracts, owned)
- UI — `MountPanel`, `SetClassicChrome`, `RegisterView`, `SetActiveView` (see [UI and layout](ui-layout.md))
- authoring — `CreateSequence`, `UpdateSequence`, `DeleteSequence`, `SelectSequence`, `OpenEditor`, `RegisterSetting`, `OverrideSetting`, `RevertSetting`, `RequestCVarProfile`, `RevertCVarProfile`, `EnsureSequenceMacro`, `RegisterSlashCommand` (the [authoring](authoring.md) tier)

The handle methods take the same specs as their `GRIPEMS.API` counterparts, with one difference: the handle's `RegisterVariableProvider(spec)` takes the spec alone and reads the id from `spec.id`, where the bare `GRIPEMS.API:RegisterVariableProvider(id, spec)` takes both. The handle already knows who owns the contribution.

## Enable and disable

EMS owns the lifecycle. The user turns your plugin on or off in EMS's settings; there's no public method to disable a plugin from code, and `RegisterPlugin` is the only lifecycle call you make.

Enabled state persists per plugin. EMS records whether your plugin is on in its saved variables, so a plugin the user disabled last session stays disabled across a reload.

`OnEnable(handle)` is where you do your work. It runs at load if the plugin was enabled last session, and when the user enables a plugin that was off. Put your registry registrations and authoring calls here. The in-memory contributions (providers, conditions, views, panels) are cleared on disable, so `OnEnable` is what re-establishes them on the next load.

`OnDisable(handle)` runs when the user disables the plugin. EMS replays the teardown journal *first* — reverting every contribution back to the default-installed state — then calls `OnDisable` so you can drop your own references and frames.

`RegisterPlugin` returns the handle even when the plugin is persisted-disabled, so you can hold it and the user can enable later. In that state `OnEnable` has not run and your contributions are not live.

!!! note "`PLUGIN_ENABLED` and `PLUGIN_DISABLED` are not public events"
    EMS fires these internally as the lifecycle moves, but they aren't in the [event catalog](../reference/event-catalog.md) and `On` won't accept them. Use your own `OnEnable` / `OnDisable` callbacks — they're the supported signal, and they hand you the handle.

## What disable reverts

Everything owned by the plugin id: its registry entries, the sequences it authored, its setting overrides, any CVar profile it requested, its views and mounted panels, and the classic chrome if it hid it. After disable, EMS is back to default-installed. The [reversibility](../concepts/reversibility.md) page is the full account.
