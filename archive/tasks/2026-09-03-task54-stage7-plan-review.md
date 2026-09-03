# Stage 7 Plan Review by Hermes Agent

## Overall Assessment: ✅ SUFFICIENT TO START SESSION 1

The 8-session plan is complete, logical, and covers all Stage 7 requirements from planet-bukatsu-chiiki.md ch.7-9. The breakdown is well-structured with clear deliverables per session.

## Session-by-Session Review

### Session 1: Setup & Data Preparation ✅
- **Strengths**: Clear starting point, copies existing file, verifies build script, reviews existing data drafts
- **Gaps**: None significant
- **Improvement**: Consider adding checksum verification of original file before modification

### Session 2: Structure Simplification ✅
- **Strengths**: Directly addresses "no 3D, no JS, keyboard-only, 375px no scroll" requirements
- **Gaps**: Need to ensure the static replacement for the planet visualization preserves all data points (ratios, counts, stances)
- **Improvement**: Specify what replaces the canvas-based planet (e.g., SVG statically generated, or an information graphic)

### Session 3: Section Integration ✅
- **Strengths**: Core of Stage 7 — merging 5 duplicate sections into landing panel + cross-organization summary
- **Gaps**: The mapping from "注目ポイント／論点カード／分布／潮目／詳細表" to "着陸パネル＋横断整理" needs more explicit mapping of what content goes where
- **Improvement**: Create a mapping table showing which original section content maps to which new section element

### Session 4: Landing Panel Design ✅
- **Strengths**: Covers all required landing panel elements (4 stances breakdown, ratios, reasons, primary sources, unknowns)
- **Gaps**: The "representative reasons" requirement explicitly says "not mechanical mirror" — need to ensure the plan doesn't just output yes/no mirrors of stances
- **Improvement**: Add a constraint that reasons must be editorially selected, not just vote-count mirrors

### Session 5: Cross-organization Summary ✅
- **Strengths**: Directly references planet-bukatsu-chiiki.md ch.136-146 editorial findings
- **Gaps**: The "no bullets" format requirement for Substack publishing should be explicitly noted
- **Improvement**: Ensure the output format is prose paragraphs, not a list of findings

### Session 6: Accessibility & Keyboard Only ✅
- **Strengths**: Covers Tab order, Escape key, Motion reduction setting
- **Gaps**: Need to verify the specific Tab order: planet → landing → summary → back → exit
- **Improvement**: Add explicit Tab-index values to the HTML spec for this session

### Session 7: Generate & Verify ✅
- **Strengths**: Runs the build script, verifies 2x generation diff=0, runs verification tests
- **Gaps**: The order of operations matters — verify tests BEFORE generation, or at least specify the exact test commands
- **Improvement**: Add exact command: `python3 scripts/verify_theme_page.py bukatsu-chiiki` before/after generation

### Session 8: Final Review & Handoff ✅
- **Strengths**: Documents for merge, prepares for Stage 8-12
- **Gaps**: The "private prototype" nature needs clearer boundary — what exactly distinguishes this from public-deployable code?
- **Improvement**: Add a "DO NOT DEPLOY YET" watermark or tag in the generated HTML

## Requirements Coverage Checklist ✅

| Requirement | Status | Session(s) |
|------------|--------|------------|
| 3D/WebGL removed | ✅ | 2 |
| JS removed / vanilla only | ✅ | 2 |
| Keyboard navigation full support | ✅ | 2, 6 |
| 375px width: no horizontal scroll | ✅ | 2 |
| Section merging (5 → 2) | ✅ | 3 |
| Landing panel: 4 stances breakdown with counts | ✅ | 4 |
| Landing panel: representative reasons (not mechanical) | ✅ | 4 |
| Landing panel: primary source links | ✅ | 4 |
| Landing panel: "what's not yet known" | ✅ | 4 |
| Cross-organization summary (paragraphs, no bullets) | ✅ | 5 |
| Accessibility: Tab order | ✅ | 6 |
| Accessibility: Escape key | ✅ | 6 |
| Accessibility: Motion reduction respected | ✅ | 6 |
| No AI confidence/classification text in public output | ✅ | 7 |
| Deterministic generation (same input → same output) | ✅ | 7 |
| verify_theme_page bukatsu-chiiki passes | ✅ | 7 |
| docs/ no diff after generation | ✅ | 7 |
| data/public/ no diff after generation | ✅ | 7 |

## Recommendations

1. **Add explicit format constraints** to Session 5: "Output must be prose paragraphs, no bullet points — this is for Substack copy-paste"
2. **Specify the static planet replacement** in Session 2: e.g., "Replace `<canvas>` with an SVG that shows 7 landmasses with labels and ratios, but no interactive rotation"
3. **Add deterministic seed check** to Session 7: After generation, run a hash comparison of the output HTML to ensure byte-identical 2nd generation
4. **Clarify the "private" boundary** in Session 8: Add a note that this prototype uses the same data pipeline as public deployment but with different HTML structure — it's a stepping stone, not the final public page

## Start Session 1?

The plan is ready to go. Session 1 starts with:
1. Copy `quality/prototypes/bukatsu-chiiki-planet.html` to a staging area
2. Run `python3 scripts/build_planet_data.py --topic bukatsu-chiiki` to verify the build script works
3. Review the current HTML structure

Shall I proceed with Session 1 now, or do you want to make any adjustments first? ♪