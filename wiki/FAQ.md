# Community FAQ

The authoritative FAQ is on the [docs site](https://JesperLive.github.io/GRIP-EMS-PluginAPI/faq/). This page is for community questions that don't have a home there yet — add yours, and if it turns out to belong in the official docs, it can move there later.

## Format

Add a question as a `##` heading and answer it underneath. Keep answers concrete, with a code snippet where it helps. If a question here is answered better on the docs site, link to it instead of duplicating.

## Questions

### Does the API work in Classic / Cata / other flavors?
The addon targets WoW Retail. If you've tested a plugin on another flavor, note what worked here.

### How do I debug what my plugin is doing?
Turn on EMS debug logging — plugin callback errors and rejected provider returns are logged there against your plugin id. `GRIPEMS.API:GetSetting("debug")` reports whether it's on.

_Add your question above this line._
