"""Generate explicit, typed fluent methods from the vendored public Rust builder.

This is build-time maintenance tooling, never runtime method injection. Run with
--check in CI to detect source drift; regenerate after updating the core snapshot.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "python/textforge/__init__.py"


def render() -> str:
    """Translate the supported Rust method shapes, failing on unknown signatures."""
    api = (ROOT / "vendor/textforge/src/api/mod.rs").read_text(encoding="utf-8")
    registry = (ROOT / "vendor/textforge/src/globals/table.rs").read_text(encoding="utf-8")
    syntax = {
        match[1]: re.findall(r"SyntaxToken::(String|Usize|Token)\b", match[2])
        for match in re.finditer(
            r'(?s)\(\s*"(\w+)",\s*0x[0-9a-fA-F]+,.*?\[([^\]]*)\]\s*,?\s*\)', registry
        )
    }
    trait = api.split("pub trait TextForgeConditionalMethods")[0]
    pattern = r"(?ms)^    fn (\w+)\(([^;]*?)\) -> Result<&mut Self, TextForgeError> \{\n(.*?)^    }"
    definitions = []
    for match in re.finditer(pattern, trait):
        name, signature, implementation = match.groups()
        token_match = re.search(r"Box::new\((\w+)::", implementation)
        if token_match is None:
            raise ValueError(f"Unknown Rust builder implementation: {name}")
        token = token_match[1]
        parameters = re.findall(r"(\w+): impl Into<(ValType|TokenWrapper)>", signature)
        kinds = syntax[token]
        if len(parameters) != len(kinds) or any(
            target == "TokenWrapper" and kind != "Token"
            for (_, target), kind in zip(parameters, kinds, strict=False)
        ):
            raise ValueError(f"Parameter mismatch for {name}: {parameters}, {kinds}")
        docs_match = re.search(r"((?:    ///[^\n]*\n|[ \t]*\n)*)$", trait[: match.start()])
        paragraphs = (
            re.split(r"\n\s*\n", re.sub(r"(?m)^    /// ?", "", docs_match[0]).strip())
            if docs_match
            else []
        )
        # Newer core docs open with "MNEMONIC — summary"; older ones with a bare
        # title such as "TBS - Trim Both Sides", followed by the description.
        first = " ".join(paragraphs[0].split()) if paragraphs else ""
        summary = first.split(" — ", 1)[1] if " — " in first else ""
        second = " ".join(paragraphs[1].split()) if len(paragraphs) > 1 else ""
        if "```" in second:
            second = ""
        if summary and second and not second.startswith(summary):
            description = f"{summary} {second}"
        else:
            description = second or summary
        if not description:
            description = {
                "mut_var": "Assign a new value to a mutable execution-context variable.",
                "eval": "Evaluate an expression and store its result in the named variable.",
                "iter": "Run one inner instruction repeatedly, using the Rust iter semantics.",
                "remove_pattern": "Remove every match of the pattern from the input.",
                "end": "End the current logical group, subject to core structural validation.",
            }.get(name, name.replace("_", " ").capitalize() + ".")
        description = description.replace('"', "'").replace("**", "")
        # Rustdoc intra-doc links mean nothing in Python: keep their text.
        description = re.sub(r"\[(`[^`]+`)\]\([^)]*\)", r"\1", description)
        description = textwrap.fill(description, width=84, break_on_hyphens=False).replace(
            "\n", "\n        "
        )
        typed = []
        values = []
        for (parameter, target), kind in zip(parameters, kinds, strict=True):
            annotation, converter = {
                "String": ("str | Variable", "_text"),
                "Usize": ("int | str | Variable", "_numeric"),
                "Token": ("Pipeline | Instruction | Variable", "_instruction"),
            }[kind]
            if target == "TokenWrapper":
                annotation, converter = "Pipeline | Instruction", "_token"
            if name in {"val", "var", "mut_var"} and parameter == "var_value":
                annotation, converter = "str | int | Variable", "_value"
            typed.append(f"{parameter}: {annotation}")
            values.append(f'{converter}({parameter}, "{parameter}")')
        args = ", ".join(["self", *typed])
        call = ", ".join([f'"{token}"', *values])
        definitions.append(
            f"    def {name}({args}) -> Pipeline:\n"
            f'        """{description}\n\n'
            f"        Matches Rust ``TextForgeBuilderMethods::{name}``.\n"
            f'        """\n'
            f"        return self._operation({call})\n"
        )
    if not definitions:
        raise ValueError("No Rust builder methods found")
    return "\n".join(definitions)


def main() -> None:
    """Write static methods or verify that the committed generated code is current."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    current = OUTPUT.read_text(encoding="utf-8")
    begin = "    # BEGIN GENERATED BUILDER METHODS\n"
    end = "    # END GENERATED BUILDER METHODS\n"
    prefix, rest = current.split(begin)
    _, suffix = rest.split(end)
    candidate = prefix + begin + render() + end + suffix
    generated = subprocess.check_output(
        [sys.executable, "-m", "ruff", "format", "--stdin-filename", str(OUTPUT), "-"],
        input=candidate,
        text=True,
    )
    if args.check:
        if OUTPUT.read_text(encoding="utf-8") != generated:
            raise SystemExit("Fluent API is stale: run python scripts/generate_builder.py")
    else:
        OUTPUT.write_text(generated, encoding="utf-8")


if __name__ == "__main__":
    main()
