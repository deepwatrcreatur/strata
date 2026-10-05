# SPDX-License-Identifier: MIT
"""Live browser tabs, keyboard routing and cross-tab file transfers."""

import pytest

from harness.interaction import MODIFIER_KEYSYMS
from harness.modes import ALL_MODES


def tab(strata, name):
    return strata.wait(
        lambda: strata.window.find(role="page tab", name=name),
        f"tab {name}",
    )


def selected_tab(strata, name):
    return strata.wait(
        lambda: tab(strata, name).has_state("selected"),
        f"active tab {name}",
    )


@pytest.mark.parametrize("tenxer", [
    pytest.param(False, marks=pytest.mark.preferences(tenxer_mode=False)),
    pytest.param(True, marks=pytest.mark.preferences(tenxer_mode=True)),
])
def test_tabs_keep_locations_and_support_numbered_shortcuts(strata, tenxer):
    root = strata.fixture.root.name
    strata.select_entry("todo.txt")
    strata.keyboard.press("ctrl+t")
    strata.open_directory("archive")
    selected_tab(strata, "archive")
    ctrl, shift = MODIFIER_KEYSYMS["ctrl"], MODIFIER_KEYSYMS["shift"]
    strata.keyboard.connection.key(ctrl, True)
    strata.keyboard.connection.key(shift, True)
    try:
        strata.wait(
            lambda: strata.window.find(role="label", name="1"),
            "tab number hints while Ctrl+Shift is held",
        )
    finally:
        strata.keyboard.connection.key(shift, False)
        strata.keyboard.connection.key(ctrl, False)
    strata.keyboard.press("ctrl+shift+1")
    selected_tab(strata, root)
    strata.wait_for_selection(["todo.txt"], root)
    strata.keyboard.press("ctrl+Tab")
    selected_tab(strata, "archive")
    strata.keyboard.press("ctrl+shift+Tab")
    selected_tab(strata, root)
    strata.keyboard.press("ctrl+shift+2")
    selected_tab(strata, "archive")
    strata.keyboard.press("ctrl+w")
    strata.wait_for_selection(["todo.txt"], root)
    # The same add control works after the strip collapses.
    strata.pointer.click(strata.wait(lambda: strata.window.find(role="button", name="New tab"), "New tab"))
    strata.open_directory("documents")
    selected_tab(strata, "documents")
    assert strata.environment.read_preferences().get("tenxer_mode") == str(tenxer).lower()


@pytest.mark.parametrize("mode", ALL_MODES)
def test_drop_on_another_tab_moves_files_into_its_location(strata, mode):
    root = strata.fixture.root.name
    strata.keyboard.press("ctrl+t")
    strata.open_directory("archive")
    selected_tab(strata, "archive")
    strata.keyboard.press("ctrl+shift+1")
    selected_tab(strata, root)
    source = strata.select_entry("todo.txt")
    strata.pointer.drag(source, tab(strata, "archive"))
    strata.wait(lambda: strata.fixture.path("archive/todo.txt").exists(), "file transferred to the other tab")
    assert not strata.fixture.path("todo.txt").exists()
    assert strata.fixture.path("archive/todo.txt").read_text() == "todo\n"


def test_hovering_a_tab_during_drag_allows_a_drop_in_its_listing(strata):
    strata.fixture.path("documents/projects").mkdir()
    root = strata.fixture.root.name
    strata.keyboard.press("ctrl+t")
    strata.open_directory("documents")
    selected_tab(strata, "documents")
    strata.keyboard.press("ctrl+shift+1")
    selected_tab(strata, root)
    source = strata.select_entry("todo.txt")
    strata.pointer.drag_points(
        strata.pointer.drag_origin(source),
        tab(strata, "documents").screen_bounds().center,
        release=False,
    )
    try:
        selected_tab(strata, "documents")
        target = strata.entry("projects")
        # A drag icon can match a row's native-surface size. Avoid the legacy
        # popup-origin correction while the drag surface is alive.
        x, y = target.window_bounds().center
        origin = strata.window.screen_bounds()
        strata.pointer.move_to(origin.x + x, origin.y + y)
    finally:
        strata.pointer.connection.button(1, False)
    strata.wait(lambda: strata.fixture.path("documents/projects/todo.txt").exists(), "file dropped after switching tabs during drag")
    assert not strata.fixture.path("todo.txt").exists()


def test_dragging_tab_labels_changes_numbered_order(strata):
    root = strata.fixture.root.name
    strata.keyboard.press("ctrl+t")
    strata.open_directory("archive")
    selected_tab(strata, "archive")
    strata.pointer.drag(tab(strata, "archive"), tab(strata, root))
    strata.keyboard.press("ctrl+shift+2")
    selected_tab(strata, root)
    strata.keyboard.press("ctrl+shift+1")
    selected_tab(strata, "archive")


def test_ctrl_drop_on_a_tab_copies_without_removing_the_source(strata):
    root = strata.fixture.root.name
    strata.keyboard.press("ctrl+t")
    strata.open_directory("archive")
    selected_tab(strata, "archive")
    strata.keyboard.press("ctrl+shift+1")
    selected_tab(strata, root)
    source = strata.select_entry("todo.txt")
    strata.pointer.drag_points(
        strata.pointer.drag_origin(source),
        tab(strata, "archive").screen_bounds().center,
        modifiers=["ctrl"],
    )
    strata.wait(lambda: strata.fixture.path("archive/todo.txt").exists(), "file copied across tabs")
    assert strata.fixture.path("todo.txt").read_bytes() == strata.fixture.path("archive/todo.txt").read_bytes()
