# The lock list

Some systems have no public write path and never will. The API may expose a read-only view of derived state from these areas, but never a way to change them. This page is the list, with the reason each is locked, so you know where the boundary is before you go looking for a setter that isn't there.

The rule of thumb: **if a call could change which spell fires, how a key is bound, who an author is, what gets transmitted, or what gets saved — it's locked.** Read-only snapshots of derived state (the active version index, the detected context, a sequence summary) are fine and are what the data accessors give you.

| Locked area | Why it's locked |
|---|---|
| Rotation execution | Changing what fires, when, or in what order *is* changing how EMS works. The engine's activate, deactivate, step-advance, reset, recompile, and compile paths are internal. |
| Secure buttons and the keybind matrix | These are taint-sensitive, and binding is EMS's core promise. The secure action buttons, override bindings, and the keybind manager have no plugin write path. |
| Authorship and signing | Sequences carry a signature chain so sharing stays honest. Letting a plugin write to identity or the modifier chain would break that integrity. |
| Peer-to-peer transmission | The sharing protocol and its abuse surface stay internal. Plugins don't send on EMS's channels. |
| Secure CVar application | Applying CVars under combat/secure rules is safety-critical and stays in EMS's hands. |
| Persistence | Direct writes to the saved-variables tables or the profile database risk silent corruption and data loss, so there's no raw write path. |
| Taint-laundering and secret values | A single tainted comparison can break secure execution. Secret-tagged values are screened out of any path that reaches macrotext (see below). |

## What you *can* read

Locked doesn't mean invisible. Through Tier 2 you can read sequence summaries, per-sequence metadata, the active version index, the detected context, and allowlisted settings — all as copies. Through Tier 1 you can observe lifecycle and UI events. That covers the large majority of what a plugin needs to react intelligently without holding a write path into anything dangerous.

## Secret values

WoW 12.0 tags certain values (a player's health, for example) as secret so they can't silently cross into protected code. Anything you return from a [variable provider](../api/registries.md) or a [condition](../api/registries.md) could end up inside macrotext bound to a secure button, so EMS screens your returns: a secret-tagged value from a provider is rejected, and a condition that yields one evaluates to `false`. You don't need to detect this yourself — just know that "I returned a secret value" reads downstream as "no result," never as a crash.

## If you need something that's locked

If you're reaching for a locked system, there's usually a supported way to get the *outcome* you want without the write path — an event to react to, or a read accessor to drive your own UI. If there genuinely isn't, describe the goal in an [issue](https://github.com/JesperLive/GRIP-EMS-PluginAPI/issues). The boundary is firm, but the read-only surface around it can grow.
