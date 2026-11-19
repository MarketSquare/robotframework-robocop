"""
Nesting depth of control flow blocks in Robot Framework keywords and test cases.

The depth is taken from the structure of the parsed model, not from the indentation. A block adds one level when it
is nested in another block:

* ``IF``, ``FOR``, ``WHILE`` and ``TRY`` are blocks and add a level.
* ``ELSE IF``, ``ELSE``, ``EXCEPT``, ``TRY ELSE`` and ``FINALLY`` are branches of the block they belong to, so they stay
  on the level of the block itself.
* Inline ``IF`` does not add a level. It is a single line that cannot contain another block, and it is the
  idiomatic guard clause (``IF    $x    RETURN``) that flattens nesting.
* ``GROUP`` is only a container: it adds no level, but the blocks inside are still analysed.
* Keyword calls, including the conditional BuiltIn keywords such as ``Run Keyword If``, never add a level.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from robot.api import Token
from robot.parsing.model.blocks import For, If, Try, While

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from robot.parsing.model.blocks import Keyword, TestCase
    from robot.parsing.model.statements import Node

PATH_SEPARATOR = " > "


@dataclass(frozen=True)
class DeepBlock:
    """
    Outermost block that exceeds the allowed nesting depth.

    ``depth`` is the deepest level reached inside this block, and ``path`` is the chain of blocks from the top of the
    keyword or test case down to that deepest level.
    """

    node: Node
    token_type: str
    depth: int
    path: tuple[str, ...]

    @property
    def path_text(self) -> str:
        return PATH_SEPARATOR.join(self.path)


def find_deep_blocks(node: Keyword | TestCase, max_depth: int) -> list[DeepBlock]:
    """
    Find the outermost blocks nested deeper than ``max_depth``.

    Blocks inside a reported block are not reported again: extracting the reported block into a keyword removes them
    all. Separate blocks that are too deep are all reported.
    """
    deep_blocks: list[DeepBlock] = []
    _find(node.body, (), max_depth, deep_blocks)
    return deep_blocks


def max_nesting_depth(node: Keyword | TestCase) -> int:
    """Return the deepest nesting level of the keyword or test case, ``0`` when it has no blocks."""
    return _deepest(node.body, ())[0]


def _block_info(node: Node) -> tuple[str, str] | None:
    """Return the path label and the type of the header token for a block that adds a nesting level."""
    if isinstance(node, If):
        return None if node.header.type == Token.INLINE_IF else ("IF", Token.IF)
    if isinstance(node, For):
        return "FOR", Token.FOR
    if isinstance(node, While):
        return "WHILE", Token.WHILE
    if isinstance(node, Try):
        return "TRY", Token.TRY
    return None


def _bodies(node: Node) -> Iterator[Iterable[Node]]:
    """
    Yield the body of a node and of all its branches.

    Branches are linked with ``orelse`` (``IF``) and ``next`` (``TRY``). They are walked with a loop, not with
    recursion: long ``ELSE IF`` / ``EXCEPT`` chains must not depend on the recursion limit.
    """
    link = "orelse" if isinstance(node, If) else "next"
    branch = node
    while branch is not None:
        yield getattr(branch, "body", ())
        branch = getattr(branch, link, None)


def _find(body: Iterable[Node], path: tuple[str, ...], max_depth: int, found: list[DeepBlock]) -> None:
    for child in body:
        if (info := _block_info(child)) is None:
            if not isinstance(child, If):  # inline IF holds a single statement and no block
                _find(getattr(child, "body", ()), path, max_depth, found)  # GROUP: transparent container
            continue
        label, token_type = info
        child_path = (*path, label)
        if len(child_path) > max_depth:
            depth, deepest_path = _deepest_in_block(child, child_path)
            found.append(DeepBlock(child, token_type, depth, deepest_path))
            continue
        for block_body in _bodies(child):
            _find(block_body, child_path, max_depth, found)


def _deepest_in_block(node: Node, block_path: tuple[str, ...]) -> tuple[int, tuple[str, ...]]:
    """Return the deepest level and its path inside a block, counting the block itself (``block_path``)."""
    best = (len(block_path), block_path)
    for body in _bodies(node):
        candidate = _deepest(body, block_path)
        if candidate[0] > best[0]:
            best = candidate
    return best


def _deepest(body: Iterable[Node], path: tuple[str, ...]) -> tuple[int, tuple[str, ...]]:
    best = (len(path), path)
    for child in body:
        if (info := _block_info(child)) is not None:
            candidate = _deepest_in_block(child, (*path, info[0]))
        elif isinstance(child, If):  # inline IF
            continue
        else:  # GROUP: transparent container
            candidate = _deepest(getattr(child, "body", ()), path)
        if candidate[0] > best[0]:
            best = candidate
    return best
