# Event catalog

These are the events you can subscribe to with [`API:On`](../api/events.md). `On` rejects any name not on this list. Your handler receives the payload arguments shown — the event name is not passed — and any table argument is a deep-copied, read-only snapshot.

The **Fires** column matters: most events are emitted by EMS today; three UI events are part of the contract and accepted by `On`, but the in-core classic UI does not emit them yet. They're reserved for a layout provider or a later EMS UI to fire. Subscribing to a reserved event is safe and forward-compatible — you just won't get callbacks from it under the stock UI.

## Sequence and plugin lifecycle

| Event | Payload | Fires | Meaning |
|---|---|---|---|
| `SEQUENCE_CREATED` | `(name, data)` | yes | a sequence was created; `data` is a read-only copy of its sequence table |
| `SEQUENCE_DELETED` | `(name)` | yes | a sequence was removed |
| `SEQUENCE_IMPORTED` | `(results)` | yes | an import finished; `results` is a table summarizing what was imported |
| `SEQUENCE_STEP_ADVANCED` | `(seqName, step, numSteps)` | yes | a sequence advanced a step during execution |
| `SETTING_CHANGED` | `(key, value)` | yes | a setting changed; fires for every changed key/value |
| `PLUGIN_REGISTERED` | `(name, version)` | yes | a plugin registered through the sequence registry |
| `PLUGIN_SEQUENCES_LOADED` | none | yes | plugin sequences finished loading into the engine |

For `SEQUENCE_CREATED`, prefer [`GetSequenceInfo(name)`](../api/data.md) for documented per-field metadata rather than reading the raw `data` copy.

## UI and preview

| Event | Payload | Fires | Meaning |
|---|---|---|---|
| `GEMS_UI_READY` | none | yes | the window and its host frames are built and initialized |
| `GEMS_UI_LAYOUT_APPLY` | none | yes | a layout pass ran (after `OnApplyLayout`) |
| `GEMS_PREVIEW_MODE_CHANGED` | `(mode)` | yes | preview mode changed to `"icons"`, `"text"`, or `"compiled"` |
| `GEMS_PREVIEW_UPDATE` | none | yes | the preview re-rendered |
| `GEMS_UI_NAV_CHANGED` | reserved | no | reserved for a provider to signal a nav change |
| `GEMS_EDITOR_TAB_CHANGED` | reserved | no | reserved for a provider to signal an editor tab change |
| `GEMS_SEQUENCE_SELECTED` | reserved | no | reserved for a provider to signal a selection change |

`GEMS_UI_READY` is the signal to do your UI setup — host frames don't exist before it.

## Not on the public bus

EMS fires other events internally (context changes, keybind changes, loadout changes, and more), but they're not part of the public contract and `On` won't accept them. For content context, read it directly with [`GetCurrentContext()`](../api/data.md). If you need an internal signal exposed as a public event, [open an issue](https://github.com/JesperLive/GRIP-EMS-PluginAPI/issues) — that's how the catalog grows.
