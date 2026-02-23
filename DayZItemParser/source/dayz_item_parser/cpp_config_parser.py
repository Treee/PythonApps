from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Token:
    kind: str
    value: str


_SINGLE = set("{}[]();:=,\n")


def _strip_comments(src: str) -> str:
    out: list[str] = []
    i = 0
    n = len(src)
    in_str = False
    str_quote = ""

    while i < n:
        ch = src[i]

        if in_str:
            out.append(ch)
            if ch == str_quote:
                in_str = False
                str_quote = ""
            i += 1
            continue

        if ch in ('"', "'"):
            in_str = True
            str_quote = ch
            out.append(ch)
            i += 1
            continue

        if ch == "/" and i + 1 < n and src[i + 1] == "/":
            i += 2
            while i < n and src[i] != "\n":
                i += 1
            continue

        if ch == "/" and i + 1 < n and src[i + 1] == "*":
            i += 2
            while i + 1 < n and not (src[i] == "*" and src[i + 1] == "/"):
                i += 1
            i += 2
            continue

        out.append(ch)
        i += 1

    return "".join(out)


def _tokenize(src: str) -> list[Token]:
    tokens: list[Token] = []
    i = 0
    n = len(src)

    while i < n:
        ch = src[i]

        if ch.isspace():
            i += 1
            continue

        if ch in ('"', "'"):
            quote = ch
            i += 1
            buf = []
            while i < n:
                c = src[i]
                if c == quote:
                    i += 1
                    break
                buf.append(c)
                i += 1
            tokens.append(Token("string", "".join(buf)))
            continue

        if ch in _SINGLE:
            tokens.append(Token("punc", ch))
            i += 1
            continue

        if ch.isdigit() or (ch == "-" and i + 1 < n and src[i + 1].isdigit()):
            start = i
            i += 1
            while i < n and (src[i].isdigit() or src[i] in ".eE+-"):
                if src[i] in "+-" and src[i - 1] not in "eE":
                    break
                i += 1
            tokens.append(Token("number", src[start:i]))
            continue

        # identifier-ish (also captures things like DayZ class names)
        start = i
        i += 1
        while i < n:
            c = src[i]
            if c.isspace() or c in _SINGLE or c in ('"', "'"):
                break
            i += 1
        tokens.append(Token("ident", src[start:i]))

    return tokens


