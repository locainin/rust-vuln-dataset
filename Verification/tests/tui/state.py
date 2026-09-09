from Verification.verifier.tui.state import InteractiveState


def check_navigation_stops_at_case_bounds():
    state = InteractiveState(case_count=3)

    state.previous_case()
    assert state.case_index == 0

    state.next_case()
    state.next_case()
    state.next_case()
    assert state.case_index == 2

    state.previous_case()
    assert state.case_index == 1


def check_navigation_resets_vertical_scroll():
    state = InteractiveState(case_count=3, case_index=1, scroll=8)

    state.next_case()

    assert state.case_index == 2
    assert state.scroll == 0


def check_diff_toggle_returns_to_the_top():
    state = InteractiveState(case_count=2, scroll=12)

    state.toggle_diffs()

    assert state.show_diffs is True
    assert state.scroll == 0

    state.toggle_diffs()
    assert state.show_diffs is False


def check_vertical_scroll_stays_inside_case_bounds():
    state = InteractiveState(case_count=1)

    state.scroll_by(7, max_scroll=5)
    assert state.scroll == 5

    state.scroll_by(-20, max_scroll=5)
    assert state.scroll == 0

    state.go_to_end(max_scroll=9)
    assert state.scroll == 9

    state.go_to_top()
    assert state.scroll == 0

    state.scroll_by(1, max_scroll=0)
    assert state.scroll == 0

    state.go_to_end(max_scroll=0)
    assert state.scroll == 0
