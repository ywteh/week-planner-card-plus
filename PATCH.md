# Fork patch: per-calendar timeline columns

This fork adds a calendar-axis day timeline to
[randrcomputers/week-planner-card-plus](https://github.com/randrcomputers/week-planner-card-plus).

## What it adds

A new `viewMode: **timelineDayByCalendar**` (aliases: `calendarColumns`,
`daybycalendar`, `timelinecalendar`, `timeline_day_by_calendar`):

- **One day at a time**, with a **date-nav bar** (‹ prev / next ›, plus a
  clickable date label that jumps back to today). It shows *today* by default
  (falling back to the first fetched day) and lets you page ± within the
  fetched range. Widen that range with `days:` / `startingDayOffset:` so
  prev/next have room to move — e.g. `days: 29`, `startingDayOffset: -7` gives
  a week back and three weeks forward.
- **One column per calendar** instead of one column per day — each visible
  (non-shared) calendar in `calendars:` becomes a column, headed by its name +
  colour dot.
- Timed events render as **blocks positioned by time** on a shared hour axis;
  overlapping events within a calendar split into sub-columns.
- All-day events render as **pills** at the top of their calendar's column.
- **Shared calendars** (e.g. a `family` calendar) span **all** columns and are
  drawn *behind* the per-person events — timed ones as translucent full-width
  spans, all-day ones as full-width pills. Mark them per-calendar with
  `shared: true`, or list their entity ids under a top-level
  `sharedCalendars: [...]`.
- **Weather nav bar** (right of the date nav), all optional:
  - Per-hour condition indicators for the shown day — driven by
    `hourlyForecastEntity:` (a sensor whose `forecast` attribute holds the
    hourly list) and `forecastHours:` (default `[9,12,15,18,21]`). Each cell
    shows the hour, a weather icon (or emoji fallback), and a
    precipitation label — **chance-of-rain `%`** if
    `precipitation_probability` is present, otherwise **`mm`** from
    `precipitation`.
  - A daily high/low + condition summary from the card's own `weather:` config.
- **Configurable visible hour window** via `startHour` / `endHour`
  (aliases `dayStartHour`/`dayEndHour`, `timelineStartHour`/`timelineEndHour`).
  Default `0`/`24`. Events fully outside the window are dropped; straddling
  events are clipped to the edge.
- **Height / scrolling**: by default the grid is `timelineHourHeight` px per
  hour (alias `scheduleHourHeight`/`hourHeight`, or the
  `--wpcp-timeline-hour-height` CSS var) and scrolls. Set `fillHeight: true`
  **or** `timelineHeight: "<css length>"` (e.g. `"calc(100dvh - 24px)"`) to pin
  the whole timeline to a fixed height and lay events out by % of the window so
  nothing scrolls — used for the full-screen wall panel.
- Event blocks use `box-sizing: border-box` so padding/border don't overflow
  the column.

Upstream's own `schedule` / `timelineDay` / `timelineWeek` / `grid` modes are
untouched — this is purely additive (a monkey-patch appended to the bundle's
existing IIFE).

## Example

This mirrors the wall-panel config in
`homeassistant/dashboards/wabisabi.yaml`:

```yaml
type: custom:week-planner-card-plus
viewMode: timelineDayByCalendar
days: 29                       # fetch range: wide enough to page prev/next
startingDayOffset: -7          # start a week back
startHour: 8
endHour: 21
timelineHeight: "calc(100dvh - 24px)"   # fill the panel, no scroll
weather:                       # daily high/low + condition (right of nav)
  entity: weather.forecast_home
  showTemperature: true
  showLowTemperature: true
  showCondition: true
  roundTemperature: true
hourlyForecastEntity: sensor.weather_forecast_hourly
forecastHours: [9, 12, 15, 18, 21]
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
  - entity: calendar.family    # spans all columns, drawn behind the rest
    name: Family
    color: '#8e7cc3'
    shared: true
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
