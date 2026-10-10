# FC27 Squad Assistant — Project Context & Build Brief

## 1. Goal
Build a local-first EA Sports FC 27 Ultimate Team squad assistant. It imports the JSON produced by the existing working FUT.GG browser extension and helps answer questions such as:
- Who should replace a selected player?
- Which purchasable players fit a position and budget?
- What happens to every player's chemistry after a transfer?
- Which owned player is a free upgrade?
- Which combination of transfers gives the best improvement per coin?
- Which players best fit the user's gameplay style?

The product design is not finalized. Build incrementally and keep components replaceable.

## 2. Existing working exporter
A working Chrome/Chromium Manifest V3 extension already exists: `FC27 Club Exporter v0.4.0`.

Current workflow:
1. User logs into FUT.GG normally.
2. User visits Players and manually browses all club-player pages.
3. User opens Squads and the active squad.
4. Extension passively observes FUT.GG JSON responses.
5. Extension exports one JSON containing owned club players, active squad and tactic data.

Safety boundary: keep the extension passive. Never access EA private Web App endpoints, automate transfer actions, export/persist EA auth tokens, cookies, authorization headers or credentials, or implement behavior likely to create account-ban risk.

The export can contain owned player instances, XI, bench, chemistry, chemistry styles, IDs, OVR, FUT.GG rating, detailed attributes, nation/league/club, positions, PlayStyles/+, Role+/++, rarity chemistry metadata, tradeability, purchase price, games/goals/assists, loans, formation, manager, tactic roles/focuses and tactic code.

Learn the exact schema from real fixtures. Do not assume it from this document.

## 3. Most important data rule
**The newest active imported export is the source of truth.**

Never infer current ownership from old chats, old exports, cached recommendations or remembered player lists.

A real failure motivating this rule: Vicky López existed in an older analysis, was later sold, and was mistakenly recommended as if still owned.

Therefore:
`CURRENT OWNED PLAYERS = players in the current/latest active export`

Historical snapshots may be retained, but must never silently contaminate current recommendations. Every recommendation should be traceable to a snapshot/import ID.

## 4. Architecture principle
Separate deterministic game logic from LLM reasoning.

Deterministic code owns:
- ownership and exact card identity
- position eligibility
- formation-slot compatibility
- chemistry and manager/special-card chemistry rules
- hypothetical substitution chemistry
- team chemistry totals
- budget arithmetic
- candidate filtering
- loan handling
- stat normalization and validation

LLM owns:
- interpreting tradeoffs
- gameplay-style reasoning
- explaining recommendations
- value-for-coins discussion
- budget allocation suggestions
- tactical reasoning and natural-language Q&A

Pipeline:
`candidate discovery -> position validation -> chemistry engine -> stats/roles/PlayStyles -> price/value -> structured results -> LLM explanation`

Never ask an LLM to guess chemistry when code can calculate it.

## 5. Chemistry engine
This is a highest-priority core component.

Before trusting chemistry-sensitive recommendations:
1. Parse a real exported XI.
2. Independently calculate chemistry.
3. Compare every player's result with exported/FUT.GG chemistry.
4. Show diagnostics for mismatches.
5. Validate against multiple fixtures.

Keep chemistry rules versioned and isolated, e.g.:
`backend/app/chemistry/{engine.py,rules.py,profiles.py}`

If a rule is uncertain, mark it unverified rather than guessing.

Golden principle:
`our calculated chemistry == exporter/FUT.GG chemistry`

## 6. Position eligibility is a hard constraint
Never recommend a card for a slot without verifying that exact card can play the required position.

Real failure motivating this: Nicole Anyomi was once suggested for RW, but that exact card could not play RW.

Candidate order should start roughly:
1. exact card valid
2. exact position valid
3. chemistry simulation
4. Role+/++ fit
5. gameplay-style fit
6. attributes/PlayStyles
7. FUT.GG rating
8. price/value
9. recommendation

OVR alone must never drive recommendations.

## 7. Initial gameplay profile
Keep preferences configurable.

User frequently:
- triggers striker runs with L1
- plays lofted through balls
- uses through balls generally
- uses one-twos
- values direct off-ball movement
- shoots from long range
- uses finesse/plase shots often

Meaningful attacker/CAM/winger attributes include:
acceleration, sprint speed, positioning, finishing, long shots, shot power, curve, composure, vision, short/long passing, ball control, agility/dribbling.

Relevant verified PlayStyles/PlayStyle+ should affect evaluation (for example Finesse Shot, Incisive Pass, Long Ball Pass, First Touch when applicable). Never invent mappings for numeric PlayStyle/role IDs.

ST: runs/finishing primary; long-range/finesse bonus.
CAM: passing/combination play + long shots/finesse + positioning/composure.
Inside winger: acceleration/runs + finishing + finesse/long shots + curve + dribbling/passing.
CDM: preserve defensive balance.

## 8. Recommendation philosophy
Best card != best transfer.

