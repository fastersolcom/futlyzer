# Exporter schema (v0.4.0)

Envelope: `extension/existing-working-exporter/background.js`.
Verified against the real export `fixtures/sanitized_exports/FC27_aaa_2026-10-10.json`.

```
exporter, exporterVersion "0.4.0", exportedAt (ISO, Z), source, privacy
capturedPages: [{page, count, url}]
counts: {players, startingXI, substitutes}
squad:
  title, activeFormationId (str, e.g. "36"), managerId, managerNationId, managerLeagueId
  startingXI / substitutes: {group FIELD|SUBSTITUTE, positionIdx, playerEaId, ggClubPlayerId (str),
      positionOverride, evolutionOverrideId, isUntradeableOverride, rarityOverrideEaId,
      + enriched: name, chemistryPoints, chemistryStyle, rolesPlus, rolesPlusPlus, playstyles, playstylesPlus}
  activeTacticSummary: {code, title, formationId, positionRoles[{roleId, focusName, positionUniqueId}],
      buildUpStyleId, defensiveApproachId, isCustomDefensiveApproach, customDefensiveApproachValue, ...}
tactics: {url, decoded {..., positionRoles, lineHeight}, exportCodeResponse}
players[]: FUT.GG gg-club items
  id "<userId>-<n>" (exact owned card), userId, eaId, chemistryPoints, chemistryStyle (e.g. 250),
  purchasedFor, gamesPlayed, goals, assists, isUntradeable, marketPrice, isInActiveSquad
  playerDef: eaId, basePlayerEaId, commonName/firstName/lastName, overall, ggRating,
    position, alternativePositionIds, nationEaId, leagueEaId, clubEaId, skillMoves, weakFoot, height,
    attribute* (35), face*, playstyles, playstylesPlus, rolesPlus, rolesPlusPlus, loanDuration,
    rarity{name, chemistryProfile{isFullChemistry, extra*Chemistry}}, chemistryStyle (different scale, e.g. 1)
```

## Verified
- XI `positionIdx` i ↔ `activeTacticSummary.positionRoles[i]` (all 11 cards eligible under this alignment).
- Position ids: see `backend/app/squad/positions.py`.
- `userId` is the only personal identifier; `backend/tools/sanitize_export.py` replaces it.

## Still unverified / TODO
- Formation id → name; slot ids for formations other than 36.
- roleId, playstyle ids, chemistryStyle ids → names.
- `chemistryProfile` semantics (special-card chemistry) — needed for M3.
- `marketPrice` shape (non-null on 11 cards).
