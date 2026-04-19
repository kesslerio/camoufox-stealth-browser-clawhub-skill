---
title: refactor: tighten stealth-browser skill packaging after skillcraft audit
type: refactor
status: completed
date: 2026-04-19
---

# refactor: tighten stealth-browser skill packaging after skillcraft audit

## Overview

Ship a focused follow-up PR that improves `shared/stealth-browser` as an OpenClaw skill without reworking the underlying runtime migration. The patch should tighten the skill contract around hostile-site browser automation, make state ownership and gotchas explicit, and add the missing skill-level validation scripts so the repo is stronger by skillcraft standards.

## Problem Frame

The recent NixOS-default migration fixed the runtime story, but the repo still has several skill-quality gaps. The current skill contract mixes the main browser-stealth job with a secondary `curl_cffi` API lane, the docs partially blur who owns browser state, the skill does not have a dedicated gotchas surface, and the repo lacks skill-level lint/discovery checks. Those are not runtime bugs; they are packaging and maintainability gaps that make the skill weaker to route, review, and evolve.

This follow-up should stay narrow. It should improve the skill as a skill, not reopen the runtime migration. Browser runtime behavior should remain NixOS-first with distrobox fallback, and `curl-api.py` should remain in the repo unless implementation reveals a clean zero-risk split. The main job is to make the repo easier to discover, safer to interpret, and easier to validate.

## Requirements Trace

- R1. Tighten the primary skill contract so discovery centers on hostile-site browser automation rather than a mixed browser-plus-API story.
- R2. Keep the repo as a single skill for now, but demote the `curl_cffi` lane from the primary skill promise to a clearly secondary or legacy adjunct.
- R3. Make state ownership explicit: the skill itself is stateless, while wrapped runtimes own their profile/cache locations.
- R4. Add concrete gotchas and assumption-breakers that correct likely operator or model mistakes.
- R5. Add skill-level validation scripts covering packaging and discovery, not just runtime adapter behavior.
- R6. Keep the patch scoped to a focused PR that does not redesign `camoufox-nixos`, replace `curl-api.py`, or change the core browser runtime order.

## Scope Boundaries

- Do not change the browser runtime order or reopen the NixOS-default migration.
- Do not split `curl-api.py` into a separate skill in this PR.
- Do not redesign the host-native `camoufox-nixos` contract.
- Do not add new browser primitives or runtime features.
- Do not replace the existing adapter tests for fetch/session/runtime selection.

### Deferred to Separate Tasks

- Extract `curl_cffi` into a sibling skill if future usage shows that the mixed repo structure still causes discovery confusion.
- Add CI automation around skill-level validation if this repo gains a broader contributor workflow.
- Revisit cross-platform packaging if macOS or Windows support becomes a real requirement rather than a documentation concern.

## Context & Research

### Relevant Code and Patterns

- `SKILL.md` currently leads with a mixed browser-and-API story: it describes the browser lane accurately, but still gives substantial first-class space to the `curl_cffi` lane.
- `README.md` repeats the same mixed framing, so repo discovery still points at two adjacent capabilities instead of one clearly primary job.
- `scripts/curl-api.py` is a self-contained helper and does not currently need redesign; the problem is how prominently the skill advertises it.
- `scripts/setup.sh` still teaches both browser and API setup, so it must be aligned carefully with any contract narrowing.
- The repo has runtime adapter tests (`tests/runtime-selection.sh`, `tests/camoufox-fetch-adapter.sh`, `tests/camoufox-session-adapter.sh`) but no skill-level packaging checks such as `scripts/lint-skill.sh` or `scripts/test-discovery.sh`.
- The repo has no local `AGENTS.md`, `CLAUDE.md`, or `docs/solutions/` archive, so this plan should stay grounded in the repo’s own structure and the recent migration work rather than expecting richer local process artifacts.

### Institutional Learnings

- The runtime migration intentionally kept one skill and one browser-default story. This follow-up should preserve that decision rather than splitting the repo under audit pressure.
- The migration already chose to keep `curl_cffi` separate from the browser lane conceptually. The remaining gap is presentation and validation, not architecture.
- The post-merge review found one real runtime bug and it was already fixed. The remaining issues are mostly contract clarity, scope boundaries, and contributor ergonomics.

### External References

- No external research was necessary. The work is about skill packaging quality inside a small local repo, and the relevant constraints are already visible in the current files and the recent migration history.

## Key Technical Decisions

- **Keep one skill, narrow the promise:** the PR should not split the repo, but it should make the primary discovery surface clearly about hostile-site browser automation.
- **Demote, do not delete, the API lane:** `scripts/curl-api.py` stays available, but docs should present it as an adjunct helper rather than equal billing with the browser lane.
- **Document state ownership honestly:** the skill should explicitly say it owns no durable state; the wrapped runtimes own their respective profile and cache directories.
- **Add a dedicated gotchas surface:** concrete footguns belong in either a `references/gotchas.md` file or an equivalent focused section, not scattered only across troubleshooting prose.
- **Add skill-level checks inside the repo:** this patch should add the expected validation scripts for lint/discovery so contributors can verify the skill contract directly.
- **Do not change core browser behavior while tightening packaging:** the patch is successful only if it improves routing and maintainability without introducing runtime churn.

