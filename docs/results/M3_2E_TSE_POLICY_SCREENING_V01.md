# M3.2e TSE-wide deterministic policy screening v0.1

Status: **MEASURED / ACCEPTANCE CANDIDATE**

Issue: #55
Generator commit: `2242b323989719787ba847e5e18c452a175bb213`

## Purpose

This result scales the completed #43 company-level policy-screening semantics across the exact #53/#54 canonical TSE snapshot. It does not add a new policy profile, Evidence source, entity resolver, benchmark, portfolio method, return calculation, or trading authority.

The decision vocabulary remains `EXCLUDE / WATCH / NONE`. `NONE` is **not** PASS, clean, safe, peaceful, approved, or evidence that relevant activity does not exist.

## Fixed inputs

- Canonical TSE entities: **3,707**
- #53 confirmed corporate-number identities: **3,699**
- #53 unresolved identities: **8**
- #53 identity semantic SHA-256: `a74d81a27e19d3a746e1d3669842f7284f43ac45d3ae8601cdd6741d7ebe6733`
- #54 coverage cells: **18,535** (`3,707 × 5`)
- #54 coverage semantic SHA-256: `ccc77af755a6022031d5aca6bc8fbd1f53b7136eb460c0fd69d17e07263f0941`
- Current example policy profiles: **3**

## Existing Evidence path reused

The measured run used the existing Ministry of Defense procurement adapter and the existing contract-subject classifier only. The fixed MOD snapshot contained **88 observations**; the existing strong-ID gate resolved **86** of them.

For each resolved observation #55 reuses two existing narrow claims:

- the MOD contract fact from `observation_to_claim()`;
- the contract-subject classification from `classification_claim()`.

This generated **172 claims** before TSE-universe intersection. The exact TSE intersection was **10 MOD observations across 7 TSE entities**, therefore **20 claims mapped** into the canonical TSE universe and **152 remained outside it**.

The existing subject classifier produced, for those 10 TSE-linked observations:

- `UNKNOWN`: **9**;
- `DUAL_USE`: **1**;
- `MILITARY_SPECIFIC`: **0**.

No new classifier, keyword, policy rule, fuzzy rescue, or name-only entity link was introduced for #55.

## Measured screening result

All **3,707 companies × 3 profiles = 11,121 company/profile views** were emitted.

| Profile | EXCLUDE | WATCH | NONE |
| --- | ---: | ---: | ---: |
| `example:controversial-weapons-only` | 0 | 0 | 3,707 |
| `example:strict-military-avoidance` | 0 | 7 | 3,700 |
| `example:transparency-first` | 0 | 7 | 3,700 |

The narrow controversial-weapons profile produces no decisive result because this snapshot contains no controversial-weapons claim. The strict profile routes the existing `UNKNOWN` contract-subject classifications through its existing uncertainty behavior, producing WATCH for the seven affected TSE entities. The transparency-first profile independently surfaces the existing MOD Evidence as WATCH. No `MILITARY_SPECIFIC` classification exists in the measured TSE intersection, so no current profile emits EXCLUDE here.

This is a measured policy result, not a finding that the other companies are free of military, political-finance, human-rights, or other relevant activity. The #54 coverage states remain part of every local view.

Pairwise decision differences on the same Evidence snapshot are:

- controversial-weapons-only vs strict-military-avoidance: **7 companies**;
- controversial-weapons-only vs transparency-first: **7 companies**;
- strict-military-avoidance vs transparency-first: **0 companies**.

## Unresolved identities

All **8** #53 unresolved TSE identities remain represented. Across the three profiles this is **24 views**. Every one has:

- `decision = NONE`;
- no linked claim results;
- explicit unresolved identity/coverage state rather than a fabricated negative match.

The #43 scaling fix is deliberately narrow: a missing confirmed bridge is accepted only when the company still carries `unresolved_identity` coverage and has no resolved `observed` or `no_match` coverage. A bridge-less company with resolved coverage fails closed.

## Traceability

There are **14 non-NONE company/profile views** in the measured result. A direct row-level verification found **0 traceability failures**: every non-NONE view has a consequential claim result retaining a claim ID, Evidence source ID, and either a matched policy rule reference or an explicit uncertainty reference.

The existing uncertainty and normal-rule paths remain separately visible. `UNKNOWN`, `DISPUTED`, and `EXPIRED` are not coerced to confirmed facts.

## Determinism

The measured #55 semantic screening SHA-256 is:

`aff7ea3437d2b19282e96b095e989f54d68bb7443eafc66e170396a9bcf2a17c`

The full 3,707-company run was executed twice from the same #53 identity artifact, #54 coverage artifact, MOD observations, and policy profiles. Both runs produced the same semantic hash and the same decision distributions.

The aggregate public JSON from both runs was also byte-identical. Its file SHA-256 is:

`69db76a92815e9a757fabc3f81844c4e4d8b9a4a132dc1edfb18219a693b77ba`

The committed aggregate machine-readable result is `docs/results/M3_2E_TSE_POLICY_SCREENING_MANIFEST_V01.json`.

## Public/private boundary

The complete **11,121 row-level views remain local-only** with the authorized #53/#54 local artifacts. They are not committed or uploaded as CI artifacts.

The committed aggregate manifest was explicitly checked to contain:

- no `views` payload;
- no `entity_id` field;
- no 13-digit corporate-number value;
- only aggregate counts, policy identifiers/hashes, comparison counts, semantic hashes, and interpretation metadata.

This preserves the existing JPX/source redistribution boundary. #55 does not change Source Registry rights or authorize redistribution of row-level identity, coverage, or procurement links.

## Future benchmark-weight interface

#55 exposes a deterministic weight-coverage summary interface for later mapped benchmark weights. It can report represented/unrepresented weight, unresolved-identity weight, and EXCLUDE/WATCH/NONE weight by profile.

It does **not** calculate returns, portfolio performance, tracking error, or construct a portfolio. Those remain later M3 work.

## Verification

At generator commit `2242b323989719787ba847e5e18c452a175bb213`:

- local full suite: **166 passed**;
- PR #74 `tests`: **SUCCESS**;
- PR #74 `user-policy`: **SUCCESS**;
- PR #74 `m2-screening`: **SUCCESS**.

The dedicated #55 workflow added with this acceptance record runs the focused company-screening, TSE-screening, and CLI contracts on pull requests that touch this path. Final PR-head CI must be green before merge.

## Acceptance against Issue #55

- Every #54 entity × every current profile exists: **PASS — 11,121 / 11,121 views**.
- Existing #43 EXCLUDE/WATCH/NONE semantics are preserved: **PASS**.
- `NONE` remains distinct from PASS/clean/safe: **PASS**.
- The 8 unresolved identities remain represented without forced matching: **PASS**.
- Every measured non-NONE result is traceable to claim/source/rule or uncertainty: **PASS — 14 / 14 views**.
- Existing UNKNOWN/DISPUTED/EXPIRED/no-evidence behavior remains covered by regression tests: **PASS**.
- Real rerun reproduces the semantic payload: **PASS — identical `aff7ea34...` hash**.
- Row-level results remain local while aggregate verification is publishable: **PASS**.
- A future benchmark-weight reporting interface exists without return calculation: **PASS**.

Subject to final PR-head CI and review-thread checks, Issue #55 meets its stated definition of done.
