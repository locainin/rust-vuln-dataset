# Tokenize Rust macro and attribute text without changing source bytes

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    # A token with source offsets and optional balanced children

    kind: str
    text: str
    children: tuple = ()
    start: int = 0
    end: int = 0


def tokenize(text: str) -> tuple[Token, ...]:
    # Parse a bounded token tree while retaining exact source ranges
    # Delimiters are tracked recursively so nested macro arguments stay intact
    opening = {"(": ")", "[": "]", "{": "}"}
    closing = set(opening.values())

    def parse(index: int, expected: str | None = None):
        result = []
        while index < len(text):
            # Whitespace is not part of the rendered token stream
            if text[index].isspace():
                index += 1
                continue
            # Comments are skipped while their surrounding source offsets remain stable
            if text.startswith("//", index):
                newline = text.find("\n", index + 2)
                index = len(text) if newline < 0 else newline + 1
                continue
            if text.startswith("/*", index):
                end = index + 2
                nesting = 1
                while end < len(text) and nesting:
                    if text.startswith("/*", end):
                        nesting += 1
                        end += 2
                    elif text.startswith("*/", end):
                        nesting -= 1
                        end += 2
                    else:
                        end += 1
                if nesting:
                    raise ValueError("unterminated Rust comment")
                index = end
                continue

            character = text[index]
            # A closing delimiter belongs to the nearest open group
            if character in closing:
                if expected != character:
                    raise ValueError("unbalanced Rust token tree")
                return result, index + 1
            if character in opening:
                # Store group content separately for quoted macro extraction
                children, end = parse(index + 1, opening[character])
                result.append(
                    Token(
                        "group",
                        character,
                        tuple(children),
                        index,
                        end,
                    )
                )
                index = end
                continue
            if (
                # Lifetimes are atoms, not the start of a character literal
                character == "'"
                and index + 1 < len(text)
                and (text[index + 1].isalpha() or text[index + 1] == "_")
            ):
                end = index + 2
                while end < len(text) and (text[end].isalnum() or text[end] == "_"):
                    end += 1
                # A closing quote makes this a character literal instead
                if end >= len(text) or text[end] != "'":
                    result.append(Token("atom", text[index:end], (), index, end))
                    index = end
                    continue
            if character in {'"', "'"}:
                # Quoted literals must stay one opaque token
                quote = character
                end = index + 1
                while end < len(text):
                    if text[end] == "\\":
                        end += 2
                        continue
                    if text[end] == quote:
                        end += 1
                        break
                    end += 1
                else:
                    raise ValueError("unterminated Rust literal")
                result.append(Token("atom", text[index:end], (), index, end))
                index = end
                continue
            if text.startswith('r"', index) or re.match(r"r#+\"", text[index:]):
                # Raw strings can contain arbitrary delimiter characters
                match = re.match(r"r(#+)?\"", text[index:])
                if match is None:
                    raise ValueError("invalid raw Rust literal")
                hashes = match.group(1) or ""
                terminator = '"' + hashes
                end = text.find(terminator, index + len(match.group(0)))
                if end < 0:
                    raise ValueError("unterminated raw Rust literal")
                end += len(terminator)
                result.append(Token("atom", text[index:end], (), index, end))
                index = end
                continue
            if character.isalpha() or character == "_":
                # Rust identifiers include Unicode letters; ASCII rules suffice here
                end = index + 1
                while end < len(text) and (text[end].isalnum() or text[end] == "_"):
                    end += 1
                result.append(Token("atom", text[index:end], (), index, end))
                index = end
                continue
            if character.isdigit():
                # Keep numeric suffixes and separators attached to the literal
                end = index + 1
                while end < len(text) and (text[end].isalnum() or text[end] in "._"):
                    end += 1
                result.append(Token("atom", text[index:end], (), index, end))
                index = end
                continue
            if text.startswith("=>", index):
                # Match the only multi-character punctuation needed by item identity
                result.append(Token("atom", "=>", (), index, index + 2))
                index += 2
                continue
            result.append(Token("atom", character, (), index, index + 1))
            index += 1
        if expected is not None:
            raise ValueError("unbalanced Rust token tree")
        return result, index

    tokens, end = parse(0)
    if end != len(text):
        raise ValueError("trailing Rust token tree")
    return tuple(tokens)


def render(tokens: tuple[Token, ...] | list[Token]) -> str:
    # Render tokens without reformatting their syntax
    # Rendering is used only for stable declaration identity
    closing = {"(": ")", "[": "]", "{": "}"}
    parts = []
    for token in tokens:
        if token.kind == "group":
            parts.extend((token.text, render(token.children), closing[token.text]))
        else:
            parts.append(token.text)
    return "".join(parts)