Consider:
`position validity + individual quality + chemistry impact + tactical role + gameplay fit + PlayStyles + Role+/++ + price + opportunity cost + owned alternatives`

A cheaper player that improves several chemistry links can be better than a more expensive raw-stat upgrade.

Keep sub-scores explainable, e.g.:
- upgrade_score
- style_fit_score
- chemistry_delta
- team_chemistry_delta
- role_fit_score
- market_value_score
- coins_per_upgrade_point

Avoid one opaque magic score.

## 9. Contextual squad snapshot (NOT permanent state)
At the time this brief was written, recent XI was 4-2-1-3:
GK Diogo Costa
RB Trent Alexander-Arnold
CB Éder Militão
CB Ibrahima Konaté
LB Cucurella
CDM Khéphren Thuram
CDM Nicolò Barella
CAM Dani Olmo
RW Kingsley Coman
ST Lautaro Martínez
LW Linda Caicedo

Recent chemistry:
Costa 0; Trent 3; Militão 3; Konaté 3; Cucurella 3; Khéphren 2; Barella 2; Olmo 3; Coman 1; Lautaro 2; Caicedo 2. Total 24/33.

This is only historical context. Ignore it automatically after a newer export is imported.

At that moment RW/Coman was the clearest transfer target. GK Costa had 0 chemistry but was a strong base card and was not necessarily the first place to spend. Approximate budget was 83k, but budget must always be editable.

## 10. Empirical user performance
Actual games/goals/assists can matter. Do not automatically remove a card that performs exceptionally well for the user merely because another card has higher OVR/GG rating. Account for sample size.

## 11. FUT.GG rating
Use GG rating as one signal, not the answer. Also compare detailed attributes, weak foot, skill moves, body/height where relevant, PlayStyles, roles, chemistry, price, exact position and gameplay fit.

## 12. Market/external data
Future market module should discover purchasable candidates and current-ish prices.

Evaluate data sources for ToS/legal access, reliability, freshness, rate limits/API availability and data quality. Do not implement aggressive scraping by default. Prefer documented/public sources where possible and cache results.

Use a provider abstraction, e.g. `MarketProvider.search(...)`.

Distinguish owned, market, historical and loan cards. Never confuse them.

## 13. Hypothetical transfer simulation
Make this first-class.

For `Coman -> Candidate X`:
1. clone current squad
2. insert exact candidate into exact slot
3. validate position
4. recompute chemistry for all XI
5. compare with baseline
6. apply chemistry-dependent stat boosts only if verified
7. compare tactical-role suitability
8. calculate budget impact
9. return structured delta

Result should include candidate chemistry, old/new team chemistry, per-player chemistry changes, style/role fit, price and remaining budget.

## 14. Multi-transfer optimization
Eventually support: “I have 83k; improve my team.”

This differs from finding the single best player under 83k. Later compare combinations under a total budget. Do not build a complex optimizer in milestone 1; merely keep interfaces compatible with it.

## 15. Suggested repository
```text
fc27-squad-assistant/
├── README.md
├── PROJECT_CONTEXT.md
├── .gitignore
├── .env.example
├── extension/
│   └── existing-working-exporter/
├── fixtures/
│   └── sanitized_exports/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── importers/
│   │   ├── chemistry/
│   │   ├── squad/
│   │   ├── recommendations/
│   │   ├── market/
│   │   ├── tactics/
│   │   └── ai/
│   └── tests/
├── frontend/
└── docs/
    ├── architecture.md
    ├── chemistry.md
    ├── exporter-schema.md
    └── roadmap.md
```

SQLite is a reasonable local persistence choice when needed.

## 16. Early UI concept
Design is intentionally unfinished.

Possible home:
- Import latest FUT.GG export
- Current squad + chemistry + editable coin budget
- Squad Analysis
- Owned Upgrades
- Buyable Players
- Transfer Planner
- Tactics

Clicking RW could show current card, chemistry, Owned Replacements, Players to Buy and Compare.

Candidate table can eventually show:
Player | Price | GG | Chem | Team Chem | Style Fit | Role | Value

Do not heavily polish UI until importer and chemistry are trustworthy.

## 17. AI integration
AI comes after deterministic core is useful. App should work without AI for imports, squad display, chemistry, filtering and comparisons.

Send concise structured context to the LLM rather than huge raw exports.

Design provider interface so OpenAI, Anthropic or local Ollama can be swapped. Keep secrets in environment variables/secure storage and never commit them.

## 18. Extension integration
Initially manual JSON import is preferred.

Later possibilities:
- extension -> localhost API
- extension -> watched local directory

Do not break/rewrite the known-good extension while building the app. Copy/version it separately.

## 19. Importer
Importer should validate version/fields, tolerate optional/null data, preserve raw JSON, create immutable snapshot ID, normalize internal models, record timestamps, identify active squad and exact card instances.

Suggested snapshot metadata:
snapshot_id, exported_at, imported_at, exporter_version, raw_file_hash, active.

Newest active snapshot alone powers recommendations unless user explicitly selects history.