## Open Questions

### Resolved During Planning

- Should this PR split `curl_cffi` into a separate skill?
  - No. Keep one skill for now and narrow the primary contract instead.
- Should the patch touch runtime adapter code again?
  - Only if needed for doc/validation alignment. Core runtime behavior is not the target.
- Should gotchas live inline or in a dedicated reference?
  - Use a dedicated reference if it keeps `SKILL.md` lean; otherwise add a clearly bounded gotchas section. The plan assumes a dedicated reference is the cleaner default.
- Should discovery validation be purely manual?
  - No. Add repo-local scripts so discovery expectations are testable like the adapter behavior already is.

### Deferred to Implementation

- Whether the dedicated gotchas surface is best named `references/gotchas.md`, `references/usage-gotchas.md`, or folded into `README.md` if a new file proves unnecessary.
- Whether `scripts/test-discovery.sh` should validate a phrase fixture file, a small inline case matrix, or both.
- Whether `scripts/lint-skill.sh` should remain narrowly repo-specific or be shaped for reuse across neighboring skill repos.

## Output Structure

    SKILL.md
    README.md
    references/
      gotchas.md
    scripts/
      lint-skill.sh
      setup.sh
      test-discovery.sh
    tests/
      discovery-cases.txt
      runtime-selection.sh
      camoufox-fetch-adapter.sh
      camoufox-session-adapter.sh

## Implementation Units

- [x] **Unit 1: Add skill-level lint and discovery validation**

**Goal:** Give contributors a direct way to validate the skill package itself, not just the runtime adapter scripts.

**Requirements:** R5, R6

**Dependencies:** None

**Files:**
- Create: `scripts/lint-skill.sh`
- Create: `scripts/test-discovery.sh`
- Create: `tests/discovery-cases.txt`
- Modify: `README.md`
- Modify: `SKILL.md`

**Approach:**
- Add a lightweight lint script that checks the skill packaging contract: frontmatter presence, required metadata, lean `SKILL.md` size, and existence of referenced support files that the docs depend on.
- Add a discovery test script backed by a small curated set of expected trigger phrases and non-goal phrases so contributors can validate that the repo’s public description still points at the right category of work.
- Document these scripts in the repo so future PRs can include them in verification output alongside the existing adapter tests.
- Keep the scripts intentionally narrow and repo-specific; they should verify the promises this repo actually makes rather than inventing a generic skill framework.

**Patterns to follow:**
- Existing shell-based test style in `tests/*.sh`
- Existing repo-local verification command style from the recent migration PR

**Test scenarios:**
- Happy path: `scripts/lint-skill.sh` passes when the skill frontmatter, referenced files, and expected packaging constraints are satisfied.
- Edge case: the discovery cases include both positive phrases (stealth browser, blocked site, persistent login) and negative/non-primary phrases so over-broad descriptions are easier to catch.
- Error path: the discovery script fails clearly when the primary contract drifts back toward a mixed or vague description.
- Integration: repo documentation for verification includes both the skill-level checks and the existing adapter tests as complementary layers.

**Verification:**
- A contributor can validate discovery and packaging directly from the repo without relying only on informal manual review.

- [x] **Unit 2: Narrow the primary skill contract and discovery surface**

**Goal:** Make the skill easier for OpenClaw and operators to route correctly by centering the contract on hostile-site browser automation.

**Requirements:** R1, R2, R6

**Dependencies:** Unit 1

**Files:**
- Modify: `SKILL.md`
- Modify: `README.md`
- Modify: `scripts/setup.sh`
- Test: `scripts/lint-skill.sh`
- Test: `scripts/test-discovery.sh`
- Test: `tests/discovery-cases.txt`

**Approach:**
- Tighten the frontmatter description in `SKILL.md` so the primary trigger language emphasizes hostile-site browser automation, login/session reuse, and anti-bot browsing rather than a mixed browser-plus-API capability.
- Reframe `README.md` so browser workflows remain the headline use case and the `curl_cffi` lane is described as a secondary helper or legacy adjunct, not a co-equal promise.
- Keep `scripts/setup.sh` aligned with the same framing: browser runtime first, API helper lane second, with no language that implies the skill’s main job is broader than it is.
- Preserve the single-skill decision by explicitly describing the API lane as “still present, not primary” instead of pretending it does not exist.

**Patterns to follow:**
- Current top-level skill docs structure in `SKILL.md` and `README.md`
- Existing runtime precedence language already established by the migration

**Test scenarios:**
- Happy path: the `SKILL.md` description clearly matches requests about blocked browser automation, hostile sites, login reuse, or stealth browsing.
- Edge case: the docs still mention `curl_cffi`, but in a secondary role that does not overshadow the primary browser-stealth contract.
- Error path: setup guidance does not imply that installing the API lane alone satisfies the main browser skill promise.
- Integration: `SKILL.md`, `README.md`, and `scripts/setup.sh` tell the same high-level story about what this skill primarily does.

