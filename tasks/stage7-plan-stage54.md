# Stage 7 Plan: Department Activity Page Prototype (Private)

## Overview
Creating a prototype of the department activity page without 3D, without JS, keyboard-only navigation, merging duplicate sections.

## Session Plan (細かく分割)

### Session 1: Setup & Data Preparation
- [ ] Copy existing `bukatsu-chiiki-planet.html` as staging area
- [ ] Verify `build_planet_data.py` produces correct output for `bukatsu-chiiki`
- [ ] Extract current structure: planet, landing panel, sections
- [ ] Review `quality/research/bukatsu-chiiki-stage3-claims-draft.md` for claim posts data
- [ ] Review `quality/research/bukatsu-chiiki-stage4-sunk-continents-draft.md` for sunk continents

### Session 2: Structure Simplification (No 3D, No JS)
- [ ] Remove 3D/WebGL dependent code
- [ ] Replace canvas-based planet with static image or ASCII/HTML representation
- [ ] Ensure keyboard navigation order: planet → landing panel → sections → back
- [ ] Remove all JS event handlers, replace with semantic HTML
- [ ] Verify 375px width: no horizontal scroll

### Session 3: Section Integration (Merge duplicates)
- [ ] Identify duplicate sections: 注目ポイント, 論点カード, 分布, 潮目, 詳細表
- [ ] Merge into: Landing panel +横断整理
- [ ] Landing panel per issue: ratio, 4-stance breakdown, representative reasons, primary sources, unknowns
- [ ] Cross-organization section: editorial findings across all issues
- [ ] Remove manual hand-written duplicates

### Session 4: Landing Panel Design
- [ ] 4 stances breakdown with actual counts (tiếng: 移行支持 / 慎重・反対 / 条件付き・改善要求 / 中立・情報)
- [ ] Ratio display: e.g., 283件 / 意見993件中28.5%
- [ ] Central question, include/exclude boundary
- [ ] Representative reasons per stance (not mechanical mirror)
- [ ] Link to primary sources
- [ ] What's not yet known
- [ ] Expression strength value and definition link

### Session 5: Cross-organization Summary
- [ ] Editorial discoveries across all issues (from planet-bukatsu-chiiki.md 136-146)
- [ ] Structure: concise paragraphs, no bullets
- [ ] Key findings: e.g., "Teacher work style shows 58% support but reverses in educational purpose"

### Session 6: Accessibility & Keyboard Only
- [ ] Tab order: planet → landing → summary → back → exit
- [ ] Escape key returns to overview
- [ ] "Back to overview" button visible
- [ ] Motion reduction setting respected (reduce motion → skip animation, show static)
- [ ] Keyboard only: all interactive elements reachable, activatable

### Session 7: Generate & Verify
- [ ] Run `python3 scripts/build_planet_data.py --topic bukatsu-chiiki`
- [ ] Verify output HTML has no AI confidence/classification text
- [ ] Run 2x generation: diff should be 0
- [ ] Run verification tests: `verify_theme_page bukatsu-chiiki`
- [ ] Check `docs/` has no diff
- [ ] Check `data/public/` has no diff

### Session 8: Final Review & Handoff
- [ ] Review complete HTML structure
- [ ] Document any intentional deviations from spec
- [ ] Prepare for merge into main branch
- [ ] Note: this is PRIVATE prototype — not for public deployment yet

## Key Metrics
- ✅ 3D/WebGL: removed
- ✅ JS: removed / vanilla only
- ✅ Keyboard navigation: full support
- ✅ 375px width: no horizontal scroll
- ✅ No AI confidence text in public output
- ✅ 2x generation diff: 0
- ✅ Tests pass: verify_theme_page bukatsu-chiiki

## Notes
- Stage 7 is PRIVATE prototype for internal review
- Public deployment waits until Stage 8-12 completion
- Same input → same output (deterministic)
- No duplication of hand-written sections