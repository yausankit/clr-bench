"""Deterministic transport compatibility for the adapted EvoSkill proposer.

The upstream implementation uses a structured-output schema; it does not have
this XML/key-value parser. This module preserves proposal values from one full
JSON object, one JSON code block, or one explicit <proposal> block. It never
repairs a proposal's meaning or invokes a model. Official optional defaults are
validated but not inserted into the returned mapping.
"""
from functools import lru_cache
import json
from pathlib import Path
import re
import runpy


FIELDS = {"action", "target_skill", "proposed_skill", "justification",
          "related_iterations"}
from common import OLD as _METHODS_ROOT
DEFAULT_SCHEMA = Path(_METHODS_ROOT) / "upstream/EvoSkill/src/schemas/skill_proposer.py"


class ProposalFormatError(ValueError):
    pass


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProposalFormatError(f"Duplicate proposal key: {key}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ProposalFormatError(f"Non-JSON numeric constant: {value}")


DECODER = json.JSONDecoder(object_pairs_hook=_unique_object,
                           parse_constant=_reject_constant, strict=False)


def _object(text):
    try:
        value = DECODER.decode(text)
    except json.JSONDecodeError as error:
        raise ProposalFormatError(str(error)) from error
    if not isinstance(value, dict):
        raise ProposalFormatError("Expected exactly one proposal object")
    return value


def _key_values(text):
    """Accept explicit keys and JSON-literal values, not general YAML."""
    result = {}
    remaining = text.strip()
    while remaining:
        match = re.match(r"(?:-\s+)?([A-Za-z_][A-Za-z_0-9]*)\s*:\s*", remaining)
        if not match:
            raise ProposalFormatError("Expected a named proposal field")
        key = match.group(1)
        if key in result:
            raise ProposalFormatError(f"Duplicate proposal key: {key}")
        try:
            value, end = DECODER.raw_decode(remaining[match.end():])
        except json.JSONDecodeError as error:
            raise ProposalFormatError(f"Invalid literal in field {key}: {error}") from error
        suffix = remaining[match.end() + end:]
        # No unquoted strings, trailing prose, commas, or field-value guessing.
        if suffix.strip() and not re.match(r"[ \t]*\r?\n", suffix):
            raise ProposalFormatError(f"Unexpected text after field {key}")
        result[key] = value
        remaining = suffix.strip()
    return result


def _extract(text):
    if not isinstance(text, str) or not text.strip():
        raise ProposalFormatError("Proposal response must be nonempty text")
    text = re.sub(r"```(?:json)?[ \t]*\r?\n?|```", "", text.strip())
    # R3: first complete JSON object; original supplied field values are unchanged.
    for match in re.finditer(r"\{", text):
        try:
            value, end = DECODER.raw_decode(text[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value, "first_json_object_strict_false"
    if text.startswith("```"):
        match = re.fullmatch(r"```(?:json)?[ \t]*\r?\n(.*?)\r?\n?```", text, re.S)
        if not match:
            raise ProposalFormatError("Expected a single complete JSON code block")
        return _object(match.group(1).strip()), "json_code_block"
    if text.startswith("{") or text.startswith("["):
        return _object(text), "json"
    if text.count("<proposal>") != 1 or text.count("</proposal>") != 1:
        raise ProposalFormatError("Expected exactly one explicit proposal block")
    match = re.search(r"<proposal>(.*?)</proposal>", text, re.S)
    if not match:
        raise ProposalFormatError("Malformed proposal block")
    outside = text[:match.start()] + text[match.end():]
    # Keep analysis in the original response, but never parse it as a candidate.
    for tag in ("analysis", "brainstorming"):
        outside = re.sub(fr"<{tag}>.*?</{tag}>", "", outside, flags=re.S)
    if outside.strip():
        raise ProposalFormatError("Unrecognized text outside the unique proposal")
    return _key_values(match.group(1)), "proposal_key_values"


@lru_cache(maxsize=None)
def _official_model(schema_file):
    # Load only the upstream schema file, without creating a harness or client.
    return runpy.run_path(str(schema_file))["SkillProposerResponse"]


def parse_proposal_with_metadata(text, *, schema_file=None):
    proposal, encoding = _extract(text)
    unknown = set(proposal) - FIELDS
    if unknown:
        raise ProposalFormatError(f"Unknown proposal fields: {sorted(unknown)}")
    # Existing adapter requires an explicit action; do not infer create/edit.
    if "action" not in proposal:
        raise ProposalFormatError("Missing explicit action")
    model = _official_model(str(schema_file or DEFAULT_SCHEMA))
    try:
        validated = model.model_validate(proposal, strict=True)
    except ValueError as error:
        raise ProposalFormatError(f"Official proposal schema: {error}") from error
    output = validated.model_dump(exclude_unset=True)
    if output != proposal:
        raise ProposalFormatError("Schema validation changed supplied field values")
    return {
        "proposal": output,
        "encoding": encoding,
        "supplied_fields": sorted(proposal),
        "defaults_inserted": False,
        "semantic_repair": False,
        "upstream_schema": str(schema_file or DEFAULT_SCHEMA),
        "parser_is_upstream": False,
    }


def parse_proposal(text, *, schema_file=None):
    """Return the unchanged fields of one schema-valid proposal."""
    return parse_proposal_with_metadata(text, schema_file=schema_file)["proposal"]
