# Navigation state for the case review screen

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InteractiveState:
    case_count: int
    case_index: int = 0
    scroll: int = 0
    show_diffs: bool = False

    def previous_case(self) -> None:
        # Navigation stops at the first case instead of wrapping
        if self.case_index > 0:
            self.case_index -= 1
            self.scroll = 0

    def next_case(self) -> None:
        # Navigation stops at the final case instead of wrapping
        if self.case_index + 1 < self.case_count:
            self.case_index += 1
            self.scroll = 0

    def toggle_diffs(self) -> None:
        # Changing the amount of content starts the view at the top
        self.show_diffs = not self.show_diffs
        self.scroll = 0

    def scroll_by(self, amount: int, max_scroll: int) -> None:
        # The screen supplies a nonnegative limit after each draw
        self.scroll = min(max(self.scroll + amount, 0), max_scroll)

    def go_to_top(self) -> None:
        # Home always returns to the first visible line
        self.scroll = 0

    def go_to_end(self, max_scroll: int) -> None:
        # End uses the current content size supplied by the renderer
        self.scroll = max_scroll
