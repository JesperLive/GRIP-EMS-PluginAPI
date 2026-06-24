# Tier 5 — Theme

One method, on `GRIPEMS.API.UI`, that makes your plugin's frames inherit the active EMS skin so they match the rest of the window. It controls colours, fonts, textures, and borders — appearance only. It gives you no structural authority over EMS frames.

## `API.UI:RegisterPanelFrame(frame, category, class)`

```lua
API.UI:RegisterPanelFrame(myFrame, "panel", "panel.acmeNav")
```

Registers `frame` with the theme system. When the user's theme changes, EMS restyles registered frames, including yours. Call it once, after you create the frame.

| Parameter | Type | Meaning |
|---|---|---|
| `frame` | frame | the frame to style |
| `category` | string | broad bucket, e.g. `"panel"` or `"overlay"` |
| `class` | string | a dotted style key, e.g. `"panel.acmeNav"` |

The method is nil-safe — if the theme system isn't present, the call does nothing rather than erroring. Always pass a `class`; registering without one is flagged as a mistake.

Pick a `class` namespaced to your plugin (`panel.acme*`) so you're styling your own frames against a known bucket rather than colliding with EMS's internal class keys. The `category` is the coarse grouping (`panel` for windows and sub-panels, `overlay` for HUD-style elements).

## When to use it

Use it for the chrome your [layout provider](ui-layout.md) builds into the host frames, so a 3-column layout looks like part of EMS instead of a bolted-on window. Theme registration is appearance only — it never changes which spell fires, how the frame behaves, or anything on the [lock list](../reference/lock-list.md).