class _Parser:
    def __init__(self, tokens: list[Token]):
        self._t = tokens
        self._i = 0

    def _peek(self) -> Optional[Token]:
        if self._i >= len(self._t):
            return None
        return self._t[self._i]

    def _pop(self) -> Token:
        tok = self._peek()
        if tok is None:
            raise ValueError("Unexpected EOF")
        self._i += 1
        return tok

    def _accept(self, *, kind: Optional[str] = None, value: Optional[str] = None) -> Optional[Token]:
        tok = self._peek()
        if tok is None:
            return None
        if kind is not None and tok.kind != kind:
            return None
        if value is not None and tok.value != value:
            return None
        self._i += 1
        return tok

    def _expect(self, *, kind: Optional[str] = None, value: Optional[str] = None) -> Token:
        tok = self._accept(kind=kind, value=value)
        if tok is None:
            got = self._peek()
            raise ValueError(f"Expected {kind or ''} {value or ''} but got {got}")
        return tok

    def parse_document(self) -> Dict[str, Any]:
        items: list[dict] = []
        while self._peek() is not None:
            node = self._parse_stmt()
            if node is not None:
                items.append(node)
        return {"items": items}

    def _parse_stmt(self) -> Optional[Dict[str, Any]]:
        tok = self._peek()
        if tok is None:
            return None

        if tok.kind == "ident" and tok.value == "class":
            return self._parse_class()

        if tok.kind == "ident":
            return self._parse_assignment_or_unknown()

        # skip unknown token
        self._pop()
        return None

    def _parse_class(self) -> Dict[str, Any]:
        self._expect(kind="ident", value="class")
        name = self._expect(kind="ident").value

        base = None
        if self._accept(kind="punc", value=":") is not None:
            base = self._expect(kind="ident").value

        # Forward declaration: `class Foo;`
        if self._accept(kind="punc", value=";") is not None:
            return {"type": "class_decl", "name": name, "base": base}

        self._expect(kind="punc", value="{")

        body_items: list[dict] = []
        while True:
            if self._accept(kind="punc", value="}") is not None:
                break
            if self._peek() is None:
                break
            node = self._parse_stmt()
            if node is not None:
                body_items.append(node)

        self._accept(kind="punc", value=";")
        return {"type": "class", "name": name, "base": base, "items": body_items}

    def _parse_assignment_or_unknown(self) -> Optional[Dict[str, Any]]:
        key = self._expect(kind="ident").value

        is_array = False
        if self._accept(kind="punc", value="[") is not None:
            self._expect(kind="punc", value="]")
            is_array = True

        if self._accept(kind="punc", value="=") is None:
            # Not an assignment; consume until ';' or block boundary.
            while self._peek() is not None and self._peek().value not in (";", "}"):
                self._pop()
            self._accept(kind="punc", value=";")
            return {"type": "unknown", "head": key}

        value = self._parse_value()
        self._accept(kind="punc", value=";")

        return {"type": "assign", "key": key, "array": is_array, "value": value}

    def _parse_value(self) -> Any:
        tok = self._peek()
        if tok is None:
            return None

        if tok.kind == "string":
            self._pop()
            return tok.value

        if tok.kind == "number":
            self._pop()
            s = tok.value
            try:
                if any(c in s for c in ".eE"):
                    return float(s)
                return int(s)
            except ValueError:
                return s

        if tok.kind == "ident":
            self._pop()
            if tok.value in ("true", "false"):
                return tok.value == "true"
            return tok.value

        if tok.kind == "punc" and tok.value == "{":
            return self._parse_brace_list()

        # fallback: consume one token
        self._pop()
        return tok.value

    def _parse_brace_list(self) -> List[Any]:
        self._expect(kind="punc", value="{")
        items = []
        while True:
            if self._accept(kind="punc", value="}") is not None:
                break
            if self._peek() is None:
                break
            if self._accept(kind="punc", value=",") is not None:
                continue
            items.append(self._parse_value())
            self._accept(kind="punc", value=",")
        return items


def parse_config_cpp(text: str) -> Dict[str, Any]:
    """Parse a DayZ/Enfusion-style config.cpp into a JSON-friendly structure.

    This is intentionally conservative: it focuses on class blocks and simple assignments
    and keeps unknown statements as placeholders so the output can be improved iteratively.
    """

    cleaned = _strip_comments(text)
    tokens = _tokenize(cleaned)
    parser = _Parser(tokens)
    return parser.parse_document()


