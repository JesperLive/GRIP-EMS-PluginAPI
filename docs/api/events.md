# Tier 1 — Events

A listen-only bus. EMS fires events as things happen; your plugin subscribes and reacts. You can't fire EMS's events — there's no public `Fire` — and you can only subscribe to names in the [event catalog](../reference/event-catalog.md).

Payloads handed to your handler are read-only snapshots: any table argument is deep-copied first, so holding onto it never reaches EMS's live state. Your handler runs inside `pcall`, so a bug in it disables your subscription's effect, not the addon.

## `API:On(event, handler)`

```lua
local handle = API:On("SEQUENCE_STEP_ADVANCED", function(seqName, step, numSteps)
    print(("%s advanced to step %d/%d"):format(seqName, step, numSteps))
end)
```

Subscribes `handler` to `event`. Returns an opaque handle string you keep for `Off`. On a bad call it returns `false` plus a reason — an unknown event name, or a handler that isn't a function:

```lua
local handle, reason = API:On("NOT_AN_EVENT", fn)
-- handle == false, reason == "On: unknown event 'NOT_AN_EVENT'"
```

Your handler receives the event's payload arguments only — the event name is not passed. Each event's payload is listed in the [catalog](../reference/event-catalog.md). For `SEQUENCE_CREATED` that's `(name, data)`; for `SETTING_CHANGED` it's `(key, value)`; some events carry nothing.

## `API:Off(handle)`

```lua
API:Off(handle)
```

Cancels the subscription that `On` returned. An unknown or already-removed handle is a no-op, so it's safe to call twice.

## `API:ListEvents()`

```lua
for _, name in ipairs(API:ListEvents()) do
    print(name)
end
```

Returns a fresh array of the event names you may subscribe to — the same set documented in the [event catalog](../reference/event-catalog.md). A new copy each call.

## Subscribe at the right time

Subscribe from an init point (see [Getting started](../getting-started.md)), not at file scope. For UI events (`GEMS_*`), subscribe after `GEMS_UI_READY` fires, since the window and its host frames don't exist until the user first opens EMS.

## A note on the UI events

Three catalog entries — `GEMS_UI_NAV_CHANGED`, `GEMS_EDITOR_TAB_CHANGED`, and `GEMS_SEQUENCE_SELECTED` — are part of the contract and accepted by `On`, but the in-core classic UI does not emit them yet. They're reserved for a layout provider (or a later EMS UI) to fire. Subscribing to them is safe and forward-compatible; just don't expect callbacks from them under the stock UI today. The catalog marks which events fire now and which are reserved.
