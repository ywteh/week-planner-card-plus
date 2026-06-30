# Fork patch: per-calendar timeline columns

This fork adds a calendar-axis day timeline to
[randrcomputers/week-planner-card-plus](https://github.com/randrcomputers/week-planner-card-plus).

## What it adds

A new `viewMode: **timelineDayByCalendar**` (aliases: `calendarColumns`,
`daybycalendar`, `timelinecalendar`, `timeline_day_by_calendar`):

- **Single day** (today; falls back to the first configured day).
- **One column per calendar** instead of one column per day — each visible
  calendar in `calendars:` becomes a column, headed by its name + colour dot.
- Timed events render as **blocks positioned by time** on a shared hour axis;
  overlapping events within a calendar split into sub-columns.
- All-day events render as **pills** at the top of their calendar's column.
- **Configurable visible hour window** via `startHour` / `endHour`
  (aliases `dayStartHour`/`dayEndHour`, `timelineStartHour`/`timelineEndHour`).
  Default `0`/`24`. Events fully outside the window are dropped; straddling
  events are clipped to the edge.
- Event blocks use `box-sizing: border-box` so padding/border don't overflow
  the column.

Upstream's own `schedule` / `timelineDay` / `timelineWeek` / `grid` modes are
untouched — this is purely additive (a monkey-patch appended to the bundle's
existing IIFE).

## Example

```yaml
type: custom:week-planner-card-plus
viewMode: timelineDayByCalendar
days: 1
startHour: 8
endHour: 20
timelineHourHeight: 48
calendars:
  - entity: calendar.person_a
    name: Person A
    color: '#e6c229'
  - entity: calendar.person_b
    name: Person B
    color: '#1a8fe3'
  - entity: calendar.person_c
    name: Person C
    color: '#ff5733'
  - entity: calendar.person_d
    name: Person D
    color: '#10b981'
```

## How the patch is maintained

Upstream ships a single bundled `week-planner-card-plus.js` (no separate
source tree), so the patch is a **deterministic transform** rather than a
hand-edited diff:

- `week-planner-card-plus.upstream.js` — pristine upstream bundle (never edited).
- `patch.py` — reads `*.upstream.js`, appends the new viewMode mapping, the
  route in `_renderDays`, and the `_rnrRenderTimelineByCalendar` function;
  writes the served `week-planner-card-plus.js`.

### Re-patching after an upstream update

```bash
git fetch upstream && git checkout upstream/main -- week-planner-card-plus.js
cp week-planner-card-plus.js week-planner-card-plus.upstream.js
python3 patch.py            # regenerate the patched bundle
node --check week-planner-card-plus.js
```

If upstream changed the anchored lines, `patch.py` will fail its asserts —
fix the anchors, then re-run.
