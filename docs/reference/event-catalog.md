# Event catalog

These are the events you can subscribe to with [`API:On`](../api/events.md). `On` rejects any name not on this list. Your handler receives the payload arguments shown — the event name is not passed — and any table argument is a deep-copied, read-only snapshot.

The **Fires** column tells you what emits today. Everything here fires from a real site in EMS, with one wrinkle: `GEMS_UI_NAV_CHANGED` only fires when a layout provider drives `SetActiveView`, since classic has no nav region of its own.

## Sequence and plugin lifecycle

| Event | Payload | Fires | Meaning |
|---|---|---|---|
| `SEQUENCE_CREATED` | `(name, data)` | yes | EMS registered a sequence under this name, which a rebuild also does (see [below](#when-sequence-events-fire)); `data` is a read-only copy of its sequence table |
| `SEQUENCE_DELETED` | `(name)` | yes | EMS unregistered a sequence under this name, which a rebuild also does (see [below](#when-sequence-events-fire)) |
| `SEQUENCE_IMPORTED` | `(results)` | yes | an import finished; `results` is a table summarizing what was imported |
| `SEQUENCE_STEP_ADVANCED` | `(seqName, step, numSteps)` | yes | a sequence advanced a step during execution |
| `SETTING_CHANGED` | `(key, value)` | yes | a setting changed; fires for every changed key/value |
| `PLUGIN_REGISTERED` | `(name, version)` | yes | a plugin registered through the sequence registry |
| `PLUGIN_SEQUENCES_LOADED` | none | yes | plugin sequences finished loading into the engine |

For `SEQUENCE_CREATED`, prefer [`GetSequenceInfo(name)`](../api/data.md) for documented per-field metadata rather than reading the raw `data` copy.

### When sequence events fire

`SEQUENCE_CREATED` fires when a sequence is created, imported or duplicated, for the new name of a renamed sequence, and when a disabled sequence is enabled again. It also fires once for each saved sequence EMS restores after login. The restore runs at the first `PLAYER_ENTERING_WORLD`, after `PLAYER_LOGIN`, so a handler you subscribe from `PLAYER_LOGIN` hears every one of them.

`SEQUENCE_DELETED` fires when a sequence is deleted, and for the old name of a renamed one.

A rebuild fires both for a sequence that stays: `SEQUENCE_DELETED` and then `SEQUENCE_CREATED`, under the same name. Adding or removing a modifier variant rebuilds the sequence, and so does calling `handle:CreateSequence` again for a name your plugin owns. A save or a version pin set or cleared can rebuild it too, and then fires `SEQUENCE_UPDATED` after the pair. So a `SEQUENCE_DELETED` that a `SEQUENCE_CREATED` for the same name follows is the same sequence, still there.

Out of combat each of these arrives before the call that caused it returns.

## Core change signals

These fire from the engine on a real change. They were internal in v1; v2 makes them public.

| Event | Payload | Fires | Meaning |
|---|---|---|---|
| `SEQUENCE_UPDATED` | `(name, data)` | yes | a sequence was saved, had a version pin set or cleared, was disabled, or was rewritten by a variable rename or by Auto-refresh macro-reference steps; `data` is a read-only copy of its table |
| `KEYBIND_CHANGED` | `(seqName, key)` | yes | a sequence keybind changed; both args may be `nil` on a bulk or clear change |
| `CONTEXT_CHANGED` | `(newContext, oldContext)` | yes | the detected content context changed |
| `LOADOUT_CHANGED` | `(newID, newName, oldID, oldName)` | yes | the active talent loadout changed |

## UI and preview

| Event | Payload | Fires | Meaning |
|---|---|---|---|
| `GEMS_UI_READY` | none | yes | the window and its host frames are built and initialized |
| `GEMS_UI_LAYOUT_APPLY` | none | yes | a layout pass ran (after `OnApplyLayout`) |
| `GEMS_PREVIEW_MODE_CHANGED` | `(mode)` | yes | preview mode changed to `"icons"`, `"text"`, or `"compiled"` |
| `GEMS_PREVIEW_UPDATE` | none | yes | the preview re-rendered |
| `GEMS_UI_NAV_CHANGED` | `(viewId)` | yes | fires from `SetActiveView`; only a layout provider driving its own nav emits it |
| `GEMS_EDITOR_TAB_CHANGED` | `(tabName)` | yes | the editor switched sub-tabs |
| `GEMS_SEQUENCE_SELECTED` | `(name)` | yes | a sequence was selected in the list |

`GEMS_UI_READY` is the signal to do your UI setup — host frames don't exist before it.

## Not on the public bus

EMS fires other events internally that aren't part of the public contract — `On` won't accept them. The catalog above is the full public set. If you need an internal signal exposed publicly, [open an issue](https://github.com/JesperLive/GRIP-EMS-PluginAPI/issues); the core change signals above were internal until they were added this way.
