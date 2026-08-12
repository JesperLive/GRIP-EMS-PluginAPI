# API changelog

What changed in the public plugin API, per EMS release. This is not the EMS changelog — the addon ships plenty that never touches your plugin, and that noise is exactly what makes a full changelog useless for this. Everything below either adds something you can call, changes what an existing call returns, or fixes a case where a call misbehaved.

Newest first. A release that isn't listed didn't change the API surface.

!!! warning "One release `API_VERSION` won't tell you about"

    From EMS 2.4.0, `API_VERSION` bumps on **any addition** to the surface, so
    `RequireVersion` is a real gate again. One release predates that rule and is
    still in the wild: EMS **2.3.7** added `GetAuthoredSteps` while the contract
    stayed at `3`, on the older "breaking changes only" policy. So
    `RequireVersion(3)` answers yes on 2.3.0 and on 2.3.9 alike, and the
    capability list can't separate them either — `stepdata` predates the method.

    If you support 2.3.7, **feature-detect the specific thing you need**:

    ```lua
    if API.GetAuthoredSteps then
        -- 2.3.7 or newer
    end
    ```

    Reading a key the API doesn't have returns `nil` rather than raising, so the
    check is safe on any build.

## EMS 2.4.0

### Added

- **[`API:GetActiveSequence()`](../api/data.md#apigetactivesequence)** — the name of the sequence EMS most recently drove, or `nil` when none has been driven this session. A read-only string with no setter. It saves you mirroring `SEQUENCE_STEP_ADVANCED` into your own variable just to answer "which sequence?". Read the name literally: it is **most recently driven**, not currently running. The value is never cleared when a sequence stops, and hold-mode activation writes it just as a secure-button click does — so a non-nil result tells you what ran last, not that anything is running now. For live start/stop, stay on `SEQUENCE_STEP_ADVANCED`.
- **`authoredsteps` capability id** — [`GetAuthoredSteps`](../api/data.md#apigetauthoredstepsname) now has an id of its own. It previously sat under `stepdata`, which predates it and therefore couldn't detect it.

### Changed

- **`API_VERSION` is now `4`, and the bump rule changed.** The contract used to say it bumped only on a breaking change; in practice v2 and v3 both bumped on purely additive growth, and 2.3.7's `GetAuthoredSteps` was the one addition that didn't. The rule now matches the practice: **any addition to the surface bumps `API_VERSION`.** Nothing about an existing call changed, so no plugin needs edits — this makes `RequireVersion(4)` a reliable gate for everything listed above, and leaves 2.3.7 as the single build where a presence check is still the only option.

## EMS 2.3.7 — 2026-07-11

### Added

- **[`API:GetAuthoredSteps(name)`](../api/data.md#apigetauthoredstepsname)** — the active version's per-step spell data in **authored base order**, as `{ index, spellID, spellName, icon }`. This is the order the user wrote, before the step function expands it and before interleave copies land. Use it when you want per-spell frequency or the base order; keep using [`GetSequenceSteps`](../api/data.md#apigetsequencestepsname) for anything that has to line up with the live step.

### Changed

- **`SEQUENCE_STEP_ADVANCED` now reports the expanded `numSteps`.** It previously fired the *authored* count while the button cycled the *expanded* array, so a 4-step Priority sequence advanced through steps 1..10 while the event told you `numSteps = 4`. It now fires `10`, and `numSteps` matches `#GetSequenceSteps(name)` for the same sequence.

    !!! danger "This one can break a working plugin"

        If you drew a progress readout from this payload, it was wrong before and
        is right now — no change needed. But if you **compensated** for the old
        mismatch (recomputing the real count yourself, or scaling the step index
        against it), that workaround now double-counts. Drop the compensation.
        Sequential and Random sequences are unaffected: expanded and authored are
        the same array there, so those never disagreed.

- **`GetSequenceList()[i].stepCount` now sits in the execution domain for dormant sequences too.** A registered-but-not-activated sequence reported the compiled count while `#GetSequenceSteps(name)` reported the expanded one — the same 4-vs-10 split, reachable through `GetSequenceList` because it iterates dormant entries. `stepCount` now always equals `#GetSequenceSteps(name)` and is a valid denominator for `currentStep`, which is what [the data reference](../api/data.md#apigetsequencelist) always claimed.

## EMS 2.3.4 — 2026-07-03

### Added

- **[`GetSequenceInfo`](../api/data.md#apigetsequenceinfoname) gained five metadata fields**: `help`, `helplink`, `changelog`, `talentString`, and `url`. All scalar copies, all `nil` when the author didn't set them. `talentString` carries a sequence's talent loadout string, which survives import, save, re-export, and duplication — so a plugin can offer "load this build" next to a rotation without asking the user to paste anything.

## EMS 2.3.1 — 2026-06-30

### Fixed

- **`GetSequenceList()` and `SEQUENCE_STEP_ADVANCED` no longer error on a version with no steps.** Three accessors checked that the version table existed but not that its `steps` field did, so an empty version raised `attempt to get length of a nil value` on the length operator. They short-circuit to `0` now.

## EMS 2.3.0 — 2026-06-30

### Added

- **`API_VERSION` 3**, with the `stepdata`, `macro`, and `slash` capabilities. This is the action-bar surface: [`GetSequenceSteps`](../api/data.md#apigetsequencestepsname) and [`GetSequenceMacroIndex`](../api/data.md#apigetsequencemacroindexname) to read, [`handle:EnsureSequenceMacro`](../api/authoring.md#sequence-macros) and [`handle:RegisterSlashCommand`](../api/authoring.md#slash-commands) to author. See the [action-bar plugin guide](../guides/action-bar-plugin.md).

## Getting notified

New entries here are posted to the **plugin-dev channel** on [Discord](https://discord.gg/temptingus) when they ship, so you don't have to poll this page.

If you'd rather not sit in Discord, watch [the docs repo](https://github.com/JesperLive/GRIP-EMS-PluginAPI) — **Watch → Custom → Releases**. Every API change here gets a matching release, and GitHub will mail you.

## Something missing?

If a release changed behaviour your plugin depends on and it isn't written down here, that's a bug in this page — [open an issue](https://github.com/JesperLive/GRIP-EMS-PluginAPI/issues) and it gets added.
