# Reversibility

The hard rule behind the plugin API: **disabling a plugin undoes everything it did.** Whatever your plugin registered, authored, overrode, or mounted, EMS removes on disable and returns to its default-installed state. A user can try a full UI overhaul, turn it off, and get the stock addon back — no leftovers, no reload needed.

This is why the [handle](../api/plugins.md) matters. EMS can only revert what it can attribute to a plugin, and the handle is how it knows. A contribution made through the handle is owned and tracked; a bare `GRIPEMS.API:Register*` call is anonymous and stays.

## The teardown journal

Behind each plugin id, EMS keeps a journal: a record of every reversible thing the plugin has done. When the plugin is disabled, EMS walks the journal, undoes each entry, then clears it. The journal has five kinds of entry.

**Registry contributions.** Variable providers, conditions, step functions, layout providers, views, panels, and setting definitions you registered. EMS records the ids and removes them on disable. These are in-memory and rebuilt each load, so your `OnEnable` re-registers them; the journal just tracks which ones are yours.

**Owned sequences.** Sequences your plugin created with `CreateSequence`. They live in a plugin-namespaced bucket and carry an `ownerPlugin` stamp. Disable deactivates each from the engine and drops it from the bucket. EMS won't touch a user's sequence or another plugin's — only the ones stamped with your id.

**Setting overrides.** Any value you changed with `OverrideSetting`. Before applying yours, EMS snapshots the value that was live: the user's own value if they'd set one, otherwise the default. Disable restores the snapshot.

**CVar profiles.** A profile you applied with `RequestCVarProfile`. EMS routes it through the same manager the built-in CVar dashboard uses, which captures each live CVar before changing it. Disable restores every CVar you touched and puts the active profile back to what it was.

**Active layout, view, and chrome.** If you set the active layout provider or view, or hid the classic chrome, the journal holds the prior state. Disable restores it, falling back to the classic provider and the default view.

## Conflict policy

Two plugins can override the same setting or CVar. The rule:

- **The user always wins.** A value the user set explicitly is never silently overwritten — it's the base EMS restores to.
- **Among plugins, the last one enabled wins.** Its override is the live value.
- **Disabling falls back, not to default.** Disable the top plugin and the value drops to the next plugin's override if there is one, and only to the user or default value when no plugin override is left.

So enabling two layout plugins doesn't corrupt anyone's settings. The most-recently-enabled one is live, and peeling them off in any order lands back on the user's own value.

## What you do to get it

Register through the handle, and put your contributions in `OnEnable`. That's the whole contract. You don't write teardown code for your registry entries, sequences, settings, or CVars — EMS journals them as you make them and reverts them for you. `OnDisable` is only for cleanup EMS can't do: dropping references you hold, hiding a frame you created outside the host system.

EMS proves this works in its own test suite. A headless reversibility test registers a plugin that contributes one of each kind, snapshots EMS state, disables the plugin, and asserts the state is back to default-installed — every registry empty for that owner, the owned sequence gone from the engine, the setting and CVar restored, the layout back to classic.
