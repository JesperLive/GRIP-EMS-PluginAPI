# Tier 5 — Authoring

The write tier. Everything here is a handle method — you call it on the [handle](plugins.md) `RegisterPlugin` gave you, never on `GRIPEMS.API` directly, because every write is owned by your plugin id and reverted when the plugin is disabled.

The ownership rule is strict: a plugin may create, change, and delete only the objects it owns. A user's own sequence (no owner stamp) and another plugin's sequence are off-limits — the write methods reject them. You author your content; you can't reach the user's.

## Owned sequences

A plugin can create, edit, and delete its own sequences at runtime. Where `RegisterSequences` ships a fixed set at load, these are live objects the plugin owns: each one is stamped with the plugin id, stored in a plugin-namespaced bucket, and activated in the engine like any other sequence.

### `handle:CreateSequence(name, data)`

```lua
local ok, reason = handle:CreateSequence("Acme Burst", {
    -- sequence definition, EMS's own sequence shape
})
```

Creates and activates a sequence owned by your plugin. `name` must be a non-empty string and `data` a table. It refuses to clobber a name that already exists and isn't yours — a user sequence or another plugin's. On success EMS deep-copies the data (so you can't mutate execution after the fact), stamps the owner, and activates it. The activation fires `SEQUENCE_CREATED`, so this method doesn't fire it again.

Calling `CreateSequence` again with a name you already own re-applies the data — a safe upsert, not a duplicate.

### `handle:UpdateSequence(name, data)`

```lua
local ok, reason = handle:UpdateSequence("Acme Burst", newData)
```

Replaces the data of a sequence you own. The sequence must already exist and carry your owner stamp; an unknown name, a user sequence, or another plugin's is rejected. Fires `SEQUENCE_UPDATED` through the engine.

### `handle:DeleteSequence(name)`

```lua
local ok, reason = handle:DeleteSequence("Acme Burst")
```

Deactivates and removes a sequence you own, from the engine and from your bucket. Owner-checked the same way. Fires `SEQUENCE_DELETED`.

### `handle:SelectSequence(name)` and `handle:OpenEditor(name)`

```lua
handle:SelectSequence("Acme Burst")  -- select it in the list
handle:OpenEditor("Acme Burst")      -- load it into the editor
```

Drive the UI to a sequence. These are UI actions, not writes — they don't change the sequence, aren't owner-scoped, and aren't journaled. Both are nil-safe when the list or editor isn't built (a headless context). `SelectSequence` fires `GEMS_SEQUENCE_SELECTED`.

## Settings

A plugin can define its own settings and override existing ones. Overrides follow the [conflict policy](../concepts/reversibility.md#conflict-policy): the user's value is the base, the last-enabled plugin wins, and disable reverts.

### `handle:RegisterSetting(def)`

```lua
local ok, reason = handle:RegisterSetting({
    key = "acme_density",
    type = "range",
    name = "Acme row density",
    desc = "How tightly the Acme layout packs rows.",
    min = 1, max = 5, step = 1,
})
```

Registers a setting definition so the EMS settings panel shows it in the Plugins group. `def.key` must be a non-empty string, and the key can't already be registered. Registration doesn't change any value — it makes the key known to the panel and to `OverrideSetting`. The key is unregistered on disable.

### `handle:OverrideSetting(key, value)` and `handle:RevertSetting(key)`

```lua
handle:OverrideSetting("uiLayout", "acme_modern")
handle:RevertSetting("uiLayout")
```

`OverrideSetting` sets a value for a known key — either a built-in EMS setting or one some plugin registered. The first time any plugin overrides a key, EMS snapshots the pre-plugin value so it's never lost. Your value goes live (last-enabled wins) and routes through the normal setting path, so `SETTING_CHANGED` fires once. An unknown key is rejected.

`RevertSetting` drops your override of a key. The live value falls to the next plugin's override if one's left, otherwise back to the snapshot. Disable reverts every key you overrode automatically; call `RevertSetting` only when you want to drop one while staying enabled.

## CVar profiles

### `handle:RequestCVarProfile(profileKey)` and `handle:RevertCVarProfile()`

```lua
local ok, reason = handle:RequestCVarProfile("Acme Combat")
handle:RevertCVarProfile()
```

`RequestCVarProfile` applies a known CVar profile through the EMS CVar profile manager, the same path the built-in CVar dashboard uses. The manager captures each live CVar before changing it and is combat- and secure-aware, so no new secure-CVar write path is created here: a plugin requests a profile, it never writes a secure CVar directly. The profile id must resolve to a built-in or stored profile, or you get `false` plus a reason. EMS records which CVars the apply touched and the active profile that was live before.

`RevertCVarProfile` restores every CVar your request changed and puts the active profile back. Disable does this for you; call it explicitly only to revert while staying enabled.

## Import and export providers

### `handle:RegisterImportProvider(spec)` and `handle:RegisterExportProvider(spec)`

```lua
handle:RegisterImportProvider({
    id = "acme_fmt",
    name = "Acme format",
    Parse = function(self, text) --[[ return a sequence table ]] end,
    Detect = function(self, text) return text:sub(1, 5) == "ACME!" end,  -- optional
})

handle:RegisterExportProvider({
    id = "acme_fmt",
    name = "Acme format",
    Serialize = function(self, seq) --[[ return a string ]] end,
})
```

Add a format to the import or export pipeline. Your plugin supplies the parser or serializer; EMS owns the pipeline and calls yours. Both validate the spec, reject a duplicate id, and journal the registration so disable removes it. `Detect` is optional on an import provider — a quick check so EMS can route a pasted string to the right parser.

## Sequence macros

A sequence can have a real WoW macro on an action bar — a simplified, draggable stand-in for the rotation. Your plugin makes sure that macro exists, then picks it up or places it; the read side, [`GetSequenceMacroIndex`](data.md#apigetsequencemacroindexname), gives the slot without creating anything.

### `handle:EnsureSequenceMacro(name)`

```lua
local index, reason = handle:EnsureSequenceMacro("Acme Burst")
if index then
    PickupMacro(index)  -- drag onto a button, or place it
end
```

Creates the sequence's action-bar macro if it doesn't exist yet and returns its slot index. The sequence must be active. If EMS or the user already made a macro for it, you get that existing index back and EMS does *not* journal it — disable never deletes a macro you didn't cause. A macro your call created *is* journaled, so disabling your plugin deletes it. You get `false` plus a reason in combat, when the macro slot pool is full, or for an unknown sequence.

The macro is the supported way to put a sequence on a third-party bar button. It's capped at 255 characters and runs in the default environment, so it's a simplified version of the sequence, not the full engine — the [action-bar plugin guide](../guides/action-bar-plugin.md#the-honest-limit) covers that trade-off.

## Slash commands

### `handle:RegisterSlashCommand(sub, handler, helpText?)`

```lua
handle:RegisterSlashCommand("acme", function(args)
    print("acme ran with: " .. args)
end, "Acme controls")
```

Registers a subcommand under EMS's own `/gems`, so a user can type `/gems acme ...` and reach your handler. `sub` is a single token — letters, digits, and underscores, lowercased for you. `handler` is called as `handler(argString)` with whatever followed the subcommand (the empty string when nothing did), inside `pcall`, so a bug in it logs and is swallowed instead of breaking the dispatcher. `helpText` is optional and shows next to your subcommand under `/gems help`.

A name that's already a built-in `/gems` subcommand, or one another plugin took, is rejected with `false` plus a reason. The registration is journaled, so disabling your plugin removes the subcommand. This is only for living under `/gems` — a plugin can still register its own top-level `/acme` directly with WoW the usual way, no API needed.

## What's still locked

Authoring is a write tier, but a narrow one. You write your own objects through validated, owner-scoped calls. You still can't reach rotation execution, the secure keybind path, identity and signing, transmission, a direct secure-CVar write, or raw persistence — those stay on the [lock list](../reference/lock-list.md) for overhaul plugins exactly as for read-only ones. The boundary moved from "additive-only" to "additive, or an owned write that reverts," but it didn't open the locked systems.
