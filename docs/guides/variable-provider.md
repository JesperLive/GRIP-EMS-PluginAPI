# Guide: a variable provider

A variable provider feeds values into the `~name~` variable system. When a user writes `~acme_haste~` in a sequence step, EMS resolves it — first against the user's own variables, then gear variables, and only then against registered providers. So your provider can add new values without ever shadowing a user's.

## Register one

```lua
local ok, reason = GRIPEMS.API:RegisterVariableProvider("acme_haste", {
    id = "acme_haste",                       -- must equal the registry id
    name = "Acme: haste percent",            -- human label
    Resolve = function(_, varName)
        if varName == "acme_haste" then
            return math.floor(GetHaste())     -- a plain number
        end
        return nil                            -- not ours
    end,
})
if not ok then print(reason) end
```

`Resolve(self, varName)` is called with whatever name EMS is trying to resolve, so check `varName` and return `nil` for anything that isn't yours. Registration order is resolution order — the first provider to return a usable value wins.

## One provider, several variables

A provider can answer for more than one name. Branch inside `Resolve`:

```lua
Resolve = function(_, varName)
    if varName == "acme_haste" then
        return math.floor(GetHaste())
    elseif varName == "acme_crit" then
        return math.floor(GetCritChance())
    end
    return nil
end,
```

## Return a plain, non-secret scalar

`Resolve` must return a string, a number, or a boolean — nothing else. A table, a function, or a [secret-tagged value](../concepts/security-model.md) is rejected and logged against your id, because the value gets substituted into macrotext that can reach the secure execution path.

That last part is the gotcha: some 12.0 values are secret-tagged even though they look like plain numbers. A player's current health is the classic one. If you return `UnitHealth("player")`, EMS screens it out and your variable resolves to nothing. Return values that aren't secret — computed stats, counts, settings, group size — or derive a non-secret number before returning.

## Keep it cheap and pure

`Resolve` runs during sequence compilation, so don't do expensive work or cause side effects in it. Read a value, return it. If you need to cache something, cache it elsewhere and have `Resolve` read the cache.

## Test it

Register the provider, then in a sequence step reference your variable (`~acme_haste~`) and watch it compile. Turn on EMS debug (`GetSetting("debug")` reflects it) to see the log line if a return gets rejected for being non-scalar or secret.