def filter_scope2_only(document: Dict[str, Any]) -> Dict[str, Any]:
    """Return a pruned document that only retains classes with `scope = 2`.

    Behavior:
    - Keeps any class that directly contains an assignment `scope = 2`.
    - For non-scope2 classes, keeps only child classes that (recursively) contain scope2.
    - Drops non-class statements (assignments, forward decls) in non-scope2 branches.
    """

    def class_has_scope2(node: Dict[str, Any]) -> bool:
        for child in node.get("items", []) or []:
            if child.get("type") == "assign" and child.get("key") == "scope":
                return child.get("value") == 2
        return False

    def prune_node(node: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(node, dict):
            return None
        if node.get("type") != "class":
            return None

        if class_has_scope2(node):
            return node

        kept_children: List[Dict[str, Any]] = []
        for child in node.get("items", []) or []:
            pruned = prune_node(child)
            if pruned is not None:
                kept_children.append(pruned)

        if not kept_children:
            return None

        return {
            "type": "class",
            "name": node.get("name"),
            "base": node.get("base"),
            "items": kept_children,
        }

    pruned_items: List[Dict[str, Any]] = []
    for item in document.get("items", []) or []:
        pruned = prune_node(item)
        if pruned is not None:
            pruned_items.append(pruned)

    return {"items": pruned_items}


def extract_scope2_classnames(document: Dict[str, Any]) -> List[str]:
    """Extract class names that have an explicit `scope = 2` assignment.

    Returns a stable-order list (deduped) of class names.
    """

    def class_has_scope2(node: Dict[str, Any]) -> bool:
        for child in node.get("items", []) or []:
            if child.get("type") == "assign" and child.get("key") == "scope":
                return child.get("value") == 2
        return False

    out: List[str] = []
    seen = set()

    def walk(node: Any) -> None:
        if not isinstance(node, dict):
            return
        if node.get("type") != "class":
            return

        if class_has_scope2(node):
            name = node.get("name")
            if isinstance(name, str) and name and name not in seen:
                seen.add(name)
                out.append(name)

        for child in node.get("items", []) or []:
            walk(child)

    for item in document.get("items", []) or []:
        walk(item)

    return out


@dataclass(frozen=True)
class _Tok:
    kind: str  # ident | number | punc
    value: str


def _iter_tokens_no_strings(src: str):
    """Tokenize for structural scanning.

    - Skips all string literal contents entirely (emits no string tokens)
    - Skips // and /* */ comments
    - Emits: identifiers, numbers, and punctuation ({ } ; : = [ ] ,)
    """

    i = 0
    n = len(src)

    while i < n:
        ch = src[i]

        # whitespace
        if ch.isspace():
            i += 1
            continue

        # comments
        if ch == "/" and i + 1 < n and src[i + 1] == "/":
            i += 2
            while i < n and src[i] != "\n":
                i += 1
            continue
        if ch == "/" and i + 1 < n and src[i + 1] == "*":
            i += 2
            while i + 1 < n and not (src[i] == "*" and src[i + 1] == "/"):
                i += 1
            i += 2
            continue

        # strings (skip)
        if ch in ('"', "'"):
            quote = ch
            i += 1
            while i < n:
                c = src[i]
                if c == quote:
                    i += 1
                    break
                i += 1
            continue

        # punctuation we care about
        if ch in "{};:=[],":
            yield _Tok("punc", ch)
            i += 1
            continue

        # number
        if ch.isdigit() or (ch == "-" and i + 1 < n and src[i + 1].isdigit()):
            start = i
            i += 1
            while i < n and (src[i].isdigit() or src[i] in ".eE+-"):
                if src[i] in "+-" and src[i - 1] not in "eE":
                    break
                i += 1
            yield _Tok("number", src[start:i])
            continue

        # identifier-ish
        start = i
        i += 1
        while i < n:
            c = src[i]
            if c.isspace() or c in "{};:=[],\"'" or c == "/":
                break
            i += 1
        yield _Tok("ident", src[start:i])


def extract_scope2_cfg_children(text: str) -> List[str]:
    """Extract item class names from immediate children of CfgVehicles/CfgWeapons/CfgMagazines.

    Rules (based on vanilla patterns):
    - Only considers `class CfgVehicles { ... }`, `class CfgWeapons { ... }`, and `class CfgMagazines { ... }` (case-insensitive).
    - Only considers *immediate* child classes inside those blocks.
    - Only returns child classes that have `scope = 2` at the child's top level.
    - Ignores forward declarations (`class Foo;`).
    """

    # Some vanilla configs vary the casing (e.g. cfgWeapons), so match case-insensitively.
    parents = {"cfgvehicles", "cfgweapons", "cfgmagazines"}
    excluded_bases = {
        "HouseNoDestruct",
        "HouseNoHestruct",
        "BaseBuildingBase",
        "ShelterBase",
        "PlantBase",
        "UndergroundStash",
        "Fireplace",
    }
    excluded_names = {
        "UndergroundStash",
        "PileOfWoodenPlanks",
        "EasterEgg",
        "Fireplace",
        "HandcuffsLocked",
        "Raycaster",
        "ObsoleteFishingRod",
        "DoorTestCamera",
        "Cassette",
        "GardenPlotGreenhouse",
        "GardenPlotPolytunnel",
        "GardenPlot",
    }
    out: List[str] = []
    seen = set()

    toks = list(_iter_tokens_no_strings(text))
    i = 0
    depth = 0

    def inherits_from(name: str, ancestor: str, base_map: Dict[str, Optional[str]]) -> bool:
        cur = name
        seen_local = set()
        while True:
            base = base_map.get(cur)
            if not base:
                return False
            if base == ancestor:
                return True
            if base in seen_local:
                return False
            seen_local.add(base)
            cur = base

    def peek(offset: int = 0) -> Optional[_Tok]:
        j = i + offset
        if j < 0 or j >= len(toks):
            return None
        return toks[j]

    while i < len(toks):
        tok = toks[i]

        if tok.kind == "punc":
            if tok.value == "{":
                depth += 1
            elif tok.value == "}":
                depth = max(0, depth - 1)
            i += 1
            continue

        # look for top-level: class CfgVehicles { ... }
        if depth == 0 and tok.kind == "ident" and tok.value == "class":
            name_tok = peek(1)
            if not name_tok or name_tok.kind != "ident":
                i += 1
                continue

            parent_name = name_tok.value
            if parent_name.lower() not in parents:
                i += 1
                continue

            # Advance to opening '{'
            i += 2
            while i < len(toks) and not (toks[i].kind == "punc" and toks[i].value in ("{", ";")):
                i += 1
            if i >= len(toks) or toks[i].value != "{":
                # forward decl or malformed
                i += 1
                continue

            # Enter parent body
            depth += 1
            parent_depth = depth
            i += 1

            # Collect immediate child base relationships for within-file inheritance checks
            base_map: Dict[str, Optional[str]] = {}
            candidates: List[Dict[str, Any]] = []

            # Scan immediate children
            while i < len(toks) and depth >= parent_depth:
                tok2 = toks[i]
                if tok2.kind == "punc":
                    if tok2.value == "{":
                        depth += 1
                    elif tok2.value == "}":
                        depth -= 1
                    i += 1
                    continue

                if depth == parent_depth and tok2.kind == "ident" and tok2.value == "class":
                    child_name_tok = peek(1)
                    if not child_name_tok or child_name_tok.kind != "ident":
                        i += 1
                        continue
                    child_name = child_name_tok.value

                    child_base: Optional[str] = None

                    # Advance to '{' or ';' of the child decl
                    i += 2
                    while i < len(toks) and not (toks[i].kind == "punc" and toks[i].value in ("{", ";")):
                        # Capture `class Child : Base` (only the first base identifier)
                        if toks[i].kind == "punc" and toks[i].value == ":":
                            base_tok = toks[i + 1] if i + 1 < len(toks) else None
                            if base_tok and base_tok.kind == "ident":
                                child_base = base_tok.value
                        i += 1

                    if i >= len(toks):
                        break

                    if toks[i].kind == "punc" and toks[i].value == ";":
                        # forward declaration, not an item
                        i += 1
                        continue

                    if toks[i].kind == "punc" and toks[i].value == "{":
                        # Enter child body and look for scope=2 at top level
                        depth += 1
                        child_depth = depth
                        i += 1
                        scope2 = False

                        while i < len(toks) and depth >= child_depth:
                            t = toks[i]
                            if t.kind == "punc":
                                if t.value == "{":
                                    depth += 1
                                elif t.value == "}":
                                    depth -= 1
                                i += 1
                                continue

                            if depth == child_depth and t.kind == "ident" and t.value == "scope":
                                if (
                                    peek(1)
                                    and peek(1).kind == "punc"
                                    and peek(1).value == "="
                                    and peek(2)
                                    and peek(2).kind == "number"
                                    and peek(2).value.strip() == "2"
                                ):
                                    scope2 = True
                            i += 1

                        base_map[child_name] = child_base
                        candidates.append({
                            "name": child_name,
                            "base": child_base,
                            "scope2": scope2,
                        })
                        continue

                i += 1

            # Apply filters (including within-block inheritance)
            for cand in candidates:
                name = cand.get("name")
                base = cand.get("base")
                scope2 = cand.get("scope2")

                if not scope2 or not isinstance(name, str) or not name:
                    continue
                if name in excluded_names:
                    continue
                if name.endswith("Kit"):
                    continue
                if (
                    name.endswith("_Opened")
                    or name.endswith("_Open")
                    or name.endswith("_Applied")
                ):
                    continue
                if name.endswith("_Standalone"):
                    continue
                if "dummy" in name.lower():
                    continue
                if base in excluded_bases:
                    continue
                # Exclude anything inheriting fireplace types within this file/block
                if inherits_from(name, "FireplaceBase", base_map):
                    continue
                if name in seen:
                    continue
                seen.add(name)
                out.append(name)

            continue

        i += 1

    return out
