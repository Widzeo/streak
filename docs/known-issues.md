# Known issues / limitations

Not blocking, deliberately deferred. Kept here so they don't get lost.

## `at_most` + `cadence=1` habits read as trivially complete

For a habit like "Budget restaurant" (`direction=at_most`, `period_scope=month`,
`cadence=1`), an unlogged day defaults to a total of 0, and 0 always satisfies
"at most X". With `cadence=1`, a single such day is enough for the whole
period to be marked `complete` — so these habits read as "on track" almost
regardless of the real total spent.

Fixed the most visible symptom (future dates always showing complete on the
heatmap, even with zero real data) by refusing to evaluate any day after
today (see `get_year_heatmap` in `app/stats/service.py`). The underlying issue
remains for past/current periods: a real overspend can still be masked once
at least one zero-activity day exists in the period.

Possible real fix: when `cadence == 1` on a multi-day scope, compare the
*summed* total of eligible days against `target` instead of counting
individual day-matches (`cadence > 1` would keep the current per-day-counting
behavior). Would touch `app/stats/completeness.py`, `count_days_met`, and the
`HabitDayProgress` display (today_total/days_met don't quite fit an aggregate
reading).

## Future-date navigation isn't guarded on "Aujourd'hui"

The date/scope navigator on the today page can move forward past today with
no limit. Landing on a future date could hit the same "trivially complete"
issue described above for `at_most`/`cadence=1` habits, since `GET /days` and
`GET /habits/{id}/stats` don't have the same "skip if in the future" guard
that the heatmap now has.

Two possible fixes, not yet decided: block forward navigation past today in
the front-end, or apply the same guard to the relevant service functions.

## No `logical_date` derivation from a timestamp

`logical_day_start_hour` exists in `app/core/config.py` but nothing uses it.
`POST /completions` takes whatever `logical_date` the client sends - there is
no function converting "now" into the correct logical date based on the
configurable day-start hour. Relevant to the "changement d'heure" robustness
scenario from the original test plan, which currently can't be tested because
the feature doesn't exist.

## "Lecture seule" badge visual

Functionally correct but the current pill badge looks flat. Worth a proper
redesign (e.g. a more visible banner/notice) during the front-end polish pass
(step 6/7), not urgent.
