# Guide: a custom step function

A step function is a step-*ordering* strategy. EMS ships a few built in (Sequential, Priority, and others). A plugin can add its own: you decide the order the steps run in, and EMS owns everything about how they execute.

The split matters for safety. You supply `Expand`, which takes the resolved step texts and returns them in execution order. EMS wraps each returned string into a macro step using its own secure click body — so your plugin never writes secure code and can't inject anything past ordered macrotext.

## Register one

```lua
local ok, reason = GRIPEMS.API:RegisterStepFunction("acme_reverse", {
    id = "acme_reverse",                  -- must equal the id; can't collide with a built-in
    name = "Reverse",
    Expand = function(_, resolvedStepTexts)
        local out = {}
        for i = #resolvedStepTexts, 1, -1 do
            out[#out + 1] = resolvedStepTexts[i]
        end
        return out
    end,
})
if not ok then print(reason) end
```

`Expand(self, resolvedStepTexts)` receives an array of the step texts after EMS has resolved variables, and returns an array of macrotext strings in the order you want them executed. Here, reverse order.

## Use it in a sequence

A registered step function becomes active when a sequence's active version names it as its `stepFunction`. The simplest path: build a sequence in EMS, set its step function to your id, and the engine routes its steps through your `Expand`. If you ship sequences with [`RegisterSequences`](../api/registries.md), set the version's `stepFunction` to your id there.

## Rules for `Expand`

- **Be pure.** Return ordered strings; don't touch game state, don't cache the input array, don't cause side effects. It runs at compile time.
- **Return strings.** Each element of your returned array is treated as macrotext for one step. Don't return tables or attribute objects — EMS builds those itself.
- **Don't expand without bound.** The result becomes the executed step list; keep it proportional to the input.

## What you can't do

You can't supply the secure click body, change which button fires, or add attributes beyond the macrotext. That's deliberate — see the [lock list](../reference/lock-list.md). A step function shapes order; it never reaches execution.

## Registration failures

`RegisterStepFunction` returns `false` plus a reason if your id collides with a built-in or another registered strategy, if the spec is malformed, or if the step-function module isn't available on that build. Check the return and surface the reason while developing.
