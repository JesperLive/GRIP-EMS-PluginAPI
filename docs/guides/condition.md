# Guide: a custom condition

A condition is a named boolean your plugin computes, which a user can branch on inside a variable body. Conditions are evaluated at runtime — they can't be folded into a native WoW macro conditional, because a plugin can't invent one — so they're a way to expose plugin logic to the variable system.

## Register one

```lua
GRIPEMS.API:RegisterCondition("acme_burst_ready", {
    id = "acme_burst_ready",              -- must equal the registry id
    name = "Acme: burst window open",     -- human label
    Evaluate = function()
        return MyPlugin.burstWindowOpen == true
    end,
})
```

`Evaluate(self)` takes no extra arguments and returns a boolean. Keep it to a clean `true`/`false`.

## Use it in a variable

The user writes a variable body that calls `EvaluateCondition`:

```lua
GRIPEMS.API:EvaluateCondition("acme_burst_ready") and "Trinket" or "Filler"
```

When EMS resolves that variable, your condition runs and the body picks one side.

## It always returns a clean boolean

`EvaluateCondition(id)` runs your `Evaluate` inside `pcall`, so you don't have to defend against every edge. All of these collapse to `false`:

- an unknown id
- `Evaluate` throwing (for example, comparing against a secret value)
- a `nil` or non-boolean result
- a secret-tagged result

That means a broken or unsafe condition degrades to "the false branch," never a crash or a taint. Write `Evaluate` to return a plain boolean and let EMS handle the rest.

## Keep it fast

Like a variable provider's `Resolve`, `Evaluate` can run during compilation and resolution, so don't do heavy work inside it. Compute your state elsewhere (an event handler, a timer) and have `Evaluate` read a flag.

## Conditions vs variables

Use a **variable provider** when you want to substitute a value (a number, a spell name). Use a **condition** when you want a yes/no that the user combines with their own choices. They pair well: a provider supplies the data, a condition gates on it.