**Verification:**
- A reader scanning only the frontmatter description and opening sections understands that this is primarily a browser-stealth skill, with `curl_cffi` as a secondary adjunct.

- [x] **Unit 3: Add explicit state-ownership and gotchas guidance**

**Goal:** Remove ambiguity about who owns browser state and surface the non-obvious footguns in one place.

**Requirements:** R3, R4, R6

**Dependencies:** Units 1-2

**Files:**
- Modify: `SKILL.md`
- Modify: `README.md`
- Create: `references/gotchas.md`
- Test: `scripts/lint-skill.sh`

**Approach:**
- Rewrite the state sections so they explicitly distinguish between skill-owned state and runtime-owned state: the skill owns no durable state, while `camoufox-nixos` and the legacy distrobox lane own their respective profile/cache locations.
- Add a focused gotchas reference covering the mistakes most likely to recur: browser lane vs API lane confusion, headed login requirements, Linux-only fallback assumptions, host-native state location expectations, and legacy-only features such as cookie import behavior.
- Link that gotchas reference from both `SKILL.md` and `README.md` so the information is easy to find without bloating the main skill body.

**Patterns to follow:**
- Existing troubleshooting style in `SKILL.md`
- Existing focused references pattern under `references/`

**Test scenarios:**
- Happy path: the docs make it clear that runtime-owned profile/cache paths are not skill-owned state.
- Edge case: a reader can distinguish “browser state persists” from “the skill persists its own state.”
- Error path: gotchas explicitly warn against assuming macOS/Windows portability or assuming old profile-path semantics on the host-native lane.
- Integration: the gotchas and state sections reinforce, rather than contradict, the narrower browser-first contract from Unit 1.

**Verification:**
- The repo has one clear answer to “where does state live?” and one dedicated place where recurring non-obvious mistakes are documented.

- [x] **Unit 4: Align legacy API helper messaging with the tightened skill boundary**

**Goal:** Keep the repo honest about `curl-api.py` without turning it into a first-class routing signal for the skill.

**Requirements:** R2, R6

**Dependencies:** Units 1-3

**Files:**
- Modify: `README.md`
- Modify: `SKILL.md`
- Modify: `scripts/setup.sh`
- Test: `scripts/lint-skill.sh`
- Test: `scripts/test-discovery.sh`

**Approach:**
- Move API-lane guidance into a clearly secondary section or appendix so it remains discoverable for contributors but does not dominate the main skill story.
- Ensure setup guidance distinguishes “browser runtime readiness” from “optional API helper lane” so contributors do not conflate the two.

**Patterns to follow:**
- Current separation between browser scripts and `curl-api.py`
- Current troubleshooting/notes structure in `README.md`

**Test expectation:** none -- this unit is documentation and positioning work around an existing helper, not a behavioral feature change.

**Verification:**
- The API helper remains usable, but the repo no longer advertises it as part of the skill’s primary routing promise.

## System-Wide Impact

- **Interaction graph:** skill discovery text -> operator docs -> setup guidance -> browser scripts and secondary API helper.
- **Error propagation:** packaging ambiguity today causes routing and expectation errors rather than runtime crashes; this patch should reduce those interpretation failures.
- **State lifecycle risks:** unclear ownership of profile/cache locations leads operators to diagnose the wrong layer when persistence behaves unexpectedly.
- **API surface parity:** browser runtime behavior should remain unchanged; this plan only narrows how the repo describes and validates itself.
- **Integration coverage:** skill-level validation needs to coexist with the existing adapter tests so discovery, docs, and runtime behavior are covered together.
- **Unchanged invariants:** the repo still supports NixOS-first browser automation with distrobox fallback, and `curl-api.py` remains available.

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| The patch over-corrects and hides useful API helper documentation | Keep `curl_cffi` documented in a clearly secondary section instead of deleting it |
| Discovery checks become brittle or gamed by wording churn | Keep the fixture set small, focused, and tied to clear routing intent rather than broad keyword matching |
| Docs drift between `SKILL.md`, `README.md`, and `scripts/setup.sh` | Update all three surfaces in the same PR and validate them together in `scripts/lint-skill.sh` |
| Packaging cleanup accidentally reopens runtime behavior | Keep runtime adapter code changes out of scope unless strictly needed for doc/help-text alignment |

## Documentation / Operational Notes

- This should land as one focused PR after the merged runtime migration, not as part of another runtime change.
- The PR description should explicitly frame the work as “skill packaging quality follow-up” rather than a feature or runtime migration.
- Verification in the PR should include both new skill-level checks and the existing adapter tests so reviewers can see the packaging/runtime split clearly.

## Sources & References

- Related code: `SKILL.md`, `README.md`, `scripts/setup.sh`, `scripts/curl-api.py`
- Existing runtime validation: `tests/runtime-selection.sh`, `tests/camoufox-fetch-adapter.sh`, `tests/camoufox-session-adapter.sh`
- Related merged work: PR `#9`
