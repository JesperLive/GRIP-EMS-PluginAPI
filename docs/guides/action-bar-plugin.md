# Guide: action-bar plugins

A sequence lives behind a keybind. Some plugins want it on an action button too — assigned to an empty slot, draggable out of the EMS window, with button glow and a cooldown swipe that a plain macro can't draw. v3 adds three pieces that make this work through supported API instead of reaching into EMS internals: per-step spell data to draw chrome from, the sequence's own action-bar macro to put on a button, and a `/gems` subcommand for your plugin's controls.

This guide ties them together. Feature-detect each with `GetCapabilities` — the ids are `stepdata`, `macro`, and `slash` — and gate on `RequireVersion(3)` before you use any of them.

```lua
if not API:RequireVersion(3) then return end  -- this EMS predates the action-bar surface
```

## Put a sequence on a button

EMS already keeps a real WoW macro for a sequence. Make sure it exists, then pick it up — the player drops it on whatever slot they want:

```lua
local index, reason = handle:EnsureSequenceMacro("My Rotation")
if index then
    PickupMacro(index)
else
    print("no macro: " .. tostring(reason))
end
```

`EnsureSequenceMacro` is owner-scoped and reversible. A macro your plugin caused EMS to create is deleted when your plugin is disabled; a macro EMS or the user already had is handed back untouched and never deleted on your behalf. It returns `false` plus a reason in combat, when the macro slot pool is full, or for a sequence that isn't active.

To read the slot without creating anything, use [`GetSequenceMacroIndex`](../api/data.md#apigetsequencemacroindexname) — it returns `nil` when there's no macro yet.

## Draw the chrome

Glow and a cooldown swipe need to know which spell the current step casts. `GetSequenceSteps` gives you the active version's steps as plain public data:

```lua
local steps = API:GetSequenceSteps("My Rotation")
-- steps[i] = { index = i, spellID = ..., spellName = ..., icon = ... }
```

Then follow the live step with the `SEQUENCE_STEP_ADVANCED` event and ask WoW for the cooldown yourself:

```lua
API:On("SEQUENCE_STEP_ADVANCED", function(seqName, step, numSteps)
    if seqName ~= "My Rotation" then return end
    local s = steps[step]
    if s and s.spellID then
        local cd = C_Spell.GetSpellCooldown(s.spellID)
        -- drive your button's swipe and glow from cd and s.icon
    end
end)
```

Spell id, name, and icon are public — never secret-tagged the way a unit's health is — so nothing here risks taint. EMS resolves the ids through the same path the engine compiles from, so they match what the sequence actually fires.

## Add your controls under /gems

Rather than register a whole separate slash command, hang a subcommand off EMS's:

```lua
handle:RegisterSlashCommand("acme", function(args)
    if args == "bind" then
        local index = handle:EnsureSequenceMacro("My Rotation")
        if index then PickupMacro(index) end
    else
        print("usage: /gems acme bind")
    end
end, "Acme action-bar controls")
```

Now `/gems acme bind` runs your handler. It's journaled like everything else on the handle, so the subcommand disappears when your plugin is disabled, and a `helpText` puts a line under `/gems help`.

## The honest limit

A WoW macro is capped at 255 characters and runs in the default environment. EMS's generated macro is a *simplified* representation of a sequence: it can't carry variable resolution, runtime conditions, or advanced step-function ordering. For many sequences the macro is enough; for the complex ones, the button gets the macro's behavior while the keybind keeps the full engine.

That split is deliberate, and it's why one thing stays off-limits: setting a keybind from a plugin. Binding is taint-sensitive and is EMS's core promise, so it has no plugin write path — you read a sequence's keybind through `GetSequenceInfo`, you don't write it. And since the 11.0.2 macro-chaining restriction stops a third-party bar button from proxying into EMS's secure execution, the macro *is* the supported bar path, not a workaround on the way to one. The [lock list](../reference/lock-list.md) has the full boundary.

So: read the steps, draw your chrome, put the macro on a bar, and drive it from a `/gems` subcommand — and let the keybind stay the place the full rotation runs.
