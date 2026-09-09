"""Validate private royal-review decisions without generating or changing them.

The three domains follow KOSHITSU_SEPARATE_AXES_V6.md. This module checks
storage and its explicit implications, not whether a judgment fits the body.
Body reading, attribution, target equivalence and evidence remain independent
editorial checks. Packet identity, hashes and reviewer separation belong to
the enclosing run validator. No existing aggregate stance is produced.
"""

SCHEMA_VERSION = "koshitsu-three-domains-v1"

# Stable coded comparison fields from the independently checked five examples.
# Free-text targets and other_evaluations still need a semantic comparison;
# equality of this tuple alone is not approval or agreement on every domain.
CORE_FIELDS = (
    "is_relevant", "is_opinion", "attribution", "reform_target",
    "current_package_stance", "provisions", "succession", "unknown_fields",
    "uncertain", "evidence_sufficient", "aggregation_route",
    "existing_stance_candidate",
)
_FIELDS = frozenset(CORE_FIELDS) | {
    "index", "main_issue", "mentioned_reform_target", "other_succession",
    "other_evaluations", "reason",
}
_AXES = frozenset({
    "male_line_only", "male_only", "female_sovereign", "female_line",
    "named_successor_aiko",
})
_STANCES = frozenset({"support", "oppose", "mixed", "unexpressed", "unknown"})


def _require(condition, path, detail):
    if not condition:
        raise ValueError(f"{path}: {detail}")


def _object(value, fields, path):
    _require(type(value) is dict, path, "must be an object")
    _require(set(value) == fields, path, "missing or unexpected fields")


def _text(value, path):
    _require(type(value) is str and bool(value.strip()), path,
             "must be a nonblank string")


def _enum(value, choices, path):
    # Check type before set membership, so malformed JSON arrays/objects raise
    # ValueError instead of leaking an unhashable-value TypeError.
    _require(type(value) is str and value in choices, path, "invalid value")


def validate_decision(row) -> None:
    """Accept exactly one v1 decision, or raise ValueError without mutating it.

    Extra keys, including legacy stance fields, are rejected. Unknown values
    require uncertainty and insufficient evidence in all three domains. Other
    uncertainty/evidence reasons may exist without unknown, so the reverse
    implication is intentionally not inferred. Array order is preserved.
    """
    _object(row, _FIELDS, "decision")
    _require(type(row["index"]) is int and row["index"] >= 0, "index",
             "must be a nonnegative integer")
    for key in ("is_relevant", "uncertain", "evidence_sufficient"):
        _require(type(row[key]) is bool, key, "must be a boolean")
    _require(row["is_opinion"] is None or type(row["is_opinion"]) is bool,
             "is_opinion", "must be a boolean or null")
    _enum(row["attribution"], {"author", "third_party_only", "mixed", "unknown"},
          "attribution")
    _enum(row["reform_target"], {
        "current_package", "specific_provision", "alternative_reform",
        "general_reform", "unexpressed", "unknown",
    }, "reform_target")
    _enum(row["current_package_stance"], _STANCES, "current_package_stance")
    for key in ("main_issue", "reason"):
        _text(row[key], key)
    for key in ("mentioned_reform_target", "other_succession"):
        if row[key] is not None:
            _text(row[key], key)
    for key in ("provisions", "other_evaluations", "unknown_fields"):
        _require(type(row[key]) is list, key, "must be an array")

    succession = row["succession"]
    _object(succession, _AXES, "succession")
    for key, value in succession.items():
        _enum(value, _STANCES, f"succession.{key}")

    unknown = {key for key in (
        "is_opinion", "attribution", "reform_target", "current_package_stance",
    ) if row[key] is None or row[key] == "unknown"}
    unknown.update(f"succession.{key}" for key, value in succession.items()
                   if value == "unknown")
    for value in row["unknown_fields"]:
        _text(value, "unknown_fields[]")
    _require(set(row["unknown_fields"]) == unknown and
             len(row["unknown_fields"]) == len(unknown), "unknown_fields",
             "must list exactly the unknown major fields, without duplicates")
    any_unknown = bool(unknown)

    for index, item in enumerate(row["provisions"]):
        path = f"provisions[{index}]"
        _object(item, {"target", "stance"}, path)
        _text(item["target"], f"{path}.target")
        _enum(item["stance"], _STANCES - {"unexpressed"}, f"{path}.stance")
        any_unknown |= item["stance"] == "unknown"

    for index, item in enumerate(row["other_evaluations"]):
        path = f"other_evaluations[{index}]"
        _object(item, {"kind", "target", "assessment", "time_scope"}, path)
        _text(item["target"], f"{path}.target")
        _enum(item["kind"], {
            "argument_validity", "historical_legitimacy", "feasibility", "tradition",
        }, f"{path}.kind")
        _enum(item["assessment"], {"affirmed", "denied", "mixed", "unknown"},
              f"{path}.assessment")
        _enum(item["time_scope"], {"historical", "present_or_future", "unspecified"},
              f"{path}.time_scope")
        any_unknown |= item["assessment"] == "unknown"

    _require(not any_unknown or
             (row["uncertain"] is True and row["evidence_sufficient"] is False),
             "evidence flags", "unknown in any domain requires uncertainty and insufficient evidence")
    _require(succession["female_sovereign"] != "support" or
             succession["male_only"] == "oppose", "succession",
             "female eligibility support requires male-only opposition")
    _require(succession["named_successor_aiko"] != "support" or
             succession["female_sovereign"] == "support", "succession",
             "named successor support requires female eligibility support")
    _enum(row["aggregation_route"], {"criteria_needed"}, "aggregation_route")
    _require(row["existing_stance_candidate"] is None, "existing_stance_candidate",
             "must remain null; aggregate adoption is outside this schema")
