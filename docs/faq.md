# FAQ

**Can my plugin break EMS?**
Not through the API. Every method either reads state or registers a contribution EMS validates and owns, and everything you hand EMS to call runs inside `pcall`. A bug in your plugin disables your feature and logs the error against your id; EMS keeps running. You can still break things by reaching into `_G.GRIPEMS` — so don't.

**When does `GRIPEMS.API` exist?**
After EMS loads. With `## Dependencies: GRIP-EMS` in your TOC, EMS loads first, so it exists by the time your files run. Do your registration from `PLAYER_LOGIN` anyway — it's the conventional ready point — and use `GEMS_UI_READY` for UI work.

**Do I need EMS installed at runtime?**
Yes. Plugins extend EMS; they don't run without it. The hard dependency means WoW won't even load your plugin if EMS is missing or disabled.

**My variable provider returns nothing. Why?**
Two common causes. Either you returned something that isn't a plain scalar (a table or function), or you returned a 12.0 secret-tagged value — a player's health, for instance, looks like a number but is secret. EMS screens both out so nothing taint-sensitive reaches macrotext. Return a non-secret string, number, or boolean. Turn on EMS debug to see the rejection log.

**Why can't I subscribe to context or keybind changes?**
Those events aren't on the public bus — only the names in the [event catalog](reference/event-catalog.md) are. For content context, read it with `GetCurrentContext()`. If you need an internal signal exposed publicly, open an issue.

**Three UI events never fire for me.**
`GEMS_UI_NAV_CHANGED`, `GEMS_EDITOR_TAB_CHANGED`, and `GEMS_SEQUENCE_SELECTED` are reserved — accepted by `On`, but the stock UI doesn't emit them yet. They're there for a layout provider to fire. Subscribing is safe and forward-compatible; just don't wait on them under the default UI.

**Can I change how a rotation executes, or how a key binds?**
No. Those are on the [lock list](reference/lock-list.md) and have no public write path. You can read derived state (the active version, the context, a sequence summary) and react to events, but you can't reach into execution, binding, identity, transmission, secure CVars, or persistence.

**My layout provider doesn't take over when the window first opens.**
EMS resolves the active provider when it builds the window — the first time the user opens it. Register at `PLAYER_LOGIN` and persist the user's opt-in with `SetActiveLayoutProvider` (it writes the `uiLayout` setting), so the next build resolves your provider. If you register after the window's already built, apply on the next `GEMS_UI_LAYOUT_APPLY` or wait for `/reload`. See the [layout guide](guides/layout-provider.md).

**Where do my errors show up?**
In the EMS debug log, not a `lua error` popup. Develop with debug on. `GetSetting("debug")` tells you whether it's enabled.

**How does versioning work? Should I check `EMS_VERSION`?**
Gate on `API_VERSION` through `RequireVersion(n)`, not on `EMS_VERSION`. `API_VERSION` tracks the API contract and only bumps on a breaking change; `EMS_VERSION` is the addon release string, useful for logs and bug reports but not for feature gating.

**Is the API stable?**
Within an `API_VERSION`, yes — that's the contract. Adding methods doesn't bump the version; a breaking change does. Build against the public surface and EMS updates won't silently break you. Build against `_G.GRIPEMS` internals and they will.