## 20. Conceptual models
Derive final schemas from actual fixtures, but likely entities include:

PlayerCard: instance_id, ea/base IDs, name, OVR, GG, positions, nation/league/club, rarity/chemistry profile, attributes, PlayStyles/+, Roles+/++, tradeability, purchase price, loan duration, games/goals/assists.

SquadSlot: formation position, player instance, chemistry, chemistry style, role, focus.

Squad: formation, manager, XI, bench, tactic.

CandidateEvaluation: candidate, position_valid, candidate chemistry, team chemistry before/after, per-player chemistry changes, style fit, role fit, stat delta, price, remaining budget, value score, warnings.

## 21. Testing
Prioritize:
- JSON parsing
- snapshot ownership isolation
- exact position eligibility
- chemistry
- hypothetical substitutions
- budget arithmetic
- candidate filtering
- loans
- manager effects
- special chemistry profiles

Use real sanitized exporter fixtures where possible.

## 22. Explainability
App should explain why A ranks above B, e.g.:
+ RW valid
+ 3 chemistry
+ raises another player 2->3
+ Finesse Shot+
+ better long shots
+ appropriate Role++
+ cheaper
- slightly slower

Avoid opaque rankings. Logs must never contain secrets/tokens.

## 23. Lessons already learned
1. Old ownership data causes mistakes: latest snapshot only.
2. Position validity comes before recommendation.
3. Chemistry requires whole-XI simulation.
4. OVR is insufficient.
5. Do not spend the entire budget merely because it exists.
6. Actual user performance matters.
7. Never let an LLM invent numeric role mappings.

## 24. Development milestones
### M0 — bootstrap
Initialize Git, README, this context file, gitignore/env example, copy existing extension unchanged, establish backend/test environment.

### M1 — importer
JSON -> validation -> normalized models -> current snapshot -> CLI/debug summary.
CLI should print players owned, formation, XI, bench, current chemistry, manager and tactic. No AI.

### M2 — position/squad engine
Exact position eligibility, formation slots, owned-player substitution simulation and before/after comparison.

### M3 — chemistry engine
Research/implement verified FC27 chemistry rules and validate against golden exports. Do not enable chemistry-sensitive recommendations until tests pass.

### M4 — basic local UI
Import JSON, display squad, click card, owned alternatives, compare.

### M5 — market provider
Research reliable source; provider abstraction + cache/rate limiting.

### M6 — buyable-player recommendations
market -> position -> budget -> chemistry -> style -> role -> value ranking.

### M7 — AI scout
Optional LLM interpretation. Deterministic numeric results remain authoritative.

### M8 — multi-transfer planner
Optimize combinations under total budget.

## 25. Do NOT build yet
No cloud accounts, subscriptions, public hosting, mobile app, EA transfer automation, complicated microservices, elaborate ML, giant vector DB, social features, polished design system, autonomous web agents, or automatic buying/selling.

Build a strong local core first.

## 26. Instructions to the coding agent
If you are ChatGPT/Claude/Codex reading this:

First inspect the repository and this file. If a working extension exists, DO NOT rewrite it.

Unless the user explicitly requests more, bootstrap only:
1. repo structure
2. README
3. backend skeleton
4. importer
5. normalized models
6. importer/ownership tests
7. CLI/debug command loading an exporter JSON and printing the exact current squad

Do not attempt the whole roadmap in one pass.

Behavior:
- make small testable changes
- preserve working behavior
- prefer typed models
- keep provider interfaces replaceable
- TODO uncertain FC27 rules instead of inventing them
- never fabricate chemistry rules, role mappings, market prices or endpoints
- never commit secrets
- never call private EA UT endpoints
- never automate transfer-market actions
- actual exporter fixtures are authoritative for schema
- ask before major irreversible architecture choices if requirements remain ambiguous

A good first session ends with something like:
`python -m app.cli import path/to/export.json`
producing a trustworthy current-club/squad summary.

That is enough. Do not rush into AI/frontend.

## 27. Immediate manual-analysis context
Manual analysis may continue independently while development waits.

At writing time:
- RW/Kingsley Coman is the immediate position under investigation.
- User wants purchasable alternatives, not only owned cards.
- Chemistry must be considered before declaring an upgrade.
- User does not want to spend the entire ~83k budget on one card without a strong reason.
- Long shots and finesse shots are important.
- Latest exporter JSON, not chat memory, must be checked before owned-player claims.

## 28. Open design questions
Decide gradually:
- desktop/web-local/Electron/Tauri approach
- frontend/backend frameworks
- exact chemistry implementation
- reliable market source(s)
- refresh cadence
- scoring weights
- Role+/++ modeling and verified ID maps
- chemistry-style boosts
- OpenAI vs Anthropic vs Ollama vs selectable providers
- future extension->localhost integration
- historical snapshot UI
- multiple user/gameplay profiles

Do not block early development on these.

## 29. Product principle
The app should answer:

**“What change makes my actual squad better for the way I actually play, given my actual budget?”**

—not merely:

**“Which card has the highest overall?”**
