# Security model

The API has one job beyond being useful: let you extend EMS without letting you — or a bug in your plugin — change how it runs. This page explains how that line holds, because understanding it tells you what to expect from every method.

## The premise: one shared Lua state

Every WoW addon runs in the same Lua state. There's no process boundary, no real sandbox. A determined addon can hook globals, wrap functions, and read or taint frames no matter what any other addon does. So "plugins can't change how EMS works" is not enforced by a wall — it's enforced by **design**. EMS doesn't hand you a wall; it hands you a surface that never had a write path into the parts that matter.

Four properties do the work:

**Additive-only.** Every public method either reads state or registers a contribution that EMS validates and owns. No call mutates rotation execution, key binding, authorship, transmission, or saved data. There is no public setter that reaches those systems.

**Frozen surface.** `GRIPEMS.API` and its sub-tables (`API.UI`, `API.Preview`) are read-only proxies. Assigning to them throws an error, and their metatables are locked, so you can't monkeypatch the API or swap a method out from under EMS. You call methods; you don't rewrite them.

**Read-only snapshots.** Accessors return fresh copies, and event payloads are deep-copied before they reach you. Holding onto a table EMS handed you never aliases its live state — mutate the copy all you like, nothing downstream changes.

**`pcall` isolation.** Everything you give EMS to call — event handlers, `Resolve`, `Evaluate`, `Expand`, layout-provider hooks — runs wrapped in `pcall`. A throw, a `nil`, or a value EMS doesn't accept degrades to "your feature didn't run," logged against your plugin id. EMS keeps going.

## The internal global is not the API

`_G.GRIPEMS` exists and holds the whole internal table. You can reach it. Don't build on it. It's undocumented, unsupported, and changes without warning on any EMS update — the same deal every large addon gives its internals. If you need something that's only reachable through `_G.GRIPEMS`, that's a gap in the public API: [open an issue](https://github.com/JesperLive/GRIP-EMS-PluginAPI/issues) and describe what you're trying to do. The public surface grows to remove reasons to touch internals; it does not bless reaching into them.

## What you can never write

Some systems have no public write path and never will. Read-only views of derived state are fine; a mutation path is not. The rule of thumb: if a call could change which spell fires, how a key is bound, who an author is, what gets transmitted, or what gets saved, it's locked. The full list, with the reasoning, is on [the lock list](../reference/lock-list.md).

## Secret values and taint

WoW 12.0 introduced secret-tagged values — a health read, for example, reports a normal type but is tagged so it can't cross into protected paths without tainting them. Anything you feed into the variable system or a condition can end up inside macrotext that reaches the secure execution environment, so EMS screens your return values: a Tier 4 provider that returns a secret-tagged value has that value rejected, and a condition that yields one evaluates to `false`. You don't have to think about this much — just know that returning a secret value means "no result," not a crash. The [registries](../api/registries.md) page covers it per method.

## What this means for you

Write your plugin against the public surface and you get a stable contract: your code can't break EMS, and EMS updates won't silently break you as long as `API_VERSION` holds. Reach around it into internals and you give both of those up. The whole API is built so you never need to.
