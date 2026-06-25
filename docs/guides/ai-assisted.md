# Guide: building a plugin with an AI assistant

An AI assistant can write a working EMS plugin, but only if you give it the API first. Out of the box it doesn't know this surface, so it makes up method names that look right and don't exist. Two habits fix that: hand it the API before you ask, and check what it writes against the real surface before you load it. This guide is that loop, with prompts you can copy.

It assumes you've written a WoW addon before. If you haven't read [Getting started](../getting-started.md) yet, skim it first; the plugin shape there is what the AI should produce.

## Give it the API first

The [AI context pack](../reference/ai-context.md) is the whole public API on one page, written for exactly this. Paste it into the chat before your first request. There's a [raw markdown link](https://raw.githubusercontent.com/JesperLive/GRIP-EMS-PluginAPI/main/docs/reference/ai-context.md) at the top of that page that copies clean.

Pasting the pack beats telling the model to "go read the docs site." It works from what's in the conversation, and the pack is dense and complete: the TOC dependency, the handshake, every tier's signatures, the event list, the lock list, and the rules that keep a plugin safe. With it in context the assistant writes against real methods instead of guessing.

## Then describe what you want

Be concrete about what the plugin does and which tier it needs (a variable, a condition, a layout). The pack already states the rules, so you don't have to repeat them, but naming the tier and the exact behaviour gets you closer on the first try.

## Example prompts

Each of these assumes you've already pasted the context pack into the chat. Adapt the names and behaviour to what you're building.

A variable provider:

```
Using the GRIP-EMS API I pasted, write a complete plugin (the .toc and one .lua file)
that registers a variable provider "acme_enemies" returning the number of nearby enemies,
so a user can put ~acme_enemies~ in a sequence. Register it through a plugin handle so it's
reversible. Return a plain number, not a secret value.
```

A condition:

```
Add to that plugin a condition "acme_big_group" that is true when there are 5 or more
group members (GetNumGroupMembers). Register it through the same handle. Show me how a user
would branch on it inside a variable body with EvaluateCondition.
```

A small listener plugin:

```
Write a GRIP-EMS plugin that prints a line whenever I create or update a sequence, with the
sequence name and its active step count. Use API:On for the events and API:GetSequenceInfo
for the details. Include the TOC dependency and the version handshake, and do the setup from
PLAYER_LOGIN.
```

A layout overhaul (bigger):

```
Write a GRIP-EMS plugin that adds a left nav rail and lays the sequence list and editor out
in two columns, with the classic chrome hidden and a way to switch back. Use a layout
provider, the host frames, MountPanel, and SetClassicChrome from the API I pasted. Keep any
secure frames off the hosts, and register on PLAYER_LOGIN so it can own the first paint.
```

## Check what it gives you

This is the part people skip, and it's the part that matters. AI writes confident code that's sometimes wrong. Before you load anything:

- Cross-check every `GRIPEMS.API:` and `handle:` call against the context pack. If a method isn't on that page, it doesn't exist. Tell the assistant so and have it redo that part; don't try to make a made-up call work.
- Confirm the `.toc` has `## Dependencies: GRIP-EMS` and the code does the handshake (null-check `GRIPEMS.API`, then `RequireVersion`).
- Confirm contributions go through the handle from `RegisterPlugin` if you want them cleaned up when the plugin is disabled.

Then load it: drop the folder in `Interface/AddOns/`, `/reload` with EMS installed, turn on EMS debug, and watch the log. Plugin errors and rejected provider returns go to the debug log, not a popup. Enable and disable your plugin once and confirm EMS goes back to stock.

## Where AI gets it wrong

The common failures, so you can spot them fast:

- It invents methods. `API:GetPlayerHealth()`, `API:SetSequence()` look plausible and aren't real. The pack is the entire surface; anything off it is a hallucination.
- It reaches into `_G.GRIPEMS`. If the code touches the internal table, it's working around the API instead of using it. Have it use the public call, or [open an issue](https://github.com/JesperLive/GRIP-EMS-PluginAPI/issues) if the public call is genuinely missing.
- It returns a secret value. A provider returning `UnitHealth("player")` resolves to nothing, because 12.0 tags health as secret. The pack says which returns have to be plain non-secret scalars.
- It registers at file scope. Setup has to run from `PLAYER_LOGIN`, or `GEMS_UI_READY` for UI work. The frame-and-event wrapper is easy for a model to drop.
- It gates on `EMS_VERSION`. Version checks go through `RequireVersion(n)` against `API_VERSION`, not the addon release string.

## A good loop

Paste the pack, describe the plugin, read the code back against the pack, load it with debug on, paste any errors into the chat, repeat. Two or three rounds usually gets a clean plugin. When the assistant keeps reaching for something the API won't do, check the [lock list](../reference/lock-list.md): it's likely locked on purpose, and there's usually an event or a read accessor that gets you the same outcome a safe way.
