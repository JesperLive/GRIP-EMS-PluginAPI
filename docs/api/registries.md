# Tier 4 — Registries

These let your plugin add *content* of kinds EMS already understands — variables, conditions, step functions, and sequences. EMS validates each contribution, stores it namespaced by id, runs your logic inside `pcall`, and owns how it's used. Your code feeds data into EMS's own compiler and evaluator; it never replaces them.

A pattern runs through all four: you register a spec table whose `id` field must equal the id you register under, a duplicate id is rejected rather than overwritten, and your callbacks run isolated. Registration returns `true`, or `false` plus a reason.

## `API:RegisterVariableProvider(id, spec)`

A variable provider is a read-only value source for the `~name~` variable system. When EMS resolves a variable, it checks the user's own variables first, then gear variables, and only then asks the registered providers — so a plugin can never shadow a user's variable. Providers are consulted in registration order, and the first one to return a usable scalar wins.

```lua
local ok, reason = API:RegisterVariableProvider("acme_haste", {
    id = "acme_haste",
    name = "Acme Haste Percent",
    Resolve = function(self, varName)
        if varName == "acme_haste" then
            return math.floor(GetHaste())   -- a plain number
        end
        return nil                          -- not mine; let the next provider try
    end,
})
```

**Spec contract**

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | must equal the registry id |
| `name` | string | yes | human label |
| `Resolve` | function | yes | `Resolve(self, varName)` → scalar or `nil` |
| `OnRegister` | function | no | called once at register time, inside `pcall` |

`Resolve` must return a **plain, non-secret scalar** — a string, number, or boolean. Return `nil` for names you don't handle. If you return a table, a function, or a [secret-tagged value](../concepts/security-model.md), EMS ignores it (and logs the ignore against your id), because that value would otherwise be substituted into macrotext that can reach the secure execution path. Keep providers cheap and side-effect-free; they run during sequence compilation.

## `API:RegisterCondition(id, spec)` and `API:EvaluateCondition(id)`

A condition is a named boolean predicate you can use inside a user variable's body at runtime. Conditions are runtime-only — they can't be baked into a native WoW macro conditional, since a plugin can't invent one — so they're evaluated when the variable resolves.

```lua
API:RegisterCondition("acme_lowmana", {
    id = "acme_lowmana",
    name = "Mana below 30%",
    Evaluate = function(self)
        return UnitPower("player") / UnitPowerMax("player") < 0.30
    end,
})
```

A user then writes a variable body that branches on it:

```lua
GRIPEMS.API:EvaluateCondition("acme_lowmana") and "Evocation" or "Fireball"
```

**Spec contract**

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | must equal the registry id |
| `name` | string | yes | human label |
| `Evaluate` | function | yes | `Evaluate(self)` → boolean |
| `OnRegister` | function | no | called once at register time, inside `pcall` |

`EvaluateCondition(id)` runs the predicate inside `pcall` and always returns a clean boolean. An unknown id, a predicate that throws (for example, a comparison against a secret value), a `nil` or non-boolean result, or a secret-tagged result all collapse to `false`. So a caller always gets a safe boolean and nothing taint-sensitive escapes — write `Evaluate` to return a plain `true`/`false` and don't worry about the edge cases crashing anything.

## `API:RegisterStepFunction(id, spec)`

A step function is a pure step-*ordering* strategy, like the built-in Priority weighting. You supply `Expand`, which takes the resolved step texts and returns them in the order you want them executed. EMS owns the secure click body (the same round-robin body it uses for Sequential) and wraps each string you return into a macro step itself — so a plugin never supplies secure code and can't inject anything beyond ordered macrotext.

```lua
local ok, reason = API:RegisterStepFunction("acme_reverse", {
    id = "acme_reverse",
    name = "Reverse",
    Expand = function(self, resolvedStepTexts)
        local out = {}
        for i = #resolvedStepTexts, 1, -1 do
            out[#out + 1] = resolvedStepTexts[i]
        end
        return out
    end,
})
```

**Spec contract**

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | must equal the registry id, and must not collide with a built-in |
| `name` | string | yes | human label |
| `Expand` | function | yes | `Expand(self, resolvedStepTexts)` → array of macrotext strings |
| `OnRegister` | function | no | called once at register time, inside `pcall` |

A registered step function becomes active when a sequence's active version names it as its `stepFunction`. Registration is rejected if the id collides with a built-in strategy or another registered one. `Expand` must be pure — return ordered strings, don't touch game state.

## `API:RegisterSequences(name, version, seqNames, seqTable)`

Registers a set of rotation sequences your plugin ships. This is the original plugin entry point, re-exposed through the API.

```lua
API:RegisterSequences("Acme Rotations", "1.0.0",
    { "Acme Fire", "Acme Frost" },
    {
        ["Acme Fire"]  = { --[[ sequence definition ]] },
        ["Acme Frost"] = { --[[ sequence definition ]] },
    })
```

| Parameter | Type | Meaning |
|---|---|---|
| `name` | string | your plugin's name |
| `version` | string | your plugin's version |
| `seqNames` | table | array of the sequence names you're registering |
| `seqTable` | table | the sequences, keyed by name |

EMS validates the inputs, namespaces them under your plugin, loads them into the engine, and fires `PLUGIN_REGISTERED`. A user's own sequence wins on a name clash, so you can't clobber their work. The per-sequence table follows EMS's own sequence format; the simplest path is to build a sequence in EMS, export it, and ship that shape.

## Detecting a tier before you use it

All four registries are gated by a capability id (`variables`, `conditions`, `stepfunctions`, `sequences`). If you want to degrade gracefully on an EMS that predates one, check `GetCapabilities()` first — see [Tier 0](discovery.md).
