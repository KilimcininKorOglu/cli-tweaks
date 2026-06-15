# Admin Panel & End-User UI Reference

Two UI surfaces this skill must build: the **admin panel** (for viewing audit logs and replays) and the **end-user UI** (consent + opt-out, required because recording is personal-data processing). Both are framework-agnostic specs — integrate them into the project's existing admin/template system and design language; build only what's missing.

---

## Part 1 — Admin Panel

Three pages. All sit behind the project's existing admin authentication; never expose them publicly.

### Page 1 — Session List (`/admin/audit`)

Lists visitors by most recent activity. Backed by `GetRecentSessions` (see `references/databases.md`) plus the filter/sort/paging clauses below.

| Column     | Content                             |
|------------|-------------------------------------|
| Visitor    | First 8 chars of `visitor_id` + `…` |
| Events     | Count of audit events               |
| First Seen | Earliest `created_at`               |
| Last Seen  | Latest `created_at`                 |
| Action     | `[view]` → visitor timeline         |

Controls (all server-side, reflected in the query — do not load every row and filter client-side):
- **Filter:** date range (last seen between X–Y), event type, minimum event count
- **Search:** `visitor_id` prefix match
- **Sort:** last seen (default, DESC), event count, first seen
- **Pagination:** page size 25 / 50 / 100, offset or keyset; show total count

Empty state: "No sessions recorded yet."

### Page 2 — Visitor Timeline (`/admin/audit/:visitorId`)

Chronological list of one visitor's events. Backed by `GetVisitorTimeline` + `GetReplaySessions`.

| Column | Content                                                                                              |
|--------|------------------------------------------------------------------------------------------------------|
| Time   | `HH:MM:SS` (group rows by day with a date divider)                                                   |
| Event  | Colored badge by `event_type` (e.g. `error` red, `page_view` neutral, `search`/`form_submit` accent) |
| Path   | Request path                                                                                         |
| Data   | `event_data` as compact `key=value`; click to expand pretty-printed JSON                             |

Features: per-visitor event-type filter; collapsible full-JSON view; "back to session list" link.

**Replay section** (same page): list the visitor's replay sessions (page_url, started_at) each with a `[play]` button that opens the player.

### Page 3 — Replay Player

Plays back an rrweb session. Reuses the player setup from SKILL.md Phase 8 (load the **UMD** build of `rrweb-player`, global `rrwebPlayer`).

- **Data:** `GetReplaySession(id)` returns batches ordered by `seq`; concatenate them in order into one events array before constructing the player.
- **Init:**
  ```javascript
  function playReplay(sessionId) {
      fetch('/admin/replay/' + sessionId)        // returns ordered, concatenated events
          .then(function (r) { return r.json(); })
          .then(function (data) {
              var c = document.getElementById('replay-container');
              c.innerHTML = '';
              new rrwebPlayer({ target: c, props: { events: data.events, width: 1024, height: 600 } });
          });
  }
  ```
- **States:** loading spinner while fetching; empty ("no replay for this visitor"); error ("replay data incomplete") if batches are missing/corrupt.

### Admin security (all three pages)

- **Authentication required** — wire into the project's existing admin auth (session/JWT/basic). Never public.
- **`Cache-Control: no-store`** on every audit and replay data endpoint.
- **Rate limit** the ingest endpoint (`/api/replay`): max 10 req/min per `visitor_id`.
- **Origin/CSRF:** validate origin on the ingest POST; CSRF-protect any admin state-changing action.
- **Reject** ingest requests without a valid `visitor_id` cookie.

---

## Part 2 — End-User UI

rrweb recording + a tracking cookie is personal-data processing. In consent-required jurisdictions (EU/UK GDPR and similar), recording MUST be gated on consent — `maskAllInputs` does not remove this obligation (visible PII text is still captured; see SKILL.md Privacy & Security).

### Component 1 — Consent banner

- Shown on first visit when no consent cookie exists.
- States plainly what is recorded (anonymized session replay + usage analytics) and links to the privacy policy.
- **Accept** / **Decline** buttons. The choice is stored in a `replay_consent` cookie (1 year).
- Decline → the recorder never starts; no replay data is sent.

### Component 2 — Opt-out

- A persistent control (account settings or footer link) so users can withdraw consent later.
- Opt-out sets `replay_consent=declined` and stops the recorder immediately.
- Optionally offer data erasure (GDPR right to erasure): delete this visitor's `audit_events` / `replay_*` rows.

### Component 3 — Recording indicator (optional)

A small, unobtrusive "session recording active" indicator. Some jurisdictions/policies expect visible transparency; include it when in doubt.

### Recorder bootstrap (consent-gated)

The recorder from SKILL.md Phase 6 must check consent before calling `rrweb.record()`:

```javascript
// at the very top of recorder.js
function getCookie(n) {
    return document.cookie.split('; ').reduce(function (a, c) {
        var p = c.split('='); return p[0] === n ? decodeURIComponent(p[1]) : a;
    }, '');
}
if (getCookie('replay_consent') !== 'accepted') return;  // no consent → do not record
```

### Reference implementation (framework-agnostic, vanilla HTML/JS)

Drop into the main layout; restyle to match the site. No build step or dependency.

```html
<div id="consent-banner" role="dialog" aria-live="polite" hidden>
  <p>We record anonymized session replays and usage analytics to improve this site.
     <a href="/privacy">Learn more</a>.</p>
  <button id="consent-accept">Accept</button>
  <button id="consent-decline">Decline</button>
</div>
<script>
(function () {
    function getCookie(n) {
        return document.cookie.split('; ').reduce(function (a, c) {
            var p = c.split('='); return p[0] === n ? decodeURIComponent(p[1]) : a;
        }, '');
    }
    function setConsent(v) {
        document.cookie = 'replay_consent=' + v + ';path=/;max-age=31536000;samesite=lax';
    }
    if (getCookie('replay_consent')) return;          // already decided
    var b = document.getElementById('consent-banner');
    b.hidden = false;
    document.getElementById('consent-accept').onclick = function () {
        setConsent('accepted'); b.hidden = true; location.reload();  // reload so the recorder starts
    };
    document.getElementById('consent-decline').onclick = function () {
        setConsent('declined'); b.hidden = true;
    };
})();
</script>
```

Load order: this banner script first (sets `replay_consent`), then `recorder.js` (which returns early unless consent is `accepted`).
