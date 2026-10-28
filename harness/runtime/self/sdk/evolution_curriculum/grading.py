"""Historical output parsing and scalar grading, independent of any harness."""
import ast
import math
import re


def equal(expected, actual):
    if type(expected) in (int, float):
        return type(actual) in (int, float) and math.isfinite(actual) and math.isclose(expected, actual, rel_tol=1e-7, abs_tol=1e-6)
    return type(expected) is type(actual) and expected == actual


def parse(text, language):
    code = text.strip()
    if "```" in code:
        langs = "sql|sqlite" if language == "sql" else "python|py"
        blocks = re.findall(r"```(?:" + langs + r")?[ \t]*\n(.*?)```", code, re.I | re.S)
        if len(blocks) != 1 or code.count("```") != 2:
            raise ValueError("Expected exactly one code block or plain source")
        code = blocks[0].strip()
    if language == "sql":
        leading = re.sub(r"\A(?:\s|--[^\n]*(?:\n|$)|/\*.*?\*/)*", "", code, flags=re.S)
        if not re.match(r"(?i)^(SELECT|WITH)\b", leading):
            raise ValueError("Final answer must be SELECT/WITH query")
    else:
        tree = ast.parse(code)
        if not any(isinstance(x, ast.FunctionDef) and x.name == "solve" for x in tree.body):
            raise ValueError("No top-level solve definition")
    return code
