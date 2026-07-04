#!/usr/bin/env python3
"""Lightweight Gradio web demo for the Mystery φ-e-π probe."""

from __future__ import annotations

import html
import logging
import os
import re
import tempfile
import time
import traceback
from collections.abc import Callable, Iterator

import gradio as gr
import matplotlib.pyplot as plt

from demo_core import (
    BOOT_QUOTE_STRING,
    CLAIMS_MD,
    E_OVER_PI,
    EXPLORE_FURTHER_MD,
    GITHUB_URL,
    HF_SPACE_URL,
    KAPPA_DOC,
    PHYSICAL_INTERPRETATION_INTRO_MD,
    PHYSICAL_INTERPRETATION_MATH_MD,
    PROBE_HOOKS_TABLE_MD,
    PROBE_SNIPPETS,
    R,
    ONBOARDING_MD,
    kappa_star,
    SIMULATION_BANNER_MD,
    TERM_KEY_ACTIONS,
    TOE_URL,
    WALLPAPER_URL,
    get_build_label,
    is_hf_space,
    wallpaper_static_paths,
    build_unit_cell_viewport_header_html,
    unit_cell_error_placeholder_html,
    render_unit_cell_deformation_video,
    render_gravity_demo_animation_video,
    render_breathing_demo_video,
    build_breathing_animation_figure,
    build_readme_full_page_html,
    create_breathing_animation,
    figure_to_viewport_cached_html,
    residual_from_scales,
    run_residual_explorer,
    run_residual_explorer_plotly,
    plotly_figure_to_render_detail_html,


    terminal_directory_help,
    terminal_figures_index,
    terminal_keypad_map,
    terminal_probe_catalog,
    terminal_probe_scope,
    terminal_results_snapshot,
    terminal_toe_linkage,
    terminal_vortex369_readout,
)


logger = logging.getLogger(__name__)


def _patch_gradio_client_bool_schema() -> None:
    """Avoid gradio_client crash when JSON schema contains bare bool nodes."""
    try:
        from gradio_client import utils as client_utils

        if getattr(client_utils, "_vqc_bool_patch", False):
            return

        orig_get_type = client_utils.get_type

        def get_type(schema):  # noqa: ANN001
            if isinstance(schema, bool):
                return "boolean"
            return orig_get_type(schema)

        client_utils.get_type = get_type
        client_utils._vqc_bool_patch = True
        logger.info("Patched gradio_client bool JSON-schema handling")
    except Exception:
        logger.warning("Could not patch gradio_client", exc_info=True)


_patch_gradio_client_bool_schema()


def _patch_gradio_asyncio_helpers() -> None:
    """Gradio 5.12 safe_get_lock() returns None on Python 3.14+ (no implicit event loop)."""
    try:
        import asyncio

        import gradio.queueing as gradio_queueing
        import gradio.utils as gradio_utils

        if getattr(gradio_utils, "_myst_asyncio_patch", False):
            return

        def safe_get_lock() -> asyncio.Lock:
            return asyncio.Lock()

        def safe_get_stop_event() -> asyncio.Event:
            return asyncio.Event()

        gradio_utils.safe_get_lock = safe_get_lock
        gradio_utils.safe_get_stop_event = safe_get_stop_event
        gradio_queueing.safe_get_lock = safe_get_lock
        gradio_utils._myst_asyncio_patch = True
        logger.info("Patched gradio asyncio lock/event helpers for Python 3.14+")
    except Exception:
        logger.warning("Could not patch gradio asyncio helpers", exc_info=True)


_patch_gradio_asyncio_helpers()

_VQC_ACCENT = "#c9a227"  # mystery gold — primary accent
_VQC_HF_RUNNING = "#1ed760"
_VQC_FIELD_FILL = "rgba(18, 10, 28, 0.52)"
_VQC_TAB_GREEN_BG = "#1a3d2a"
_VQC_TAB_GREEN_BG_HOVER = "#1f4d34"
_VQC_TAB_GREEN_BORDER = "#33ff66"
_VQC_TAB_GREEN_TEXT = "#86efac"
_VQC_TAB_GREEN_TEXT_HOVER = "#bbf7d0"
_VQC_TAB_ORANGE_BG = "#3d2a5c"
_VQC_TAB_ORANGE_BORDER = "#6a4c93"
_VQC_TAB_ORANGE_TEXT = "#d4b8ff"
_VQC_MATRIX_GREEN = "#33ff66"

# ====================== GLOBAL STYLING THEME ======================
NAV_THEME: dict = {
    "default_gap_height": 0.20,
    "nav_label": {
        "font_size": "14px",
        "font_weight": "500",
        "text_color": "#e0e0e0",
        "padding_right": "10px",
        "width": "4.75rem",
    },
    "nav_grid_gap": "4px",
    "nav_button": {
        "height": "2.05rem",
        "default_width": "58px",
        "min_width": "58px",
        "padding": "6px 12px",
        "shape_padding": "6px 10px",
        "font_size": "14px",
        "font_weight": "500",
        "text_align": "center",
        "vertical_align": "center",
        "border_radius": "8px",
        "border_width": "2px",
        "transition": "background 0.15s ease, border-color 0.15s ease, color 0.15s ease",
        "text_color": "#ffffff",
        "body_color": "#2a1f10",
        "border_color": "#6b4f1d",
        "active": {
            "text_color": "#00FF00",
            "border_color": "#00FF00",
            "body_color": "#1a3d2a",
        },
    },
}

# Legacy aliases — prefer NAV_THEME for new code.
DEFAULT_BUTTON_BORDER_COLOR = NAV_THEME["nav_button"]["border_color"]
DEFAULT_BUTTON_BODY_HEIGHT = NAV_THEME["nav_button"]["height"]
DEFAULT_GAP = "8px"
default_gap_height = NAV_THEME["default_gap_height"]
_myst_default_gap_height = f"{default_gap_height}rem"
_MYST_STATUS_LAYER_ALPHA = 0.2
# Individual preset panel backgrounds: 30% transparent (30% opaque).
_MYST_STATUS_PANEL_ALPHA = 0.3
_STATUS_ZOOM_PRESET_COUNT = 9
_VQC_MATRIX_GREEN_BG = "#0a1f12"
_VQC_LOGO_GOLD = "#c9a227"
_VQC_HOME_KEY_BG = "#000000"

OPTICS_LOGO_HTML = """
<div class="vqc-optics-logo" role="img" aria-label="Mystery φ-e-π Control Panel">
  <span class="vqc-optics-brand">MYSTERY</span>
  <span class="vqc-optics-panel-title">φ · e · π Control Panel</span>
  <span class="vqc-optics-subtitle">PROBE · SCALE · COMPARE · CLI READOUT</span>
</div>
"""

GRAVITY_OPTICS_LOGO_HTML = """
<div class="vqc-optics-logo" role="img" aria-label="Mystery Gravity Control Panel">
  <span class="vqc-optics-brand">MYSTERY</span>
  <span class="vqc-optics-panel-title">Gravity Control Panel</span>
  <span class="vqc-optics-subtitle">DEFORM · BOW · CONCAVE · RESIDUAL</span>
</div>
"""

CONTROL_PANEL_HEADER_HTML = """
<div class="myst-cube-viewport-header" role="img" aria-label="Gravity control panel">
  <span class="myst-cube-viewport-brand">MYSTERY</span>
  <span class="myst-cube-viewport-title">Gravity Control Panel</span>
  <span class="myst-cube-viewport-sub">deform · residual · viewport</span>
</div>
"""

QUICK_PRESETS_PANEL_HEADER_HTML = """
<div class="myst-gravity-presets-header myst-gravity-presets-header-compact myst-gravity-presets-header-single" role="img" aria-label="Quick presets panel">
  <span class="myst-cube-viewport-title">QUICK PRESETs</span>
</div>
"""

GRAVITY_PRESET_TUI_HEADER_HTML = """
<div class="myst-gravity-preset-tui-header" role="img" aria-label="Preset metrics terminal">
  <span class="myst-cube-viewport-brand">MYSTERY</span>
  <span class="myst-cube-viewport-title">Preset Metrics TUI</span>
  <span class="myst-cube-viewport-tag">quick preset loadout · live readout</span>
</div>
"""

# Client-side CSS phosphor scan — no server streaming loop (HF-safe).
SIGNAL_SCANNER_HTML = f"""
<div class="myst-signal-scan" role="img" aria-label="Phosphor signal scan">
  <div class="myst-signal-scanlines" aria-hidden="true"></div>
  <div class="myst-signal-beam" aria-hidden="true"></div>
  <pre class="myst-signal-body">PHOSPHOR SIGNAL SCAN — φ · e · π
{'─' * 72}
R = φ²+e²−π²     {R:+.6f}
κ_doc = {KAPPA_DOC}    κ* ≈ {kappa_star():.5f}
angles ≈ 31.0° / 59.9° / 89.1°
369 tens ≈ 3.10 / 5.99 / 8.91
{'─' * 72}
▸ holonomy-gap B(κ) = π²(e/π−κ)
▸ emergent signature — not forced identity
▸ {GITHUB_URL}
{'─' * 72}
press any keypad to exit</pre>
</div>
"""

_OPTICS_TERM_BAR = "─" * 48
_OPTICS_TERM_CHAR_DELAY_S = 0.014
_OPTICS_TERM_NEWLINE_DELAY_S = 0.048
_OPTICS_TERM_UPLINK_DELAY_S = 0.22
_OPTICS_TERM_CURSOR = "▌"
_OPTICS_TERM_RELEASE_DELAY_S = 0.25
_BOOT_QUOTE_CHAR_DELAY_S = 0.1
_BOOT_POST_QUOTE_DELAY_S = 3.0
_BOOT_DOT_INTERVAL_S = 0.5
_BOOT_DOT_COUNT = 6
_BOOT_TERM_LINES = 14
_BOOT_TERM_COLS = 56


def _strip_md_plain(text: str) -> str:
    """Flatten markdown blockquotes and emphasis for terminal readout."""
    plain = re.sub(r"^>\s*", "", text.strip(), flags=re.MULTILINE)
    plain = re.sub(r"\*\*([^*]+)\*\*", r"\1", plain)
    plain = re.sub(r"`([^`]+)`", r"\1", plain)
    return plain.strip()


def _optics_terminal_frame(title: str, body: str) -> str:
    return f"{title}\n{_OPTICS_TERM_BAR}\n{body}"


TERM_KEYPAD_PROG_COLS = 12
TERM_KEYPAD_PROG_ROWS = 2
TERM_KEYPAD_COUNT = TERM_KEYPAD_PROG_COLS * TERM_KEYPAD_PROG_ROWS
TERM_KEYPAD_DEFINED: dict[int, str] = {
    index: action for index, (action, _desc) in TERM_KEY_ACTIONS.items()
}
TERM_KEYPAD_HOME_KEY = "key01"
TERM_KEYPAD_DESCRIPTIONS: dict[int, str] = {
    index: desc for index, (_action, desc) in TERM_KEY_ACTIONS.items()
}
TERM_MENU_ACTIONS: tuple[str, ...] = (
    "home",
    "status",
    "scope",
    "directory",
    "results",
    "build",
    "help",
    "scan",
)
TERM_UI_MENU = "menu"
TERM_UI_PAGE = "page"
TERM_NAV_KEYS: tuple[str, ...] = (
    "dpad_select",
    "dpad_up",
    "dpad_down",
    "dpad_left",
    "dpad_right",
    "clear",
)
TERM_DPAD_HOLD_KEYS: tuple[str, ...] = (
    "dpad_select",
    "dpad_up",
    "dpad_down",
    "dpad_left",
    "dpad_right",
)
TERM_NAV_DEFINED: dict[str, str] = {
    "dpad_select": "Enter — confirm menu item",
    "dpad_up": "Up — previous menu item",
    "dpad_down": "Down — next menu item",
    "dpad_left": "Left — previous menu item",
    "dpad_right": "Right — next menu item",
    "clear": "Clear — blank display",
}
TERM_KEYPAD_CONTROL_ORDER: tuple[str, ...] = (
    *TERM_NAV_KEYS,
    *(f"key{i:02d}" for i in range(1, TERM_KEYPAD_COUNT + 1)),
)


def _optics_assigned_keypad_lines() -> str:
    """Only keys with real functions — omit latch-only / unassigned slots."""
    lines = []
    for index in sorted(TERM_KEYPAD_DEFINED):
        tag = "01 Home" if index == 1 else f"{index:02d}"
        lines.append(f"  [{tag}]  {TERM_KEYPAD_DESCRIPTIONS[index]}")
    for nav_key in TERM_NAV_KEYS:
        if nav_key in TERM_NAV_DEFINED:
            tag = "CLR" if nav_key == "clear" else nav_key.removeprefix("dpad_").upper()
            lines.append(f"  [{tag}]  {TERM_NAV_DEFINED[nav_key]}")
    return "\n".join(lines)


def _optics_terminal_home() -> str:
    return _optics_terminal_frame("PROGRAMMABLE KEYPAD", terminal_keypad_map())


def _default_term_ui_state() -> dict:
    return {"mode": TERM_UI_MENU, "index": 0, "scan": False}


def _optics_terminal_menu(menu_index: int) -> str:
    lines = [
        "▲▼ ◀▶ move highlight · enter confirm · 01 Home",
        "",
    ]
    for index, (_action, keypad_key, label, _stream) in enumerate(_term_menu_items()):
        mark = "▶" if index == menu_index else " "
        lines.append(f"{keypad_key:02d} --- [{mark}] {label}")
    return _optics_terminal_frame("SELECTION MENU", "\n".join(lines))


def _term_menu_label(action: str) -> str:
    labels = {
        "home": "Home — Keypad Map",
        "status": "Status — Live Constants",
        "scope": "Scope — Space vs Local Suite",
        "directory": "Directory — Repo Layout",
        "results": "Results — φ-e-π Snapshot",
        "build": "Build — Deploy Stamp",
        "help": "Help — D-pad Navigation",
        "scan": "Scan — Phosphor Display",
    }
    return labels.get(action, action)


def _term_menu_keypad_index(action: str) -> int:
    for index, (key, _desc) in TERM_KEY_ACTIONS.items():
        if key == action:
            return index
    return 1


def _term_menu_items() -> tuple[tuple[str, int, str, Callable[[], Iterator[str]]], ...]:
    items = []
    for action in TERM_MENU_ACTIONS:
        stream_fn = TERM_KEYPAD_STREAMERS.get(action)
        if stream_fn is None:
            continue
        items.append(
            (
                action,
                _term_menu_keypad_index(action),
                _term_menu_label(action),
                stream_fn,
            )
        )
    return tuple(items)


def _term_menu_index_for_action(action: str) -> int:
    for index, (key, _keypad, _label, _stream) in enumerate(_term_menu_items()):
        if key == action:
            return index
    return 0


def _term_menu_step(menu_index: int, delta: int) -> int:
    count = len(_term_menu_items())
    return (menu_index + delta) % count


def _optics_terminal_status() -> str:
    on_hf = is_hf_space()
    env = "Hugging Face Space" if on_hf else "Local Gradio"
    k_star = kappa_star()
    return _optics_terminal_frame(
        "SYSTEM STATUS",
        "\n".join(
            [
                f"Environment : {env}",
                f"κ default   : {KAPPA_DOC} (documented invariant)",
                f"R residual  : {R:+.6f}  (~1.39% Pythagorean error)",
                f"κ*          : {k_star:.5f}  (0.16% from κ_doc)",
                "Pipeline    : φ-e-π triangle → B(κ) scaling → figures",
                "Full suite  : run_all.py (11 probes) — local only",
                f"TOE parent  : {TOE_URL}",
                "",
                "05 Results · 09 Probes · 08 Matrix · Run analysis below.",
            ]
        ),
    )


def _optics_terminal_scope() -> str:
    return _optics_terminal_frame("PROBE SCOPE", terminal_probe_scope())


def _optics_terminal_directory() -> str:
    return _optics_terminal_frame("REPO DIRECTORY", terminal_directory_help())


def _optics_terminal_results() -> str:
    return _optics_terminal_frame("RESULTS SNAPSHOT", terminal_results_snapshot())


def _optics_terminal_probes() -> str:
    return _optics_terminal_frame("PROBE CATALOG", terminal_probe_catalog())


def _optics_terminal_vortex369() -> str:
    return _optics_terminal_frame("3-6-9 VORTEX", terminal_vortex369_readout())


def _optics_terminal_toe() -> str:
    return _optics_terminal_frame("TOE LINKAGE", terminal_toe_linkage())


def _optics_terminal_figures() -> str:
    return _optics_terminal_frame("FIGURES INDEX", terminal_figures_index())


def _optics_terminal_build() -> str:
    build = get_build_label().replace("`", "")
    return _optics_terminal_frame(
        "BUILD / LAST UPDATED",
        "\n".join(
            [
                build,
                "",
                "Synced from mystery via scripts/sync_hf_space.sh on deploy.",
                f"Repo: {GITHUB_URL}",
                f"Space: {HF_SPACE_URL}",
            ]
        ),
    )


def _optics_terminal_help() -> str:
    return _optics_terminal_frame(
        "KEYPAD REFERENCE",
        "\n".join(
            [
                "D-pad — ▲▼ ◀▶ move highlight · enter opens item",
                "01 Home → selection menu (momentary)",
                "02–08 mirror menu · 09–12 direct shortcuts",
                "08 / menu item 08 → phosphor scan (any key stops)",
                "clear → blank display",
                "",
                "Press 01 Home for full keypad map.",
            ]
        ),
    )


def _stream_optics_terminal_text(full_text: str) -> Iterator[str]:
    """Reveal terminal text one character at a time — typewriter / uplink effect."""
    shown = ""
    for ch in full_text:
        shown += ch
        yield shown + _OPTICS_TERM_CURSOR
        time.sleep(_OPTICS_TERM_NEWLINE_DELAY_S if ch == "\n" else _OPTICS_TERM_CHAR_DELAY_S)
    yield shown


def _optics_terminal_uplink_banner(mode: str) -> str:
    stamp = time.strftime("%H:%M:%S", time.gmtime())
    return f"> UPLINK {mode.upper()} @ {stamp} UTC…\n"


def _optics_terminal_stream(builder: Callable[[], str], *, mode: str) -> Iterator[str]:
    """Stream a keyed readout: uplink banner, then body character-by-character."""
    banner = _optics_terminal_uplink_banner(mode)
    yield banner + _OPTICS_TERM_CURSOR
    time.sleep(_OPTICS_TERM_UPLINK_DELAY_S)
    yield from _stream_optics_terminal_text(banner + builder())


def _stream_optics_terminal_home() -> Iterator[str]:
    yield from _optics_terminal_stream(_optics_terminal_home, mode="home")


def _stream_optics_terminal_status() -> Iterator[str]:
    yield from _optics_terminal_stream(_optics_terminal_status, mode="status")


def _stream_optics_terminal_scope() -> Iterator[str]:
    yield from _optics_terminal_stream(_optics_terminal_scope, mode="scope")


def _stream_optics_terminal_directory() -> Iterator[str]:
    yield from _optics_terminal_stream(_optics_terminal_directory, mode="directory")


def _stream_optics_terminal_results() -> Iterator[str]:
    yield from _optics_terminal_stream(_optics_terminal_results, mode="results")


def _stream_optics_terminal_probes() -> Iterator[str]:
    yield from _optics_terminal_stream(_optics_terminal_probes, mode="probes")


def _stream_optics_terminal_vortex369() -> Iterator[str]:
    yield from _optics_terminal_stream(_optics_terminal_vortex369, mode="vortex369")


def _stream_optics_terminal_toe() -> Iterator[str]:
    yield from _optics_terminal_stream(_optics_terminal_toe, mode="toe")


def _stream_optics_terminal_figures() -> Iterator[str]:
    yield from _optics_terminal_stream(_optics_terminal_figures, mode="figures")


def _stream_scan_stub() -> Iterator[str]:
    """Menu placeholder — real scan uses CSS toggle via key 08 / d-pad."""
    return iter(())


def _stream_optics_terminal_build() -> Iterator[str]:
    yield from _optics_terminal_stream(_optics_terminal_build, mode="build")


def _stream_optics_terminal_help() -> Iterator[str]:
    yield from _optics_terminal_stream(_optics_terminal_help, mode="help")


def _stream_optics_terminal_menu(menu_index: int = 0) -> Iterator[str]:
    yield from _optics_terminal_stream(
        lambda: _optics_terminal_menu(menu_index),
        mode="menu",
    )


def _stream_optics_terminal_clear(current: str) -> Iterator[str]:
    """Erase display in paced chunks — inverse of the typewriter feed."""
    text = current or ""
    if not text:
        yield ""
        return
    chunk = max(1, len(text) // 36)
    for end in range(len(text), -1, -chunk):
        yield text[:end] + (_OPTICS_TERM_CURSOR if end else "")
        time.sleep(0.01)
    yield ""


TERM_KEYPAD_STREAMERS: dict[str, Callable[[], Iterator[str]]] = {}


def _term_key_id(index: int) -> str:
    return f"key{index:02d}"


def _term_keypad_label(index: int) -> str:
    """Home key is '01 Home'; 08 shows matrix glyph hint."""
    if index == 1:
        return "01 Home"
    if index == 8:
        return "08~"
    return f"{index:02d}"


def _term_key_is_defined_prog(key: str) -> bool:
    """True for assigned prog keys (02–24) that have a real function."""
    for index in TERM_KEYPAD_DEFINED:
        if index == 1:
            continue
        if _term_key_id(index) == key:
            return True
    return False


def _term_key_btn_classes(key: str, active: str) -> list[str]:
    """Black/white idle caps; matrix-green latch on active keys (never home)."""
    classes = ["vqc-optics-key"]
    if key in TERM_NAV_KEYS:
        classes.append("vqc-optics-dpad-key")
    if key == TERM_KEYPAD_HOME_KEY:
        classes.append("vqc-optics-key-home")
    elif key.startswith("dpad_"):
        classes.append("vqc-optics-key-dpad")
    if key == "clear":
        classes.append("vqc-optics-key-clear")
    if _term_key_is_defined_prog(key):
        classes.append("vqc-optics-key-defined")
    if key == active and key != TERM_KEYPAD_HOME_KEY:
        classes.append("active")
    return classes


def _term_keypad_btn_updates(active: str) -> tuple:
    return tuple(
        gr.update(elem_classes=_term_key_btn_classes(key_id, active))
        for key_id in TERM_KEYPAD_CONTROL_ORDER
    )


def _term_keypad_outputs(terminal_text: str, active: str, ui_state: dict | None = None) -> tuple:
    state = _default_term_ui_state() if ui_state is None else ui_state
    scanning = bool(state.get("scan"))
    return (
        gr.update(
            value=terminal_text,
            visible=not scanning,
            elem_classes=["vqc-optics-terminal-wrap", "vqc-optics-terminal"],
        ),
        gr.update(visible=scanning),
        *_term_keypad_btn_updates(active),
        active,
        state,
    )


def _term_yield_stream_then_release(
    stream: Iterator[str],
    *,
    active: str,
    ui_state: dict,
    release_delay: float | None = None,
) -> Iterator[tuple]:
    """Stream terminal text, latch while typing, release latch after a short pause."""
    delay = _OPTICS_TERM_RELEASE_DELAY_S if release_delay is None else release_delay
    last_partial = ""
    for partial in stream:
        last_partial = partial
        yield _term_keypad_outputs(partial, active, ui_state)
    time.sleep(delay)
    yield _term_keypad_outputs(last_partial, "", ui_state)


def _term_stream_with_latch(
    stream_fn: Callable[[], Iterator[str]],
    *,
    active: str,
    ui_state: dict,
) -> Iterator[tuple]:
    """Stream terminal text and latch matrix-green active state on the pressed key."""
    yield from _term_yield_stream_then_release(stream_fn(), active=active, ui_state=ui_state)


def _make_term_stream_click(
    active_key: str,
    stream_fn: Callable[[], Iterator[str]],
    *,
    menu_action: str | None = None,
):
    def handler(ui_state: dict) -> Iterator[tuple]:
        state = dict(ui_state) if ui_state else _default_term_ui_state()
        if menu_action is not None:
            state.update(
                {
                    "mode": TERM_UI_PAGE,
                    "index": _term_menu_index_for_action(menu_action),
                    "scan": menu_action == "scan",
                }
            )
        else:
            state["scan"] = False
        yield from _term_stream_with_latch(stream_fn, active=active_key, ui_state=state)

    return handler


def _make_term_clear_click(active_key: str):
    def handler(current: str, ui_state: dict) -> Iterator[tuple]:
        state = dict(ui_state) if ui_state else _default_term_ui_state()
        state["scan"] = False
        yield from _term_yield_stream_then_release(
            _stream_optics_terminal_clear(current),
            active=active_key,
            ui_state=state,
        )

    return handler


def _make_term_momentary_click(active_key: str, *, release_delay: float):
    """Brief latch flash — momentary, no maintained state."""

    def handler(current: str, ui_state: dict) -> Iterator[tuple]:
        state = dict(ui_state) if ui_state else _default_term_ui_state()
        yield _term_keypad_outputs(current, active_key, state)
        time.sleep(release_delay)
        yield _term_keypad_outputs(current, "", state)

    return handler


def _make_term_dpad_click(active_key: str):
    """D-pad click — navigate menu, confirm with SEL, brief matrix-green latch."""

    def handler(_current: str, ui_state: dict) -> Iterator[tuple]:
        state = dict(ui_state) if ui_state else _default_term_ui_state()
        mode = state.get("mode", TERM_UI_MENU)
        menu_index = int(state.get("index", 0))
        nav_delta = {
            "dpad_up": -1,
            "dpad_left": -1,
            "dpad_down": 1,
            "dpad_right": 1,
        }

        if active_key in nav_delta:
            if mode == TERM_UI_PAGE:
                menu_state = {"mode": TERM_UI_MENU, "index": menu_index, "scan": False}
                text = _optics_terminal_menu(menu_index)
            else:
                new_index = _term_menu_step(menu_index, nav_delta[active_key])
                menu_state = {"mode": TERM_UI_MENU, "index": new_index, "scan": False}
                text = _optics_terminal_menu(new_index)
            yield _term_keypad_outputs(text, active_key, menu_state)
            time.sleep(_OPTICS_TERM_RELEASE_DELAY_S)
            yield _term_keypad_outputs(text, "", menu_state)
            return

        if active_key == "dpad_select":
            if mode == TERM_UI_MENU:
                action, _keypad, _label, stream_fn = _term_menu_items()[menu_index]
                if action == "scan":
                    page_state = {
                        "mode": TERM_UI_PAGE,
                        "index": menu_index,
                        "scan": True,
                    }
                    yield _term_keypad_outputs("", "dpad_select", page_state)
                    time.sleep(_OPTICS_TERM_RELEASE_DELAY_S)
                    yield _term_keypad_outputs("", "", page_state)
                    return
                page_state = {
                    "mode": TERM_UI_PAGE,
                    "index": menu_index,
                    "scan": False,
                }
                yield from _term_yield_stream_then_release(
                    stream_fn(),
                    active="dpad_select",
                    ui_state=page_state,
                )
                return
            menu_state = {"mode": TERM_UI_MENU, "index": menu_index, "scan": False}
            text = _optics_terminal_menu(menu_index)
            yield _term_keypad_outputs(text, active_key, menu_state)
            time.sleep(_OPTICS_TERM_RELEASE_DELAY_S)
            yield _term_keypad_outputs(text, "", menu_state)

    return handler


def _make_term_latch_click(active_key: str):
    """Undefined keypad slots — latch matrix-green only, terminal unchanged."""

    def handler(current: str, ui_state: dict) -> tuple:
        state = dict(ui_state) if ui_state else _default_term_ui_state()
        state["scan"] = False
        return _term_keypad_outputs(current, active_key, state)

    return handler


def _make_activate_signal_scan(active_key: str, *, menu_action: str = "scan"):
    """Toggle CSS phosphor scan — one yield, no server animation loop."""

    def handler(ui_state: dict) -> Iterator[tuple]:
        state = dict(ui_state) if ui_state else _default_term_ui_state()
        state.update(
            {
                "mode": TERM_UI_PAGE,
                "index": _term_menu_index_for_action(menu_action),
                "scan": True,
            }
        )
        yield _term_keypad_outputs("", active_key, state)
        time.sleep(_OPTICS_TERM_RELEASE_DELAY_S)
        yield _term_keypad_outputs("", "", state)

    return handler


def _make_term_home_momentary():
    """Home — momentary return to the selection menu."""

    def handler(current_active: str, ui_state: dict) -> Iterator[tuple]:
        menu_state = {"mode": TERM_UI_MENU, "index": 0, "scan": False}
        menu_text = _optics_terminal_menu(0)
        yield _term_keypad_outputs(menu_text, current_active, menu_state)
        time.sleep(_OPTICS_TERM_RELEASE_DELAY_S)
        yield _term_keypad_outputs(menu_text, "", menu_state)

    return handler


def _boot_quote_prefix() -> str:
    """Pad so the quote types out near the middle of the terminal panel."""
    v_pad = max(0, (_BOOT_TERM_LINES - 1) // 2)
    h_pad = max(0, (_BOOT_TERM_COLS - len(BOOT_QUOTE_STRING)) // 2)
    return "\n" * v_pad + (" " * h_pad)


def _stream_term_boot() -> Iterator[tuple]:
    """One-shot startup: centered quote, dot countdown, then selection menu."""
    boot_state = _default_term_ui_state()
    shown = _boot_quote_prefix()
    yield _term_keypad_outputs(shown, "", boot_state)

    for ch in BOOT_QUOTE_STRING:
        shown += ch
        yield _term_keypad_outputs(shown + _OPTICS_TERM_CURSOR, "", boot_state)
        time.sleep(_BOOT_QUOTE_CHAR_DELAY_S)

    yield _term_keypad_outputs(shown, "", boot_state)
    time.sleep(_BOOT_POST_QUOTE_DELAY_S)

    for _ in range(_BOOT_DOT_COUNT):
        shown += "."
        yield _term_keypad_outputs(shown, "", boot_state)
        time.sleep(_BOOT_DOT_INTERVAL_S)

    menu_text = _optics_terminal_menu(0)
    yield _term_keypad_outputs(menu_text, "", boot_state)


def _register_term_keypad_streamers() -> None:
    TERM_KEYPAD_STREAMERS.update(
        {
            "home": _stream_optics_terminal_home,
            "status": _stream_optics_terminal_status,
            "scope": _stream_optics_terminal_scope,
            "directory": _stream_optics_terminal_directory,
            "results": _stream_optics_terminal_results,
            "build": _stream_optics_terminal_build,
            "help": _stream_optics_terminal_help,
            "scan": _stream_scan_stub,
            "probes": _stream_optics_terminal_probes,
            "vortex369": _stream_optics_terminal_vortex369,
            "toe": _stream_optics_terminal_toe,
            "figures": _stream_optics_terminal_figures,
        }
    )


_register_term_keypad_streamers()


def _external_tab_html(label: str, url: str, tab_id: str) -> str:
    """External Source bookmark — opens in a new tab."""
    return (
        f'<a href="{url}" class="vqc-source-tab" data-tab="{tab_id}" '
        f'target="_blank" rel="noopener noreferrer">{label}</a>'
    )


_MAIN_NAV_TAB_SPECS = (
    ("home", "Home"),
    ("render", "Render"),
    ("status", "Presets"),
    ("readme", "Docs"),
)

_SHAPE_NAV_IDS: tuple[str, ...] = ("D4", "D6", "D8", "D12", "D20")
_DEFAULT_ACTIVE_SHAPE = "D6"


def _nav_theme_gap_rem(*, half: bool = False) -> float:
    """Return gap height in rem from NAV_THEME."""
    gap = float(NAV_THEME["default_gap_height"])
    return gap / 2 if half else gap


def _nav_theme_gradio_css_vars() -> str:
    """CSS custom properties derived from NAV_THEME for injection into HFB_CSS."""
    gap = NAV_THEME["default_gap_height"]
    nb = NAV_THEME["nav_button"]
    nl = NAV_THEME["nav_label"]
    active = nb["active"]
    return f"""
    --myst-default-gap-height: {gap}rem;
    --myst-half-gap-height: calc({gap}rem * 0.5);
    --nav-label-font-size: {nl["font_size"]};
    --nav-label-font-weight: {nl["font_weight"]};
    --nav-label-text-color: {nl["text_color"]};
    --nav-label-padding-right: {nl["padding_right"]};
    --nav-label-width: {nl["width"]};
    --nav-grid-gap: {NAV_THEME["nav_grid_gap"]};
    --nav-btn-height: {nb["height"]};
    --nav-btn-default-width: {nb["default_width"]};
    --nav-btn-min-width: {nb["min_width"]};
    --nav-btn-padding: {nb["padding"]};
    --nav-btn-shape-padding: {nb["shape_padding"]};
    --nav-btn-font-size: {nb["font_size"]};
    --nav-btn-font-weight: {nb["font_weight"]};
    --nav-btn-text-align: {nb["text_align"]};
    --nav-btn-vertical-align: {nb["vertical_align"]};
    --nav-btn-border-radius: {nb["border_radius"]};
    --nav-btn-border-width: {nb["border_width"]};
    --nav-btn-transition: {nb["transition"]};
    --nav-btn-text-color: {nb["text_color"]};
    --nav-btn-body-color: {nb["body_color"]};
    --nav-btn-border-color: {nb["border_color"]};
    --nav-btn-active-text-color: {active["text_color"]};
    --nav-btn-active-border-color: {active["border_color"]};
    --nav-btn-active-body-color: {active["body_color"]};
    """


def _nav_theme_button(
    label: str,
    *,
    elem_classes: list[str] | None = None,
    elem_id: str | None = None,
    interactive: bool = True,
    scale: int = 1,
    **kwargs,
) -> gr.Button:
    """Create a navigation tab button using NAV_THEME defaults."""
    btn_kwargs: dict = {
        "variant": "secondary",
        "scale": scale,
        "interactive": interactive,
    }
    if elem_classes:
        btn_kwargs["elem_classes"] = elem_classes
    if elem_id:
        btn_kwargs["elem_id"] = elem_id
    btn_kwargs.update(kwargs)
    return gr.Button(label, **btn_kwargs)


def _place_back_button(
    label: str = "← Back",
    *,
    elem_id: str | None = None,
    elem_classes: list[str] | None = None,
    visible: bool = True,
    interactive: bool = True,
    min_width: int = 110,
) -> gr.Button:
    """Standard pill back button — shared across README, Render, Presets, etc."""
    classes = ["myst-standard-back-btn"]
    if elem_classes:
        classes.extend(elem_classes)
    kwargs: dict = {
        "elem_classes": classes,
        "variant": "secondary",
        "scale": 0,
        "min_width": min_width,
    }
    if elem_id:
        kwargs["elem_id"] = elem_id
    if not visible:
        kwargs["visible"] = False
    if not interactive:
        kwargs["interactive"] = interactive
    return gr.Button(label, **kwargs)


def _shape_btn_classes(shape: str, active_shape: str) -> list[str]:
    classes = ["vqc-source-tab", "shape-btn"]
    if shape == active_shape:
        classes.append("active")
    return classes


def _set_active_shape(new_shape: str) -> tuple:
    """Latching updates for D4–D20; active button gets cyan text + strong cyan glow."""
    shape = str(new_shape or _DEFAULT_ACTIVE_SHAPE).strip().upper()
    if shape not in _SHAPE_NAV_IDS:
        shape = _DEFAULT_ACTIVE_SHAPE
    updates: list = [gr.update(value=shape)]
    for shape_id in _SHAPE_NAV_IDS:
        is_active = shape_id == shape
        updates.append(
            gr.update(
                elem_classes=_shape_btn_classes(shape_id, shape),
                interactive=not is_active,
                variant="secondary",
            )
        )
    return tuple(updates)


def _main_nav_btn_classes(page_id: str, active_page: str) -> list[str]:
    classes = ["vqc-source-tab", "main-nav-btn"]
    if page_id == active_page:
        classes.append("active")
    return classes


def _main_nav_btn_update(page_id: str, *, active: bool) -> gr.Update:
    classes = ["vqc-source-tab", "main-nav-btn"]
    if active:
        classes.append("active")
    return gr.update(
        elem_classes=classes,
        interactive=not active,
        variant="secondary",
    )


def _place_unified_main_nav(
    *,
    active_page: str = "home",
    default_shape: str = _DEFAULT_ACTIVE_SHAPE,
) -> dict[str, gr.Button]:
    """Single top bar on all pages: Home/Render/Presets/Docs + D4–D20."""
    buttons: dict[str, gr.Button] = {}
    active = str(active_page or "home").strip().lower()
    default_shape = default_shape if default_shape in _SHAPE_NAV_IDS else _DEFAULT_ACTIVE_SHAPE
    with gr.Row(
        elem_id="myst-unified-main-nav",
        elem_classes=[
            "myst-main-nav",
            "myst-nav-bar-row",
            "vqc-source-tabs-row",
            "vqc-main-nav-row",
        ],
    ):
        gr.HTML('<span class="vqc-source-label vqc-nav-row-label">Mystery:</span>')
        with gr.Row(elem_classes=["nav-button-grid"]):
            for page_id, label in _MAIN_NAV_TAB_SPECS:
                is_active = page_id == active
                buttons[page_id] = _nav_theme_button(
                    label,
                    elem_classes=_main_nav_btn_classes(page_id, active),
                    interactive=not is_active,
                )
            for shape_id in _SHAPE_NAV_IDS:
                is_active = shape_id == default_shape
                buttons[shape_id] = _nav_theme_button(
                    shape_id,
                    elem_classes=_shape_btn_classes(shape_id, default_shape),
                    interactive=not is_active,
                )
    return buttons


def _place_status_zoom_nav_row(
    active_slot: int = -1,
) -> dict[str, gr.Button]:
    """Status sub-nav — Demo: label and nine presets (01 … 09)."""
    buttons: dict[str, gr.Button] = {}
    active = int(active_slot)
    with gr.Row(
        elem_id="myst-status-zoom-nav",
        elem_classes=[
            "myst-secondary-nav",
            "myst-nav-bar-row",
            "myst-status-preset-nav-wrap",
            "myst-gravity-child-nav-row",
        ],
    ):
        gr.HTML(
            '<span class="vqc-source-label vqc-nav-row-label myst-gravity-child-nav-label">'
            "Demo:</span>"
        )
        with gr.Row(elem_classes=["nav-button-grid"]):
            for slot in range(_STATUS_ZOOM_PRESET_COUNT):
                preset_id = _gravity_preset_id(slot)
                is_active = slot == active
                classes = ["vqc-source-tab", "demo-btn", "myst-status-preset-btn"]
                if is_active:
                    classes.append("active")
                buttons[str(slot)] = _nav_theme_button(
                    preset_id,
                    elem_id=f"myst-status-preset-btn-{preset_id}",
                    elem_classes=classes,
                    interactive=not is_active,
                )
    return buttons


def _place_status_save_edit_row() -> tuple[gr.Button, gr.Button]:
    """Presets page — Save + Edit on one row below the Demo: numeric bar."""
    with gr.Row(elem_classes=["myst-save-edit-row", "myst-nav-bar-row"]):
        gr.HTML(
            '<span class="vqc-source-label vqc-nav-row-label vqc-nav-label-spacer" '
            'aria-hidden="true">&nbsp;</span>'
        )
        with gr.Row(elem_classes=["nav-button-grid", "nav-button-grid-pair"]):
            save_btn = gr.Button(
                "Save",
                variant="secondary",
                elem_classes=[
                    *_STATUS_ZOOM_SAVE_BTN_CLASSES,
                    "save-btn",
                    "placeholder-btn",
                ],
                interactive=False,
                scale=1,
            )
            edit_btn = _nav_theme_button(
                "Edit",
                elem_id="myst-status-nav-edit-btn",
                elem_classes=[
                    "vqc-source-tab",
                    "myst-status-preset-btn",
                    "myst-status-nav-edit-btn",
                    "edit-btn",
                ],
            )
    return save_btn, edit_btn


def _add_gap_row(*, slot: str | None = None, half_height: bool = False) -> None:
    """Inserts a consistent gap row using rem units from NAV_THEME."""
    slot_key = str(slot or "default").strip() or "default"
    height_rem = _nav_theme_gap_rem(half=half_height)
    row_classes = ["myst-gap-row-host", "myst-status-gap-row", f"myst-gap-row-host-{slot_key}"]
    if half_height:
        row_classes.append("myst-gap-row-half")
        row_classes.append("myst-status-gap-half")
    with gr.Row(elem_id=f"myst-gap-row-{slot_key}", elem_classes=row_classes):
        gr.HTML(
            f"""
            <div class="myst-default-gap-row"
                 style="height: {height_rem}rem;
                        min-height: {height_rem}rem;
                        max-height: {height_rem}rem;
                        width: 100%;
                        margin: 0;
                        padding: 0;
                        line-height: 0;
                        display: block;
                        flex-shrink: 0;"
                 aria-hidden="true"></div>
            """
        )


def _place_status_gap_row(*, slot: str, half_height: bool = False) -> None:
    """Backward-compatible alias for legacy Presets/Render gap rows."""
    _add_gap_row(slot=slot, half_height=half_height)


def _status_zoom_nav_edit_btn_update(*, in_zoom: bool, edit_open: bool) -> gr.Update:
    classes = [
        "vqc-source-tab",
        "myst-status-preset-btn",
        "myst-status-nav-edit-btn",
        "edit-btn",
    ]
    if edit_open:
        classes.append("active")
    _ = in_zoom
    return gr.update(interactive=True, elem_classes=classes, variant="secondary")


def _status_zoom_back_to_grid() -> tuple:
    """Return from preset zoom to the 3×3 grid overview."""
    dials = dict(_GRAVITY_HOME_DIALS)
    slider_updates = _gravity_slider_control_updates(dials, edit_enabled=False)
    return (
        *_status_panel_levels_update(-1, grid_active_slot=None, visible=True),
        *_status_zoom_btn_updates(-1),
        -1,
        False,
        gr.update(visible=False),
        _status_zoom_nav_edit_btn_update(in_zoom=False, edit_open=False),
        *slider_updates,
        _status_zoom_save_btn_placeholder_update(),
        False,
    )


def _source_tab_btn_update(*, active: bool) -> gr.Update:
    """Source tab — matrix-green label when active; default brown body either way."""
    if active:
        return gr.update(
            interactive=False,
            elem_classes=["vqc-source-tab", "active"],
            variant="secondary",
        )
    return gr.update(interactive=True, elem_classes=["vqc-source-tab"], variant="secondary")


def _close_links_panels() -> tuple:
    """Hide both Links-bar panels and reset their tab highlights."""
    return (
        gr.update(visible=False),
        _source_tab_btn_update(active=False),
        False,
        gr.update(visible=False),
        _source_tab_btn_update(active=False),
        False,
    )


def _status_zoom_btn_classes(slot: int, active_slot: int) -> list[str]:
    classes = ["vqc-source-tab", "myst-status-preset-btn"]
    if int(slot) == int(active_slot):
        classes.append("active")
    return classes


def _status_zoom_btn_updates(active_slot: int) -> tuple:
    active = int(active_slot)
    return tuple(
        gr.update(
            interactive=(i != active),
            elem_classes=_status_zoom_btn_classes(i, active),
            variant="secondary",
        )
        for i in range(_STATUS_ZOOM_PRESET_COUNT)
    )


def _nav_to_status_page(current_page: str, content_open: bool) -> tuple:
    """Open Status page, or toggle its grid closed under the Status tab when already there."""
    grid_reset = _status_zoom_back_to_grid()
    skip_reset = tuple(gr.skip() for _ in grid_reset)
    if current_page == "status":
        new_open = not bool(content_open)
        reset = grid_reset if (not bool(content_open) and new_open) else skip_reset
        return (
            *_nav_to_page("status"),
            gr.update(visible=new_open),
            new_open,
            *reset,
        )
    return (
        *_nav_to_page("status"),
        gr.update(visible=True),
        True,
        *grid_reset,
    )


_README_RETURN_PAGES = frozenset({"home", "render", "status"})


def _readme_return_page(from_page: str) -> str:
    page = str(from_page or "home").strip().lower()
    return page if page in _README_RETURN_PAGES else "home"


def _open_readme_page(from_page: str) -> tuple:
    """Open Documentation full-page view; remember prior tab for Back."""
    return (*_nav_to_page("readme"), _readme_return_page(from_page))


def _readme_back_to_app(return_page: str) -> tuple:
    """Return from README to the tab the user came from."""
    page = _readme_return_page(return_page)
    return (*_nav_to_page(page), _home_demo_nav_visible(page == "home"))


def _home_demo_nav_visible(visible: bool) -> gr.Update:
    """Show or hide the Home-only Demo: A–I bar section."""
    classes = ["myst-home-demo-nav-section"]
    if visible:
        classes.append("myst-force-visible")
    return gr.update(visible=bool(visible), elem_classes=classes)


def _nav_to_page(page: str) -> tuple:
    """Switch between home, render, documentation, status, and edit; refresh unified nav."""
    on_render = page == "render"
    on_home = page == "home"
    on_readme = page == "readme"
    on_status = page == "status"
    closed = _close_links_panels()
    return (
        gr.update(visible=on_home),
        gr.update(visible=on_render),
        gr.update(visible=on_readme),
        gr.update(visible=on_status),
        gr.update(visible=False),
        _main_nav_btn_update("home", active=on_home),
        _main_nav_btn_update("render", active=on_render),
        _main_nav_btn_update("readme", active=on_readme),
        _main_nav_btn_update("status", active=on_status),
        *closed,
        page,
    )


def _toggle_newhere(is_open: bool) -> tuple:
    """Expand/collapse the beginner guide; close Claims if opening New here?."""
    show = not is_open
    return (
        gr.update(visible=show),
        _source_tab_btn_update(active=show),
        show,
        gr.update(visible=False),
        _source_tab_btn_update(active=False),
        False,
    )


def _toggle_claims(is_open: bool) -> tuple:
    """Expand/collapse VQC claims; close New here? if opening Claims."""
    show = not is_open
    return (
        gr.update(visible=show),
        _source_tab_btn_update(active=show),
        show,
        gr.update(visible=False),
        _source_tab_btn_update(active=False),
        False,
    )


def _minimize_newhere() -> tuple:
    return (
        gr.update(visible=False),
        _source_tab_btn_update(active=False),
        False,
    )


def _minimize_claims() -> tuple:
    return (
        gr.update(visible=False),
        _source_tab_btn_update(active=False),
        False,
    )


def _build_vqc_theme() -> gr.themes.Base:
    """Dark transparent theme — mystery gold/purple (HF-safe)."""
    return (
        gr.themes.Base(
            primary_hue=gr.themes.colors.amber,
            secondary_hue=gr.themes.colors.purple,
            neutral_hue=gr.themes.colors.zinc,
        )
        .set(
            body_background_fill="transparent",
            body_background_fill_dark="transparent",
            background_fill_primary="transparent",
            background_fill_primary_dark="transparent",
            background_fill_secondary="transparent",
            background_fill_secondary_dark="transparent",
            block_background_fill=_VQC_FIELD_FILL,
            block_background_fill_dark=_VQC_FIELD_FILL,
            panel_background_fill=_VQC_FIELD_FILL,
            panel_background_fill_dark=_VQC_FIELD_FILL,
            input_background_fill=_VQC_FIELD_FILL,
            input_background_fill_dark=_VQC_FIELD_FILL,
            body_text_color="#e8e0f8",
            body_text_color_dark="#e8e0f8",
            block_label_text_color="#c9b8ff",
            block_label_text_color_dark="#c9b8ff",
            block_title_text_color="#f0e6ff",
            block_title_text_color_dark="#f0e6ff",
            border_color_primary="rgba(255, 255, 255, 0.12)",
            border_color_primary_dark="rgba(255, 255, 255, 0.12)",
            button_primary_background_fill="#c9a227",
            button_primary_background_fill_dark="#c9a227",
            button_primary_text_color="#ffffff",
            button_primary_text_color_dark="#ffffff",
            button_secondary_background_fill="rgba(28, 22, 48, 0.92)",
            button_secondary_background_fill_dark="rgba(28, 22, 48, 0.92)",
            button_secondary_text_color="#e8e0f8",
            button_secondary_text_color_dark="#e8e0f8",
            checkbox_label_background_fill="transparent",
            checkbox_label_background_fill_dark="transparent",
            checkbox_label_background_fill_hover="transparent",
            checkbox_label_background_fill_hover_dark="transparent",
            slider_color=_VQC_ACCENT,
            slider_color_dark=_VQC_ACCENT,
            link_text_color=_VQC_ACCENT,
            link_text_color_dark=_VQC_ACCENT,
            link_text_color_hover="#d4b8ff",
            link_text_color_hover_dark="#d4b8ff",
            link_text_color_active=_VQC_ACCENT,
            link_text_color_active_dark=_VQC_ACCENT,
            link_text_color_visited=_VQC_ACCENT,
            link_text_color_visited_dark=_VQC_ACCENT,
        )
    )


# Wallpaper: #vqc-wallpaper (body child) + body::before fallback — cover, fixed to viewport.
WALLPAPER_HEAD = f"""
<style id="vqc-wallpaper-style">
#vqc-wallpaper {{
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: -9999 !important;
    pointer-events: none !important;
    background-color: #0a0818 !important;
    background-image: url('{WALLPAPER_URL}') !important;
    background-size: cover !important;
    background-position: center center !important;
    background-repeat: no-repeat !important;
}}
</style>
<script>
(function() {{
    window.mystOnHf = {'true' if is_hf_space() else 'false'};
    function mountWallpaper() {{
        if (document.getElementById('vqc-wallpaper')) return;
        var wp = document.createElement('div');
        wp.id = 'vqc-wallpaper';
        wp.setAttribute('aria-hidden', 'true');
        document.body.insertBefore(wp, document.body.firstChild);
    }}
    if (document.body) mountWallpaper();
    document.addEventListener('DOMContentLoaded', mountWallpaper);
    window.addEventListener('load', mountWallpaper);
}})();
(function() {{
    function mystSyncVisorHeight() {{
        var visor = document.querySelector('.myst-unit-cell-visor')
            || document.querySelector('.myst-gravity-single-viewport')
            || document.querySelector('#myst-gravity-viewport');
        var leftCard = document.querySelector('.myst-gravity-presets-tui-card');
        var page = document.querySelector('.myst-gravity-page');
        if (!visor) return;
        var top = visor.getBoundingClientRect().top;
        var anchorBottom = leftCard
            ? leftCard.getBoundingClientRect().bottom
            : (page ? page.getBoundingClientRect().bottom : window.innerHeight);
        var target = Math.max(638, Math.round(anchorBottom - top));
        document.documentElement.style.setProperty('--myst-unit-cell-visor-height', target + 'px');
        var vp = document.getElementById('unit-cell-main-view');
        if (vp) {{
            vp.style.setProperty('height', '100%', 'important');
            vp.style.setProperty('min-height', '100%', 'important');
            vp.style.setProperty('max-height', '100%', 'important');
            vp.style.setProperty('max-width', '100%', 'important');
        }}
        var vid = visor.querySelector('video');
        if (vid) {{
            vid.style.setProperty('height', '100%', 'important');
            vid.style.setProperty('max-height', '100%', 'important');
        }}
    }}
    function mystReflowViewport() {{
        mystSyncVisorHeight();
        var vp = document.getElementById('unit-cell-main-view');
        var visor = document.querySelector('.myst-unit-cell-visor');
        if (vp) void vp.offsetHeight;
        if (visor) void visor.offsetHeight;
        window.dispatchEvent(new Event('resize'));
    }}
    function bootViewportReflow() {{
        mystReflowViewport();
        requestAnimationFrame(mystReflowViewport);
        if (window.__mystViewportReflowObs) return;
        window.__mystViewportReflowObs = new MutationObserver(function() {{
            requestAnimationFrame(mystReflowViewport);
        }});
        var roots = [
            document.querySelector('.myst-unit-cell-visor'),
            document.querySelector('.myst-gravity-preset-tui-section'),
            document.querySelector('.myst-gravity-presets-tui-card'),
            document.querySelector('.myst-gravity-page'),
        ];
        roots.forEach(function(root) {{
            if (!root) return;
            window.__mystViewportReflowObs.observe(root, {{
                subtree: true, childList: true, attributes: true, attributeFilter: ['style', 'class']
            }});
        }});
        window.addEventListener('resize', function() {{
            requestAnimationFrame(mystReflowViewport);
        }});
        document.addEventListener('ended', function(e) {{
            var t = e.target;
            if (!t || !t.matches || !t.matches('.myst-unit-cell-visor video')) return;
            t.removeAttribute('src');
            requestAnimationFrame(mystReflowViewport);
        }}, true);
    }}
    if (document.body) bootViewportReflow();
    document.addEventListener('DOMContentLoaded', bootViewportReflow);
    window.addEventListener('load', bootViewportReflow);
}})();
(function() {{
    function mystHomePageActive() {{
        var gravityPage = document.querySelector('.myst-gravity-page');
        var renderPage = document.querySelector('.myst-render-page');
        var statusPage = document.querySelector('.myst-status-page');
        var readmePage = document.querySelector('.myst-readme-page');
        if (renderPage && !renderPage.classList.contains('hide')) return false;
        if (statusPage && !statusPage.classList.contains('hide')) return false;
        if (readmePage && !readmePage.classList.contains('hide')) return false;
        return !!(gravityPage && !gravityPage.classList.contains('hide'));
    }}
    function mystSyncHomeDemoNav() {{
        var section = document.getElementById('myst-home-demo-nav-section')
            || document.querySelector('.myst-home-demo-nav-section');
        var nav = document.getElementById('myst-gravity-child-nav');
        if (!section) return;
        var onHome = mystHomePageActive();
        if (onHome) {{
            section.classList.remove('hide');
            section.classList.add('myst-force-visible');
            section.style.setProperty('display', 'flex', 'important');
            section.style.setProperty('visibility', 'visible', 'important');
            if (nav) {{
                nav.classList.remove('hide');
                nav.style.setProperty('display', 'flex', 'important');
                nav.style.setProperty('visibility', 'visible', 'important');
            }}
        }} else {{
            section.classList.remove('myst-force-visible');
            section.classList.add('hide');
            section.style.setProperty('display', 'none', 'important');
            section.style.setProperty('visibility', 'hidden', 'important');
            if (nav) {{
                nav.style.setProperty('display', 'none', 'important');
                nav.style.setProperty('visibility', 'hidden', 'important');
            }}
        }}
    }}
    function bootHomeDemoNav() {{
        mystSyncHomeDemoNav();
        requestAnimationFrame(mystSyncHomeDemoNav);
        if (window.__mystHomeDemoNavObs) return;
        window.__mystHomeDemoNavObs = new MutationObserver(function() {{
            requestAnimationFrame(mystSyncHomeDemoNav);
        }});
        [
            document.querySelector('.myst-gravity-page'),
            document.querySelector('.myst-render-page'),
            document.querySelector('.myst-status-page'),
            document.querySelector('.myst-readme-page'),
        ].forEach(function(page) {{
            if (!page) return;
            window.__mystHomeDemoNavObs.observe(page, {{
                attributes: true,
                attributeFilter: ['class', 'style'],
            }});
        }});
        var section = document.getElementById('myst-home-demo-nav-section')
            || document.querySelector('.myst-home-demo-nav-section');
        if (section) {{
            window.__mystHomeDemoNavObs.observe(section, {{
                attributes: true,
                attributeFilter: ['class', 'style'],
            }});
        }}
    }}
    if (document.body) bootHomeDemoNav();
    document.addEventListener('DOMContentLoaded', bootHomeDemoNav);
    window.addEventListener('load', bootHomeDemoNav);
}})();
(function() {{
    function mystOpenRenderDetail(slot) {{
        var btn = document.getElementById('myst-render-cell-btn-' + slot);
        if (btn) btn.click();
    }}
    function mystRenderDetailPlotEl() {{
        return document.querySelector('#myst-render-detail-plot .plotly-graph-div')
            || document.querySelector('.myst-render-detail-plot .plotly-graph-div')
            || document.querySelector('.myst-render-detail-plot-host .plotly-graph-div')
            || document.querySelector('.myst-render-detail-plot-host #myst-render-detail-plotly');
    }}
    function mystResizeRenderDetailPlot() {{
        var split = document.querySelector('.myst-render-split-row');
        var host = document.querySelector('.myst-render-right-panel')
            || document.querySelector('.myst-render-detail-plot')
            || document.querySelector('#myst-render-detail-plot');
        var plotDiv = mystRenderDetailPlotEl();
        if (!host || !plotDiv || !window.Plotly) return;
        var rect = (split || host).getBoundingClientRect();
        var h = Math.max(550, Math.round(rect.height) - 4);
        plotDiv.style.height = h + 'px';
        plotDiv.style.width = '100%';
        try {{
            window.Plotly.Plots.resize(plotDiv);
        }} catch (_err) {{}}
    }}
    function mystRenderDetailZoom(factor) {{
        var plotDiv = mystRenderDetailPlotEl();
        if (!plotDiv || !window.Plotly) return;
        var cam = plotDiv.layout && plotDiv.layout.scene && plotDiv.layout.scene.camera;
        if (!cam || !cam.eye) return;
        var ex = cam.eye.x, ey = cam.eye.y, ez = cam.eye.z;
        try {{
            window.Plotly.relayout(plotDiv, {{
                'scene.camera.eye': {{ x: ex * factor, y: ey * factor, z: ez * factor }}
            }});
        }} catch (_err) {{}}
    }}
    function mystRenderDetailResetView() {{
        var plotDiv = mystRenderDetailPlotEl();
        if (!plotDiv || !window.Plotly) return;
        try {{
            window.Plotly.relayout(plotDiv, {{ 'scene.camera': null }});
        }} catch (_err) {{}}
    }}
    function mystRenderDetailDownloadPng() {{
        var plotDiv = mystRenderDetailPlotEl();
        if (!plotDiv || !window.Plotly) return;
        try {{
            window.Plotly.downloadImage(plotDiv, {{
                format: 'png',
                width: plotDiv.offsetWidth || 1200,
                height: plotDiv.offsetHeight || 800,
                filename: 'mystery-render-preset'
            }});
        }} catch (_err) {{}}
    }}
    function mystRenderDetailFullscreen() {{
        var host = document.querySelector('.myst-render-right-panel')
            || document.querySelector('.myst-render-detail-plot')
            || document.querySelector('#myst-render-detail-plot');
        if (!host) return;
        var req = host.requestFullscreen || host.webkitRequestFullscreen;
        if (req) req.call(host);
    }}
    function mystBindRenderDetailActions() {{
        var map = [
            ['myst-render-detail-zoom-in', function() {{ mystRenderDetailZoom(0.82); }}],
            ['myst-render-detail-zoom-out', function() {{ mystRenderDetailZoom(1.22); }}],
            ['myst-render-detail-reset', mystRenderDetailResetView],
            ['myst-render-detail-download', mystRenderDetailDownloadPng],
            ['myst-render-detail-fullscreen', mystRenderDetailFullscreen],
        ];
        map.forEach(function(entry) {{
            var btn = document.getElementById(entry[0]);
            if (!btn || btn.dataset.mystBound === '1') return;
            btn.dataset.mystBound = '1';
            btn.addEventListener('click', function(e) {{
                e.preventDefault();
                e.stopPropagation();
                entry[1]();
            }}, true);
        }});
    }}
    function mystBindRenderGridClicks() {{
        document.querySelectorAll('.myst-render-cell-clickable[data-slot]').forEach(function(cell) {{
            if (cell.dataset.mystBound === '1') return;
            cell.dataset.mystBound = '1';
            cell.addEventListener('click', function() {{
                mystOpenRenderDetail(cell.getAttribute('data-slot'));
            }});
            cell.addEventListener('keydown', function(e) {{
                if (e.key === 'Enter' || e.key === ' ') {{
                    e.preventDefault();
                    mystOpenRenderDetail(cell.getAttribute('data-slot'));
                }}
            }});
        }});
        if (document.querySelector('#myst-render-detail-wrapper:not(.hide), .myst-render-detail-view:not(.hide)')) {{
            requestAnimationFrame(function() {{
                mystResizeRenderDetailPlot();
                mystBindRenderDetailActions();
                requestAnimationFrame(mystResizeRenderDetailPlot);
            }});
        }}
    }}
    function bootRenderGridClicks() {{
        mystBindRenderGridClicks();
        mystBindRenderDetailActions();
        if (window.__mystRenderGridObs) return;
        window.__mystRenderGridObs = new MutationObserver(function() {{
            requestAnimationFrame(function() {{
                mystBindRenderGridClicks();
                mystBindRenderDetailActions();
                mystResizeRenderDetailPlot();
            }});
        }});
        var host = document.getElementById('myst-render-grid-host');
        if (host) {{
            window.__mystRenderGridObs.observe(host, {{
                subtree: true, childList: true
            }});
        }}
        var detailHost = document.getElementById('myst-render-detail-wrapper')
            || document.querySelector('.myst-render-detail-view');
        if (detailHost) {{
            window.__mystRenderGridObs.observe(detailHost, {{
                subtree: true, childList: true
            }});
        }}
        window.addEventListener('resize', function() {{
            requestAnimationFrame(mystResizeRenderDetailPlot);
        }});
    }}
    if (document.body) bootRenderGridClicks();
    document.addEventListener('DOMContentLoaded', bootRenderGridClicks);
    window.addEventListener('load', bootRenderGridClicks);
}})();
(function() {{
    function mystBreathingPlotDiv() {{
        return document.getElementById('myst-gravity-viewport-plotly')
            || document.querySelector('#myst-gravity-viewport .plotly-graph-div')
            || document.querySelector('.myst-gravity-viewport-plot-host .plotly-graph-div');
    }}
    function mystResizeGravityPlot() {{
        var host = document.getElementById('myst-gravity-viewport-wrapper')
            || document.getElementById('myst-gravity-viewport');
        var plot = mystBreathingPlotDiv();
        if (!host || !plot || !window.Plotly) return;
        var h = Math.max(580, Math.round(host.getBoundingClientRect().height) - 8);
        plot.style.height = h + 'px';
        plot.style.width = '100%';
        try {{ window.Plotly.Plots.resize(plot); }} catch (_err) {{}}
    }}
    function mystRunBreathingAnimate(plotDiv) {{
        if (!plotDiv || !window.Plotly) return false;
        var frames = (plotDiv._transitionData && plotDiv._transitionData.frames)
            || plotDiv.frames;
        if (!frames || frames.length <= 5) return false;
        mystResizeGravityPlot();
        var animOpts = {{
            frame: {{ duration: 70, redraw: true }},
            transition: {{ duration: 0 }},
            mode: 'immediate'
        }};
        try {{
            window.Plotly.animate(plotDiv, null, animOpts);
        }} catch (_err) {{
            console.warn('Plotly.animate failed', _err);
            return false;
        }}
        if (plotDiv.dataset.mystBreathingLoopBound !== '1') {{
            plotDiv.dataset.mystBreathingLoopBound = '1';
            plotDiv.on('plotly_animated', function() {{
                window.Plotly.animate(plotDiv, null, animOpts);
            }});
        }}
        return true;
    }}
    function mystBindBreathingMenuButtons() {{
        var host = document.getElementById('myst-gravity-viewport');
        if (!host) return;
        host.querySelectorAll('.updatemenu button, .modebar-btn').forEach(function(btn) {{
            if (btn.dataset.mystBreathingBound === '1') return;
            var label = (btn.getAttribute('data-title') || btn.textContent || '').toLowerCase();
            if (label.indexOf('breathing') < 0 && label.indexOf('play') < 0) return;
            btn.dataset.mystBreathingBound = '1';
            btn.addEventListener('click', function() {{
                setTimeout(function() {{
                    var plot = mystBreathingPlotDiv();
                    if (plot) mystRunBreathingAnimate(plot);
                }}, 80);
            }}, true);
        }});
    }}
    function startBreathingAnimation() {{
        var plotDiv = mystBreathingPlotDiv();
        if (!plotDiv) {{
            setTimeout(startBreathingAnimation, 500);
            return;
        }}
        if (plotDiv.dataset.mystBreathingPoll === '1') return;
        plotDiv.dataset.mystBreathingPoll = '1';
        var tries = 0;
        var checkFrames = setInterval(function() {{
            tries += 1;
            var plot = mystBreathingPlotDiv();
            if (!plot || !window.Plotly) {{
                if (tries > 40) clearInterval(checkFrames);
                return;
            }}
            var frameCount = 0;
            if (plot._transitionData && plot._transitionData.frames) {{
                frameCount = plot._transitionData.frames.length;
            }} else if (plot.frames) {{
                frameCount = plot.frames.length;
            }}
            mystBindBreathingMenuButtons();
            mystResizeGravityPlot();
            if (frameCount > 5) {{
                clearInterval(checkFrames);
                plot.dataset.mystBreathingPoll = '0';
                mystRunBreathingAnimate(plot);
            }} else if (tries > 40) {{
                clearInterval(checkFrames);
                plot.dataset.mystBreathingPoll = '0';
            }}
        }}, 300);
    }}
    function bootBreathingAnimation() {{
        setTimeout(startBreathingAnimation, 1200);
        if (window.__mystGravityBreathingObs) return;
        window.__mystGravityBreathingObs = new MutationObserver(function() {{
            var plot = mystBreathingPlotDiv();
            if (plot) {{
                plot.dataset.mystBreathingPoll = '0';
                plot.dataset.mystBreathingLoopBound = '0';
            }}
            mystBindBreathingMenuButtons();
            mystResizeGravityPlot();
            setTimeout(startBreathingAnimation, 400);
        }});
        var host = document.getElementById('myst-gravity-viewport')
            || document.getElementById('myst-gravity-viewport-wrapper')
            || document.querySelector('.myst-gravity-page');
        if (host) {{
            window.__mystGravityBreathingObs.observe(host, {{
                subtree: true, childList: true, attributes: true
            }});
        }}
        window.addEventListener('resize', function() {{
            requestAnimationFrame(mystResizeGravityPlot);
        }});
    }}
    window.mystForceBreathingAnimate = function() {{
        var plot = mystBreathingPlotDiv();
        if (!plot) {{
            console.log('plotly-graph-div not ready');
            return false;
        }}
        var n = (plot._transitionData && plot._transitionData.frames && plot._transitionData.frames.length)
            || (plot.frames && plot.frames.length) || 0;
        console.log('Frame count:', n);
        return mystRunBreathingAnimate(plot);
    }};
    document.addEventListener('DOMContentLoaded', bootBreathingAnimation);
    if (document.body) bootBreathingAnimation();
    window.addEventListener('load', bootBreathingAnimation);
}})();
</script>
"""

HFB_CSS = f"""
:root, :root .dark {{
    {_nav_theme_gradio_css_vars()}
    --myst-control-bar-height: 1.54rem;
    --myst-button-height: 26px;
    --myst-viewport-min-height: 18rem;
    --myst-viewport-plot-height: 700px;
    --myst-viewport-aspect: 7 / 5;
    --myst-unit-cell-plot-height: 31rem;
    --myst-unit-cell-visor-height: 31rem;
    --body-background-fill: transparent !important;
    --background-fill-primary: transparent !important;
    --background-fill-secondary: transparent !important;
    --block-background-fill: {_VQC_FIELD_FILL} !important;
    --panel-background-fill: {_VQC_FIELD_FILL} !important;
    --input-background-fill: {_VQC_FIELD_FILL} !important;
    --body-text-color: #e8e0f8 !important;
    --block-label-text-color: #c9b8ff !important;
    --block-title-text-color: #f0e6ff !important;
    --border-color-primary: rgba(255, 255, 255, 0.12) !important;
    --link-text-color: {_VQC_ACCENT} !important;
    --link-text-color-hover: #d4b8ff !important;
    --link-text-color-active: {_VQC_ACCENT} !important;
    --link-text-color-visited: {_VQC_ACCENT} !important;
    color-scheme: dark;
}}
/* Global compact controls (~25% shorter than prior 2.05rem bars) */
.gradio-container button,
.gradio-container .gr-button {{
    min-height: var(--myst-button-height, 26px) !important;
    height: auto !important;
    padding-top: 2px !important;
    padding-bottom: 2px !important;
    font-size: 0.81rem !important;
    line-height: 1.2 !important;
}}
.gradio-container .vqc-source-tab,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab,
.gradio-container .vqc-nav-cell a.vqc-source-tab {{
    min-height: var(--myst-control-bar-height, 1.54rem) !important;
    height: var(--myst-control-bar-height, 1.54rem) !important;
    padding-top: 2px !important;
    padding-bottom: 2px !important;
    font-size: 0.78rem !important;
}}
.gradio-container .myst-gravity-controls-accordion > .label-wrap,
.gradio-container .gr-accordion > .label-wrap {{
    min-height: var(--myst-control-bar-height, 1.54rem) !important;
    height: var(--myst-control-bar-height, 1.54rem) !important;
    padding-top: 4px !important;
    padding-bottom: 4px !important;
}}
.gradio-container button.myst-gravity-quick-preset,
.gradio-container button.myst-gravity-quick-preset span {{
    min-height: var(--myst-button-height, 26px) !important;
    height: var(--myst-button-height, 26px) !important;
    padding: 2px 10px !important;
    font-size: 0.78rem !important;
}}
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-header-slot,
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-header-slot.block,
.gradio-container .myst-gravity-cube-panel > .block:has(.myst-cube-viewport-header-fixed) {{
    flex: 0 0 auto !important;
    height: auto !important;
    max-height: 4.25rem !important;
    min-height: 0 !important;
    overflow: hidden !important;
    overflow-y: hidden !important;
    margin: 0 0 0.25rem 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-cube-viewport-header-fixed {{
    flex: 0 0 auto !important;
    max-height: 4rem !important;
    height: auto !important;
    overflow: hidden !important;
    overflow-y: hidden !important;
    margin: 0 !important;
    padding: 0.4rem 0.55rem !important;
    border: 1px solid #444 !important;
    border-radius: 6px !important;
    background: rgba(20, 20, 20, 0.65) !important;
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
    box-sizing: border-box !important;
}}
.gradio-container .myst-cube-viewport-header-fixed .myst-cube-viewport-title-line {{
    font-size: 0.94rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    color: #dddddd !important;
    line-height: 1.2 !important;
    margin: 0 0 0.2rem 0 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}
.gradio-container .myst-cube-viewport-header-fixed .myst-cube-viewport-sub-line {{
    font-size: 0.74rem !important;
    color: #aaaaaa !important;
    line-height: 1.25 !important;
    margin: 0 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-header {{
    flex: 0 0 auto !important;
    max-height: 4.25rem !important;
    padding-bottom: 0 !important;
    overflow: hidden !important;
}}
html {{
    background-color: #0a0818 !important;
    min-height: 100% !important;
}}
body {{
    background: transparent !important;
    background-color: transparent !important;
    color: #e8e0f8 !important;
    min-height: 100vh !important;
    width: 100% !important;
    overflow-x: hidden !important;
    position: relative !important;
}}
body::before {{
    content: "" !important;
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: -9998 !important;
    pointer-events: none !important;
    background-color: #0a0818 !important;
    background-image: url('{WALLPAPER_URL}') !important;
    background-size: cover !important;
    background-position: center center !important;
    background-repeat: no-repeat !important;
}}
#root, .app {{
    background: transparent !important;
    background-color: transparent !important;
    min-height: 0 !important;
    height: auto !important;
    width: 100% !important;
}}
.gradio-container {{
    {_nav_theme_gradio_css_vars()}
    --default-border-color: var(--nav-btn-border-color, {DEFAULT_BUTTON_BORDER_COLOR});
    --button-body-height: var(--nav-btn-height, {DEFAULT_BUTTON_BODY_HEIGHT});
    --default-gap: {DEFAULT_GAP};
    position: relative !important;
    width: 100% !important;
    max-width: 100% !important;
    min-height: 0 !important;
    height: auto !important;
    padding: 0.3rem 0.5rem 0.15rem !important;
    background: transparent !important;
    background-color: transparent !important;
    box-sizing: border-box !important;
}}
.gradio-container .main,
.gradio-container .main > .wrap {{
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}}
footer {{
    background: transparent !important;
}}
.gradio-container .main,
.gradio-container .wrap,
.gradio-container .contain,
.gradio-container .tabs,
.gradio-container .tabitem,
.gradio-container .form,
.gradio-container .column,
.gradio-container .row,
.gradio-container .gr-group,
.gradio-container label.wrap,
.gradio-container .label-wrap {{
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
}}
.gradio-container .block {{
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    background-color: {_VQC_FIELD_FILL} !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 10px !important;
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
}}
.gradio-container .markdown,
.gradio-container .prose,
.gradio-container .markdown p,
.gradio-container .markdown h1,
.gradio-container .markdown h2,
.gradio-container .markdown li {{
    color: #e8e0f8 !important;
}}
.gradio-container .vqc-source-tabs-row {{
    display: flex !important;
    flex-wrap: wrap !important;
    align-items: center !important;
    gap: 0.45rem 0.65rem !important;
    margin: 0.35rem 0 0.1rem 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
.gradio-container .myst-gravity-page .vqc-source-tabs-row {{
    margin: 0.12rem 0 0.03rem 0 !important;
}}
.gradio-container .vqc-source-nav-row {{
    margin: 0 0 0.1rem 0 !important;
}}
.gradio-container .vqc-links-panel {{
    margin: 0 0 0.35rem 0 !important;
    padding: 0.65rem 0.85rem !important;
}}
.gradio-container .vqc-links-panel .markdown h3 {{
    margin: 0 !important;
    font-size: 1rem !important;
    color: #f0e6ff !important;
}}
.gradio-container .vqc-panel-header-row {{
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    gap: 0.5rem !important;
    width: 100% !important;
    margin: 0 0 0.35rem 0 !important;
}}
.gradio-container .vqc-panel-header-row > .block,
.gradio-container .vqc-panel-header-row > .form {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
    flex: 1 1 auto !important;
    width: auto !important;
}}
.gradio-container button.vqc-panel-minimize {{
    flex: 0 0 auto !important;
    min-width: 2.1rem !important;
    padding: 0.2rem 0.6rem !important;
    border-radius: 999px !important;
    border: 1px solid {_VQC_TAB_GREEN_BORDER} !important;
    background: {_VQC_TAB_GREEN_BG} !important;
    color: {_VQC_TAB_GREEN_TEXT} !important;
    -webkit-text-fill-color: {_VQC_TAB_GREEN_TEXT} !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    line-height: 1 !important;
    box-shadow: none !important;
    opacity: 0.8 !important;
    cursor: pointer !important;
}}
.gradio-container button.vqc-panel-minimize:hover {{
    border-color: {_VQC_TAB_ORANGE_BORDER} !important;
    background: {_VQC_TAB_ORANGE_BG} !important;
    color: {_VQC_TAB_ORANGE_TEXT} !important;
    -webkit-text-fill-color: {_VQC_TAB_ORANGE_TEXT} !important;
}}
.gradio-container .vqc-source-tabs-row > .block,
.gradio-container .vqc-source-tabs-row > .form,
.gradio-container .vqc-source-tabs-row .block,
.gradio-container .vqc-source-tabs-row .form {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
    min-width: 0 !important;
    width: auto !important;
    flex: 0 0 auto !important;
}}
.gradio-container .vqc-source-tabs-row .html-container {{
    padding: 0 !important;
    margin: 0 !important;
}}
/* ========== NAVIGATION LABELS (Mystery: / Demo:) ========== */
.gradio-container .vqc-source-label {{
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    min-width: var(--nav-label-width, 4.75rem) !important;
    max-width: var(--nav-label-width, 4.75rem) !important;
    flex: 0 0 var(--nav-label-width, 4.75rem) !important;
    width: 100% !important;
    height: 100% !important;
    padding-right: var(--nav-label-padding-right, 10px) !important;
    margin-right: 0 !important;
    color: var(--nav-label-text-color, #e0e0e0) !important;
    font-size: var(--nav-label-font-size, 14px) !important;
    font-weight: var(--nav-label-font-weight, 500) !important;
    line-height: 1.2 !important;
    text-align: left !important;
    white-space: nowrap !important;
}}
.gradio-container .vqc-nav-spreadsheet-row > .block:has(.vqc-source-label),
.gradio-container .vqc-nav-spreadsheet-row > .form:has(.vqc-source-label) {{
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    text-align: left !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .vqc-nav-spreadsheet-row .html-container:has(.vqc-source-label) {{
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    width: 100% !important;
    text-align: left !important;
}}
.gradio-container button.myst-standard-back-btn {{
    border-radius: 9999px !important;
    padding: 0.45rem 1rem !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    background: #1a1a1a !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: 1px solid #444444 !important;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.45) !important;
}}
.gradio-container button.myst-standard-back-btn:hover {{
    background: #2a2a2a !important;
    border-color: #666666 !important;
    color: #ffffff !important;
}}
.gradio-container button.myst-standard-back-btn.vqc-source-tab {{
    background: #1a1a1a !important;
    border: 1px solid #444444 !important;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.45) !important;
}}
.gradio-container button.myst-standard-back-btn.vqc-source-tab.active {{
    color: #B85C00 !important;
    -webkit-text-fill-color: #B85C00 !important;
}}
.gradio-container .vqc-source-tab,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab span,
.gradio-container .vqc-nav-cell a.vqc-source-tab {{
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: var(--nav-btn-padding, 0.34rem 0.78rem) !important;
    border: var(--nav-btn-border-width, 2px) solid var(--nav-btn-border-color, #6b4f1d) !important;
    border-radius: var(--nav-btn-border-radius, 8px) !important;
    background: linear-gradient(180deg, #3d2e14 0%, #1f1608 100%) !important;
    background-color: var(--nav-btn-body-color, #2a1f10) !important;
    box-shadow: inset 0 1px 0 rgba(255, 220, 150, 0.12), 0 2px 4px rgba(0, 0, 0, 0.35) !important;
    color: var(--nav-btn-text-color, #ffffff) !important;
    -webkit-text-fill-color: var(--nav-btn-text-color, #ffffff) !important;
    text-decoration: none !important;
    font-weight: var(--nav-btn-font-weight, 500) !important;
    font-size: var(--nav-btn-font-size, 14px) !important;
    text-align: var(--nav-btn-text-align, center) !important;
    line-height: 1.2 !important;
    letter-spacing: 0.03em !important;
    text-transform: none !important;
    white-space: nowrap !important;
    min-width: var(--nav-btn-default-width, var(--nav-btn-min-width, 58px)) !important;
    min-height: var(--nav-btn-height, var(--myst-control-bar-height, 2.05rem)) !important;
    height: var(--nav-btn-height, var(--myst-control-bar-height, 2.05rem)) !important;
    box-sizing: border-box !important;
    width: auto !important;
    margin: 0 !important;
    opacity: 1 !important;
    text-shadow: none !important;
    transition: var(--nav-btn-transition, background 0.15s ease, border-color 0.15s ease, color 0.15s ease);
}}
.gradio-container a.vqc-source-tab:hover,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab:not(.active):hover,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab:not(.active):hover span {{
    color: #fff8e8 !important;
    -webkit-text-fill-color: #fff8e8 !important;
    background: linear-gradient(180deg, #6b4f1d 0%, #3d2e14 100%) !important;
    border-color: #8b6914 !important;
    text-decoration: none !important;
}}
.gradio-container .vqc-source-tabs-row button.vqc-source-tab {{
    cursor: pointer !important;
    font-family: inherit !important;
}}
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.secondary,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.secondary:hover,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.secondary:focus {{
    border: 2px solid #6b4f1d !important;
    background: linear-gradient(180deg, #3d2e14 0%, #1f1608 100%) !important;
    box-shadow: inset 0 1px 0 rgba(255, 220, 150, 0.12), 0 2px 4px rgba(0, 0, 0, 0.35) !important;
}}
.gradio-container .vqc-source-tabs-row button.vqc-source-tab:disabled:not(.active),
.gradio-container .vqc-source-tabs-row button.vqc-source-tab[disabled]:not(.active),
.gradio-container .vqc-source-tabs-row button.vqc-source-tab:disabled:not(.active) span,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab[disabled]:not(.active) span {{
    cursor: pointer !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: linear-gradient(180deg, #3d2e14 0%, #1f1608 100%) !important;
    text-decoration: none !important;
}}
.gradio-container .vqc-source-tab.active:not(.main-nav-btn):not(.shape-btn):not(.demo-btn),
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.active:not(.main-nav-btn):not(.shape-btn):not(.demo-btn),
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.active:not(.main-nav-btn):not(.shape-btn):not(.demo-btn) span,
.gradio-container .vqc-source-tab.active:not(.main-nav-btn):not(.shape-btn):not(.demo-btn):hover,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.active:not(.main-nav-btn):not(.shape-btn):not(.demo-btn):hover,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.active:not(.main-nav-btn):not(.shape-btn):not(.demo-btn):hover span,
.gradio-container a.vqc-source-tab.active:not(.main-nav-btn):not(.shape-btn):not(.demo-btn) {{
    color: {_VQC_MATRIX_GREEN} !important;
    -webkit-text-fill-color: {_VQC_MATRIX_GREEN} !important;
    background: linear-gradient(180deg, #3d2e14 0%, #1f1608 100%) !important;
    border-color: #6b4f1d !important;
    text-decoration: none !important;
    cursor: default !important;
    opacity: 1 !important;
    box-shadow: inset 0 1px 0 rgba(255, 220, 150, 0.12), 0 2px 4px rgba(0, 0, 0, 0.35) !important;
}}
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.active:not(.main-nav-btn):not(.shape-btn):not(.demo-btn):disabled,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.active:not(.main-nav-btn):not(.shape-btn):not(.demo-btn)[disabled],
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.active:not(.main-nav-btn):not(.shape-btn):not(.demo-btn):disabled span,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.active:not(.main-nav-btn):not(.shape-btn):not(.demo-btn)[disabled] span {{
    color: {_VQC_MATRIX_GREEN} !important;
    -webkit-text-fill-color: {_VQC_MATRIX_GREEN} !important;
    background: linear-gradient(180deg, #3d2e14 0%, #1f1608 100%) !important;
    border-color: #6b4f1d !important;
    text-decoration: none !important;
    cursor: default !important;
}}
/* ========== 9-COLUMN NAV BAR (label + button grid) ========== */
.gradio-container .myst-nav-bar-row {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: stretch !important;
    width: 100% !important;
    gap: var(--nav-grid-gap, 4px) !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-nav-bar-row > .gap {{
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-nav-bar-row > .block:has(.vqc-source-label),
.gradio-container .myst-nav-bar-row > .form:has(.vqc-source-label) {{
    flex: 0 0 var(--nav-label-width, 4.75rem) !important;
    width: var(--nav-label-width, 4.75rem) !important;
    min-width: var(--nav-label-width, 4.75rem) !important;
    max-width: var(--nav-label-width, 4.75rem) !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-nav-bar-row > .block:has(.nav-button-grid),
.gradio-container .myst-nav-bar-row > .form:has(.nav-button-grid) {{
    flex: 1 1 0% !important;
    min-width: 0 !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-render-action-row {{
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
}}
.gradio-container .myst-render-action-row > .block,
.gradio-container .myst-render-action-row > .form {{
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container button.full-width-btn,
.gradio-container button.myst-render-nav-render-btn.full-width-btn {{
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    height: var(--nav-btn-height, 2.05rem) !important;
    min-height: var(--nav-btn-height, 2.05rem) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: var(--nav-btn-font-size, 14px) !important;
    font-weight: var(--nav-btn-font-weight, 500) !important;
    box-sizing: border-box !important;
}}
.gradio-container button.full-width-btn:not(.active):hover,
.gradio-container button.myst-render-nav-render-btn.full-width-btn:not(.active):hover {{
    background: linear-gradient(180deg, #4a4a4a 0%, #3a3a3a 100%) !important;
    border-color: #8b6914 !important;
}}
.gradio-container .nav-button-grid,
.gradio-container .row.nav-button-grid,
.gradio-container .myst-nav-bar-row .nav-button-grid {{
    display: grid !important;
    grid-template-columns: repeat(9, minmax(0, 1fr)) !important;
    gap: var(--nav-grid-gap, 4px) !important;
    width: 100% !important;
    align-items: stretch !important;
    margin: 0 !important;
    padding: 0 !important;
    flex: 1 1 auto !important;
}}
.gradio-container .nav-button-grid > .gap {{
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .nav-button-grid > .block,
.gradio-container .nav-button-grid > .form {{
    min-width: 0 !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
.gradio-container .nav-button-grid button.vqc-source-tab,
.gradio-container .nav-button-grid button.save-btn,
.gradio-container .nav-button-grid button.edit-btn {{
    width: 100% !important;
    min-width: 0 !important;
    height: var(--nav-btn-height, 2.05rem) !important;
    min-height: var(--nav-btn-height, 2.05rem) !important;
    margin: 0 !important;
}}
.gradio-container .vqc-nav-label-spacer {{
    visibility: hidden !important;
}}
/* Gravity child nav — uniform sizing + align with main nav */
.gradio-container .myst-gravity-child-nav-row {{
    padding-left: 0 !important;
    margin-left: 0 !important;
    width: 100% !important;
}}
#myst-gravity-child-nav button.myst-status-preset-btn,
#myst-gravity-child-nav button.myst-gravity-preset-btn {{
    min-height: var(--nav-btn-height, 2.05rem) !important;
    height: var(--nav-btn-height, 2.05rem) !important;
    min-width: 0 !important;
    width: 100% !important;
    padding: var(--nav-btn-padding, 6px 12px) !important;
    font-size: var(--nav-btn-font-size, 14px) !important;
    font-weight: var(--nav-btn-font-weight, 500) !important;
    margin-right: 0 !important;
}}
#myst-gravity-child-nav .myst-gravity-child-nav-label {{
    color: var(--nav-label-text-color, #e0e0e0) !important;
    text-transform: none !important;
}}
/* Main nav tabs — match Demo (A–I) child tab height */
.gradio-container .vqc-main-nav-row button.vqc-source-tab,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab {{
    min-height: var(--nav-btn-height, 2.05rem) !important;
    height: var(--nav-btn-height, 2.05rem) !important;
    padding: var(--nav-btn-padding, 6px 12px) !important;
    font-size: var(--nav-btn-font-size, 14px) !important;
    font-weight: var(--nav-btn-font-weight, 500) !important;
}}

#myst-gravity-viewport-wrapper,
.gradio-container .myst-gravity-page .myst-gravity-single-viewport {{
    position: relative !important;
    min-height: 620px !important;
    height: 620px !important;
    flex: 1 1 auto !important;
    width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    margin: 0 !important;
    padding: 0 !important;
    background: #0a0a0f !important;
    overflow: visible !important;
}}
.gradio-container .myst-gravity-page .myst-gravity-video-host,
.gradio-container .myst-gravity-page .myst-gravity-viewport-anim .html-container,
.gradio-container .myst-gravity-page .myst-gravity-viewport-anim .prose {{
    width: 100% !important;
    height: 100% !important;
    min-height: 580px !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: visible !important;
}}
.gradio-container .myst-gravity-page #myst-gravity-viewport,
.gradio-container .myst-gravity-page #myst-gravity-viewport .block,
.gradio-container .myst-gravity-page #myst-gravity-viewport .video-container,
.gradio-container .myst-gravity-page #myst-gravity-viewport .wrap,
.gradio-container .myst-gravity-page #myst-gravity-viewport video,
.gradio-container .myst-gravity-page .myst-gravity-demo-video video {{
    width: 100% !important;
    height: 100% !important;
    min-height: 580px !important;
    max-height: 620px !important;
    object-fit: contain !important;
    background: #0a0a0f !important;
    display: block !important;
}}
.gradio-container .myst-gravity-page #myst-gravity-viewport-plot,
.gradio-container .myst-gravity-page .myst-gravity-viewport-plot {{
    flex: 1 1 auto !important;
    width: 100% !important;
    min-height: 580px !important;
}}
#myst-gravity-viewport .plotly-graph-div,
#myst-gravity-viewport-plotly,
.gradio-container .myst-gravity-viewport-plot-host,
.gradio-container .myst-gravity-viewport-plot-host .plotly-graph-div,
.gradio-container .myst-gravity-viewport-plot-host #myst-gravity-viewport-plotly {{
    height: 100% !important;
    min-height: 600px !important;
    width: 100% !important;
}}
.gradio-container .myst-gravity-page #myst-gravity-viewport .html-container,
.gradio-container .myst-gravity-page #myst-gravity-viewport .prose {{
    width: 100% !important;
    height: 100% !important;
    min-height: 600px !important;
    padding: 0 !important;
    margin: 0 !important;
}}
.gradio-container .myst-gravity-page #myst-gravity-viewport {{
    flex: 1 1 auto !important;
    width: 100% !important;
    height: 100% !important;
    min-height: 600px !important;
    margin: 0 !important;
    padding: 0 !important;
    background: #0a0a0f !important;
    border: 1px solid #2a2a3a !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-gravity-page .myst-gravity-viewport-inner {{
    width: 100% !important;
    height: 100% !important;
    min-height: calc(100dvh - 10rem) !important;
    display: flex !important;
    flex-direction: column !important;
    background: #0a0a0f !important;
}}
.gradio-container .myst-gravity-page .myst-gravity-viewport-title {{
    flex: 0 0 auto !important;
    color: #f5e6c8 !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    padding: 0.55rem 0.75rem 0.2rem !important;
}}
.gradio-container .myst-gravity-page .myst-gravity-viewport-sub {{
    flex: 0 0 auto !important;
    color: #aaaaaa !important;
    font-size: 0.78rem !important;
    padding: 0 0.75rem 0.45rem !important;
}}
.gradio-container .myst-gravity-page .myst-gravity-demo-video,
.gradio-container .myst-gravity-page .myst-gravity-viewport-frame,
.gradio-container .myst-gravity-page .myst-gravity-viewport-frame img {{
    flex: 1 1 auto !important;
    width: 100% !important;
    height: 100% !important;
    min-height: calc(100dvh - 12rem) !important;
    object-fit: contain !important;
    background: #000000 !important;
}}
.gradio-container .myst-gravity-page #myst-gravity-viewport .block {{
    flex: 1 1 auto !important;
    width: 100% !important;
    height: 100% !important;
    min-height: 600px !important;
    display: flex !important;
    flex-direction: column !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-gravity-page #myst-gravity-viewport .plot-container {{
    flex: 1 1 auto !important;
    width: 100% !important;
    height: 100% !important;
    min-height: 600px !important;
    background: #000000 !important;
    padding: 0 !important;
    margin: 0 !important;
}}
.gradio-container .myst-gravity-page #myst-gravity-viewport .plotly-graph-div,
.gradio-container .myst-gravity-page #myst-gravity-viewport .js-plotly-plot {{
    flex: 1 1 auto !important;
    width: 100% !important;
    height: 100% !important;
    min-height: 600px !important;
    max-height: none !important;
}}
.gradio-container .myst-gravity-page .myst-gravity-viewport .modebar,
.gradio-container .myst-gravity-page #myst-gravity-viewport .modebar {{
    right: 0.35rem !important;
    top: 0.2rem !important;
}}
.gradio-container a:hover:not(.vqc-source-tab),
.gradio-container .markdown a:hover:not(.vqc-source-tab),
.gradio-container .prose a:hover:not(.vqc-source-tab) {{
    color: #d4b8ff !important;
    -webkit-text-fill-color: #d4b8ff !important;
}}
.gradio-container .vqc-build-label {{
    color: #a89ec8 !important;
    font-size: 0.9rem;
    margin: 0 0 0.5rem 0;
}}
.gradio-container .vqc-animations-page .markdown h2 {{
    font-size: 1.35rem !important;
    margin: 0.15rem 0 0.35rem 0 !important;
}}
.gradio-container .vqc-animations-page .markdown p {{
    font-size: 0.92rem !important;
    margin: 0.15rem 0 0.35rem 0 !important;
    line-height: 1.45 !important;
}}
.gradio-container .vqc-animations-page,
.gradio-container .vqc-animations-page > .block,
.gradio-container .vqc-animations-page .html-container {{
    width: 100% !important;
    max-width: 100% !important;
}}
.gradio-container .vqc-screencast-wrap {{
    display: grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    gap: 0.75rem !important;
    width: 100% !important;
    max-width: 100% !important;
    margin: 0.25rem 0 0.5rem 0 !important;
    padding: 0 !important;
    box-sizing: border-box !important;
}}
.gradio-container .vqc-screencast-video {{
    width: 100% !important;
    min-width: 0 !important;
    height: auto !important;
    aspect-ratio: 16 / 9 !important;
    max-height: min(36vh, 360px) !important;
    object-fit: contain !important;
    border-radius: 8px !important;
    display: block !important;
    background: rgba(10, 8, 24, 0.35) !important;
}}
.gradio-container .vqc-optics-panel {{
    background: linear-gradient(165deg, #2a1838 0%, #1a1028 38%, #120c18 100%) !important;
    border: 3px solid #6a4c93 !important;
    border-radius: 14px !important;
    box-shadow:
        inset 0 2px 8px rgba(255, 220, 150, 0.08),
        inset 0 -4px 14px rgba(0, 0, 0, 0.55),
        0 8px 22px rgba(0, 0, 0, 0.45) !important;
    padding: 0 1rem 1rem !important;
    margin: 0.5rem 0 0.75rem 0 !important;
    gap: 0 !important;
}}
.gradio-container .vqc-optics-panel > .gap {{
    display: none !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .vqc-optics-panel > .block,
.gradio-container .vqc-optics-panel .block {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
.gradio-container .vqc-optics-panel-header {{
    display: flex !important;
    flex-wrap: wrap !important;
    align-items: center !important;
    gap: 0.75rem 1.1rem !important;
    margin: 0 0 0 0 !important;
    padding: 0.7rem 0.85rem 1.35rem !important;
    border: none !important;
    border-bottom: 1px solid rgba(106, 76, 147, 0.55) !important;
    border-radius: 10px 10px 0 0 !important;
    background: linear-gradient(180deg, #1f1428 0%, #0f0a14 100%) !important;
    box-shadow: inset 0 0 18px rgba(0, 0, 0, 0.65) !important;
    width: 100% !important;
    min-height: 5.25rem !important;
}}
.gradio-container .vqc-optics-panel-header > .block,
.gradio-container .vqc-optics-panel-header > .form,
.gradio-container .vqc-optics-panel-header .block,
.gradio-container .vqc-optics-panel-header .form {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
    min-width: 0 !important;
}}
.gradio-container .vqc-optics-panel-header > .block:first-child,
.gradio-container .vqc-optics-panel-header > .form:first-child {{
    flex: 0 0 auto !important;
    width: auto !important;
}}
.gradio-container .vqc-optics-panel-nav {{
    flex: 1 1 18rem !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 0.28rem !important;
    justify-content: center !important;
    min-width: 0 !important;
    width: auto !important;
}}
.gradio-container .vqc-optics-panel-nav > .block,
.gradio-container .vqc-optics-panel-nav > .form {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
    width: 100% !important;
}}
.gradio-container .vqc-optics-panel-nav .vqc-source-tabs-row {{
    margin: 0 !important;
}}
.gradio-container .myst-main-nav,
.gradio-container .vqc-main-nav-row {{
    margin-bottom: 0 !important;
}}
/* Equal-width nav buttons — Mystery + Demo rows share 9-column grid */
.gradio-container .myst-main-nav button.vqc-source-tab,
.gradio-container #myst-gravity-child-nav button.vqc-source-tab,
.gradio-container #myst-render-sub-nav button.vqc-source-tab,
.gradio-container #myst-status-zoom-nav button.vqc-source-tab,
.gradio-container .myst-save-edit-row button.save-btn,
.gradio-container .myst-save-edit-row button.edit-btn {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-width: var(--nav-btn-default-width, 58px) !important;
    width: 100% !important;
    flex: 1 1 0% !important;
    text-align: var(--nav-btn-text-align, center) !important;
    padding: var(--nav-btn-padding, 6px 12px) !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-main-nav button.vqc-source-tab span,
.gradio-container #myst-gravity-child-nav button.vqc-source-tab span,
.gradio-container #myst-render-sub-nav button.vqc-source-tab span,
.gradio-container #myst-status-zoom-nav button.vqc-source-tab span,
.gradio-container .myst-save-edit-row button.save-btn span,
.gradio-container .myst-save-edit-row button.edit-btn span {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-width: 0 !important;
    width: 100% !important;
    flex: 1 1 0% !important;
    text-align: var(--nav-btn-text-align, center) !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-main-nav > .block,
.gradio-container #myst-gravity-child-nav > .block {{
    min-width: 0 !important;
    width: 100% !important;
}}
.gradio-container .myst-unified-nav-host {{
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
    row-gap: 0 !important;
    flex-shrink: 0 !important;
}}
.gradio-container .myst-unified-nav-host > .gap {{
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}}
.gradio-container .myst-unified-nav-host + .gap {{
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}}
.gradio-container .myst-unified-nav-host + .column.myst-gravity-page,
.gradio-container .myst-unified-nav-host + .myst-gravity-page,
.gradio-container .myst-unified-nav-host + .column.myst-render-page,
.gradio-container .myst-unified-nav-host + .myst-render-page,
.gradio-container .myst-unified-nav-host + .column.myst-status-page,
.gradio-container .myst-unified-nav-host + .myst-status-page {{
    margin-top: 0 !important;
    padding-top: 0 !important;
}}
.gradio-container .myst-gap-row-host-after-main-nav,
.gradio-container #myst-gap-row-after-main-nav {{
    margin: 0 !important;
    padding: 0 !important;
    min-height: var(--myst-default-gap-height, {_myst_default_gap_height}) !important;
    height: var(--myst-default-gap-height, {_myst_default_gap_height}) !important;
    max-height: var(--myst-default-gap-height, {_myst_default_gap_height}) !important;
    flex: 0 0 var(--myst-default-gap-height, {_myst_default_gap_height}) !important;
    overflow: hidden !important;
}}
.gradio-container .myst-render-page .myst-render-stack > .block:first-child,
.gradio-container .myst-render-page .myst-render-stack > .form:first-child,
.gradio-container .myst-status-page .myst-status-stack > .block:first-child,
.gradio-container .myst-status-page .myst-status-stack > .form:first-child {{
    margin-top: 0 !important;
    padding-top: 0 !important;
}}
/* Demo bar → viewport: theme gap only (0.20rem) */
.gradio-container .myst-gravity-page > .block:has(#myst-gap-row-after-demo-nav),
.gradio-container .myst-gravity-page > .form:has(#myst-gap-row-after-demo-nav),
.gradio-container .myst-gap-row-host-after-demo-nav,
.gradio-container #myst-gap-row-after-demo-nav {{
    margin: 0 !important;
    padding: 0 !important;
    min-height: var(--myst-default-gap-height, {_myst_default_gap_height}) !important;
    height: var(--myst-default-gap-height, {_myst_default_gap_height}) !important;
    max-height: var(--myst-default-gap-height, {_myst_default_gap_height}) !important;
    flex: 0 0 var(--myst-default-gap-height, {_myst_default_gap_height}) !important;
    overflow: hidden !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
.gradio-container .myst-gravity-page > .block:has(.myst-gravity-single-viewport),
.gradio-container .myst-gravity-page > .block:has(#myst-gravity-viewport-wrapper),
.gradio-container .myst-gravity-page #myst-gravity-viewport-plot,
.gradio-container .myst-gravity-page #myst-gravity-viewport-wrapper,
.gradio-container .myst-gravity-page .myst-gravity-single-viewport {{
    margin-top: 0 !important;
    padding-top: 0 !important;
}}
.gradio-container .myst-unified-nav-host .vqc-source-tabs-row,
.gradio-container .myst-unified-nav-host .myst-main-nav,
.gradio-container .myst-unified-nav-host .myst-secondary-nav {{
    margin: 0 !important;
}}
.gradio-container .myst-home-demo-nav-section {{
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
    row-gap: 0 !important;
    min-height: fit-content !important;
    flex-shrink: 0 !important;
    flex-direction: column !important;
}}
.gradio-container .myst-home-demo-nav-section.hide {{
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    overflow: hidden !important;
    opacity: 0 !important;
}}
.gradio-container:has(.myst-render-page:not(.hide):not(.hidden)) .myst-home-demo-nav-section,
.gradio-container:has(.myst-status-page:not(.hide):not(.hidden)) .myst-home-demo-nav-section,
.gradio-container:has(.myst-readme-page:not(.hide):not(.hidden)) .myst-home-demo-nav-section {{
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    overflow: hidden !important;
    opacity: 0 !important;
}}
.gradio-container .myst-home-demo-nav-section.myst-force-visible:not(.hide) {{
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    height: auto !important;
    min-height: fit-content !important;
    max-height: none !important;
    overflow: visible !important;
}}
.gradio-container .myst-home-demo-nav-section:not(.hide) #myst-gravity-child-nav,
.gradio-container .myst-home-demo-nav-section.myst-force-visible:not(.hide) #myst-gravity-child-nav {{
    display: flex !important;
    visibility: visible !important;
    width: 100% !important;
    opacity: 1 !important;
}}
.gradio-container .myst-home-demo-nav-section.hide #myst-gravity-child-nav,
.gradio-container:has(.myst-render-page:not(.hide):not(.hidden)) #myst-gravity-child-nav,
.gradio-container:has(.myst-status-page:not(.hide):not(.hidden)) #myst-gravity-child-nav,
.gradio-container:has(.myst-readme-page:not(.hide):not(.hidden)) #myst-gravity-child-nav {{
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    min-height: 0 !important;
    overflow: hidden !important;
    opacity: 0 !important;
}}
/* Render / Presets secondary nav — same theme grid as Home */
.gradio-container .myst-render-page .myst-nav-bar-row,
.gradio-container .myst-status-page .myst-nav-bar-row {{
    width: 100% !important;
    margin: 0 !important;
}}
.gradio-container .myst-render-page .nav-button-grid,
.gradio-container .myst-status-page .nav-button-grid {{
    display: grid !important;
    grid-template-columns: repeat(9, minmax(0, 1fr)) !important;
    gap: var(--nav-grid-gap, 4px) !important;
}}
.gradio-container .myst-home-demo-nav-section > .gap {{
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}}
.gradio-container .myst-gap-row-host,
.gradio-container .myst-gap-row-host > .block,
.gradio-container .myst-gap-row-host > .form {{
    margin: 0 !important;
    padding: 0 !important;
    min-height: 0 !important;
    gap: 0 !important;
    flex-shrink: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
.gradio-container .myst-main-nav,
.gradio-container .myst-secondary-nav {{
    margin-bottom: 0 !important;
}}
.gradio-container .myst-secondary-nav {{
    margin-top: 0 !important;
    gap: var(--nav-grid-gap, 4px) !important;
}}
/* Mystery → Demo: theme gap only (Home: gap row; Render/Presets: page sub-nav margin) */
.gradio-container .myst-unified-nav-host .myst-main-nav + .myst-gap-row-host-after-main-nav + .myst-home-demo-nav-section:not(.hide) .myst-secondary-nav,
.gradio-container .myst-unified-nav-host .myst-main-nav + .myst-gap-row-host-after-main-nav + .myst-home-demo-nav-section.myst-force-visible:not(.hide) .myst-secondary-nav {{
    margin-top: 0 !important;
}}
.gradio-container:has(.myst-render-page:not(.hide):not(.hidden)) #myst-gap-row-after-main-nav,
.gradio-container:has(.myst-render-page:not(.hide):not(.hidden)) .myst-gap-row-host-after-main-nav {{
    min-height: 0 !important;
    height: 0 !important;
    max-height: 0 !important;
    flex: 0 0 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}}
.gradio-container:has(.myst-status-page:not(.hide):not(.hidden)) #myst-gap-row-after-main-nav,
.gradio-container:has(.myst-status-page:not(.hide):not(.hidden)) .myst-gap-row-host-after-main-nav {{
    min-height: 0 !important;
    height: 0 !important;
    max-height: 0 !important;
    flex: 0 0 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}}
.gradio-container:has(.myst-readme-page:not(.hide):not(.hidden)) #myst-gap-row-after-main-nav,
.gradio-container:has(.myst-readme-page:not(.hide):not(.hidden)) .myst-gap-row-host-after-main-nav {{
    min-height: 0 !important;
    height: 0 !important;
    max-height: 0 !important;
    flex: 0 0 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}}
/* Gradio Columns also use class "gap" — never hide .myst-unified-nav-host ~ .gap (it hides page columns). */
.gradio-container:has(.myst-render-page:not(.hide):not(.hidden)) .myst-render-page,
.gradio-container:has(.myst-render-page:not(.hide):not(.hidden)) .myst-render-page > .block,
.gradio-container:has(.myst-render-page:not(.hide):not(.hidden)) .myst-render-page > .form,
.gradio-container:has(.myst-render-page:not(.hide):not(.hidden)) .myst-render-page > .column,
.gradio-container:has(.myst-render-page:not(.hide):not(.hidden)) .myst-render-stack,
.gradio-container:has(.myst-status-page:not(.hide):not(.hidden)) .myst-status-page,
.gradio-container:has(.myst-status-page:not(.hide):not(.hidden)) .myst-status-page > .block,
.gradio-container:has(.myst-status-page:not(.hide):not(.hidden)) .myst-status-page > .form,
.gradio-container:has(.myst-status-page:not(.hide):not(.hidden)) .myst-status-page > .column,
.gradio-container:has(.myst-status-page:not(.hide):not(.hidden)) .myst-status-stack {{
    display: flex !important;
    visibility: visible !important;
    margin-top: 0 !important;
    padding-top: 0 !important;
    overflow: visible !important;
    pointer-events: auto !important;
}}
.gradio-container:has(.myst-gravity-page:not(.hide):not(.hidden)) .myst-gravity-page,
.gradio-container:has(.myst-gravity-page:not(.hide):not(.hidden)) .myst-gravity-page > .block,
.gradio-container:has(.myst-gravity-page:not(.hide):not(.hidden)) .myst-gravity-page > .form,
.gradio-container:has(.myst-gravity-page:not(.hide):not(.hidden)) .myst-gravity-page > .column,
.gradio-container:has(.myst-gravity-page:not(.hide):not(.hidden)) #myst-gravity-viewport-wrapper,
.gradio-container:has(.myst-gravity-page:not(.hide):not(.hidden)) .myst-gravity-single-viewport,
.gradio-container:has(.myst-gravity-page:not(.hide):not(.hidden)) #myst-gravity-viewport-plot {{
    display: flex !important;
    visibility: visible !important;
    height: auto !important;
    min-height: 0 !important;
    overflow: visible !important;
    pointer-events: auto !important;
}}
.gradio-container:has(.myst-gravity-page:not(.hide):not(.hidden)) #myst-gravity-viewport-plot {{
    display: block !important;
}}
.gradio-container:has(.myst-render-page:not(.hide):not(.hidden)) #myst-render-sub-nav.myst-secondary-nav,
.gradio-container:has(.myst-status-page:not(.hide):not(.hidden)) #myst-status-zoom-nav.myst-secondary-nav {{
    margin-top: var(--myst-default-gap-height, {_myst_default_gap_height}) !important;
    margin-bottom: 0 !important;
}}
/* Consistent nav button width from NAV_THEME */
.gradio-container button.vqc-source-tab.main-nav-btn,
.gradio-container button.vqc-source-tab.shape-btn,
.gradio-container button.vqc-source-tab.demo-btn,
.gradio-container .myst-save-edit-row button.save-btn,
.gradio-container .myst-save-edit-row button.edit-btn {{
    min-width: var(--nav-btn-default-width, 58px) !important;
    box-sizing: border-box !important;
}}
.gradio-container .nav-button-grid button.vqc-source-tab,
.gradio-container .nav-button-grid button.save-btn,
.gradio-container .nav-button-grid button.edit-btn {{
    width: 100% !important;
    min-width: var(--nav-btn-default-width, 58px) !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-default-gap-row {{
    display: block !important;
    width: 100% !important;
    min-height: var(--myst-default-gap-height, {_myst_default_gap_height}) !important;
    height: var(--myst-default-gap-height, {_myst_default_gap_height}) !important;
    max-height: var(--myst-default-gap-height, {_myst_default_gap_height}) !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    flex: 0 0 auto !important;
    flex-shrink: 0 !important;
}}
.gradio-container .myst-default-gap-row > .block,
.gradio-container .myst-default-gap-row > .form {{
    width: 100% !important;
    min-height: var(--myst-default-gap-height) !important;
    height: var(--myst-default-gap-height) !important;
    max-height: var(--myst-default-gap-height) !important;
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
.gradio-container .myst-gap-fill,
.gradio-container .myst-gap-fill-host,
.gradio-container .myst-gap-fill-host .html-container {{
    display: block !important;
    width: 100% !important;
    min-height: var(--myst-default-gap-height) !important;
    max-height: var(--myst-default-gap-height) !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 0 !important;
    font-size: 0 !important;
    overflow: hidden !important;
}}
.gradio-container .myst-gap-row-half {{
    min-height: var(--myst-half-gap-height) !important;
    height: var(--myst-half-gap-height) !important;
    max-height: var(--myst-half-gap-height) !important;
}}
.gradio-container .myst-gap-row-half .myst-gap-fill,
.gradio-container .myst-gap-row-half .myst-gap-fill-host {{
    min-height: var(--myst-half-gap-height) !important;
    max-height: var(--myst-half-gap-height) !important;
}}
/* ========== MAIN MYSTERY: TABS (Home, Render, Presets, Docs) ========== */
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.main-nav-btn.active,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.main-nav-btn.active span,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.main-nav-btn.active:disabled,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.main-nav-btn.active[disabled],
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.main-nav-btn.active:disabled span,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.main-nav-btn.active[disabled] span {{
    color: var(--nav-btn-active-text-color, #00FF00) !important;
    -webkit-text-fill-color: var(--nav-btn-active-text-color, #00FF00) !important;
    border-color: var(--nav-btn-active-border-color, #00FF00) !important;
    background-color: var(--nav-btn-active-body-color, #1a3d2a) !important;
    box-shadow: 0 0 12px rgba(0, 255, 0, 0.75), 0 0 22px rgba(0, 255, 0, 0.45), 0 0 0 1px var(--nav-btn-active-border-color, #00FF00) !important;
    font-weight: 600 !important;
}}
/* ========== SHAPE TABS (D4, D6, D8, D12, D20) ========== */
.gradio-container button.shape-btn {{
    font-weight: var(--nav-btn-font-weight, 500) !important;
    min-width: 0 !important;
    padding: var(--nav-btn-shape-padding, 6px 10px) !important;
}}
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.shape-btn.active,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.shape-btn.active span,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.shape-btn.active:disabled,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.shape-btn.active[disabled],
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.shape-btn.active:disabled span,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.shape-btn.active[disabled] span {{
    color: cyan !important;
    -webkit-text-fill-color: cyan !important;
    border-color: cyan !important;
    box-shadow: 0 0 14px rgba(0, 255, 255, 0.85), 0 0 26px rgba(0, 255, 255, 0.5), 0 0 0 1px cyan !important;
    font-weight: 600 !important;
}}
/* ========== DEMO: BAR (A–I) + Render/Presets 01–09 ========== */
.gradio-container button.vqc-source-tab.demo-btn.active,
.gradio-container button.vqc-source-tab.demo-btn.active:disabled,
.gradio-container button.vqc-source-tab.demo-btn.active[disabled],
#myst-gravity-child-nav button.vqc-source-tab.demo-btn.active {{
    border-color: orange !important;
    box-shadow: 0 0 12px rgba(255, 165, 0, 0.8), 0 0 22px rgba(255, 165, 0, 0.5), 0 0 0 1px orange !important;
    font-weight: 600 !important;
}}
.gradio-container .vqc-nav-spreadsheet-row.vqc-nav-spreadsheet-row-8 {{
    grid-template-columns: 4.75rem repeat(8, minmax(3.2rem, 1fr)) !important;
}}
.gradio-container .myst-demo-preset-nav-row,
.gradio-container .vqc-status-preset-nav-row {{
    margin: 0 !important;
    width: 100% !important;
    overflow: visible !important;
}}
.gradio-container .myst-secondary-nav .vqc-source-label {{
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    padding: 0 var(--nav-label-padding-right, 10px) 0 0 !important;
    font-size: var(--nav-label-font-size, 14px) !important;
    font-weight: var(--nav-label-font-weight, 500) !important;
    color: var(--nav-label-text-color, #e0e0e0) !important;
    white-space: nowrap !important;
    text-align: left !important;
}}
#myst-render-sub-nav button.vqc-source-tab,
#myst-status-zoom-nav button.vqc-source-tab {{
    min-width: 0 !important;
    width: 100% !important;
    padding: var(--nav-btn-padding, 6px 12px) !important;
    box-sizing: border-box !important;
}}
/* ========== NAVIGATION BUTTONS — center label text ========== */
.gradio-container .vqc-source-tab,
.gradio-container button.vqc-source-tab.demo-btn,
.gradio-container button.vqc-source-tab.main-nav-btn,
.gradio-container button.vqc-source-tab.shape-btn,
.gradio-container .myst-save-edit-row button.save-btn,
.gradio-container .myst-save-edit-row button.edit-btn {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: var(--nav-btn-text-align, center) !important;
}}
.gradio-container .vqc-source-tabs-row button.vqc-source-tab span,
.gradio-container button.vqc-source-tab.demo-btn span,
.gradio-container button.vqc-source-tab.main-nav-btn span,
.gradio-container button.vqc-source-tab.shape-btn span,
.gradio-container .myst-save-edit-row button.save-btn span,
.gradio-container .myst-save-edit-row button.edit-btn span {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
    text-align: var(--nav-btn-text-align, center) !important;
}}
.gradio-container .myst-save-edit-row {{
    align-items: stretch !important;
    width: 100% !important;
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}}
.gradio-container .myst-main-nav button.vqc-source-tab,
.gradio-container .myst-secondary-nav button.vqc-source-tab {{
    height: var(--nav-btn-height, var(--button-body-height, {DEFAULT_BUTTON_BODY_HEIGHT})) !important;
    min-height: var(--nav-btn-height, var(--button-body-height, {DEFAULT_BUTTON_BODY_HEIGHT})) !important;
}}
.gradio-container .myst-save-edit-row button.save-btn,
.gradio-container .myst-save-edit-row button.edit-btn {{
    height: var(--button-body-height, {DEFAULT_BUTTON_BODY_HEIGHT}) !important;
    min-height: var(--button-body-height, {DEFAULT_BUTTON_BODY_HEIGHT}) !important;
}}
.gradio-container .myst-save-edit-row button.save-btn.placeholder-btn,
.gradio-container .myst-save-edit-row button.save-btn.placeholder-btn span {{
    opacity: 0.55 !important;
    cursor: not-allowed !important;
}}
.gradio-container .myst-save-edit-row button.save-btn,
.gradio-container .myst-save-edit-row button.edit-btn {{
    min-width: 80px !important;
    font-weight: var(--nav-btn-font-weight, 500) !important;
    font-size: var(--nav-btn-font-size, 14px) !important;
    flex: 1 1 0% !important;
}}
.gradio-container .vqc-status-preset-nav-row > .block,
.gradio-container .vqc-status-preset-nav-row > .form,
.gradio-container .vqc-status-preset-nav-row > button {{
    flex: none !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: none !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .vqc-status-preset-nav-row > .block > .form,
.gradio-container .vqc-status-preset-nav-row > .form > .block {{
    width: 100% !important;
    min-width: 0 !important;
}}
.gradio-container .myst-status-page > .block:has(.vqc-main-nav-row),
.gradio-container .myst-status-page > .form:has(.vqc-main-nav-row),
.gradio-container .myst-status-page .myst-status-stack > .block:has(.vqc-main-nav-row) {{
    margin-bottom: 0.05rem !important;
}}
.gradio-container .myst-status-page .myst-status-stack {{
    margin-top: 0 !important;
    padding-top: 0 !important;
}}
.gradio-container .myst-status-page .vqc-main-nav-row {{
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}}
.gradio-container .vqc-main-nav-row .vqc-nav-cell button.vqc-source-tab,
.gradio-container .vqc-status-preset-nav-row .vqc-nav-cell button.vqc-source-tab {{
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
}}
.gradio-container .vqc-status-preset-nav-row .vqc-nav-cell button.myst-status-preset-btn {{
    padding-left: 0.34rem !important;
    padding-right: 0.34rem !important;
}}
.gradio-container .vqc-status-preset-nav-row .vqc-nav-cell,
.gradio-container .vqc-status-preset-nav-row .vqc-nav-cell > .block,
.gradio-container .vqc-status-preset-nav-row .vqc-nav-cell > .form {{
    min-width: 0 !important;
    width: 100% !important;
    overflow: visible !important;
}}
.gradio-container .vqc-status-preset-nav-row button.myst-status-preset-btn,
.gradio-container .vqc-status-preset-nav-row button.myst-status-nav-back-btn,
.gradio-container .vqc-status-preset-nav-row button.myst-status-nav-edit-btn {{
    visibility: visible !important;
    display: inline-flex !important;
    opacity: 1 !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
}}
.gradio-container .vqc-nav-spreadsheet-row > .block,
.gradio-container .vqc-nav-spreadsheet-row > .form,
.gradio-container .vqc-nav-spreadsheet-row > .column {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
    min-width: 0 !important;
    width: 100% !important;
}}
.gradio-container .vqc-nav-row-label {{
    justify-self: start !important;
    align-self: center !important;
    text-align: left !important;
    padding-right: var(--nav-label-padding-right, 10px) !important;
}}
.gradio-container .vqc-nav-cell,
.gradio-container .vqc-nav-cell > .block,
.gradio-container .vqc-nav-cell > .form {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    min-height: 1.55rem !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 0.1rem 0.2rem !important;
}}
.gradio-container .vqc-nav-cell .html-container,
.gradio-container .vqc-nav-cell .html-container p {{
    margin: 0 !important;
    padding: 0 !important;
    text-align: center !important;
    width: 100% !important;
}}
.gradio-container .vqc-nav-cell-empty {{
    visibility: hidden !important;
}}
.gradio-container .vqc-optics-logo {{
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 0.1rem !important;
    min-width: 10.5rem !important;
    padding-right: 0.65rem !important;
    border-right: 1px solid rgba(107, 79, 29, 0.45) !important;
}}
.gradio-container .vqc-optics-brand {{
    font-size: 0.62rem !important;
    letter-spacing: 0.28em !important;
    color: {_VQC_LOGO_GOLD} !important;
    font-weight: 700 !important;
}}
.gradio-container .vqc-optics-panel-title {{
    font-size: 1.15rem !important;
    letter-spacing: 0.12em !important;
    color: #f5e6c8 !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    text-shadow: 0 0 10px rgba(255, 180, 80, 0.35) !important;
}}
.gradio-container .vqc-optics-subtitle {{
    font-size: 0.68rem !important;
    letter-spacing: 0.22em !important;
    color: #9a8458 !important;
}}
.gradio-container .vqc-optics-terminal-caption {{
    font-size: 0.58rem !important;
    letter-spacing: 0.18em !important;
    color: #3dff7a !important;
    text-shadow: 0 0 8px rgba(61, 255, 122, 0.45) !important;
    margin-top: 0.1rem !important;
}}
.gradio-container .vqc-optics-panel .vqc-optics-terminal textarea,
.gradio-container .vqc-optics-panel .vqc-optics-terminal input {{
    background: rgba(2, 10, 4, 0.1) !important;
    border: 2px inset #1a4d2a !important;
    color: #33ff66 !important;
    -webkit-text-fill-color: #33ff66 !important;
    font-family: "Courier New", Courier, monospace !important;
    font-size: 0.78rem !important;
    line-height: 1.45 !important;
    text-shadow: 0 0 6px rgba(51, 255, 102, 0.35) !important;
    box-shadow:
        inset 0 0 18px rgba(0, 40, 12, 0.65),
        0 0 12px rgba(51, 255, 102, 0.08) !important;
    border-radius: 6px !important;
    caret-color: #33ff66 !important;
}}
.gradio-container .vqc-optics-panel .vqc-optics-terminal .label-wrap span {{
    color: #3dff7a !important;
    letter-spacing: 0.14em !important;
    text-shadow: 0 0 6px rgba(61, 255, 122, 0.35) !important;
}}
.gradio-container .vqc-optics-panel .vqc-optics-terminal-wrap {{
    background: rgba(2, 10, 4, 0.1) !important;
    border: 1px solid #1a4d2a !important;
    border-radius: 10px !important;
    padding: 0.5rem 0.6rem 0.45rem !important;
    margin: 0.55rem 0 0.55rem 0 !important;
}}
.gradio-container .vqc-animations-nav-row {{
    margin: 0.35rem 0 0.65rem 0 !important;
}}
.gradio-container .myst-gravity-page .vqc-animations-nav-row {{
    margin: 0.12rem 0 0.22rem 0 !important;
}}
.gradio-container .vqc-optics-panel .vqc-optics-terminal textarea {{
    min-height: 13.5rem !important;
    white-space: pre !important;
    overflow-x: hidden !important;
}}
.gradio-container .myst-signal-scan {{
    position: relative !important;
    width: 100% !important;
    min-height: 14rem !important;
    margin: 0.55rem 0 !important;
    padding: 0.65rem 0.75rem !important;
    background: rgba(2, 10, 4, 0.45) !important;
    border: 2px inset #1a4d2a !important;
    border-radius: 6px !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-signal-scanlines {{
    position: absolute !important;
    inset: 0 !important;
    pointer-events: none !important;
    background: repeating-linear-gradient(
        0deg,
        transparent 0px,
        transparent 2px,
        rgba(51, 255, 102, 0.04) 2px,
        rgba(51, 255, 102, 0.04) 4px
    ) !important;
    animation: myst-scan-drift 12s linear infinite !important;
}}
.gradio-container .myst-signal-beam {{
    position: absolute !important;
    left: 0 !important;
    right: 0 !important;
    height: 18% !important;
    pointer-events: none !important;
    background: linear-gradient(
        180deg,
        transparent 0%,
        rgba(51, 255, 102, 0.12) 45%,
        rgba(51, 255, 102, 0.22) 50%,
        rgba(51, 255, 102, 0.12) 55%,
        transparent 100%
    ) !important;
    animation: myst-scan-beam 4s ease-in-out infinite !important;
}}
.gradio-container .myst-signal-body {{
    position: relative !important;
    z-index: 1 !important;
    margin: 0 !important;
    color: #33ff66 !important;
    font-family: "Courier New", Courier, monospace !important;
    font-size: 0.78rem !important;
    line-height: 1.45 !important;
    text-shadow: 0 0 6px rgba(51, 255, 102, 0.35) !important;
    white-space: pre-wrap !important;
    animation: myst-phosphor-flicker 3.5s ease-in-out infinite !important;
}}
@keyframes myst-scan-drift {{
    0% {{ transform: translateY(-8%); }}
    100% {{ transform: translateY(8%); }}
}}
@keyframes myst-scan-beam {{
    0%, 100% {{ top: -20%; }}
    50% {{ top: 85%; }}
}}
@keyframes myst-phosphor-flicker {{
    0%, 100% {{ opacity: 1; }}
    48% {{ opacity: 0.92; }}
    50% {{ opacity: 0.78; }}
    52% {{ opacity: 0.95; }}
}}
.gradio-container .vqc-optics-keypad {{
    background: linear-gradient(180deg, #16120c 0%, #0a0806 100%) !important;
    border: 2px inset #3d3020 !important;
    border-radius: 10px !important;
    padding: 0.42rem 0.38rem 0.48rem !important;
    margin: 0 0 0.65rem 0 !important;
    box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.55) !important;
}}
.gradio-container .vqc-optics-keypad > .block,
.gradio-container .vqc-optics-keypad .block {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
}}
.gradio-container .vqc-optics-dpad-group {{
    margin: 0 0 0.28rem 0 !important;
    padding: 0 0 0.12rem 0 !important;
}}
.gradio-container .vqc-optics-panel .vqc-optics-dpad-row,
.gradio-container .vqc-optics-panel .vqc-optics-prog-row {{
    gap: 0.2rem !important;
    margin: 0 0 0.2rem 0 !important;
    justify-content: stretch !important;
    width: 100% !important;
}}
.gradio-container .vqc-optics-keypad button.vqc-optics-key,
.gradio-container .vqc-optics-keypad button.vqc-optics-key span {{
    font-family: "Courier New", Courier, monospace !important;
    font-size: 1.44rem !important;
    font-weight: 700 !important;
    line-height: 1.1 !important;
}}
.gradio-container .vqc-optics-keypad button.vqc-optics-key {{
    flex: 1 1 0 !important;
    min-width: 0 !important;
    max-width: none !important;
    min-height: 3rem !important;
    height: 3rem !important;
    max-height: 3rem !important;
    aspect-ratio: auto !important;
    background: #000000 !important;
    border: none !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    letter-spacing: 0.03em !important;
    padding: 0.28rem 0.1rem !important;
    box-shadow: none !important;
}}
.gradio-container .vqc-optics-panel .vqc-optics-dpad-row button.vqc-optics-key-dpad,
.gradio-container .vqc-optics-panel .vqc-optics-dpad-row button.vqc-optics-key-dpad span {{
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif !important;
    font-size: 1.44rem !important;
    font-weight: 700 !important;
    line-height: 1 !important;
}}
.gradio-container .vqc-optics-panel .vqc-optics-dpad-row button.vqc-optics-key-dpad:active,
.gradio-container .vqc-optics-panel .vqc-optics-dpad-row button.vqc-optics-key-dpad:active span {{
    background: {_VQC_MATRIX_GREEN} !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    box-shadow: 0 0 12px rgba(51, 255, 102, 0.45) !important;
}}
.gradio-container .vqc-optics-panel button.vqc-optics-key-clear {{
    text-transform: lowercase !important;
    letter-spacing: 0.06em !important;
}}
.gradio-container .vqc-optics-panel button.vqc-optics-key-home,
.gradio-container .vqc-optics-panel button.vqc-optics-key-home:hover {{
    background: {_VQC_HOME_KEY_BG} !important;
    box-shadow: none !important;
}}
.gradio-container .vqc-optics-panel button.vqc-optics-key-home,
.gradio-container .vqc-optics-panel button.vqc-optics-key-home:hover,
.gradio-container .vqc-optics-panel button.vqc-optics-key-home span {{
    color: {_VQC_MATRIX_GREEN} !important;
    -webkit-text-fill-color: {_VQC_MATRIX_GREEN} !important;
    font-size: 1.44rem !important;
    font-weight: 700 !important;
    text-shadow: 0 0 6px rgba(51, 255, 102, 0.35) !important;
}}
.gradio-container .vqc-optics-panel button.vqc-optics-key-home:hover {{
    background: #141414 !important;
}}
.gradio-container .vqc-optics-panel button.vqc-optics-key-defined:not(.active),
.gradio-container .vqc-optics-panel button.vqc-optics-key-defined:not(.active) span {{
    color: {_VQC_MATRIX_GREEN} !important;
    -webkit-text-fill-color: {_VQC_MATRIX_GREEN} !important;
    text-shadow: 0 0 6px rgba(51, 255, 102, 0.35) !important;
}}
.gradio-container .vqc-optics-panel button.vqc-optics-key-defined:not(.active):hover,
.gradio-container .vqc-optics-panel button.vqc-optics-key-defined:not(.active):hover span {{
    color: #7dff9a !important;
    -webkit-text-fill-color: #7dff9a !important;
}}
.gradio-container .vqc-optics-panel button.vqc-optics-key:not(.active):not(.vqc-optics-key-home):not(.vqc-optics-key-defined):hover {{
    background: #141414 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}}
.gradio-container .vqc-optics-panel button.vqc-optics-key-defined:not(.active):hover {{
    background: #141414 !important;
}}
.gradio-container .vqc-optics-panel button.vqc-optics-key.active,
.gradio-container .vqc-optics-panel button.vqc-optics-key.active:hover {{
    background: {_VQC_MATRIX_GREEN} !important;
    box-shadow: 0 0 12px rgba(51, 255, 102, 0.45) !important;
}}
.gradio-container .vqc-optics-panel button.vqc-optics-key.active,
.gradio-container .vqc-optics-panel button.vqc-optics-key.active:hover,
.gradio-container .vqc-optics-panel button.vqc-optics-key.active span {{
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    text-shadow: none !important;
    -webkit-text-stroke: none !important;
}}
.gradio-container .vqc-optics-panel .label-wrap span,
.gradio-container .vqc-optics-panel label span {{
    color: #e8d4a8 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    font-weight: 700 !important;
}}
.gradio-container .vqc-optics-panel .info {{
    color: #9a8458 !important;
    font-size: 0.72rem !important;
    font-style: italic !important;
}}
.gradio-container .vqc-optics-panel input[type="text"],
.gradio-container .vqc-optics-panel textarea {{
    background: #120c06 !important;
    border: 2px inset #5c4a1f !important;
    color: #ffb347 !important;
    font-family: "Courier New", Courier, monospace !important;
    border-radius: 6px !important;
    box-shadow: inset 0 0 10px rgba(255, 140, 40, 0.12) !important;
}}
.gradio-container .vqc-optics-panel input[type="number"] {{
    background: #120c06 !important;
    border: 2px inset #5c4a1f !important;
    color: #ffb347 !important;
    font-family: "Courier New", Courier, monospace !important;
    font-weight: 700 !important;
    text-align: center !important;
    border-radius: 4px !important;
    box-shadow: inset 0 0 12px rgba(255, 140, 40, 0.18) !important;
    min-width: 4.2rem !important;
}}
.gradio-container .vqc-optics-panel input[type="range"] {{
    height: 6px !important;
    background: linear-gradient(90deg, #1a1208, #3d2e14, #1a1208) !important;
    border: 1px solid #5c4a1f !important;
    border-radius: 999px !important;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.6) !important;
}}
.gradio-container .vqc-optics-panel input[type="range"]::-webkit-slider-thumb {{
    -webkit-appearance: none !important;
    width: 24px !important;
    height: 24px !important;
    border-radius: 50% !important;
    background: radial-gradient(circle at 32% 28%, #fff2cc 0%, #c9a227 38%, #5c4212 72%, #2a1f08 100%) !important;
    border: 2px solid #1a1208 !important;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.55), inset 0 -2px 4px rgba(0, 0, 0, 0.35) !important;
    cursor: pointer !important;
}}
.gradio-container .vqc-optics-panel input[type="range"]::-moz-range-thumb {{
    width: 24px !important;
    height: 24px !important;
    border-radius: 50% !important;
    background: radial-gradient(circle at 32% 28%, #fff2cc 0%, #c9a227 38%, #5c4212 72%, #2a1f08 100%) !important;
    border: 2px solid #1a1208 !important;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.55) !important;
    cursor: pointer !important;
}}
.gradio-container .vqc-optics-panel .vqc-optics-dial-wrap {{
    background: rgba(0, 0, 0, 0.22) !important;
    border: 1px solid #4a3818 !important;
    border-radius: 10px !important;
    padding: 0.55rem 0.65rem 0.45rem !important;
    margin: 0 !important;
}}
.gradio-container .vqc-optics-panel .vqc-optics-tune-row {{
    gap: 0.65rem !important;
    margin-bottom: 0.55rem !important;
}}
.gradio-container .vqc-optics-panel .vqc-optics-dial-row {{
    gap: 0.65rem !important;
    align-items: stretch !important;
}}
.gradio-container .vqc-optics-panel fieldset {{
    background: rgba(0, 0, 0, 0.18) !important;
    border: 1px solid #4a3818 !important;
    border-radius: 10px !important;
    padding: 0.45rem 0.55rem !important;
}}
.gradio-container .vqc-optics-panel .vqc-band-switch button {{
    border: 1px solid #6b4f1d !important;
    background: #1a1208 !important;
    color: #c9a227 !important;
    border-radius: 6px !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.05em !important;
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.45) !important;
}}
.gradio-container .vqc-optics-panel .vqc-band-switch button.selected,
.gradio-container .vqc-optics-panel .vqc-band-switch button[aria-checked="true"] {{
    background: linear-gradient(180deg, #8b6914 0%, #4a3818 100%) !important;
    color: #fff2cc !important;
    box-shadow: 0 0 10px rgba(255, 160, 60, 0.35) !important;
}}
.gradio-container .vqc-optics-presets-label {{
    color: #c9a227 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    margin: 0.45rem 0 0.35rem 0 !important;
    text-align: center !important;
}}
.gradio-container .vqc-optics-panel button.vqc-receiver-preset {{
    background: linear-gradient(180deg, #3d2e14 0%, #1f1608 100%) !important;
    border: 2px solid #6b4f1d !important;
    border-radius: 8px !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.04em !important;
    box-shadow: inset 0 1px 0 rgba(255, 220, 150, 0.15), 0 2px 4px rgba(0, 0, 0, 0.4) !important;
}}
.gradio-container .vqc-optics-panel button.vqc-receiver-preset,
.gradio-container .vqc-optics-panel button.vqc-receiver-preset span {{
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}}
.gradio-container .vqc-optics-panel button.vqc-receiver-preset:hover,
.gradio-container .vqc-optics-panel button.vqc-receiver-preset:not(.active):hover,
.gradio-container .vqc-optics-panel button.vqc-receiver-preset:not(.active):hover span {{
    background: linear-gradient(180deg, #6b4f1d 0%, #3d2e14 100%) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}}
.gradio-container .myst-gravity-page .vqc-gravity-panel button.vqc-receiver-preset.active,
.gradio-container .myst-gravity-page .vqc-gravity-panel button.vqc-receiver-preset.active span,
.gradio-container .myst-gravity-page .vqc-gravity-panel button.vqc-receiver-preset.active:hover,
.gradio-container .myst-gravity-page .vqc-gravity-panel button.vqc-receiver-preset.active:hover span {{
    background: linear-gradient(180deg, #3d2e14 0%, #1f1608 100%) !important;
    border-color: #6b4f1d !important;
    color: {_VQC_MATRIX_GREEN} !important;
    -webkit-text-fill-color: {_VQC_MATRIX_GREEN} !important;
    box-shadow: inset 0 1px 0 rgba(255, 220, 150, 0.15), 0 2px 4px rgba(0, 0, 0, 0.4) !important;
}}
.gradio-container .vqc-optics-panel .vqc-slm-toggle label {{
    color: #c9a227 !important;
    font-size: 0.76rem !important;
}}
.gradio-container .markdown blockquote {{
    border-left-color: rgba(255, 180, 80, 0.5) !important;
    background: transparent !important;
}}
.gradio-container .accordion,
.gradio-container details,
.gradio-container summary {{
    background-color: {_VQC_FIELD_FILL} !important;
    color: #e8e0f8 !important;
    border-radius: 10px;
}}
.gradio-container .image-container img,
.gradio-container .gr-image img,
.gradio-container video,
.gradio-container .plot-container {{
    background-color: transparent !important;
    opacity: 1 !important;
}}
.gradio-container #unit-cell-main-view .image-container,
.gradio-container #unit-cell-main-view .image-container img,
.gradio-container #unit-cell-main-view .gr-image img {{
    background-color: #000000 !important;
    mix-blend-mode: normal !important;
}}
.gradio-container button,
.gradio-container .gr-button {{
    opacity: 1 !important;
}}
.gradio-container input[type="range"] {{
    opacity: 1 !important;
}}
.gradio-container .vqc-full-width {{
    width: 100% !important;
}}
.gradio-container .main,
.gradio-container .wrap {{
    width: 100% !important;
    max-width: 100% !important;
    min-height: 0 !important;
    height: auto !important;
}}
.gradio-container .contain {{
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 auto !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    min-height: 0 !important;
    height: auto !important;
}}
.gradio-container .vqc-animation-panel,
.gradio-container .vqc-figure-panel,
.gradio-container .vqc-plot3d-panel {{
    width: 100% !important;
    max-width: 100% !important;
    min-height: 0 !important;
}}
.gradio-container .vqc-animation-panel video,
.gradio-container .vqc-animation-panel .image-container,
.gradio-container .vqc-animation-panel img,
.gradio-container .vqc-figure-panel .image-container,
.gradio-container .vqc-figure-panel img {{
    width: 100% !important;
    max-width: 100% !important;
    object-fit: contain;
}}
.gradio-container .vqc-plot3d-panel .plot-container {{
    width: 100% !important;
    min-height: 360px;
}}
.gradio-container .myst-cube-viewport-media .vqc-plot3d-panel .plot-container {{
    min-height: var(--myst-viewport-min-height, calc(100dvh - 11rem)) !important;
    height: 100% !important;
}}
.gradio-container .gr-video .empty,
.gradio-container .gr-image .empty,
.gradio-container .gr-image .icon-wrap {{
    min-height: 80px !important;
    background: transparent !important;
}}
footer {{ visibility: hidden; }}
.gradio-container .myst-gravity-page .markdown table {{
    display: block !important;
    overflow-x: auto !important;
    -webkit-overflow-scrolling: touch !important;
    max-width: 100% !important;
}}
.gradio-container .myst-gravity-page pre,
.gradio-container .myst-ascii-block {{
    overflow-x: auto !important;
    font-size: 0.72rem !important;
    line-height: 1.35 !important;
}}
.gradio-container .myst-github-banner {{
    padding: 0.55rem 0.75rem !important;
    border: 1px solid rgba(201, 162, 39, 0.35) !important;
    border-radius: 8px !important;
    background: rgba(18, 10, 28, 0.55) !important;
    margin-bottom: 0.5rem !important;
}}
.gradio-container .myst-gravity-page .plot-container {{
    flex: 1 1 auto !important;
    width: 100% !important;
    min-height: calc(100dvh - 12rem) !important;
    background-color: #000000 !important;
}}
.gradio-container .myst-gravity-page .vqc-plot3d-panel,
.gradio-container .myst-gravity-page .vqc-plot3d-panel .block,
.gradio-container .myst-gravity-page .vqc-plot3d-panel img {{
    background-color: #000000 !important;
}}
.gradio-container:has(.myst-gravity-page:not(.hide):not(.hidden)) {{
    overflow: hidden !important;
    max-height: 100dvh !important;
    padding: 0.15rem 0.5rem 0 !important;
    display: flex !important;
    flex-direction: column !important;
    min-height: calc(100dvh - 3.5rem) !important;
    box-sizing: border-box !important;
}}
.gradio-container:has(.myst-gravity-page:not(.hide):not(.hidden)) .main,
.gradio-container:has(.myst-gravity-page:not(.hide):not(.hidden)) .main > .wrap,
.gradio-container:has(.myst-gravity-page:not(.hide):not(.hidden)) .contain {{
    flex: 1 1 0 !important;
    min-height: 0 !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
}}

.gradio-container .myst-gravity-page {{
    --myst-gravity-ui-scale: 1.33;
    --myst-gravity-control-bar-height: calc(1.54rem * var(--myst-gravity-ui-scale));
    --myst-gravity-keypad-height: calc(2.39rem * var(--myst-gravity-ui-scale));
    --myst-gravity-keypad-font: calc(0.86rem * var(--myst-gravity-ui-scale));
    --myst-gravity-keypad-arrow-font: calc(1.08rem * var(--myst-gravity-ui-scale));
    --myst-gravity-keypad-circle: calc(1.18rem * var(--myst-gravity-ui-scale));
    --myst-gravity-tui-font: calc(0.8rem * var(--myst-gravity-ui-scale));
    --myst-gravity-action-font: calc(0.82rem * var(--myst-gravity-ui-scale));
    --myst-gravity-nav-font: calc(0.82rem * var(--myst-gravity-ui-scale));
    --myst-gravity-nav-height: calc(2.05rem * var(--myst-gravity-ui-scale));
    --myst-gravity-header-font: calc(0.94rem * var(--myst-gravity-ui-scale));
    --myst-gravity-header-sub-font: calc(0.74rem * var(--myst-gravity-ui-scale));
    width: 100% !important;
    max-width: none !important;
    padding: 0 0.25rem 0 !important;
    flex: 1 1 0 !important;
    height: 100% !important;
    min-height: calc(100dvh - 4.25rem) !important;
    max-height: none !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
    gap: 0 !important;
    display: flex !important;
    flex-direction: column !important;
}}
.gradio-container .myst-gravity-page .vqc-source-tabs-row button.vqc-source-tab,
.gradio-container .myst-gravity-page .vqc-source-tabs-row button.vqc-source-tab span,
.gradio-container .myst-gravity-page .vqc-main-nav-row button.vqc-source-tab,
.gradio-container .myst-gravity-page .vqc-main-nav-row button.vqc-source-tab span {{
    font-size: var(--myst-gravity-nav-font) !important;
    min-height: var(--myst-gravity-nav-height) !important;
    height: var(--myst-gravity-nav-height) !important;
}}
.gradio-container .myst-gravity-page .vqc-nav-cell {{
    min-width: calc(72px * var(--myst-gravity-ui-scale)) !important;
}}
.gradio-container .myst-gravity-page .myst-cube-viewport-title,
.gradio-container .myst-gravity-page .myst-gravity-presets-header .myst-cube-viewport-title {{
    font-size: var(--myst-gravity-header-font) !important;
}}
.gradio-container .myst-gravity-page .myst-cube-viewport-brand,
.gradio-container .myst-gravity-page .myst-cube-viewport-sub,
.gradio-container .myst-gravity-page .myst-cube-viewport-tag {{
    font-size: var(--myst-gravity-header-sub-font) !important;
}}
.gradio-container .myst-gravity-page > .block:has(.myst-gravity-single-viewport),
.gradio-container .myst-gravity-page > .block:has(.myst-gravity-split),
.gradio-container .myst-gravity-page > .block:has(.vqc-animations-nav-row) + .block {{
    flex: 1 1 0 !important;
    min-height: 0 !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-gravity-page > .block:has(.vqc-animations-nav-row) {{
    flex: 0 0 auto !important;
}}
.gradio-container .myst-gravity-page > .gap {{
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-gravity-page > .block {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
}}
.gradio-container .myst-gravity-split {{
    display: grid !important;
    grid-template-columns: minmax(292px, 27%) minmax(0, 1fr) !important;
    grid-template-rows: 1fr !important;
    align-items: stretch !important;
    gap: 0.5rem !important;
    width: 100% !important;
    flex: 1 1 0 !important;
    height: 100% !important;
    min-height: 0 !important;
    max-height: 100% !important;
    box-sizing: border-box !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-gravity-left-panel,
.gradio-container .myst-gravity-right-panel {{
    display: flex !important;
    flex-direction: column !important;
    height: 100% !important;
    min-height: 0 !important;
    overflow: hidden !important;
}}
.gradio-container .myst-gravity-right-stack {{
    gap: 0 !important;
    flex: 1 1 0 !important;
    min-height: 0 !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
}}
.gradio-container .myst-gravity-visuals-col .myst-gravity-cube-panel,
.gradio-container .myst-gravity-visuals-col .gr-group.myst-gravity-cube-panel {{
    flex: 1 1 0 !important;
    min-height: 0 !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
}}
.gradio-container .myst-gravity-left-stack {{
    flex: 1 1 0 !important;
    min-height: 0 !important;
    height: 100% !important;
    gap: 0.3rem !important;
    overflow: hidden !important;
    display: grid !important;
    grid-template-rows: auto minmax(0, 1fr) !important;
    grid-template-columns: minmax(0, 1fr) !important;
    align-content: stretch !important;
}}
.gradio-container .myst-gravity-left-stack > .gap {{
    display: none !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-gravity-left-stack > .block,
.gradio-container .myst-gravity-left-stack > .form {{
    min-height: 0 !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
}}
.gradio-container .myst-gravity-left-stack > .block:has(.myst-gravity-left-control-slot),
.gradio-container .myst-gravity-left-stack > .block:has(.myst-gravity-control-panel),
.gradio-container .myst-gravity-left-stack > .block:has(.myst-gravity-control-top-slot) {{
    grid-row: 1 !important;
    min-height: 0 !important;
    height: auto !important;
    overflow: visible !important;
    align-self: start !important;
    display: flex !important;
    flex-direction: column !important;
}}
.gradio-container .myst-gravity-left-stack > .block:has(.myst-gravity-left-presets-tui-slot),
.gradio-container .myst-gravity-left-stack > .block:has(.myst-gravity-presets-tui-card) {{
    grid-row: 1 !important;
    min-height: 0 !important;
    height: 100% !important;
    align-self: stretch !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
}}
.gradio-container .myst-gravity-left-stack > .column.myst-gravity-left-control-slot,
.gradio-container .myst-gravity-left-stack > .column.myst-gravity-control-top-slot {{
    grid-row: 1 !important;
    min-height: 0 !important;
    height: auto !important;
    overflow: visible !important;
}}
.gradio-container .myst-gravity-left-stack > .column.myst-gravity-left-presets-tui-slot {{
    grid-row: 1 !important;
    min-height: 0 !important;
    height: 100% !important;
    overflow: hidden !important;
}}
.gradio-container .myst-gravity-presets-fixed {{
    flex: 0 0 auto !important;
    z-index: 5 !important;
}}
.gradio-container .myst-gravity-left-control-slot,
.gradio-container .myst-gravity-control-panel.myst-gravity-left-frame,
.gradio-container .myst-gravity-control-top-slot {{
    flex: 0 0 auto !important;
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
    width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: visible !important;
}}
.gradio-container .myst-gravity-control-top-slot.myst-gravity-panel-window.vqc-optics-panel {{
    padding: 0 0.55rem 0.35rem !important;
    margin: 0 !important;
}}
.gradio-container .myst-gravity-control-panel .myst-cube-viewport-header {{
    flex: 0 0 auto !important;
    min-height: 0 !important;
    max-height: none !important;
    overflow: visible !important;
}}
.gradio-container .myst-gravity-presets-tui-card {{
    flex: 1 1 0 !important;
    min-height: 0 !important;
    height: 100% !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 0.55rem 0.5rem !important;
    gap: 0 !important;
    display: grid !important;
    grid-template-rows: auto auto minmax(0, 1fr) !important;
    grid-template-columns: minmax(0, 1fr) !important;
    overflow: hidden !important;
    background: linear-gradient(180deg, #1a1008 0%, #0a0604 100%) !important;
    box-shadow: inset 0 0 18px rgba(0, 0, 0, 0.42) !important;
}}
.gradio-container .myst-gravity-presets-tui-card > .block:has(button.vqc-full-width) {{
    grid-row: 2 !important;
    height: auto !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 0.45rem !important;
}}
.gradio-container .myst-gravity-presets-tui-card > .gap {{
    display: none !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-gravity-presets-tui-card > .block,
.gradio-container .myst-gravity-presets-tui-card > .column,
.gradio-container .myst-gravity-presets-tui-card > .form {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-gravity-presets-tui-card .myst-gravity-presets-panel {{
    grid-row: 1 !important;
    height: auto !important;
    min-height: 0 !important;
    width: 100% !important;
    padding: 0 !important;
    overflow: visible !important;
    display: flex !important;
    flex-direction: column !important;
}}
.gradio-container .myst-gravity-presets-tui-card .myst-gravity-left-tui-slot,
.gradio-container .myst-gravity-presets-tui-card .myst-gravity-preset-tui-section {{
    grid-row: 3 !important;
    min-height: 0 !important;
    height: 100% !important;
    width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
}}
.gradio-container .myst-gravity-presets-header.myst-gravity-presets-header-single {{
    flex-direction: row !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0.32rem 0.65rem 0.38rem !important;
    gap: 0 !important;
}}
.gradio-container .myst-gravity-presets-header.myst-gravity-presets-header-compact {{
    align-items: center !important;
    text-align: center !important;
}}
.gradio-container .myst-gravity-page .myst-gravity-presets-header {{
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: calc(0.06rem * var(--myst-gravity-ui-scale, 1)) !important;
    width: 100% !important;
    margin: 0 !important;
    padding: calc(0.5rem * var(--myst-gravity-ui-scale, 1)) calc(0.65rem * var(--myst-gravity-ui-scale, 1)) calc(0.55rem * var(--myst-gravity-ui-scale, 1)) !important;
    border-bottom: 1px solid rgba(74, 56, 24, 0.55) !important;
    border-radius: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
}}
.gradio-container .myst-gravity-presets-tui-card .myst-gravity-presets-header.myst-gravity-presets-header-compact {{
    align-items: center !important;
    text-align: center !important;
}}
.gradio-container .myst-gravity-presets-panel .myst-gravity-preset-grid,
.gradio-container .myst-gravity-presets-panel .myst-gravity-preset-grid-wrap {{
    width: 100% !important;
    margin: 0.35rem 0 0.45rem 0 !important;
    padding: 0 0.55rem !important;
    display: block !important;
    visibility: visible !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-gravity-keypad-wrap {{
    width: 100% !important;
    margin: calc(0.35rem * var(--myst-gravity-ui-scale, 1)) calc(0.45rem * var(--myst-gravity-ui-scale, 1)) calc(0.4rem * var(--myst-gravity-ui-scale, 1)) !important;
    padding: calc(0.48rem * var(--myst-gravity-ui-scale, 1)) calc(0.55rem * var(--myst-gravity-ui-scale, 1)) calc(0.52rem * var(--myst-gravity-ui-scale, 1)) !important;
    background: linear-gradient(180deg, #16120c 0%, #0a0806 100%) !important;
    border: 2px inset #3d3020 !important;
    border-radius: 10px !important;
    box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.55) !important;
    box-sizing: border-box !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
}}
.gradio-container .myst-gravity-keypad-row,
.gradio-container .myst-gravity-keypad-row.row {{
    display: grid !important;
    grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
    gap: calc(0.25rem * var(--myst-gravity-ui-scale, 1)) !important;
    width: 92% !important;
    max-width: 92% !important;
    margin: 0 auto calc(0.22rem * var(--myst-gravity-ui-scale, 1)) auto !important;
    padding: 0 !important;
    visibility: visible !important;
}}
.gradio-container .myst-gravity-keypad-row:last-child {{
    margin-bottom: 0 !important;
}}
.gradio-container .myst-gravity-presets-panel .myst-gravity-preset-row,
.gradio-container .myst-gravity-presets-panel .myst-gravity-preset-row.row {{
    display: grid !important;
    grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
    gap: 0.28rem !important;
    width: 100% !important;
    margin: 0 0 0.24rem 0 !important;
    padding: 0 0.45rem !important;
    visibility: visible !important;
    min-height: var(--myst-control-bar-height, 2.05rem) !important;
}}
.gradio-container .myst-gravity-presets-panel .myst-gravity-preset-row > .block,
.gradio-container .myst-gravity-presets-panel .myst-gravity-preset-row > .form,
.gradio-container .myst-gravity-presets-panel .myst-gravity-preset-row > .column {{
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    min-width: 0 !important;
    width: 100% !important;
    min-height: var(--myst-control-bar-height, 2.05rem) !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-gravity-page button.myst-gravity-keypad-btn,
.gradio-container .myst-gravity-page button.myst-gravity-keypad-btn span,
.gradio-container .myst-gravity-keypad-wrap button.myst-gravity-keypad-btn,
.gradio-container .myst-gravity-keypad-wrap button.myst-gravity-keypad-btn span,
.gradio-container .myst-gravity-page button.myst-gravity-quick-preset,
.gradio-container .myst-gravity-page button.myst-gravity-quick-preset span,
.gradio-container .myst-gravity-presets-panel button.myst-gravity-quick-preset,
.gradio-container .myst-gravity-presets-panel button.myst-gravity-quick-preset span,
.gradio-container #gravity-preset-btn-0,
.gradio-container #gravity-preset-btn-1 {{
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: auto !important;
    position: relative !important;
    z-index: 12 !important;
    width: 100% !important;
    min-height: var(--myst-gravity-keypad-height, 2.39rem) !important;
    height: var(--myst-gravity-keypad-height, 2.39rem) !important;
    box-sizing: border-box !important;
    padding: calc(0.3rem * var(--myst-gravity-ui-scale, 1)) calc(0.42rem * var(--myst-gravity-ui-scale, 1)) !important;
    font-size: var(--myst-gravity-keypad-font, 0.86rem) !important;
    line-height: 1.2 !important;
}}
.gradio-container .myst-gravity-keypad-wrap button.myst-gravity-keypad-arrow,
.gradio-container .myst-gravity-keypad-wrap button.myst-gravity-keypad-arrow span {{
    font-size: var(--myst-gravity-keypad-arrow-font, 1.08rem) !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}}
.gradio-container .myst-gravity-keypad-wrap button.myst-gravity-keypad-enter,
.gradio-container .myst-gravity-keypad-wrap button.myst-gravity-keypad-stop {{
    background: linear-gradient(180deg, #3d2e14 0%, #1f1608 100%) !important;
    border: 2px solid #6b4f1d !important;
    padding: 0 !important;
}}
.gradio-container .myst-gravity-keypad-wrap button.myst-gravity-keypad-enter span,
.gradio-container .myst-gravity-keypad-wrap button.myst-gravity-keypad-stop span {{
    display: none !important;
}}
.gradio-container .myst-gravity-keypad-wrap button.myst-gravity-keypad-enter::after,
.gradio-container .myst-gravity-keypad-wrap button.myst-gravity-keypad-stop::after {{
    content: "" !important;
    display: block !important;
    width: var(--myst-gravity-keypad-circle, 1.18rem) !important;
    height: var(--myst-gravity-keypad-circle, 1.18rem) !important;
    min-width: var(--myst-gravity-keypad-circle, 1.18rem) !important;
    min-height: var(--myst-gravity-keypad-circle, 1.18rem) !important;
    border-radius: 50% !important;
    box-shadow: inset 0 -2px 4px rgba(0, 0, 0, 0.35) !important;
    pointer-events: none !important;
}}
.gradio-container .myst-gravity-keypad-wrap button.myst-gravity-keypad-enter::after {{
    background: radial-gradient(circle at 35% 30%, #9dff9a 0%, #33ff66 58%, #1a7a34 100%) !important;
    border: 1px solid #6bffb0 !important;
}}
.gradio-container .myst-gravity-keypad-wrap button.myst-gravity-keypad-stop::after {{
    background: radial-gradient(circle at 35% 30%, #ff8a8a 0%, #e11d48 58%, #7f1d1d 100%) !important;
    border: 1px solid #fb7185 !important;
}}
.gradio-container .myst-gravity-keypad-wrap button.myst-gravity-keypad-btn.active,
.gradio-container .myst-gravity-keypad-wrap button.myst-gravity-keypad-btn.active span {{
    color: {_VQC_MATRIX_GREEN} !important;
    -webkit-text-fill-color: {_VQC_MATRIX_GREEN} !important;
}}
.gradio-container .myst-preset-tui-viewport {{
    width: 100% !important;
    height: 100% !important;
    overflow: hidden !important;
    position: relative !important;
}}
.gradio-container .myst-preset-tui-viewport .myst-preset-tui-serial {{
    transform: translateY(calc(-1 * var(--tui-scroll, 0px))) !important;
    transition: transform 0.12s ease-out !important;
}}
.gradio-container .myst-gravity-page button.vqc-receiver-preset.vqc-full-width,
.gradio-container .myst-gravity-presets-panel button.vqc-receiver-preset.vqc-full-width,
.gradio-container .myst-gravity-presets-tui-card button.vqc-receiver-preset.vqc-full-width {{
    margin: 0.1rem 0.45rem 0.35rem !important;
    width: calc(100% - 0.9rem) !important;
    min-height: var(--myst-gravity-control-bar-height, var(--myst-control-bar-height, 2.05rem)) !important;
    height: var(--myst-gravity-control-bar-height, var(--myst-control-bar-height, 2.05rem)) !important;
    box-sizing: border-box !important;
    padding: calc(0.34rem * var(--myst-gravity-ui-scale, 1)) calc(0.78rem * var(--myst-gravity-ui-scale, 1)) !important;
    font-size: var(--myst-gravity-action-font, 0.82rem) !important;
    line-height: 1.2 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
}}
.gradio-container .myst-gravity-page .myst-gravity-controls-accordion > .label-wrap {{
    min-height: var(--myst-gravity-control-bar-height, var(--myst-control-bar-height, 2.05rem)) !important;
    height: var(--myst-gravity-control-bar-height, var(--myst-control-bar-height, 2.05rem)) !important;
    padding: 0 0.75rem !important;
    display: flex !important;
    align-items: center !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-gravity-page .myst-gravity-controls-accordion > .label-wrap span {{
    line-height: 1.2 !important;
    font-size: 0.82rem !important;
}}
.gradio-container .myst-gravity-presets-tui-card .myst-gravity-preset-tui-section {{
    flex: 1 1 auto !important;
    margin: 0 !important;
    padding: 0 !important;
    border-top: 1px solid rgba(74, 56, 24, 0.5) !important;
    background: transparent !important;
    min-height: 0 !important;
}}
.gradio-container .myst-gravity-presets-tui-card .myst-gravity-left-tui-slot .myst-gravity-preset-tui-wrap,
.gradio-container .myst-gravity-presets-tui-card .myst-gravity-left-tui-slot .myst-gravity-preset-tui-wrap.block {{
    flex: 1 1 0 !important;
    min-height: calc(100dvh - 20.5rem) !important;
    height: 100% !important;
    max-height: none !important;
    display: block !important;
    visibility: visible !important;
    overflow-y: auto !important;
}}
.gradio-container .myst-gravity-cube-panel {{
    flex: 1 1 0 !important;
    min-height: 0 !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
    gap: 0 !important;
}}
.gradio-container .myst-gravity-cube-panel > .block,
.gradio-container .myst-gravity-cube-panel > .column,
.gradio-container .myst-gravity-cube-panel > .form {{
    display: flex !important;
    flex-direction: column !important;
    flex: 0 0 auto !important;
    min-height: 0 !important;
    width: 100% !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-gravity-cube-panel > .block:not(.myst-cube-plot-inner) {{
    flex: 0 0 auto !important;
    overflow: visible !important;
    min-height: 0 !important;
    max-height: none !important;
}}
.gradio-container .myst-gravity-cube-panel > .block:has(.myst-cube-viewport-media),
.gradio-container .myst-gravity-cube-panel > .block:has(.myst-cube-viewport-media-slot) {{
    flex: 1 1 0 !important;
    min-height: var(--myst-viewport-min-height, calc(100dvh - 11rem)) !important;
    height: 100% !important;
    width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
}}
.gradio-container .myst-gravity-cube-panel > .block:has(.myst-cube-viewport-media) > .form,
.gradio-container .myst-gravity-cube-panel > .block:has(.myst-cube-viewport-media-slot) > .form {{
    flex: 1 1 0 !important;
    min-height: 0 !important;
    height: 100% !important;
    width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-gravity-cube-panel > .column.myst-cube-viewport-media,
.gradio-container .myst-gravity-cube-panel > .column.myst-cube-viewport-media-slot,
.gradio-container .myst-gravity-cube-panel .column.myst-cube-viewport-media,
.gradio-container .myst-gravity-cube-panel .column.myst-cube-viewport-media-slot {{
    flex: 1 1 0 !important;
    min-height: var(--myst-viewport-min-height, calc(100dvh - 11rem)) !important;
    max-height: 100% !important;
    overflow: hidden !important;
}}
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-header:not(.myst-cube-viewport-header-fixed) {{
    flex: 0 0 auto !important;
    min-height: 0 !important;
    max-height: 7.5rem !important;
    height: auto !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
    padding-bottom: 0.3rem !important;
}}
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-header.myst-cube-viewport-header-fixed {{
    flex: 0 0 auto !important;
    min-height: 0 !important;
    max-height: 4rem !important;
    height: auto !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
    padding-bottom: 0 !important;
}}
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-status {{
    display: block !important;
    min-height: 0 !important;
    max-height: none !important;
    overflow: visible !important;
    line-height: 1.25 !important;
}}
.gradio-container .myst-gravity-cube-panel > .column.myst-cube-viewport-media,
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-media {{
    position: relative !important;
    flex: 1 1 0 !important;
    min-height: var(--myst-viewport-min-height, calc(100dvh - 11rem)) !important;
    height: 100% !important;
    max-height: 100% !important;
    width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
    padding: 0 !important;
    margin: 0 !important;
    align-self: stretch !important;
}}
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-media > .gap {{
    display: none !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-media > .block.myst-cube-plot-inner,
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-media > .block.myst-cube-anim-video,
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-media .myst-cube-plot-inner.block,
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-media .myst-cube-anim-video.block {{
    position: absolute !important;
    inset: 0 !important;
    width: 100% !important;
    height: 100% !important;
    min-height: var(--myst-viewport-min-height, calc(100dvh - 11rem)) !important;
    max-height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
    flex: none !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 2 !important;
    display: block !important;
}}
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-media .myst-cube-plot-inner.block .wrap,
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-media #unit-cell-viewport .wrap {{
    display: block !important;
    width: 100% !important;
    height: 100% !important;
    flex: none !important;
}}
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-media .myst-cube-anim-video.block {{
    z-index: 3 !important;
}}
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-media > .block[style*="display: none"],
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-media > .block.hidden,
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-media > .block[hidden] {{
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
    min-height: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
}}
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-media .myst-cube-anim-video .wrap,
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-media .myst-cube-anim-video .video-container,
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-media .myst-cube-anim-video video {{
    width: 100% !important;
    height: 100% !important;
    max-width: 100% !important;
    max-height: 100% !important;
    object-fit: contain !important;
    object-position: center center !important;
    background: #000000 !important;
    display: block !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-gravity-preset-tui-section {{
    flex: 1 1 auto !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    border-top: none !important;
    position: relative !important;
    z-index: 4 !important;
    background: transparent !important;
    min-height: 0 !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
}}
.gradio-container .myst-gravity-preset-tui-header {{
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: calc(0.05rem * var(--myst-gravity-ui-scale, 1)) !important;
    width: 100% !important;
    margin: 0 !important;
    padding: calc(0.38rem * var(--myst-gravity-ui-scale, 1)) calc(0.65rem * var(--myst-gravity-ui-scale, 1)) calc(0.42rem * var(--myst-gravity-ui-scale, 1)) !important;
    border-bottom: 1px solid rgba(74, 56, 24, 0.45) !important;
    border-radius: 0 !important;
    background: transparent !important;
    flex: 0 0 auto !important;
}}
.gradio-container .myst-gravity-preset-tui-section .myst-gravity-preset-tui-wrap,
.gradio-container .myst-gravity-preset-tui-section .myst-gravity-preset-tui-wrap.block {{
    flex: 1 1 0 !important;
    width: calc(100% - 0.9rem) !important;
    height: 100% !important;
    min-height: calc(100dvh - 17rem) !important;
    max-height: none !important;
    margin: calc(0.3rem * var(--myst-gravity-ui-scale, 1)) calc(0.45rem * var(--myst-gravity-ui-scale, 1)) calc(0.4rem * var(--myst-gravity-ui-scale, 1)) !important;
    padding: calc(0.5rem * var(--myst-gravity-ui-scale, 1)) calc(0.6rem * var(--myst-gravity-ui-scale, 1)) !important;
    border: 2px inset #5c4a1f !important;
    border-radius: 8px !important;
    background: rgba(0, 0, 0, 0.62) !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-gravity-preset-tui-section .html-container,
.gradio-container .myst-gravity-preset-tui-section .html-container .prose {{
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-preset-tui-serial {{
    min-height: 8rem !important;
    font-family: "Courier New", Courier, monospace !important;
    font-size: var(--myst-gravity-tui-font, 0.8rem) !important;
    line-height: 1.45 !important;
    color: #ffffff !important;
}}
.gradio-container .myst-preset-tui-menu .myst-preset-tui-lines {{
    color: #f5e6c8 !important;
}}
.gradio-container .myst-preset-tui-status {{
    margin: 0 0 0.5rem 0 !important;
    font-weight: 700 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    color: #ffffff !important;
}}
.gradio-container .myst-preset-tui-status u {{
    text-decoration: underline !important;
    text-underline-offset: 3px !important;
}}
.gradio-container .myst-preset-tui-key-label {{
    margin: 0.35rem 0 0.2rem 0 !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: #33ff66 !important;
    font-weight: 700 !important;
}}
.gradio-container .myst-preset-tui-key-metrics {{
    margin: 0 0 0.45rem 0 !important;
    white-space: pre !important;
    color: #33ff66 !important;
    text-shadow: 0 0 6px rgba(51, 255, 102, 0.25) !important;
    font-family: inherit !important;
    font-size: inherit !important;
    line-height: inherit !important;
}}
.gradio-container .myst-preset-tui-lines {{
    margin: 0 !important;
    white-space: pre !important;
    color: #f5e6c8 !important;
    font-family: inherit !important;
    font-size: inherit !important;
    line-height: inherit !important;
}}
.gradio-container .myst-gravity-preset-grid {{
    width: 100% !important;
    margin: 0 0 0.35rem 0 !important;
}}
.gradio-container .myst-gravity-preset-grid .myst-gravity-preset-row {{
    display: grid !important;
    grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
    gap: 0.28rem !important;
    width: 100% !important;
    margin: 0 0 0.28rem 0 !important;
}}
.gradio-container .myst-gravity-preset-grid .myst-gravity-preset-row > .block,
.gradio-container .myst-gravity-preset-grid .myst-gravity-preset-row > .form {{
    min-width: 0 !important;
    width: 100% !important;
}}
.gradio-container .myst-gravity-page .vqc-gravity-panel button.myst-gravity-quick-preset {{
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    padding: 0.26rem 0.2rem !important;
    font-size: 0.72rem !important;
}}
.gradio-container .myst-gravity-left-frame.myst-gravity-panel-window.vqc-optics-panel {{
    flex: 0 0 auto !important;
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 0.75rem 0.85rem !important;
    display: flex !important;
    flex-direction: column !important;
    box-sizing: border-box !important;
    overflow: visible !important;
}}
.gradio-container .myst-gravity-presets-tui-card.myst-gravity-left-frame.myst-gravity-panel-window.vqc-optics-panel {{
    flex: 1 1 0 !important;
    height: 100% !important;
    min-height: 0 !important;
    max-height: none !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: hidden !important;
}}
.gradio-container .myst-gravity-cube-panel.myst-gravity-panel-window.vqc-optics-panel {{
    flex: 1 1 0 !important;
    height: 100% !important;
    min-height: var(--myst-viewport-min-height, calc(100dvh - 11rem)) !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    display: grid !important;
    grid-template-rows: auto minmax(var(--myst-viewport-min-height, 18rem), 1fr) !important;
    grid-template-columns: minmax(0, 1fr) !important;
    align-content: stretch !important;
    align-items: stretch !important;
    box-sizing: border-box !important;
    overflow: visible !important;
}}
.gradio-container .myst-gravity-cube-panel.myst-gravity-panel-window > .block,
.gradio-container .myst-gravity-cube-panel.myst-gravity-panel-window > .column {{
    min-height: 0 !important;
}}
.gradio-container .myst-gravity-cube-panel.myst-gravity-panel-window > .gap {{
    display: none !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-gravity-cube-panel.myst-gravity-panel-window > .block:not(:has(.myst-cube-viewport-media)):not(:has(.myst-cube-viewport-media-slot)):not(:has(.myst-cube-viewport-plot-slot)):not(:has(.myst-cube-viewport-animation-slot)) {{
    grid-row: 1 !important;
    flex: unset !important;
    height: auto !important;
    min-height: 0 !important;
    overflow: visible !important;
}}
.gradio-container .myst-gravity-cube-panel.myst-gravity-panel-window > .block:has(.myst-cube-viewport-animation-slot),
.gradio-container .myst-gravity-cube-panel.myst-gravity-panel-window > .column.myst-cube-viewport-animation-slot {{
    grid-row: 3 !important;
    flex: 0 0 auto !important;
    height: auto !important;
    min-height: 10rem !important;
    max-height: none !important;
    overflow: visible !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 4 !important;
}}
.gradio-container .myst-gravity-cube-panel.myst-gravity-panel-window > .block:has(.myst-cube-viewport-media),
.gradio-container .myst-gravity-cube-panel.myst-gravity-panel-window > .block:has(.myst-cube-viewport-media-slot) {{
    grid-row: 2 !important;
    flex: unset !important;
    height: 100% !important;
    min-height: 0 !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
    justify-content: stretch !important;
}}
.gradio-container .myst-gravity-cube-panel.myst-gravity-panel-window > .column.myst-cube-viewport-media,
.gradio-container .myst-gravity-cube-panel.myst-gravity-panel-window > .column.myst-cube-viewport-media-slot {{
    grid-row: 2 !important;
    width: 100% !important;
    max-width: 100% !important;
    height: 100% !important;
    max-height: 100% !important;
    min-height: var(--myst-viewport-min-height, calc(100dvh - 11rem)) !important;
    align-self: stretch !important;
    margin: 0 !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 0 !important;
}}
.gradio-container .myst-gravity-left-frame .myst-gravity-controls-accordion {{
    flex: 0 0 auto !important;
    background: rgba(0, 0, 0, 0.18) !important;
    border: 1px solid #4a3818 !important;
    border-radius: 10px !important;
    box-shadow: inset 0 1px 0 rgba(255, 220, 150, 0.08) !important;
    overflow: hidden !important;
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 0 0.4rem 0 !important;
}}
.gradio-container .myst-gravity-left-frame .myst-gravity-levels-accordion .accordion {{
    max-height: min(28vh, 16rem) !important;
    overflow-y: auto !important;
}}
.gradio-container .myst-gravity-left-frame .myst-gravity-manual-edit-accordion {{
    flex: 0 0 auto !important;
    margin: 0 !important;
    overflow: hidden !important;
}}
.gradio-container .myst-gravity-left-frame .myst-gravity-manual-edit-accordion .accordion {{
    max-height: min(42vh, 26rem) !important;
    overflow-y: auto !important;
}}
.gradio-container .myst-gravity-left-frame .myst-gravity-manual-edit-accordion .myst-cube-viewport-header {{
    margin-top: 0.15rem !important;
}}
.gradio-container .myst-gravity-left-frame .myst-gravity-metrics-inner {{
    flex: 0 0 auto !important;
    min-height: 10rem !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
    padding: 0.45rem 0.55rem 0.55rem !important;
    border: 1px solid #4a3818 !important;
    border-radius: 10px !important;
    background: rgba(0, 0, 0, 0.22) !important;
}}
.gradio-container .myst-gravity-left-frame .myst-gravity-metrics-inner textarea {{
    flex: 0 0 auto !important;
    min-height: 8.5rem !important;
    height: auto !important;
    max-height: 12rem !important;
}}
.gradio-container .myst-gravity-controls-col .myst-gravity-controls-accordion {{
    flex: 0 1 auto !important;
}}
.gradio-container .myst-gravity-controls-col .myst-gravity-controls-accordion > .label-wrap {{
    background: linear-gradient(180deg, #1f140a 0%, #0f0a06 100%) !important;
    border-bottom: 1px solid rgba(74, 56, 24, 0.65) !important;
    padding: 0 0.75rem !important;
    margin: 0 !important;
    min-height: var(--myst-control-bar-height, 2.05rem) !important;
    height: var(--myst-control-bar-height, 2.05rem) !important;
    display: flex !important;
    align-items: center !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-gravity-controls-col .myst-gravity-controls-accordion > .label-wrap span {{
    color: #f5e6c8 !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}}
.gradio-container .myst-gravity-controls-col .myst-gravity-controls-accordion .accordion {{
    padding: 0.65rem 0.75rem 0.85rem !important;
    background: transparent !important;
}}
.gradio-container .myst-gravity-controls-col .myst-gravity-controls-accordion .vqc-gravity-panel.vqc-optics-panel {{
    border: none !important;
    box-shadow: none !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-gravity-left-frame .myst-gravity-metrics-inner .label-wrap span {{
    color: #e8d4a8 !important;
    font-size: 0.76rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}}
/* Grid cells: override global .block {{ width:100% }} that forces row wrap */
.gradio-container .myst-gravity-split > .column,
.gradio-container .myst-gravity-split > .block,
.gradio-container .myst-gravity-split > .form,
.gradio-container .myst-gravity-split > .gr-box {{
    min-width: 0 !important;
    min-height: 0 !important;
    height: 100% !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
}}
.gradio-container .myst-gravity-split > .column.myst-gravity-visuals-col,
.gradio-container .myst-gravity-split > .block:has(.myst-gravity-visuals-col) {{
    display: flex !important;
    flex-direction: column !important;
    flex-wrap: nowrap !important;
    align-self: stretch !important;
    min-height: 100% !important;
    min-width: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    overflow: hidden !important;
}}
.gradio-container .myst-gravity-visuals-col > .column.myst-gravity-visuals-stack,
.gradio-container .myst-gravity-visuals-col > .block:has(.myst-gravity-visuals-stack) {{
    flex: 1 1 0 !important;
    min-height: 0 !important;
    height: 100% !important;
    width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    flex-wrap: nowrap !important;
    overflow: hidden !important;
}}
.gradio-container .myst-gravity-split > .block:has(.myst-gravity-visuals-col) > .form {{
    flex: 1 1 0 !important;
    min-height: 0 !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
}}
.gradio-container .myst-gravity-controls-col .vqc-gravity-panel.vqc-optics-panel {{
    width: 100% !important;
}}
.gradio-container .myst-gravity-controls-col .myst-gravity-control-top-slot.vqc-optics-panel {{
    height: auto !important;
    flex: 0 0 auto !important;
}}
.gradio-container .myst-gravity-controls-col .myst-gravity-presets-tui-card.vqc-optics-panel {{
    height: 100% !important;
    flex: 1 1 0 !important;
    min-height: 0 !important;
    padding: 0.2rem 0.55rem 0.35rem !important;
    margin: 0 !important;
}}
.gradio-container .myst-gravity-wired-hidden,
.gradio-container .myst-gravity-wired-hidden.block,
.gradio-container .myst-gravity-wired-hidden.column {{
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    visibility: hidden !important;
    pointer-events: none !important;
}}
.gradio-container .myst-gravity-presets-tui-card .myst-gravity-presets-header.myst-gravity-presets-header-single {{
    margin-top: 0 !important;
    padding-top: 0.1rem !important;
}}
.gradio-container .myst-gravity-visuals-col {{
    align-items: stretch !important;
    align-self: stretch !important;
    display: flex !important;
    flex-direction: column !important;
    flex-wrap: nowrap !important;
    height: 100% !important;
    min-height: 0 !important;
    overflow: hidden !important;
}}
.gradio-container .myst-gravity-visuals-stack {{
    display: flex !important;
    flex-direction: column !important;
    flex-wrap: nowrap !important;
    flex: 1 1 0 !important;
    height: 100% !important;
    min-height: 0 !important;
    width: 100% !important;
    gap: 0.5rem !important;
    overflow: hidden !important;
}}
.gradio-container .myst-gravity-visuals-stack > .gap {{
    display: none !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-gravity-visuals-col .myst-cube-viewport-frame,
.gradio-container .myst-gravity-visuals-col .gr-group.myst-cube-viewport-frame {{
    width: 100% !important;
    max-width: 100% !important;
    flex: 1 1 0 !important;
    height: 100% !important;
    min-height: 0 !important;
    margin: 0 !important;
}}
.gradio-container .myst-gravity-page .myst-cube-viewport-frame.vqc-optics-panel {{
    width: 100% !important;
    max-width: none !important;
    margin: 0 !important;
}}
.gradio-container .myst-gravity-page .myst-cube-viewport-frame .myst-cube-viewport-media {{
    flex: 1 1 0 !important;
    min-height: var(--myst-viewport-min-height, calc(100dvh - 11rem)) !important;
    height: 100% !important;
    max-height: 100% !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
    position: relative !important;
}}
.gradio-container .myst-gravity-page .myst-cube-viewport-frame > .block:has(.myst-cube-viewport-media) {{
    flex: 1 1 0 !important;
    min-height: var(--myst-viewport-min-height, calc(100dvh - 11rem)) !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
}}
.gradio-container .myst-gravity-page .myst-cube-viewport-frame .myst-cube-plot-inner {{
    min-height: 0 !important;
    max-height: 100% !important;
    height: 100% !important;
    flex: none !important;
}}
.gradio-container .myst-gravity-page .myst-cube-viewport-frame .myst-cube-viewport-header:not(.myst-cube-viewport-header-fixed) {{
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 0.05rem !important;
    width: 100% !important;
    margin: 0 0 0.3rem 0 !important;
    padding: 0.45rem 0.55rem 0.5rem !important;
    min-height: 0 !important;
    max-height: 4.25rem !important;
    overflow: hidden !important;
}}
.gradio-container .myst-gravity-page .myst-cube-viewport-header:not(.myst-cube-viewport-header-fixed) {{
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 0.08rem !important;
    width: 100% !important;
    margin: 0 0 0.35rem 0 !important;
    padding: 0.65rem 0.75rem 0.75rem !important;
    border-bottom: 1px solid rgba(74, 56, 24, 0.65) !important;
    border-radius: 10px 10px 0 0 !important;
    background: linear-gradient(180deg, #1f140a 0%, #0f0a06 100%) !important;
    box-shadow: inset 0 0 14px rgba(0, 0, 0, 0.55) !important;
    max-height: 4.25rem !important;
    overflow: hidden !important;
}}
.gradio-container .myst-cube-viewport-brand {{
    font-size: 0.58rem !important;
    letter-spacing: 0.28em !important;
    color: #c9a227 !important;
    font-weight: 700 !important;
}}
.gradio-container .myst-cube-viewport-title {{
    font-size: 1rem !important;
    letter-spacing: 0.1em !important;
    color: #f5e6c8 !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
}}
.gradio-container .myst-cube-viewport-sub,
.gradio-container .myst-cube-viewport-tag {{
    font-size: 0.64rem !important;
    letter-spacing: 0.14em !important;
    color: #e8d4a8 !important;
    text-transform: uppercase !important;
    font-weight: 600 !important;
}}
.gradio-container .myst-cube-viewport-status {{
    font-size: 0.78rem !important;
    letter-spacing: 0.04em !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    margin-top: 0.12rem !important;
}}
.gradio-container .myst-cube-viewport-legend {{
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 0.28rem 0.55rem !important;
    width: 100% !important;
    margin-top: 0.22rem !important;
    padding-top: 0.22rem !important;
    border-top: 1px solid rgba(74, 56, 24, 0.45) !important;
}}
.gradio-container .myst-cube-legend-item {{
    display: inline-flex !important;
    align-items: center !important;
    gap: 0.28rem !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.03em !important;
}}
.gradio-container .myst-cube-legend-swatch {{
    font-size: 0.72rem !important;
    line-height: 1 !important;
}}
.gradio-container .myst-cube-legend-label {{
    color: #ffffff !important;
    opacity: 0.88 !important;
}}
.gradio-container .myst-cube-viewport-equation {{
    width: 100% !important;
    margin-top: 0.22rem !important;
    margin-bottom: 0.08rem !important;
    padding: 0.28rem 0.4rem !important;
    border: 1px solid #c9a227 !important;
    border-radius: 6px !important;
    background: rgba(0, 0, 0, 0.45) !important;
    color: #ffffff !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.03em !important;
    font-weight: 600 !important;
    text-align: center !important;
    line-height: 1.35 !important;
    overflow: visible !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-equation {{
    flex: 0 0 auto !important;
}}
.gradio-container .myst-gravity-page .myst-cube-viewport-frame .myst-cube-plot-inner .label-wrap {{
    display: none !important;
}}
.gradio-container .myst-gravity-page .myst-cube-viewport-frame .myst-cube-plot-inner,
.gradio-container .myst-gravity-page .myst-cube-viewport-frame .myst-cube-plot-inner.block {{
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0.2rem 0.3rem 0.3rem !important;
    background: rgba(0, 0, 0, 0.22) !important;
    border: 1px solid #4a3818 !important;
    border-radius: 8px !important;
    flex: none !important;
    min-height: var(--myst-viewport-min-height, calc(100dvh - 11rem)) !important;
    height: 100% !important;
    max-height: 100% !important;
    display: block !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
    position: absolute !important;
    inset: 0 !important;
    z-index: 2 !important;
}}
.gradio-container .myst-gravity-page .myst-cube-viewport-frame .myst-cube-plot-inner .label-wrap span {{
    color: #e8d4a8 !important;
    font-size: 0.76rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    font-weight: 700 !important;
}}
.gradio-container .myst-gravity-page .myst-cube-viewport-frame .plot-container {{
    width: 100% !important;
    height: var(--myst-viewport-plot-height, calc(100dvh - 12.5rem)) !important;
    min-height: var(--myst-viewport-plot-height, calc(100dvh - 12.5rem)) !important;
    max-height: var(--myst-viewport-plot-height, calc(100dvh - 12.5rem)) !important;
    border: 2px inset #5c4a1f !important;
    border-radius: 8px !important;
    background-color: #000000 !important;
    padding: 0.15rem !important;
    box-shadow: inset 0 0 18px rgba(0, 0, 0, 0.75) !important;
    display: block !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
    flex: none !important;
}}
.gradio-container .myst-gravity-page .myst-cube-viewport-frame .plot-container > div,
.gradio-container .myst-gravity-page .myst-cube-viewport-frame .plot-container .matplotlib {{
    width: 100% !important;
    height: 100% !important;
    max-width: 100% !important;
    max-height: 100% !important;
    display: block !important;
    flex: none !important;
}}
.gradio-container .myst-gravity-page .myst-cube-viewport-frame .plot-container img,
.gradio-container .myst-gravity-page .myst-cube-viewport-frame .plot-container canvas,
.gradio-container .myst-gravity-page .myst-cube-viewport-frame .plot-container svg {{
    width: 100% !important;
    height: 100% !important;
    max-width: 100% !important;
    max-height: 100% !important;
    margin: 0 !important;
    display: block !important;
    flex: none !important;
    object-fit: contain !important;
    object-position: center center !important;
}}
.gradio-container .myst-gravity-visuals-col,
.gradio-container .myst-gravity-split > .column.myst-gravity-visuals-col,
.gradio-container .column:has(#unit-cell-viewport) {{
    flex: 1 1 0 !important;
    height: 100% !important;
    min-height: var(--myst-viewport-min-height, calc(100dvh - 11rem)) !important;
    display: flex !important;
    flex-direction: column !important;
    align-self: stretch !important;
}}
.gradio-container .myst-cube-viewport-media .myst-cube-plot-inner.block,
.gradio-container .myst-cube-viewport-media #unit-cell-viewport,
.gradio-container .myst-cube-viewport-media #unit-cell-viewport .wrap {{
    width: 100% !important;
    height: 100% !important;
    min-height: 100% !important;
    max-height: 100% !important;
    display: block !important;
    flex: none !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-gravity-cube-panel .myst-cube-viewport-media .plot-container {{
    width: 100% !important;
    height: var(--myst-viewport-plot-height, calc(100dvh - 12.5rem)) !important;
    min-height: var(--myst-viewport-plot-height, calc(100dvh - 12.5rem)) !important;
    max-height: var(--myst-viewport-plot-height, calc(100dvh - 12.5rem)) !important;
    display: block !important;
    flex: none !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-gravity-page .vqc-gravity-panel.vqc-optics-panel {{
    background: linear-gradient(165deg, #2a1810 0%, #1a1008 38%, #120c06 100%) !important;
    border: 3px solid #6b4f1d !important;
    margin: 0 !important;
}}
.gradio-container .myst-gravity-page .vqc-gravity-panel .vqc-optics-panel-header {{
    border-bottom: 1px solid rgba(74, 56, 24, 0.65) !important;
    background: linear-gradient(180deg, #1f140a 0%, #0f0a06 100%) !important;
}}
.gradio-container .myst-gravity-page .vqc-gravity-panel .vqc-optics-logo {{
    border-right-color: rgba(107, 79, 29, 0.45) !important;
}}
.gradio-container .myst-gravity-page .vqc-gravity-panel .label-wrap span,
.gradio-container .myst-gravity-page .vqc-gravity-panel label span {{
    color: #e8d4a8 !important;
}}
.gradio-container .myst-gravity-page .vqc-gravity-panel .info {{
    color: #9a8458 !important;
}}
.gradio-container .myst-gravity-page .vqc-gravity-panel input[type="range"] {{
    background: linear-gradient(90deg, #1a1208, #3d2e14, #1a1208) !important;
    border: 1px solid #5c4a1f !important;
}}
.gradio-container .myst-gravity-page .vqc-gravity-panel input[type="range"]::-webkit-slider-thumb {{
    background: radial-gradient(circle at 32% 28%, #fff2cc 0%, #ea580c 38%, #7c2d12 72%, #2a1f08 100%) !important;
}}
.gradio-container .myst-gravity-page .vqc-gravity-panel input[type="range"]::-moz-range-thumb {{
    background: radial-gradient(circle at 32% 28%, #fff2cc 0%, #ea580c 38%, #7c2d12 72%, #2a1f08 100%) !important;
}}
.gradio-container .myst-gravity-page .vqc-gravity-panel .vqc-optics-dial-wrap {{
    background: rgba(0, 0, 0, 0.22) !important;
    border: 1px solid #4a3818 !important;
}}
.gradio-container .myst-gravity-page .vqc-gravity-panel button.vqc-receiver-preset {{
    background: linear-gradient(180deg, #3d2e14 0%, #1f1608 100%) !important;
    border: 2px solid #6b4f1d !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
}}
.gradio-container .myst-gravity-page .vqc-gravity-panel button.vqc-receiver-preset,
.gradio-container .myst-gravity-page .vqc-gravity-panel button.vqc-receiver-preset span {{
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}}
.gradio-container .myst-gravity-page .vqc-gravity-panel button.vqc-receiver-preset:hover,
.gradio-container .myst-gravity-page .vqc-gravity-panel button.vqc-receiver-preset:not(.active):hover,
.gradio-container .myst-gravity-page .vqc-gravity-panel button.vqc-receiver-preset:not(.active):hover span {{
    background: linear-gradient(180deg, #6b4f1d 0%, #3d2e14 100%) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}}
.gradio-container .myst-gravity-page .vqc-gravity-panel button.vqc-receiver-preset.vqc-full-width {{
    width: 100% !important;
    margin-top: 0.2rem !important;
}}
.gradio-container .myst-gravity-control-panel button.myst-gravity-edit-params-btn.active,
.gradio-container .myst-gravity-control-panel button.myst-gravity-edit-params-btn.active span,
.gradio-container .myst-gravity-control-panel button.myst-gravity-edit-params-btn.active:hover,
.gradio-container .myst-gravity-control-panel button.myst-gravity-edit-params-btn.active:hover span {{
    color: {_VQC_MATRIX_GREEN} !important;
    -webkit-text-fill-color: {_VQC_MATRIX_GREEN} !important;
}}
.gradio-container .myst-gravity-page .vqc-gravity-panel textarea {{
    background: #120c06 !important;
    border: 2px inset #5c4a1f !important;
    color: #ffb347 !important;
    font-family: "Courier New", Courier, monospace !important;
}}
.gradio-container .myst-gravity-control-levels-wrap,
.gradio-container .myst-gravity-control-levels-wrap .html-container {{
    width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
}}
.gradio-container .myst-render-page .myst-gravity-control-levels-wrap,
.gradio-container .myst-render-page .myst-gravity-control-levels-wrap .html-container {{
    width: 100% !important;
    max-width: 100% !important;
    height: 100% !important;
    min-height: 0 !important;
    flex: 1 1 auto !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
    justify-content: flex-start !important;
}}
.gradio-container .myst-gravity-level-panel {{
    width: 100% !important;
    padding: 0.55rem 0.65rem 0.65rem !important;
    background: #000000 !important;
    border: 2px inset #5c4a1f !important;
    border-radius: 8px !important;
    font-family: "Courier New", Courier, monospace !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-gravity-level-title {{
    color: #f5e6c8 !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.14em !important;
    text-align: center !important;
    text-transform: uppercase !important;
}}
.gradio-container .myst-gravity-level-rule {{
    border: none !important;
    border-top: 1px solid rgba(245, 230, 200, 0.55) !important;
    margin: 0.45rem 0 0.55rem 0 !important;
}}
.gradio-container .myst-gravity-level-row {{
    display: grid !important;
    grid-template-columns: 2.35rem 1fr auto auto !important;
    align-items: center !important;
    gap: 0.28rem 0.35rem !important;
    margin: 0.18rem 0 !important;
    font-size: 0.74rem !important;
    line-height: 1.2 !important;
}}
.gradio-container .myst-gravity-level-id {{
    color: #f5e6c8 !important;
    font-weight: 600 !important;
    white-space: nowrap !important;
}}
.gradio-container .myst-gravity-level-bar {{
    display: inline-flex !important;
    gap: 1px !important;
    min-height: 0.72rem !important;
    align-items: center !important;
}}
.gradio-container .myst-level-block {{
    display: inline-block !important;
    width: 0.46rem !important;
    height: 0.72rem !important;
    border-radius: 1px !important;
}}
.gradio-container .myst-level-block.myst-level-fill.myst-level-pos {{
    background: #33ff66 !important;
    box-shadow: 0 0 4px rgba(51, 255, 102, 0.45) !important;
}}
.gradio-container .myst-level-block.myst-level-fill.myst-level-neg {{
    background: #ff3344 !important;
    box-shadow: 0 0 4px rgba(255, 51, 68, 0.45) !important;
}}
.gradio-container .myst-level-block.myst-level-empty {{
    background: rgba(255, 255, 255, 0.08) !important;
}}
.gradio-container .myst-gravity-level-sep {{
    color: #f5e6c8 !important;
    opacity: 0.85 !important;
}}
.gradio-container .myst-gravity-level-val {{
    min-width: 4.1rem !important;
    text-align: right !important;
    font-weight: 700 !important;
    white-space: nowrap !important;
}}
.gradio-container .myst-gravity-level-val.myst-val-pos {{
    color: #33ff66 !important;
}}
.gradio-container .myst-gravity-level-val.myst-val-neg {{
    color: #ff3344 !important;
}}
.gradio-container .myst-gravity-level-foot,
.gradio-container .myst-gravity-level-hint {{
    margin-top: 0.55rem !important;
    color: #9a8458 !important;
    font-size: 0.66rem !important;
    letter-spacing: 0.06em !important;
    text-align: center !important;
}}
.gradio-container .myst-preset-tui-menu .myst-preset-tui-lines,
.gradio-container .myst-preset-tui-values .myst-preset-tui-lines {{
    color: #e8d4a8 !important;
    font-size: 0.68rem !important;
    line-height: 1.35 !important;
}}
.gradio-container .myst-gravity-levels-accordion > .label-wrap span {{
    color: #f5e6c8 !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}}

.gradio-container .myst-gravity-visuals-col .markdown.prose {{
    font-size: 0.92rem !important;
    line-height: 1.45 !important;
}}
.gradio-container .myst-app-footer,
.gradio-container .myst-app-footer.block,
.gradio-container .myst-app-footer > .block,
.gradio-container .myst-app-footer > .form {{
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    pointer-events: none !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
.gradio-container .myst-app-footer .markdown,
.gradio-container .myst-app-footer .prose,
.gradio-container .myst-app-footer p {{
    margin: 0 !important;
    padding: 0 !important;
    font-size: 0.66rem !important;
    line-height: 1.2 !important;
    color: #9a90b8 !important;
}}
.gradio-container .myst-readme-page {{
    width: 100% !important;
    max-width: none !important;
    height: calc(100dvh - 3.5rem) !important;
    max-height: calc(100dvh - 3.5rem) !important;
    min-height: 0 !important;
    background: #000000 !important;
    padding: 0 !important;
    margin: 0 !important;
    position: relative !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
    overflow: hidden !important;
}}
.gradio-container .myst-readme-page > .block,
.gradio-container .myst-readme-page > .form {{
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 auto !important;
    min-height: 0 !important;
    max-height: 100% !important;
    overflow: hidden !important;
}}
.gradio-container .myst-scrollable-panel,
.gradio-container .myst-readme-scrollable-content {{
    max-height: calc(100dvh - 10rem) !important;
    min-height: 0 !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    padding-right: 12px !important;
    scrollbar-width: thin !important;
    scrollbar-color: #4a4a6a #1a1a22 !important;
}}
.gradio-container .myst-scrollable-panel::-webkit-scrollbar,
.gradio-container .myst-readme-scrollable-content::-webkit-scrollbar {{
    width: 8px !important;
}}
.gradio-container .myst-scrollable-panel::-webkit-scrollbar-track,
.gradio-container .myst-readme-scrollable-content::-webkit-scrollbar-track {{
    background: #1a1a22 !important;
    border-radius: 4px !important;
}}
.gradio-container .myst-scrollable-panel::-webkit-scrollbar-thumb,
.gradio-container .myst-readme-scrollable-content::-webkit-scrollbar-thumb {{
    background-color: #4a4a6a !important;
    border-radius: 4px !important;
    border: 2px solid #1a1a22 !important;
}}
.gradio-container .myst-scrollable-panel::-webkit-scrollbar-thumb:hover,
.gradio-container .myst-readme-scrollable-content::-webkit-scrollbar-thumb:hover {{
    background-color: #6a6a8a !important;
}}
.gradio-container .myst-readme-page .myst-readme-body,
.gradio-container .myst-readme-page #readme-scroll-container {{
    flex: 1 1 auto !important;
    width: 100% !important;
    min-height: 0 !important;
    max-height: calc(100dvh - 10rem) !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    background: #000000 !important;
    padding: 0 0 3rem !important;
    scrollbar-color: #4a4a6a #1a1a22 !important;
    scrollbar-width: thin !important;
}}
.gradio-container .myst-readme-page .myst-readme-body > .block,
.gradio-container .myst-readme-page .myst-readme-body > .form,
.gradio-container .myst-readme-page #readme-scroll-container > .block,
.gradio-container .myst-readme-page #readme-scroll-container > .form {{
    min-height: 0 !important;
    max-height: inherit !important;
    overflow: visible !important;
}}
.gradio-container .myst-readme-page .myst-readme-body .html-container,
.gradio-container .myst-readme-page .myst-readme-body .prose,
.gradio-container .myst-readme-page #readme-scroll-container .html-container,
.gradio-container .myst-readme-page #readme-scroll-container .prose {{
    width: 100% !important;
    max-width: none !important;
    padding: 0 !important;
    margin: 0 !important;
    background: #000000 !important;
}}
.gradio-container .myst-readme-heading {{
    color: #e0e0e0 !important;
    margin-top: 1.5rem !important;
    margin-bottom: 0.75rem !important;
}}
.gradio-container .myst-readme-fullpage {{
    color: #ffffff !important;
    background: #000000 !important;
    font-family: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif !important;
    font-size: 1.125rem !important;
    line-height: 1.75 !important;
    max-width: 52rem !important;
    margin: 0 auto !important;
    padding: 1.25rem 1.5rem 4rem !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-readme-fullpage h1 {{
    font-size: 2rem !important;
    line-height: 1.2 !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    margin: 0.35rem 0 1rem !important;
}}
.gradio-container .myst-readme-fullpage h2 {{
    font-size: 1.45rem !important;
    line-height: 1.3 !important;
    font-weight: 650 !important;
    color: #ffffff !important;
    margin: 0 0 0.85rem !important;
}}
.gradio-container .myst-readme-fullpage h3 {{
    font-size: 1.15rem !important;
    line-height: 1.35 !important;
    font-weight: 600 !important;
    color: #f0f0f0 !important;
    margin: 1.25rem 0 0.65rem !important;
}}
.gradio-container .myst-readme-fullpage p,
.gradio-container .myst-readme-fullpage li {{
    color: #ffffff !important;
    font-size: 1.125rem !important;
    line-height: 1.75 !important;
}}
.gradio-container .myst-readme-fullpage a {{
    color: #9ecbff !important;
    text-decoration: underline !important;
    text-underline-offset: 2px !important;
}}
.gradio-container .myst-readme-fullpage a:hover {{
    color: #c8e4ff !important;
}}
.gradio-container .myst-readme-fullpage code {{
    color: #e8e8e8 !important;
    background: #1a1a1a !important;
    padding: 0.1rem 0.35rem !important;
    border-radius: 4px !important;
    font-size: 0.95em !important;
}}
.gradio-container .myst-readme-fullpage blockquote {{
    border-left: 3px solid #444444 !important;
    margin: 1rem 0 !important;
    padding: 0.35rem 0 0.35rem 1.1rem !important;
    color: #dddddd !important;
    font-style: italic !important;
}}
.gradio-container .myst-readme-kicker {{
    font-size: 0.82rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: #888888 !important;
    margin: 0 0 0.35rem !important;
}}
.gradio-container .myst-readme-lead {{
    color: #cccccc !important;
    margin-top: 0 !important;
}}
.gradio-container .myst-readme-muted {{
    color: #aaaaaa !important;
    font-size: 1rem !important;
}}
.gradio-container .myst-readme-formula {{
    font-size: 1.55rem !important;
    font-weight: 600 !important;
    text-align: center !important;
    letter-spacing: 0.04em !important;
    margin: 1rem 0 1.25rem !important;
    color: #ffffff !important;
}}
.gradio-container .myst-readme-divider {{
    border: none !important;
    border-top: 1px solid #2a2a2a !important;
    margin: 2rem 0 !important;
}}
.gradio-container .myst-readme-card {{
    background: #0a0a0a !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 10px !important;
    padding: 1.15rem 1.25rem !important;
    margin-bottom: 1.5rem !important;
}}
.gradio-container .myst-readme-exec-title {{
    margin-top: 0 !important;
    font-size: 1.2rem !important;
    color: #f5e6c8 !important;
}}
.gradio-container .myst-readme-exec-list,
.gradio-container .myst-readme-steps {{
    margin: 0.75rem 0 0 !important;
    padding-left: 1.35rem !important;
}}
.gradio-container .myst-readme-table {{
    width: 100% !important;
    border-collapse: collapse !important;
    margin-top: 0.75rem !important;
    font-size: 1rem !important;
}}
.gradio-container .myst-readme-table th,
.gradio-container .myst-readme-table td {{
    border: 1px solid #333333 !important;
    padding: 0.55rem 0.7rem !important;
    text-align: left !important;
    color: #ffffff !important;
}}
.gradio-container .myst-readme-table th {{
    background: #141414 !important;
    color: #dddddd !important;
    font-weight: 600 !important;
}}
.gradio-container .myst-readme-figure-grid {{
    display: grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    gap: 1rem !important;
    margin-top: 1rem !important;
}}
.gradio-container .myst-readme-figure {{
    margin: 0 !important;
    background: #0a0a0a !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}}
.gradio-container .myst-readme-figure img {{
    width: 100% !important;
    height: auto !important;
    display: block !important;
    background: #000000 !important;
}}
.gradio-container .myst-readme-figure figcaption {{
    padding: 0.45rem 0.6rem !important;
    font-size: 0.88rem !important;
    color: #aaaaaa !important;
    text-align: center !important;
}}
.gradio-container .myst-readme-footer .myst-readme-tagline {{
    font-size: 1.2rem !important;
    margin: 1.25rem 0 0.5rem !important;
}}
.gradio-container .myst-readme-signature {{
    color: #cccccc !important;
    margin-top: 0.5rem !important;
}}
.gradio-container .myst-readme-back-row {{
    position: sticky !important;
    top: 0 !important;
    z-index: 40 !important;
    display: flex !important;
    justify-content: flex-end !important;
    padding: 0.45rem 0.75rem !important;
    background: linear-gradient(180deg, #000000 78%, transparent) !important;
    pointer-events: none !important;
}}
.gradio-container .myst-readme-back-row .myst-standard-back-btn {{
    pointer-events: auto !important;
    min-width: 9.5rem !important;
}}
@media (max-width: 720px) {{
    .gradio-container .myst-readme-fullpage {{
        padding: 1rem 1rem 3.5rem !important;
        font-size: 1.05rem !important;
    }}
    .gradio-container .myst-readme-figure-grid {{
        grid-template-columns: 1fr !important;
    }}
}}
.gradio-container .myst-status-page,
.gradio-container .myst-render-page,
.gradio-container .myst-edit-page {{
    width: 100% !important;
    max-width: none !important;
    padding: 0 0.25rem 0 !important;
}}
.gradio-container .myst-status-page,
.gradio-container .myst-render-page {{
    {_nav_theme_gradio_css_vars()}
    min-height: calc(100dvh - 4.25rem) !important;
    height: auto !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
    justify-content: flex-start !important;
    gap: 0 !important;
    row-gap: 0 !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-render-page {{
    --myst-render-grid-gap: 0.18rem;
    --myst-render-grid-bottom-frame: 0.38rem;
    padding: 0 !important;
}}
.gradio-container .myst-status-page .myst-status-gap-row,
.gradio-container .myst-status-page .myst-default-gap-row,
.gradio-container .myst-status-page .myst-status-zoom-edit-col > .row.myst-status-gap-row,
.gradio-container .myst-render-page .myst-status-gap-row,
.gradio-container .myst-render-page .myst-default-gap-row {{
    min-height: var(--myst-default-gap-height) !important;
    height: var(--myst-default-gap-height) !important;
    max-height: var(--myst-default-gap-height) !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    flex: 0 0 auto !important;
    width: 100% !important;
    display: flex !important;
    visibility: visible !important;
    align-items: stretch !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
.gradio-container .myst-status-page > .block:has(.myst-status-gap-row),
.gradio-container .myst-status-page > .form:has(.myst-status-gap-row),
.gradio-container .myst-status-page .myst-status-stack > .block:has(.myst-status-gap-row),
.gradio-container .myst-status-page .myst-status-stack > .form:has(.myst-status-gap-row),
.gradio-container .myst-status-page .myst-status-zoom-edit-col > .block:has(.myst-status-gap-row),
.gradio-container .myst-status-page .myst-status-zoom-edit-col > .form:has(.myst-status-gap-row),
.gradio-container .myst-status-page .myst-status-gap-row > .block.myst-status-gap-fill-host,
.gradio-container .myst-status-page .myst-status-gap-row > .form.myst-status-gap-fill-host {{
    min-height: var(--myst-default-gap-height) !important;
    height: var(--myst-default-gap-height) !important;
    max-height: var(--myst-default-gap-height) !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    flex: 0 0 auto !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
.gradio-container .myst-status-page .myst-status-gap-row.myst-status-gap-half,
.gradio-container .myst-status-page > .block:has(.myst-status-gap-half),
.gradio-container .myst-status-page > .form:has(.myst-status-gap-half),
.gradio-container .myst-status-page .myst-status-stack > .block:has(.myst-status-gap-half),
.gradio-container .myst-status-page .myst-status-stack > .form:has(.myst-status-gap-half),
.gradio-container .myst-status-page .myst-status-gap-half > .block.myst-status-gap-fill-host,
.gradio-container .myst-status-page .myst-status-gap-half > .form.myst-status-gap-fill-host {{
    min-height: var(--myst-half-gap-height) !important;
    height: var(--myst-half-gap-height) !important;
    max-height: var(--myst-half-gap-height) !important;
}}
.gradio-container .myst-status-page .myst-status-gap-fill,
.gradio-container .myst-status-page .myst-status-gap-fill-host,
.gradio-container .myst-status-page .myst-status-gap-fill-host .html-container,
.gradio-container .myst-status-page [id^="myst-status-gap-fill-"] {{
    width: 100% !important;
    height: 100% !important;
    min-height: var(--myst-default-gap-height) !important;
    max-height: var(--myst-default-gap-height) !important;
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    pointer-events: none !important;
}}
.gradio-container .myst-status-page .myst-status-gap-half .myst-status-gap-fill,
.gradio-container .myst-status-page .myst-status-gap-half .myst-status-gap-fill-host,
.gradio-container .myst-status-page .myst-status-gap-half .myst-status-gap-fill-host .html-container,
.gradio-container .myst-status-page .myst-status-gap-half [id^="myst-status-gap-fill-"] {{
    min-height: var(--myst-half-gap-height) !important;
    max-height: var(--myst-half-gap-height) !important;
}}
.gradio-container .myst-status-page > .block:has(.vqc-main-nav-row),
.gradio-container .myst-status-page > .form:has(.vqc-main-nav-row) {{
    flex: 0 0 auto !important;
    height: auto !important;
    margin-bottom: 0 !important;
}}
.gradio-container .myst-status-page > .block:has(.myst-status-stack),
.gradio-container .myst-status-page > .form:has(.myst-status-stack),
.gradio-container .myst-status-page > .column.myst-status-stack,
.gradio-container .myst-render-page > .block:has(.myst-render-stack),
.gradio-container .myst-render-page > .form:has(.myst-render-stack),
.gradio-container .myst-render-page > .column.myst-render-stack {{
    flex: 1 1 auto !important;
    width: 100% !important;
    max-width: 100% !important;
    height: auto !important;
    min-height: 0 !important;
    margin-top: 0 !important;
    padding-top: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    justify-content: flex-start !important;
    align-content: stretch !important;
    align-items: stretch !important;
}}
.gradio-container .myst-status-page > .block,
.gradio-container .myst-status-page > .form,
.gradio-container .myst-status-page > .column,
.gradio-container .myst-status-page .block,
.gradio-container .myst-status-page .form {{
    background: transparent !important;
    box-shadow: none !important;
}}
.gradio-container .myst-status-page > .block:has(.vqc-animations-nav-row),
.gradio-container .myst-edit-page > .block:has(.vqc-animations-nav-row) {{
    flex: 0 0 auto !important;
}}
.gradio-container .myst-status-page .myst-status-preset-nav-wrap,
.gradio-container .myst-status-page .myst-status-preset-nav-wrap.row,
.gradio-container .myst-status-page #myst-status-zoom-nav,
.gradio-container .myst-status-page .row#myst-status-zoom-nav,
.gradio-container .myst-status-page .myst-status-stack > .block:has(#myst-status-zoom-nav),
.gradio-container .myst-status-page .myst-status-stack > .form:has(#myst-status-zoom-nav) {{
    flex: 0 0 auto !important;
    width: 100% !important;
    height: auto !important;
    min-height: var(--myst-control-bar-height, 2.05rem) !important;
    max-height: none !important;
    overflow: visible !important;
    margin: 0.04rem 0 0 !important;
    padding: 0 !important;
    align-self: stretch !important;
    display: grid !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-status-page .myst-status-grid-view.hide,
.gradio-container .myst-status-page .myst-status-grid-view.hidden,
.gradio-container .myst-status-page .myst-status-zoom-view.hide,
.gradio-container .myst-status-page .myst-status-zoom-view.hidden,
.gradio-container .myst-status-page .myst-status-panels-host > .hide,
.gradio-container .myst-status-page .myst-status-panels-host > .hidden,
.gradio-container .myst-status-page .myst-status-panels-host > .block.hide,
.gradio-container .myst-status-page .myst-status-panels-host > .block.hidden,
.gradio-container .myst-status-page .myst-status-panels-host > .form.hide,
.gradio-container .myst-status-page .myst-status-panels-host > .form.hidden,
.gradio-container .myst-status-page .myst-status-panels-host > .column.hide,
.gradio-container .myst-status-page .myst-status-panels-host > .column.hidden {{
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    overflow: hidden !important;
    pointer-events: none !important;
    flex: 0 0 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-status-page .myst-status-grid-view:not(.hide):not(.hidden),
.gradio-container .myst-status-page .myst-status-zoom-view:not(.hide):not(.hidden) {{
    width: 100% !important;
    height: auto !important;
    min-height: calc(100dvh - 7.5rem) !important;
    flex: 1 1 auto !important;
    background: transparent !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
}}
.gradio-container .myst-status-page .myst-status-zoom-host,
.gradio-container .myst-status-page .myst-status-zoom-host .html-container {{
    width: 100% !important;
    height: auto !important;
    min-height: 12rem !important;
    flex: 1 1 auto !important;
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    display: flex !important;
    flex-direction: column !important;
}}
.gradio-container .myst-status-page .myst-status-zoom-wrap {{
    width: 100% !important;
    height: auto !important;
    min-height: 12rem !important;
    flex: 1 1 auto !important;
    background: transparent !important;
    display: flex !important;
    flex-direction: column !important;
}}
.gradio-container .myst-status-page .myst-status-zoom-panel {{
    flex: 1 1 auto !important;
    height: auto !important;
    min-height: 12rem !important;
    max-height: none !important;
    overflow-y: visible !important;
}}
.gradio-container .myst-status-page .myst-status-zoom-panel .myst-gravity-level-title,
.gradio-container .myst-status-page .myst-status-zoom-panel .myst-gravity-level-foot,
.gradio-container .myst-status-page .myst-status-zoom-level-row,
.gradio-container .myst-status-page .myst-status-zoom-level-row .myst-gravity-level-id,
.gradio-container .myst-status-page .myst-status-zoom-level-row .myst-gravity-level-desc,
.gradio-container .myst-status-page .myst-status-zoom-level-row .myst-gravity-level-range,
.gradio-container .myst-status-page .myst-status-zoom-level-row .myst-gravity-level-val {{
    font-size: 0.82rem !important;
    line-height: 1.2 !important;
}}
.gradio-container .myst-status-page .myst-status-zoom-level-row {{
    grid-template-columns: 1.45rem minmax(0, 0.48fr) minmax(4.75rem, 0.72fr) minmax(0, 1.45fr) minmax(3.6rem, auto) !important;
    gap: 0.2rem 0.28rem !important;
    margin: 0 !important;
}}
.gradio-container .vqc-status-preset-nav-row .vqc-nav-cell button.myst-status-nav-back-btn,
.gradio-container .vqc-status-preset-nav-row .vqc-nav-cell button.myst-status-nav-edit-btn {{
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
}}
.gradio-container .vqc-status-preset-nav-row .vqc-nav-cell button.myst-status-nav-back-btn {{
    font-size: 0.72rem !important;
    padding-left: 0.28rem !important;
    padding-right: 0.28rem !important;
    letter-spacing: 0.01em !important;
}}
.gradio-container .myst-status-page .myst-status-zoom-edit-drawer.myst-gravity-control-panel {{
    background: transparent !important;
}}
.gradio-container .myst-status-page .myst-status-zoom-edit-drawer {{
    position: relative !important;
    left: auto !important;
    right: auto !important;
    top: auto !important;
    bottom: auto !important;
    z-index: 12 !important;
    width: 100% !important;
    margin: 0 0 0.55rem 0 !important;
    padding: 0 !important;
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    max-height: none !important;
    height: auto !important;
    min-height: 0 !important;
    flex: 0 0 auto !important;
    flex-shrink: 0 !important;
    overflow: visible !important;
}}
.gradio-container .myst-status-page .myst-status-panels-host > .block:has(.myst-status-zoom-edit-drawer),
.gradio-container .myst-status-page .myst-status-panels-host > .form:has(.myst-status-zoom-edit-drawer),
.gradio-container .myst-status-page .myst-status-panels-host > .column:has(.myst-status-zoom-edit-drawer) {{
    flex: 0 0 auto !important;
    flex-shrink: 0 !important;
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
    overflow: visible !important;
}}

.gradio-container .myst-status-page .myst-status-zoom-edit-drawer > .block,
.gradio-container .myst-status-page .myst-status-zoom-edit-drawer > .form,
.gradio-container .myst-status-page .myst-status-zoom-edit-drawer > .column,
.gradio-container .myst-status-page .myst-status-zoom-edit-col,
.gradio-container .myst-status-page .myst-status-zoom-edit-col > .block,
.gradio-container .myst-status-page .myst-status-zoom-edit-col > .form {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
.gradio-container .myst-status-page .myst-status-zoom-edit-col {{
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
    gap: 0.34rem !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    height: auto !important;
    min-height: 0 !important;
    max-height: 72vh !important;
    flex-shrink: 0 !important;
    overflow-x: hidden !important;
    overflow-y: auto !important;
    scrollbar-width: thin !important;
    scrollbar-color: #c9a227 #2a1f08 !important;
}}
.gradio-container .myst-status-page .myst-status-zoom-edit-col::-webkit-scrollbar {{
    width: 8px !important;
}}
.gradio-container .myst-status-page .myst-status-zoom-edit-col::-webkit-scrollbar-track {{
    background: #2a1f08 !important;
}}
.gradio-container .myst-status-page .myst-status-zoom-edit-col::-webkit-scrollbar-thumb {{
    background: #c9a227 !important;
    border-radius: 4px !important;
}}
.gradio-container .myst-status-page .myst-status-zoom-edit-col > .block,
.gradio-container .myst-status-page .myst-status-zoom-edit-col > .form,
.gradio-container .myst-status-page .myst-status-zoom-edit-col > .row:not(.slider-row):not(.myst-status-gap-row),
.gradio-container .myst-status-page .myst-status-zoom-edit-col > .column {{
    flex: 0 0 auto !important;
    flex-shrink: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    align-self: stretch !important;
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
    overflow: visible !important;
    position: static !important;
    z-index: auto !important;
    display: block !important;
}}
.gradio-container .myst-status-page .myst-status-zoom-edit-col > .row.slider-row {{
    display: flex !important;
}}
.gradio-container .myst-status-page .myst-status-zoom-edit-col > .block:has(.slider-row),
.gradio-container .myst-status-page .myst-status-zoom-edit-col > .form:has(.slider-row),
.gradio-container .myst-status-page .myst-status-zoom-edit-col .block:has(.slider-row),
.gradio-container .myst-status-page .myst-status-zoom-edit-col .form:has(.slider-row) {{
    min-height: 4.35rem !important;
    height: auto !important;
    width: 100% !important;
    max-width: 100% !important;
    margin: 0.08rem 0 !important;
    padding: 0 !important;
    overflow: visible !important;
    visibility: visible !important;
    opacity: 1 !important;
    flex: 0 0 auto !important;
    display: block !important;
}}
.gradio-container .myst-status-page .slider-row,
.gradio-container .myst-status-page .myst-status-zoom-edit-col .slider-row {{
    min-height: 4.35rem !important;
    height: auto !important;
    align-items: stretch !important;
    margin: 0 !important;
    padding: 0 !important;
    display: flex !important;
    flex-direction: row !important;
    width: 100% !important;
    max-width: 100% !important;
    flex: 0 0 auto !important;
    overflow: visible !important;
}}
.gradio-container .myst-status-page .slider-row > .block,
.gradio-container .myst-status-page .slider-row > .form {{
    flex: 1 1 100% !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    height: auto !important;
    min-height: 3.9rem !important;
    margin: 0 !important;
    padding: 0 !important;
    align-self: stretch !important;
    overflow: visible !important;
    display: block !important;
    visibility: visible !important;
}}

.gradio-container .myst-status-page .myst-status-zoom-edit-save-row {{
    display: flex !important;
    justify-content: stretch !important;
    align-items: stretch !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    min-height: var(--myst-control-bar-height, 2.05rem) !important;
    flex: 0 0 auto !important;
}}
.gradio-container .myst-status-page .myst-status-zoom-edit-col > .block:has(.myst-status-zoom-edit-save-row),
.gradio-container .myst-status-page .myst-status-zoom-edit-col > .form:has(.myst-status-zoom-edit-save-row),
.gradio-container .myst-status-page .myst-status-zoom-edit-save-row > .block,
.gradio-container .myst-status-page .myst-status-zoom-edit-save-row > .form {{
    width: 100% !important;
    flex: 1 1 auto !important;
    min-width: 0 !important;
    max-width: 100% !important;
}}
.gradio-container .myst-status-page .myst-status-zoom-edit-drawer .vqc-optics-dial-wrap,
.gradio-container .myst-status-page .myst-status-zoom-edit-col .vqc-optics-dial-wrap {{
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    width: 100% !important;
    min-height: 3.9rem !important;
    height: auto !important;
    padding: 0.5rem 0.8rem !important;
    margin: 0 !important;
    border-radius: 9px !important;
    background: rgba(26, 18, 38, 0.72) !important;
    border: 1px solid rgba(201, 162, 39, 0.28) !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25) !important;
    max-width: 100% !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
    overflow: visible !important;
}}
.gradio-container .myst-status-page .myst-status-zoom-edit-col .vqc-optics-dial-wrap > .wrap.hide,
.gradio-container .myst-status-page .myst-status-zoom-edit-col .vqc-optics-dial-wrap > .wrap.hidden,
.gradio-container .myst-status-page .myst-status-zoom-edit-col .vqc-optics-dial-wrap > .wrap.default.hidden {{
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    width: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    pointer-events: none !important;
    position: absolute !important;
}}
.gradio-container .myst-status-page .myst-status-zoom-edit-drawer .vqc-optics-dial-wrap .wrap:not(.hide):not(.hidden),
.gradio-container .myst-status-page .myst-status-zoom-edit-col .vqc-optics-dial-wrap .wrap:not(.hide):not(.hidden) {{
    display: flex !important;
    visibility: visible !important;
    position: static !important;
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    height: auto !important;
    margin: 0 !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-status-page .myst-status-zoom-edit-drawer .vqc-optics-dial-wrap .wrap > div,
.gradio-container .myst-status-page .myst-status-zoom-edit-col .vqc-optics-dial-wrap .wrap > div,
.gradio-container .myst-status-page .myst-status-zoom-edit-drawer .vqc-optics-dial-wrap input[type="range"],
.gradio-container .myst-status-page .myst-status-zoom-edit-col .vqc-optics-dial-wrap input[type="range"] {{
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    margin: 0 !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-status-page #myst-status-slider-02,
.gradio-container .myst-status-page #myst-status-slider-03 {{
    display: block !important;
    visibility: visible !important;
    width: 100% !important;
    max-width: 100% !important;
    min-height: 3.9rem !important;
    height: auto !important;
}}
.gradio-container .myst-status-page .myst-status-zoom-edit-save-row button.myst-status-zoom-save-btn,
.gradio-container .myst-status-page .myst-save-edit-row button.myst-status-zoom-save-btn {{
    width: 100% !important;
    min-width: 80px !important;
    max-width: 100% !important;
    min-height: var(--myst-control-bar-height, 2.05rem) !important;
    height: var(--myst-control-bar-height, 2.05rem) !important;
    margin: 0 !important;
    visibility: visible !important;
    opacity: 1 !important;
}}
/* ========== SAVE BUTTON ========== */
.gradio-container .myst-save-edit-row button.save-btn,
.gradio-container .myst-save-edit-row button.save-btn span {{
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border-color: var(--default-border-color, {DEFAULT_BUTTON_BORDER_COLOR}) !important;
}}
.gradio-container .myst-save-edit-row button.save-btn.saved,
.gradio-container .myst-save-edit-row button.save-btn.saved span {{
    color: #ff0000 !important;
    -webkit-text-fill-color: #ff0000 !important;
    border-color: #ff0000 !important;
    font-weight: 600 !important;
}}
/* ========== EDIT BUTTON ========== */
.gradio-container .myst-save-edit-row button.edit-btn,
.gradio-container .myst-save-edit-row button.edit-btn span,
.gradio-container .myst-status-page button.myst-status-nav-edit-btn.edit-btn,
.gradio-container .myst-status-page button.myst-status-nav-edit-btn.edit-btn span {{
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border-color: var(--default-border-color, {DEFAULT_BUTTON_BORDER_COLOR}) !important;
}}
.gradio-container .myst-status-page button.myst-status-zoom-save-btn {{
    padding-left: 0.78rem !important;
    padding-right: 0.78rem !important;
}}

.gradio-container .myst-status-page .myst-status-stack {{
    width: 100% !important;
    height: auto !important;
    min-height: calc(100dvh - 8rem) !important;
    flex: 1 1 auto !important;
    background: transparent !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
    align-items: stretch !important;
    gap: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-status-page .myst-status-stack > .block:has(.myst-status-panels-host),
.gradio-container .myst-status-page .myst-status-stack > .form:has(.myst-status-panels-host),
.gradio-container .myst-status-page .myst-status-panels-host {{
    width: 100% !important;
    flex: 0 0 auto !important;
    min-height: 0 !important;
    max-height: none !important;
    height: auto !important;
    display: flex !important;
    flex-direction: column !important;
    overflow-x: hidden !important;
    overflow-y: visible !important;
    position: relative !important;
    z-index: 4 !important;
    margin: 0 !important;
    padding: 0 !important;
    align-items: stretch !important;
}}
.gradio-container .myst-status-page .myst-status-panels-host > .block,
.gradio-container .myst-status-page .myst-status-panels-host > .form,
.gradio-container .myst-status-page .myst-status-panels-host > .column {{
    width: 100% !important;
    overflow: visible !important;
}}
.gradio-container .myst-status-page .myst-status-stack > .block:has(.myst-status-catalog-host):not(.hide):not(.hidden),
.gradio-container .myst-status-page .myst-status-stack > .form:has(.myst-status-catalog-host):not(.hide):not(.hidden),
.gradio-container .myst-status-page .myst-status-stack > .column.myst-status-catalog-host:not(.hide):not(.hidden),
.gradio-container .myst-status-page .myst-status-catalog-host:not(.hide):not(.hidden) {{
    flex: 1 1 auto !important;
    min-height: calc(100dvh - 8.5rem) !important;
    height: auto !important;
}}
.gradio-container .myst-status-page .myst-status-stack:has(.myst-status-edit-active),
.gradio-container .myst-status-page .myst-status-stack:has(.myst-status-zoom-edit-drawer:not(.hide):not(.hidden)) {{
    min-height: 0 !important;
    gap: 0.35rem !important;
}}
.gradio-container .myst-status-page .myst-status-panels-host.myst-status-edit-active,
.gradio-container .myst-status-page .myst-status-panels-host:has(.myst-status-zoom-edit-drawer:not(.hide):not(.hidden)) {{
    min-height: 0 !important;
    height: auto !important;
    max-height: none !important;
    flex: 0 0 auto !important;
    overflow: visible !important;
}}
.gradio-container .myst-status-page .myst-status-panels-host.myst-status-edit-active + .myst-status-catalog-host,
.gradio-container .myst-status-page .myst-status-panels-host.myst-status-edit-active + .block:has(.myst-status-catalog-host),
.gradio-container .myst-status-page .myst-status-panels-host.myst-status-edit-active + .form:has(.myst-status-catalog-host),
.gradio-container .myst-status-page .myst-status-stack:has(.myst-status-edit-active) .myst-status-catalog-host,
.gradio-container .myst-status-page .myst-status-stack:has(.myst-status-zoom-edit-drawer:not(.hide):not(.hidden)) .myst-status-catalog-host,
.gradio-container .myst-status-page .myst-status-stack:has(.myst-status-zoom-edit-drawer:not(.hide):not(.hidden)) .myst-status-catalog-host > .block,
.gradio-container .myst-status-page .myst-status-stack:has(.myst-status-zoom-edit-drawer:not(.hide):not(.hidden)) .myst-status-catalog-host > .form,
.gradio-container .myst-status-page .myst-status-stack:has(.myst-status-zoom-edit-drawer:not(.hide):not(.hidden)) .myst-status-catalog-host > .column {{
    display: none !important;
    min-height: 0 !important;
    height: 0 !important;
    flex: 0 0 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    visibility: hidden !important;
    pointer-events: none !important;
}}
.gradio-container .myst-status-page .myst-status-catalog-host.hide,
.gradio-container .myst-status-page .myst-status-catalog-host.hidden,
.gradio-container .myst-status-page .myst-status-catalog-host > .block.hide,
.gradio-container .myst-status-page .myst-status-catalog-host > .block.hidden,
.gradio-container .myst-status-page .myst-status-catalog-host > .form.hide,
.gradio-container .myst-status-page .myst-status-catalog-host > .form.hidden,
.gradio-container .myst-status-page .myst-status-catalog-host > .column.hide,
.gradio-container .myst-status-page .myst-status-catalog-host > .column.hidden {{
    display: none !important;
    min-height: 0 !important;
    height: 0 !important;
    flex: 0 0 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}}
.gradio-container .myst-status-page .myst-status-catalog-host:not(.hide):not(.hidden) #myst-status-panel-host,
.gradio-container .myst-status-page .myst-status-catalog-host:not(.hide):not(.hidden) #myst-status-panel-host .html-container,
.gradio-container .myst-status-page .myst-status-catalog-host:not(.hide):not(.hidden) #myst-status-grid-host,
.gradio-container .myst-status-page .myst-status-catalog-host:not(.hide):not(.hidden) #myst-status-grid-host .html-container,
.gradio-container .myst-status-page .myst-status-catalog-host:not(.hide):not(.hidden) .myst-status-panel-host,
.gradio-container .myst-status-page .myst-status-catalog-host:not(.hide):not(.hidden) .myst-status-panel-host .html-container,
.gradio-container .myst-status-page .myst-status-grid-view .myst-status-grid-host,
.gradio-container .myst-status-page .myst-status-grid-view .myst-status-grid-host .html-container {{
    width: 100% !important;
    min-height: calc(100dvh - 8.5rem) !important;
    height: auto !important;
    flex: 1 1 auto !important;
    overflow: visible !important;
    position: relative !important;
    z-index: 3 !important;
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    display: flex !important;
    flex-direction: column !important;
}}
.gradio-container .myst-status-page.hide,
.gradio-container .myst-status-page.hidden,
.gradio-container .myst-render-page.hide,
.gradio-container .myst-render-page.hidden,
.gradio-container .myst-gravity-page.hide,
.gradio-container .myst-gravity-page.hidden,
.gradio-container .myst-edit-page.hide,
.gradio-container .myst-edit-page.hidden,
.gradio-container .myst-readme-page.hide,
.gradio-container .myst-readme-page.hidden,
.gradio-container .vqc-animations-page.hide,
.gradio-container .vqc-animations-page.hidden {{
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    pointer-events: none !important;
    border: none !important;
    box-shadow: none !important;
    opacity: 0 !important;
}}
.gradio-container .myst-gravity-page.hide > .block,
.gradio-container .myst-gravity-page.hide > .form,
.gradio-container .myst-gravity-page.hidden > .block,
.gradio-container .myst-gravity-page.hidden > .form,
.gradio-container .myst-render-page.hide > .block,
.gradio-container .myst-render-page.hide > .form,
.gradio-container .myst-status-page.hide > .block,
.gradio-container .myst-status-page.hide > .form {{
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    border: none !important;
    box-shadow: none !important;
}}
.gradio-container .myst-status-page .myst-status-grid-wrap {{
    width: 100% !important;
    height: auto !important;
    min-height: calc(100dvh - 8.5rem) !important;
    flex: 1 1 auto !important;
    background: transparent !important;
    display: flex !important;
    flex-direction: column !important;
}}
.gradio-container .myst-status-page .myst-status-grid {{
    display: grid !important;
    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
    grid-template-rows: repeat(3, minmax(10rem, 1fr)) !important;
    gap: 0.45rem !important;
    width: 100% !important;
    height: auto !important;
    min-height: calc(100dvh - 7.5rem) !important;
    flex: 1 1 auto !important;
    background: transparent !important;
    align-content: stretch !important;
    position: relative !important;
    z-index: 3 !important;
}}
.gradio-container .myst-status-page .myst-status-grid-cell {{
    min-width: 0 !important;
    min-height: 0 !important;
    height: 100% !important;
    background: transparent !important;
    display: flex !important;
    flex-direction: column !important;
}}
.gradio-container .myst-status-page .myst-status-grid-cell-active .myst-status-preset-panel {{
    box-shadow:
        0 0 0 2px rgba(61, 255, 122, {_MYST_STATUS_LAYER_ALPHA}),
        inset 0 0 12px rgba(61, 255, 122, {_MYST_STATUS_LAYER_ALPHA}) !important;
}}
.gradio-container .myst-status-page .myst-status-preset-panel {{
    padding: 0.42rem 0.46rem 0.52rem !important;
    flex: 1 1 0 !important;
    height: 100% !important;
    min-height: 0 !important;
    max-height: none !important;
    overflow-x: hidden !important;
    overflow-y: auto !important;
    background: rgba(0, 0, 0, {_MYST_STATUS_PANEL_ALPHA}) !important;
    border: 2px inset rgba(92, 74, 31, {_MYST_STATUS_PANEL_ALPHA}) !important;
    box-shadow: none !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-status-page .myst-status-preset-panel {{
    font-weight: 700 !important;
}}
.gradio-container .myst-status-page .myst-status-preset-panel .myst-gravity-level-title {{
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.03em !important;
    line-height: 1.2 !important;
}}
.gradio-container .myst-status-page .myst-status-preset-panel .myst-gravity-level-rule {{
    margin: 0.28rem 0 0.35rem 0 !important;
    border-top-color: rgba(245, 230, 200, {_MYST_STATUS_PANEL_ALPHA}) !important;
}}
.gradio-container .myst-status-page .myst-status-level-row {{
    grid-template-columns: 1.45rem minmax(0, 0.5fr) minmax(4.25rem, 0.68fr) minmax(0, 1.15fr) minmax(3.6rem, auto) !important;
    gap: 0.14rem 0.18rem !important;
    margin: 0 !important;
    font-size: 0.82rem !important;
    line-height: 1.2 !important;
    align-items: center !important;
}}
.gradio-container .myst-status-page .myst-status-level-spacer {{
    display: block !important;
    width: 100% !important;
    min-height: 0.82rem !important;
    height: 0.82rem !important;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
    pointer-events: none !important;
    flex: 0 0 0.82rem !important;
}}
.gradio-container .myst-status-page .myst-status-preset-panel .myst-gravity-level-id,
.gradio-container .myst-status-page .myst-status-preset-panel .myst-gravity-level-desc,
.gradio-container .myst-status-page .myst-status-preset-panel .myst-gravity-level-range,
.gradio-container .myst-status-page .myst-status-preset-panel .myst-gravity-level-val,
.gradio-container .myst-status-page .myst-status-preset-panel .myst-gravity-level-foot {{
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    line-height: 1.2 !important;
}}
.gradio-container .myst-status-page .myst-status-level-row .myst-gravity-level-range {{
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-weight: 600 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    min-width: 0 !important;
    justify-self: start !important;
    text-align: left !important;
}}
.gradio-container .myst-status-page .myst-status-catalog-header .myst-gravity-level-id,
.gradio-container .myst-status-page .myst-status-catalog-header .myst-gravity-level-desc,
.gradio-container .myst-status-page .myst-status-catalog-header .myst-gravity-level-range {{
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}}
.gradio-container .myst-status-page .myst-status-catalog-header .myst-gravity-level-val {{
    color: #f5e6c8 !important;
    -webkit-text-fill-color: #f5e6c8 !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
    font-size: 0.72rem !important;
}}
.gradio-container .myst-status-page .myst-status-catalog-header .myst-gravity-level-bar {{
    visibility: hidden !important;
}}
.gradio-container .myst-status-page .myst-status-notes-wrap {{
    width: 100% !important;
    margin: 0.18rem 0 0.1rem 0 !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-status-page .myst-status-notes-label {{
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    line-height: 1.2 !important;
    margin: 0 0 0.28rem 0 !important;
}}
.gradio-container .myst-status-page .myst-status-notes-box {{
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    line-height: 1.35 !important;
    border: 2px solid #6b4f1d !important;
    border-radius: 8px !important;
    padding: 0.48rem 0.55rem !important;
    background: rgba(0, 0, 0, 0.38) !important;
    box-shadow: inset 0 1px 0 rgba(255, 220, 150, 0.08) !important;
    box-sizing: border-box !important;
    width: 100% !important;
    min-height: 2.6rem !important;
}}
.gradio-container .myst-status-page .myst-status-level-row .myst-gravity-level-desc {{
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-weight: 700 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    min-width: 0 !important;
}}
.gradio-container .myst-status-page .myst-status-level-row .myst-gravity-level-id {{
    font-weight: 700 !important;
}}
.gradio-container .myst-status-page .myst-status-level-row .myst-gravity-level-val {{
    font-weight: 700 !important;
}}
.gradio-container .myst-status-page .myst-status-level-row .myst-gravity-level-bar {{
    width: 100% !important;
    min-height: 0.72rem !important;
    justify-self: stretch !important;
    display: flex !important;
    gap: 2px !important;
    align-items: stretch !important;
    box-sizing: border-box !important;
    padding-right: 4ch !important;
}}
.gradio-container .myst-status-page .myst-status-level-row .myst-gravity-level-val {{
    min-width: 3.6rem !important;
    justify-self: end !important;
    text-align: right !important;
}}
.gradio-container .myst-status-page .myst-level-block {{
    flex: 1 1 0 !important;
    width: auto !important;
    min-width: 2px !important;
    max-width: none !important;
    height: 0.72rem !important;
}}
.gradio-container .myst-status-page .myst-level-block.myst-level-fill.myst-level-pos {{
    background: #33ff66 !important;
    box-shadow: 0 0 4px rgba(51, 255, 102, 0.55) !important;
    opacity: 1 !important;
}}
.gradio-container .myst-status-page .myst-level-block.myst-level-fill.myst-level-neg {{
    background: #ff3344 !important;
    box-shadow: 0 0 4px rgba(255, 51, 68, 0.55) !important;
    opacity: 1 !important;
}}
.gradio-container .myst-status-page .myst-level-block.myst-level-empty {{
    background: rgba(255, 255, 255, 0.12) !important;
    opacity: 1 !important;
}}
/* Status preset nav — keep the 11-button row inline; never flex-stretch or wrap */
.gradio-container .myst-status-page .myst-status-stack #myst-status-zoom-nav {{
    position: relative !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
}}
.gradio-container .myst-status-page .vqc-status-preset-nav-row.vqc-source-tabs-row {{
    display: grid !important;
    flex-wrap: nowrap !important;
}}
.gradio-container .myst-status-page .vqc-main-nav-row.vqc-source-tabs-row {{
    margin: 0.12rem 0 0.05rem 0 !important;
}}
.gradio-container .myst-edit-page .myst-edit-panel {{
    width: 100% !important;
    margin-top: 0.35rem !important;
}}
.gradio-container .myst-edit-page .myst-gravity-controls-accordion {{
    flex: 0 0 auto !important;
    background: rgba(0, 0, 0, 0.18) !important;
    border: 1px solid #4a3818 !important;
    border-radius: 10px !important;
    box-shadow: inset 0 1px 0 rgba(255, 220, 150, 0.08) !important;
    overflow: hidden !important;
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
}}
.gradio-container .myst-edit-page .myst-gravity-manual-edit-accordion .accordion {{
    max-height: min(70vh, 42rem) !important;
    overflow-y: auto !important;
}}
.gradio-container .myst-edit-page .myst-gravity-controls-accordion > .label-wrap {{
    background: linear-gradient(180deg, #1f140a 0%, #0f0a06 100%) !important;
    border-bottom: 1px solid rgba(74, 56, 24, 0.65) !important;
}}
.gradio-container .myst-edit-page .myst-gravity-controls-accordion > .label-wrap span {{
    color: #f5e6c8 !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}}
.gradio-container .myst-render-page .myst-render-grid-wrap {{
    width: 100% !important;
    height: auto !important;
    min-height: 0 !important;
    max-height: calc(100dvh - 9rem - var(--myst-render-grid-bottom-frame, 0.38rem)) !important;
    flex: 1 1 auto !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
    align-content: stretch !important;
    justify-content: flex-start !important;
    padding: 0 0 var(--myst-render-grid-bottom-frame, 0.38rem) 0 !important;
    margin: 0 !important;
    overflow-x: hidden !important;
    overflow-y: auto !important;
    background: transparent !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-render-page .myst-render-grid {{
    display: grid !important;
    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
    grid-template-rows: repeat(3, minmax(10rem, auto)) !important;
    gap: var(--myst-render-grid-gap, 0.18rem) !important;
    width: 100% !important;
    height: auto !important;
    min-height: 0 !important;
    flex: 0 0 auto !important;
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    align-content: start !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-render-page .myst-render-grid-cell {{
    min-width: 0 !important;
    min-height: 0 !important;
    width: 100% !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
}}
.gradio-container .myst-render-page .myst-render-cell-clickable {{
    cursor: pointer !important;
}}
.gradio-container .myst-render-page .myst-render-cell-clickable:hover .myst-render-preset-panel {{
    box-shadow:
        0 0 0 2px rgba(212, 175, 55, 0.45),
        inset 0 0 10px rgba(212, 175, 55, 0.12) !important;
}}
.gradio-container .myst-render-page .myst-render-catalog-host:not(.hide):not(.hidden) {{
    flex: 1 1 auto !important;
    min-height: 0 !important;
    max-height: calc(100dvh - 9rem) !important;
    height: auto !important;
    display: flex !important;
    flex-direction: column !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: hidden !important;
    align-items: stretch !important;
}}
.gradio-container .myst-render-page .myst-render-catalog-host:not(.hide):not(.hidden) #myst-render-grid-host,
.gradio-container .myst-render-page .myst-render-catalog-host:not(.hide):not(.hidden) #myst-render-grid-host .html-container,
.gradio-container .myst-render-page .myst-render-panel-host,
.gradio-container .myst-render-page .myst-render-panel-host .html-container,
.gradio-container .myst-render-page #myst-render-grid-host,
.gradio-container .myst-render-page #myst-render-grid-host .html-container,
.gradio-container .myst-render-page #myst-render-grid-host.block,
.gradio-container .myst-render-page #myst-render-grid-host .wrap,
.gradio-container .myst-render-page #myst-render-grid-host .gradio-html,
.gradio-container .myst-render-page #myst-render-grid-host .prose {{
    width: 100% !important;
    max-width: 100% !important;
    min-height: 0 !important;
    height: auto !important;
    max-height: calc(100dvh - 9rem - var(--myst-render-grid-bottom-frame, 0.38rem)) !important;
    flex: 1 1 auto !important;
    overflow-x: hidden !important;
    overflow-y: auto !important;
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
    align-content: start !important;
    justify-content: flex-start !important;
    box-sizing: border-box !important;
}}
.gradio-container:has(.myst-render-page:not(.hide):not(.hidden)) {{
    padding-left: 0 !important;
    padding-right: 0 !important;
}}
.gradio-container .myst-render-page #myst-render-detail-wrapper,
.gradio-container .myst-render-page .myst-render-detail-wrapper,
.gradio-container .myst-render-page .myst-render-detail-view {{
    flex: 1 1 auto !important;
    width: 100% !important;
    min-height: 0 !important;
    overflow: visible !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 0.28rem !important;
    padding: 0 !important;
    margin: 0 !important;
    align-items: stretch !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-render-page .myst-render-detail-toolbar {{
    flex: 0 0 auto !important;
    margin: 0 !important;
    padding: 0 0 0.12rem 0 !important;
    gap: 0.35rem !important;
}}
.gradio-container .myst-render-page .myst-render-split-row {{
    flex: 1 1 auto !important;
    gap: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    min-height: calc(100dvh - 11.5rem) !important;
    background: #0a0a0f !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid #2a2a3a !important;
    align-items: stretch !important;
}}
.gradio-container .myst-render-page .myst-render-left-panel,
.gradio-container .myst-render-page .myst-render-right-panel {{
    background: #0a0a0f !important;
    padding: 1rem 1.25rem !important;
    border: none !important;
    box-shadow: none !important;
    margin: 0 !important;
    min-height: 0 !important;
    height: 100% !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-render-page .myst-render-left-panel {{
    flex: 1 1 33% !important;
    max-width: 34% !important;
    overflow-x: hidden !important;
    overflow-y: auto !important;
    border-radius: 12px 0 0 12px !important;
}}
.gradio-container .myst-render-page .myst-render-right-panel {{
    flex: 2 1 66% !important;
    min-width: 0 !important;
    padding: 0 !important;
    display: flex !important;
    flex-direction: column !important;
    border-radius: 0 12px 12px 0 !important;
}}
.gradio-container .myst-render-page .myst-render-panel-header {{
    color: #aaaaaa !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    margin-bottom: 0.75rem !important;
    text-transform: uppercase !important;
}}
.gradio-container .myst-render-page .myst-render-verbose-desc,
.gradio-container .myst-render-page .myst-render-verbose-desc .prose {{
    color: #e0e0e0 !important;
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
    background: transparent !important;
    border: none !important;
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-render-page .myst-render-verbose-desc h3,
.gradio-container .myst-render-page .myst-render-verbose-desc h4 {{
    color: #ffffff !important;
    margin-top: 1rem !important;
}}
.gradio-container .myst-render-page .myst-render-verbose-desc pre,
.gradio-container .myst-render-page .myst-render-verbose-desc code {{
    background: #1a1a22 !important;
    color: #d4af37 !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    font-size: 0.82rem !important;
}}
.gradio-container .myst-render-page .myst-render-detail-plot,
.gradio-container .myst-render-page .myst-render-detail-plot-host,
.gradio-container .myst-render-page #myst-render-detail-plot,
.gradio-container .myst-render-page #myst-render-detail-plot.block {{
    flex: 1 1 auto !important;
    width: 100% !important;
    min-width: 0 !important;
    min-height: 520px !important;
    height: 100% !important;
    max-height: none !important;
    margin: 0 !important;
    padding: 0 !important;
    background: #0a0a0f !important;
    border: none !important;
    border-radius: 0 12px 12px 0 !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
}}
.gradio-container .myst-render-page .myst-render-detail-plot .plot-container,
.gradio-container .myst-render-page .myst-render-detail-plot .js-plotly-plot,
.gradio-container .myst-render-page .myst-render-detail-plot .plotly-graph-div,
.gradio-container .myst-render-page .myst-render-detail-plot-host .plot-container,
.gradio-container .myst-render-page .myst-render-detail-plot-host .js-plotly-plot,
.gradio-container .myst-render-page .myst-render-detail-plot-host .plotly-graph-div,
.gradio-container .myst-render-page #myst-render-detail-plot .plot-container,
.gradio-container .myst-render-page #myst-render-detail-plot .plotly-graph-div {{
    width: 100% !important;
    height: 100% !important;
    min-height: 550px !important;
    max-height: none !important;
}}
.gradio-container .myst-render-page .myst-render-detail-actions {{
    flex: 0 0 auto !important;
    gap: 0.28rem !important;
    margin: 0 !important;
    padding: 0.08rem 0 0.2rem 0 !important;
    flex-wrap: wrap !important;
}}
.gradio-container .myst-render-page .myst-render-detail-wrap {{
    width: 100% !important;
    height: 100% !important;
    min-height: 0 !important;
    flex: 1 1 auto !important;
    display: flex !important;
    flex-direction: column !important;
}}
.gradio-container .myst-render-page .myst-render-detail-panel {{
    flex: 1 1 auto !important;
    min-height: 0 !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 0.15rem !important;
    padding: 0.22rem 0.28rem 0.24rem !important;
    background: rgba(0, 0, 0, {_MYST_STATUS_PANEL_ALPHA}) !important;
    border: 2px inset rgba(92, 74, 31, {_MYST_STATUS_PANEL_ALPHA}) !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-render-page .myst-render-detail-title {{
    flex: 0 0 auto !important;
    font-size: 0.9rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    color: #f5e6c8 !important;
    text-transform: uppercase !important;
    margin: 0 !important;
    padding: 0.08rem 0.1rem !important;
    line-height: 1.2 !important;
}}
.gradio-container .myst-render-page .myst-render-detail-panel .myst-gravity-level-rule {{
    flex: 0 0 auto !important;
    margin: 0.1rem 0 0.12rem 0 !important;
}}
.gradio-container .myst-render-page .myst-render-detail-plot-host {{
    flex: 1 1 auto !important;
    min-height: 0 !important;
    width: 100% !important;
    height: 100% !important;
    display: flex !important;
    align-items: stretch !important;
    justify-content: stretch !important;
    overflow: hidden !important;
    background: #000000 !important;
    padding: 0 !important;
    margin: 0 !important;
}}
.gradio-container .myst-render-page .myst-render-detail-plotly-wrap,
.gradio-container .myst-render-page .myst-render-detail-plot-host .plotly-graph-div,
.gradio-container .myst-render-page .myst-render-detail-plot-host .js-plotly-plot,
.gradio-container .myst-render-page .myst-render-detail-plot-host #myst-render-detail-plotly {{
    flex: 1 1 auto !important;
    width: 100% !important;
    height: 100% !important;
    min-height: calc(100dvh - 8.25rem) !important;
    max-height: none !important;
}}
.gradio-container .myst-render-page .myst-render-detail-plot-host .modebar {{
    right: 0.35rem !important;
    top: 0.2rem !important;
}}
.gradio-container .myst-render-page .myst-render-detail-plot-host .myst-unit-cell-viewport-inner {{
    width: 100% !important;
    height: 100% !important;
    min-height: 0 !important;
    max-height: none !important;
}}
.gradio-container .myst-render-page .myst-render-detail-plot-host img {{
    width: 100% !important;
    height: 100% !important;
    max-width: 100% !important;
    max-height: 100% !important;
    object-fit: contain !important;
}}
.gradio-container .myst-render-page .myst-render-preset-panel {{
    padding: 0.16rem !important;
    flex: 1 1 0 !important;
    height: 100% !important;
    min-height: 0 !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 0 !important;
    overflow: hidden !important;
    background: rgba(0, 0, 0, {_MYST_STATUS_PANEL_ALPHA}) !important;
    border: 2px inset rgba(92, 74, 31, {_MYST_STATUS_PANEL_ALPHA}) !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-render-page .myst-render-preset-header {{
    flex: 0 0 auto !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-render-page .myst-render-preset-panel .myst-gravity-level-title {{
    font-size: 0.66rem !important;
    letter-spacing: 0.05em !important;
    line-height: 1.1 !important;
    margin: 0 !important;
    padding: 0 0.04rem !important;
    flex: 0 0 auto !important;
}}
.gradio-container .myst-render-page .myst-render-preset-panel .myst-gravity-level-rule {{
    margin: 0.08rem 0 0.1rem 0 !important;
    flex: 0 0 auto !important;
}}
.gradio-container .myst-render-page .myst-render-grid-cell-active .myst-render-preset-panel {{
    box-shadow:
        0 0 0 2px rgba(212, 175, 55, 0.72),
        inset 0 0 12px rgba(212, 175, 55, 0.18) !important;
}}
.gradio-container .myst-render-page .myst-render-plot-host {{
    flex: 1 1 auto !important;
    min-height: 9rem !important;
    width: 100% !important;
    height: 100% !important;
    display: flex !important;
    align-items: stretch !important;
    justify-content: stretch !important;
    overflow: hidden !important;
    background: #000000 !important;
    padding: 0 !important;
    margin: 0 !important;
}}
.gradio-container .myst-render-page .myst-render-plot-host .myst-unit-cell-viewport-inner,
.gradio-container .myst-render-page .myst-render-plot-host .myst-render-grid-viewport {{
    width: 100% !important;
    height: 100% !important;
    min-height: 9rem !important;
    max-height: none !important;
    max-width: none !important;
    display: block !important;
    align-items: unset !important;
    justify-content: unset !important;
    overflow: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-render-page .myst-render-plot-host img {{
    width: 100% !important;
    height: 100% !important;
    min-height: 8rem !important;
    max-width: 100% !important;
    max-height: 100% !important;
    object-fit: contain !important;
    display: block !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-render-page .myst-render-plot-placeholder {{
    flex: 1 1 auto !important;
    min-height: 9rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    color: rgba(245, 230, 200, 0.55) !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.04em !important;
}}
.gradio-container .myst-render-page .myst-render-plot-placeholder.myst-render-plot-loading {{
    color: rgba(212, 175, 55, 0.82) !important;
}}
.gradio-container .myst-render-page .myst-render-accent {{
    color: #d4af37 !important;
    font-weight: 700 !important;
}}
.gradio-container .myst-render-page .myst-render-catalog-host,
.gradio-container .myst-render-page .myst-render-grid-host {{
    flex: 1 1 auto !important;
    width: 100% !important;
    min-height: 0 !important;
}}
.gradio-container .myst-render-page .myst-render-stack {{
    width: 100% !important;
    flex: 1 1 auto !important;
    min-height: 0 !important;
    max-height: calc(100dvh - 5.5rem) !important;
    height: auto !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
    justify-content: flex-start !important;
    gap: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: hidden !important;
    background: transparent !important;
}}
.gradio-container .myst-render-page .myst-render-stack > .block:has(.myst-render-catalog-host):not(.hide):not(.hidden),
.gradio-container .myst-render-page .myst-render-stack > .form:has(.myst-render-catalog-host):not(.hide):not(.hidden),
.gradio-container .myst-render-page .myst-render-stack > .column.myst-render-catalog-host:not(.hide):not(.hidden) {{
    flex: 1 1 auto !important;
    min-height: 0 !important;
    max-height: calc(100dvh - 9rem) !important;
    height: auto !important;
    width: 100% !important;
    overflow: hidden !important;
    align-items: stretch !important;
}}
.gradio-container .myst-render-page .myst-render-preset-nav-wrap,
.gradio-container .myst-render-page .myst-render-preset-nav-wrap.row,
.gradio-container .myst-render-page #myst-render-sub-nav {{
    flex: 0 0 auto !important;
    margin: 0 !important;
    padding: 0 !important;
}}

.gradio-container .myst-status-preset-nav-wrap button.myst-status-nav-back-btn {{
    min-width: 82px !important;
    width: 82px !important;
}}
.gradio-container .myst-render-page > .block,
.gradio-container .myst-render-page > .form,
.gradio-container .myst-render-page > .column,
.gradio-container .myst-render-page .myst-render-catalog-host .block,
.gradio-container .myst-render-page .myst-render-catalog-host .form,
.gradio-container .myst-render-page .myst-render-catalog-host .column {{
    width: 100% !important;
    max-width: 100% !important;
    background: transparent !important;
    box-shadow: none !important;
    border: none !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    align-items: stretch !important;
}}
@media (max-width: 1100px) {{
    .gradio-container .myst-status-page .myst-status-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        grid-template-rows: auto !important;
    }}
}}
@media (max-width: 720px) {{
    .gradio-container .myst-status-page .myst-status-grid {{
        grid-template-columns: minmax(0, 1fr) !important;
    }}
}}
/* === UNIT CELL VIEWPORT header — hidden (plot only) === */
.gradio-container .myst-gravity-visuals-col .myst-cube-viewport-header-slot,
.gradio-container .myst-gravity-visuals-col .myst-cube-viewport-header-slot.block {{
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    overflow: hidden !important;
    visibility: hidden !important;
    pointer-events: none !important;
}}
/* === UNIT CELL VIEWPORT — flex height fix (Gradio unequal-height row) === */
.gradio-container .myst-gravity-split > .column.myst-gravity-visuals-col {{
    min-width: 0 !important;
    width: 100% !important;
    overflow: visible !important;
}}
.gradio-container .myst-gravity-visuals-col {{
    min-width: 0 !important;
    width: 100% !important;
    overflow: visible !important;
}}
.gradio-container .myst-unit-cell-visor,
.gradio-container .row.myst-unit-cell-visor {{
    position: relative !important;
    height: var(--myst-unit-cell-visor-height, var(--myst-unit-cell-plot-height, 31rem)) !important;
    min-height: var(--myst-unit-cell-visor-height, var(--myst-unit-cell-plot-height, 31rem)) !important;
    max-height: none !important;
    flex: 1 1 var(--myst-unit-cell-visor-height, 31rem) !important;
    flex-shrink: 1 !important;
    width: 100% !important;
    min-width: 0 !important;
    align-items: stretch !important;
    align-self: stretch !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
    background: #000000 !important;
    margin: 0 !important;
    padding: 0 !important;
}}
.gradio-container .myst-unit-cell-visor-slot {{
    position: relative !important;
    flex: 1 1 0 !important;
    height: 100% !important;
    min-height: 0 !important;
    width: 100% !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
}}
.gradio-container .myst-unit-cell-visor .myst-unit-cell-visor-image,
.gradio-container .myst-unit-cell-visor .myst-unit-cell-visor-image.block,
.gradio-container .myst-unit-cell-visor .myst-unit-cell-visor-video,
.gradio-container .myst-unit-cell-visor .myst-unit-cell-visor-video.block {{
    position: absolute !important;
    inset: 0 !important;
    width: 100% !important;
    height: 100% !important;
    min-height: 100% !important;
    max-height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    box-sizing: border-box !important;
    background: #000000 !important;
}}
.gradio-container .myst-unit-cell-visor .myst-unit-cell-visor-image,
.gradio-container .myst-unit-cell-visor .myst-unit-cell-visor-image.block {{
    z-index: 1 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    opacity: 1 !important;
    visibility: visible !important;
    pointer-events: auto !important;
    transition: opacity 0.15s ease !important;
}}
.gradio-container .myst-unit-cell-visor .myst-unit-cell-visor-video,
.gradio-container .myst-unit-cell-visor .myst-unit-cell-visor-video.block {{
    z-index: 2 !important;
    opacity: 0 !important;
    visibility: hidden !important;
    pointer-events: none !important;
    transition: opacity 0.15s ease !important;
}}
.gradio-container .myst-unit-cell-visor:has(video[src]) .myst-unit-cell-visor-image,
.gradio-container .myst-unit-cell-visor:has(video[src]) .myst-unit-cell-visor-image.block {{
    opacity: 0 !important;
    visibility: hidden !important;
    pointer-events: none !important;
}}
.gradio-container .myst-unit-cell-visor:has(video[src]) .myst-unit-cell-visor-video,
.gradio-container .myst-unit-cell-visor:has(video[src]) .myst-unit-cell-visor-video.block {{
    opacity: 1 !important;
    visibility: visible !important;
    pointer-events: auto !important;
}}
.gradio-container .myst-unit-cell-visor .myst-unit-cell-visor-image > .form,
.gradio-container .myst-unit-cell-visor .myst-unit-cell-visor-image .gradio-html,
.gradio-container .myst-unit-cell-visor .myst-unit-cell-visor-image .html-container,
.gradio-container .myst-unit-cell-visor .myst-unit-cell-visor-image .prose,
.gradio-container .myst-unit-cell-visor .myst-unit-cell-viewport-image {{
    height: 100% !important;
    min-height: 100% !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0 !important;
    margin: 0 !important;
    box-sizing: border-box !important;
}}
.gradio-container .myst-unit-cell-visor .wrap.center.full,
.gradio-container .myst-unit-cell-visor .wrap.center.hidden,
.gradio-container .myst-unit-cell-visor .wrap.default.hidden {{
    display: none !important;
    opacity: 0 !important;
    pointer-events: none !important;
    visibility: hidden !important;
}}
.gradio-container #unit-cell-main-view,
.gradio-container #unit-cell-main-view.myst-unit-cell-viewport-inner {{
    height: 100% !important;
    min-height: 100% !important;
    max-height: 100% !important;
    width: 100% !important;
    max-width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: #000000 !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
    margin: 0 auto !important;
}}
.gradio-container #unit-cell-main-view img {{
    max-width: 100% !important;
    max-height: 100% !important;
    width: auto !important;
    height: auto !important;
    object-fit: contain !important;
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}}
.gradio-container .myst-unit-cell-viewport-image,
.gradio-container #unit-cell-animation,
.gradio-container #unit-cell-animation.block {{
    background-color: #000000 !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
}}
.gradio-container .myst-unit-cell-visor #unit-cell-animation,
.gradio-container .myst-unit-cell-visor #unit-cell-animation .wrap,
.gradio-container .myst-unit-cell-visor #unit-cell-animation .video-container,
.gradio-container .myst-unit-cell-visor #unit-cell-animation video {{
    width: 100% !important;
    height: 100% !important;
    min-height: 100% !important;
    max-height: 100% !important;
    object-fit: contain !important;
    background: #000000 !important;
}}
.gradio-container .myst-unit-cell-visor .myst-unit-cell-visor-video .label-wrap {{
    display: none !important;
}}
.gradio-container .gradio-image:not(#unit-cell-main-view) img {{
    width: 100% !important;
    height: auto !important;
    max-height: 100% !important;
    object-fit: contain !important;
}}
@media (max-width: 768px) {{
    .gradio-container .myst-gravity-split {{
        grid-template-columns: 1fr !important;
        grid-template-rows: auto auto !important;
        height: auto !important;
        max-height: none !important;
        min-height: auto !important;
    }}
}}

"""

_GRAVITY_KEYPAD_NUMERIC_KEYS = tuple(str(i) for i in range(10))
_GRAVITY_KEYPAD_NAV_KEYS = ("up", "right", "left", "down", "enter", "stop")
_GRAVITY_KEYPAD_LAYOUT: tuple[tuple[str, str, str, str], ...] = (
    ("1", "2", "3", "up"),
    ("4", "5", "6", "right"),
    ("7", "8", "9", "left"),
    ("0", "enter", "stop", "down"),
)
_GRAVITY_KEYPAD_ALL_KEYS: tuple[str, ...] = (
    *_GRAVITY_KEYPAD_LAYOUT[0],
    *_GRAVITY_KEYPAD_LAYOUT[1],
    *_GRAVITY_KEYPAD_LAYOUT[2],
    *_GRAVITY_KEYPAD_LAYOUT[3],
)
_GRAVITY_QUICK_PRESET_KEYS = _GRAVITY_KEYPAD_NUMERIC_KEYS
_GRAVITY_PRESET_BTN_KEYS = _GRAVITY_KEYPAD_NUMERIC_KEYS
_GRAVITY_TUI_SCROLL_STEP_PX = 22
_GRAVITY_TUI_MENU_FOCUS_MAX = 9
_UNIT_CELL_IMAGE_DPI = 100
_RENDER_GRID_IMAGE_DPI = 100
_RENDER_DETAIL_IMAGE_DPI = 120
# Index of unit_cell_image within gravity_preset_outputs
# (16 keypad + 1 legacy back skip + 9 child nav + 2 edit btns + 20 sliders + …).
_GRAVITY_PRESET_IMAGE_OUT_INDEX = 51
_GRAVITY_CHILD_NAV_LETTERS: tuple[str, ...] = tuple(chr(ord("A") + i) for i in range(9))
_GRAVITY_HOME_DIALS = {
    "phi": 1.0,
    "e": 1.0,
    "pi": 1.0,
    "kappa": KAPPA_DOC,
    "dz": 0.1,
    "alpha": 1.0,
    "beta": 1.0,
    "pressure": 0.35,
    "elev": 26.0,
    "azim": 45.0,
}
_GRAVITY_PRESET_SLOT_LABELS = {
    0: "menu · parameter catalog",
    1: "rigid cube",
    2: "full π bowl + φ/e concave pinch",
    3: "full π bowl",
    4: "φ/e concave pinch",
    5: "κ_doc home blend",
    6: "moderate bowl",
    7: "φ leg emphasis",
    8: "e leg emphasis",
    9: "π leg emphasis",
}
_GRAVITY_PRESET_TUI_LABELS: dict[int, str] = {
    0: "Parameter Catalog",
    1: "Rigid Cube",
    2: "Full Bowl + φ/e Concave Pinch",
    3: "Full π Bowl",
    4: "φ/e Concave Pinch",
    5: "κ_doc Home Blend",
    6: "Moderate Bowl",
    7: "φ Leg Emphasis",
    8: "e Leg Emphasis",
    9: "π Leg Emphasis",
}
_GRAVITY_PRESET_STATUS_NOTES: dict[int, str] = {
    0: (
        "Reference catalog for all ten φ-e-π deformation controls. "
        "Use presets 02–09 for programmed shapes; ranges show allowable slider spans."
    ),
    1: (
        "Rigid-cube baseline: deformation pressure 0%, δ_z push disabled. "
        "φ², e², and π² legs remain at nominal unity with κ_doc holonomy gap."
    ),
    2: (
        "Maximum programmed deformation — full π bowl plus φ/e concave pinch. "
        "Pressure 100%; φ²/e² skew 0.962/1.038; elevated α and β side coupling."
    ),
    3: (
        "Full π-bowl profile at 100% deformation pressure with moderate δ_z primary push. "
        "Leg scales nominal; suited to holonomy-gap studies at κ_doc."
    ),
    4: (
        "Partial φ/e concave pinch — 68% deformation pressure with φ²/e² bias 0.975/1.025. "
        "Stronger α/β geometry coupling without full bowl closure."
    ),
    5: (
        "κ_doc home blend — 35% deformation pressure, δ_z 0.10, nominal leg scales. "
        "Default Mystery explorer envelope for residual B(κ)−R comparisons."
    ),
    6: (
        "Moderate bowl — 50% deformation pressure, δ_z 0.12, κ at κ_doc. "
        "Intermediate between rigid cube and full-bowl extremes."
    ),
    7: (
        "φ-leg emphasis — φ² scale 0.950 with 45% deformation pressure. "
        "Highlights golden-ratio leg response in the concave pinch geometry."
    ),
    8: (
        "e-leg emphasis — e² scale 1.050 with 45% deformation pressure. "
        "Highlights natural-base leg response against nominal φ² and π² legs."
    ),
    9: (
        "π-leg emphasis — π² scale 0.980 with 55% deformation pressure. "
        "Highlights circle-completeness leg response in the concave bowl geometry."
    ),
}
_GRAVITY_PARAM_CATALOG: tuple[dict[str, object], ...] = (
    {
        "id": "01",
        "key": "pressure",
        "label": "deformation pressure",
        "kind": "percent",
        "min": -1.0,
        "max": 1.0,
        "default": 0.35,
        "desc": "+1 = max convex · 0 = rigid cube · −1 = max concave",
    },
    {
        "id": "02",
        "key": "phi",
        "label": "φ² scale",
        "kind": "float",
        "min": 0.90,
        "max": 1.10,
        "default": 1.0,
        "desc": "Golden-ratio leg scale; unity = nominal φ²",
    },
    {
        "id": "03",
        "key": "e",
        "label": "e² scale",
        "kind": "float",
        "min": 0.90,
        "max": 1.10,
        "default": 1.0,
        "desc": "Natural-base leg scale; unity = nominal e²",
    },
    {
        "id": "04",
        "key": "pi",
        "label": "π² scale",
        "kind": "float",
        "min": 0.90,
        "max": 1.10,
        "default": 1.0,
        "desc": "Circle-completeness leg scale; unity = nominal π²",
    },
    {
        "id": "05",
        "key": "kappa",
        "label": "κ holonomy-gap",
        "kind": "float",
        "min": 0.70,
        "max": 0.95,
        "default": KAPPA_DOC,
        "desc": f"κ_doc = {KAPPA_DOC} · κ* nulls B(κ)−R",
    },
    {
        "id": "06",
        "key": "dz",
        "label": "δ_z primary push",
        "kind": "float",
        "min": 0.0,
        "max": 0.5,
        "default": 0.1,
        "desc": "Top-face downward push amplitude",
    },
    {
        "id": "07",
        "key": "alpha",
        "label": "α geometry factor",
        "kind": "float",
        "min": 0.0,
        "max": 2.0,
        "default": 1.0,
        "desc": "Side contraction geometry coupling",
    },
    {
        "id": "08",
        "key": "beta",
        "label": "β residual coupling",
        "kind": "float",
        "min": 0.0,
        "max": 2.0,
        "default": 1.0,
        "desc": "Residual-bound feedback into δ_side",
    },
    {
        "id": "09",
        "key": "elev",
        "label": "view elevation",
        "kind": "degrees",
        "min": 5.0,
        "max": 75.0,
        "default": 22.0,
        "desc": "Camera elevation angle (°)",
    },
    {
        "id": "10",
        "key": "azim",
        "label": "view azimuth",
        "kind": "degrees",
        "min": 0.0,
        "max": 360.0,
        "default": 45.0,
        "desc": "Camera azimuth angle (°)",
    },
)
_STATUS_GRID_PRESET_COUNT = 9

_RENDER_NEUTRAL_DIALS: dict[str, float] = {
    "phi": 1.0,
    "e": 1.0,
    "pi": 1.0,
    "kappa": KAPPA_DOC,
    "dz": 0.1,
    "alpha": 1.0,
    "beta": 1.0,
    "elev": 26.0,
    "azim": 45.0,
}
# Render / Status presets 01–09: signed deformation sweep (convex → rigid → concave).
_RENDER_PRESET_DEFORMATIONS: tuple[tuple[float, str, str, str], ...] = (
    (
        1.00,
        "Max Convex",
        "Very High Internal Pressure",
        "Maximum outward bow on all faces — the convex limit of the deformation envelope.",
    ),
    (
        0.75,
        "Strong Convex",
        "High Internal Pressure",
        "Strong outward bulge with clearly convex φ/e/π sides.",
    ),
    (
        0.50,
        "Moderate Convex",
        "Elevated Internal Pressure",
        "Balanced convex curvature midway between max convex and the rigid neutral cube.",
    ),
    (
        0.25,
        "Mild Convex",
        "Slight Internal Pressure",
        "Gentle outward bow — subtle convex rounding before the neutral rigid state.",
    ),
    (
        0.00,
        "Rigid Cube",
        "Neutral",
        "Perfect rigid cube at 0% deformation — no inward or outward face bow.",
    ),
    (
        -0.25,
        "Mild Concave",
        "Slight Low Internal Pressure",
        "Gentle inward pinch — π-face begins to bowl while φ/e sides curve inward.",
    ),
    (
        -0.50,
        "Moderate Concave",
        "Low Internal Pressure",
        "Clear concave geometry — π bowl and φ/e side pinch at half the concave span.",
    ),
    (
        -0.75,
        "Strong Concave",
        "Very Low Internal Pressure",
        "Strong inward curvature approaching the concave extreme.",
    ),
    (
        -1.00,
        "Max Concave",
        "Very Low Internal Pressure",
        "Maximum concave sides — full inward bowl and side pinch at the deformation floor.",
    ),
)
_RENDER_PRESET_PROFILES: dict[int, dict[str, float]] = {
    slot: {**_RENDER_NEUTRAL_DIALS, "pressure": deform[0]}
    for slot, deform in enumerate(_RENDER_PRESET_DEFORMATIONS)
}
_RENDER_PRESET_LABELS: dict[int, str] = {
    slot: deform[1].lower() for slot, deform in enumerate(_RENDER_PRESET_DEFORMATIONS)
}


def _render_preset_dials_for_slot(slot: int) -> dict[str, float]:
    """Dial bundle for Render tab presets 01–09 (slots 0–8)."""
    slot = int(slot)
    if slot in _RENDER_PRESET_PROFILES:
        return dict(_RENDER_PRESET_PROFILES[slot])
    return dict(_RENDER_NEUTRAL_DIALS)


def _render_preset_shape_meta(slot: int) -> dict[str, str]:
    """Shape / pressure copy for Render detail left panel."""
    slot = int(slot)
    if not (0 <= slot < len(_RENDER_PRESET_DEFORMATIONS)):
        return {
            "title": f"Preset {_gravity_preset_id(slot)}",
            "shape_type": "Unknown",
            "pressure_label": "N/A",
            "deform_display": "N/A",
            "summary": "No description available.",
        }
    deform, title, pressure_label, summary = _RENDER_PRESET_DEFORMATIONS[slot]
    if deform > 0.0:
        shape_type = "Convex"
    elif deform < 0.0:
        shape_type = "Concave"
    else:
        shape_type = "Rigid (neutral)"
    deform_display = f"{deform * 100:.0f}%"
    return {
        "title": title,
        "shape_type": shape_type,
        "pressure_label": pressure_label,
        "deform_display": deform_display,
        "summary": summary,
    }


def _gravity_preset_dials_for_slot(slot: int) -> dict[str, float]:
    """Programmed dial bundle for a preset slot (status grid / static readout)."""
    slot = int(slot)
    if slot in _GRAVITY_PRESET_PROFILES:
        return dict(_GRAVITY_PRESET_PROFILES[slot])
    return dict(_GRAVITY_HOME_DIALS)


_GRAVITY_PRESET_PROFILES: dict[int, dict[str, float]] = {
    1: {
        "phi": 1.0,
        "e": 1.0,
        "pi": 1.0,
        "kappa": KAPPA_DOC,
        "dz": 0.0,
        "alpha": 1.0,
        "beta": 1.0,
        "pressure": 0.0,
        "elev": 26.0,
        "azim": 45.0,
    },
    2: {
        "phi": 0.962,
        "e": 1.038,
        "pi": 1.0,
        "kappa": KAPPA_DOC,
        "dz": 0.22,
        "alpha": 1.38,
        "beta": 1.48,
        "pressure": 1.0,
        "elev": 26.0,
        "azim": 45.0,
    },
    3: {
        **_GRAVITY_HOME_DIALS,
        "pressure": 1.0,
        "dz": 0.18,
    },
    4: {
        **_GRAVITY_HOME_DIALS,
        "pressure": 0.68,
        "dz": 0.14,
        "alpha": 1.30,
        "beta": 1.40,
        "phi": 0.975,
        "e": 1.025,
    },
    5: dict(_GRAVITY_HOME_DIALS),
    6: {
        **_GRAVITY_HOME_DIALS,
        "pressure": 0.50,
        "dz": 0.12,
    },
    7: {
        **_GRAVITY_HOME_DIALS,
        "phi": 0.950,
        "pressure": 0.45,
    },
    8: {
        **_GRAVITY_HOME_DIALS,
        "e": 1.050,
        "pressure": 0.45,
    },
    9: {
        **_GRAVITY_HOME_DIALS,
        "pi": 0.980,
        "pressure": 0.55,
        "dz": 0.15,
    },
}


def _gravity_dial_bundle(
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
    deform_pressure: float,
    view_elev: float,
    view_azim: float,
) -> dict[str, float]:
    return {
        "phi": float(phi_sq_scale),
        "e": float(e_sq_scale),
        "pi": float(pi_sq_scale),
        "kappa": float(kappa),
        "dz": float(delta_z),
        "alpha": float(alpha),
        "beta": float(beta),
        "pressure": float(deform_pressure),
        "elev": float(view_elev),
        "azim": float(view_azim),
    }


def _gravity_preset_id(slot: int) -> str:
    return f"{int(slot) + 1:02d}"


def _build_render_preset_meta() -> dict[int, dict[str, str]]:
    """Metadata for Render tab full-viewport preset detail panels."""
    meta: dict[int, dict[str, str]] = {}
    for slot in range(_STATUS_GRID_PRESET_COUNT):
        preset_id = _gravity_preset_id(slot)
        shape = _render_preset_shape_meta(slot)
        dials = _render_preset_dials_for_slot(slot)
        params = "\n".join(
            [
                f"Deformation: {dials['pressure'] * 100:.0f}%",
                f"Shape type: {shape['shape_type']}",
                f"Pressure level: {shape['pressure_label']}",
                f"φ² scale: {dials['phi']:.3f}",
                f"e² scale: {dials['e']:.3f}",
                f"π² scale: {dials['pi']:.3f}",
                f"κ (holonomy): {dials['kappa']:.3f}",
                f"δ_z push: {dials['dz']:.3f}",
                f"α geometry: {dials['alpha']:.3f}",
                f"β coupling: {dials['beta']:.3f}",
                f"View elevation: {dials['elev']:.1f}°",
                f"View azimuth: {dials['azim']:.1f}°",
            ]
        )
        meta[slot] = {
            "title": f"Preset {preset_id} – {shape['title']}",
            "description": (
                f"**Shape type:** {shape['shape_type']}  \n"
                f"**Pressure level:** {shape['pressure_label']} ({shape['deform_display']})  \n\n"
                f"{shape['summary']}  \n\n"
                "Drag to orbit 360°, scroll or pinch to zoom; use the Plotly toolbar "
                "for pan, reset, download, and fullscreen."
            ),
            "params": params,
            "notes": shape["summary"],
        }
    return meta


RENDER_PRESET_META = _build_render_preset_meta()


def _gravity_param_display(spec: dict[str, object], value: float) -> str:
    kind = str(spec["kind"])
    if kind == "percent":
        return f"{float(value) * 100.0:.1f}%"
    if kind == "degrees":
        return f"{float(value):.1f}°"
    return f"{float(value):.4f}"


def _gravity_param_default_display(spec: dict[str, object]) -> str:
    return _gravity_param_display(spec, float(spec["default"]))


def _gravity_param_range_label(spec: dict[str, object]) -> str:
    kind = str(spec["kind"])
    lo = float(spec["min"])
    hi = float(spec["max"])
    if kind == "percent":
        return f"{lo * 100:.0f}–{hi * 100:.0f}%"
    if kind == "degrees":
        return f"{lo:.0f}–{hi:.0f}°"
    return f"{lo:.3f}–{hi:.3f}"


def _gravity_param_range_parens(spec: dict[str, object]) -> str:
    """Min–max (or option span) for a catalog parameter, wrapped in parentheses."""
    options = spec.get("options")
    if options:
        return f"({' · '.join(str(opt) for opt in options)})"
    return f"({_gravity_param_range_label(spec)})"


def _gravity_level_blocks(value: float, spec: dict[str, object]) -> tuple[str, str]:
    lo = float(spec["min"])
    hi = float(spec["max"])
    span = max(hi - lo, 1e-9)
    centered = float(value) - (lo + hi) / 2.0
    if centered < 0 and abs(centered) > span * 0.05:
        frac = min(1.0, abs(centered) / (span / 2.0))
        n = max(1, min(10, round(frac * 10)))
        blocks = (
            '<span class="myst-level-block myst-level-fill myst-level-neg"></span>' * n
        )
        return blocks, "myst-val-neg"
    norm = (float(value) - lo) / span
    n = max(0, min(10, round(norm * 10)))
    blocks = (
        '<span class="myst-level-block myst-level-fill myst-level-pos"></span>' * n
    )
    blocks += '<span class="myst-level-block myst-level-empty"></span>' * (10 - n)
    return blocks, "myst-val-pos"


_GRAVITY_PIPELINE_SOFT_LIMIT = 5
_GRAVITY_MAIN_MENU_ITEMS: tuple[tuple[str, str], ...] = (
    ("preset_list", "Load Preset — catalog"),
    ("animate", "Animate Current Preset"),
    ("pipeline", "Pipeline Animation — stitch sequence"),
    ("catalog", "Parameter Catalog"),
)
_GRAVITY_MAIN_MENU_FOCUS_MAX = max(0, len(_GRAVITY_MAIN_MENU_ITEMS) - 1)


def _default_gravity_tui_state() -> dict[str, object]:
    return {
        "menu": "main",
        "focus": 0,
        "scroll": 0,
        "pipeline": [],
        "message": "",
        "pending": "",
    }


def _coerce_gravity_tui_state(value: object) -> dict[str, object]:
    """Normalize TUI menu/nav state — current_menu, pipeline_sequence, scroll/focus."""
    if isinstance(value, dict):
        menu = str(value.get("menu", "main"))
        if menu not in {"main", "preset_list", "pipeline"}:
            menu = "main"
        try:
            scroll = int(value.get("scroll", 0))
        except (TypeError, ValueError):
            scroll = 0
        try:
            focus = int(value.get("focus", 0))
        except (TypeError, ValueError):
            focus = 0
        pipeline_raw = value.get("pipeline", [])
        pipeline: list[int] = []
        if isinstance(pipeline_raw, list):
            for item in pipeline_raw:
                try:
                    pipeline.append(max(0, min(_GRAVITY_TUI_MENU_FOCUS_MAX, int(item))))
                except (TypeError, ValueError):
                    continue
        pending = str(value.get("pending", "") or "")
        message = str(value.get("message", "") or "")
        focus_max = (
            _GRAVITY_MAIN_MENU_FOCUS_MAX
            if menu == "main"
            else _GRAVITY_TUI_MENU_FOCUS_MAX
        )
        return {
            "menu": menu,
            "scroll": max(0, scroll),
            "focus": max(0, min(focus_max, focus)),
            "pipeline": pipeline,
            "message": message,
            "pending": pending,
        }
    if isinstance(value, (int, float, str)):
        try:
            slot = max(0, min(_GRAVITY_TUI_MENU_FOCUS_MAX, int(value)))
        except (TypeError, ValueError):
            slot = 0
        state = _default_gravity_tui_state()
        state["menu"] = "preset_list"
        state["focus"] = slot
        return state
    return _default_gravity_tui_state()


def _coerce_active_preset(value: object) -> int:
    if isinstance(value, dict):
        return _coerce_gravity_tui_state(value)["focus"]
    try:
        return max(0, min(_GRAVITY_TUI_MENU_FOCUS_MAX, int(value)))
    except (TypeError, ValueError):
        return 0


def _gravity_preset_handler_outputs(
    outputs: tuple,
    *,
    menu_state: dict[str, object] | None = None,
) -> tuple:
    """Map explorer outputs (…, tui, active_slot) → preset outputs (…, tui, tui_state, active_slot)."""
    out = list(outputs)
    active_slot_val = out.pop()
    return (*out, _coerce_gravity_tui_state(menu_state), active_slot_val)


def _gravity_keypad_label(key: str) -> str:
    if key in {"enter", "stop"}:
        return "\u00a0"
    return {
        "up": "↑",
        "down": "↓",
        "left": "←",
        "right": "→",
    }.get(key, key)


def _gravity_preset_tui_short_label(slot: int) -> str:
    slot = int(slot)
    if slot in _RENDER_PRESET_LABELS:
        return _RENDER_PRESET_LABELS[slot].title()
    return _GRAVITY_PRESET_TUI_LABELS.get(
        slot,
        _GRAVITY_PRESET_SLOT_LABELS.get(slot, "Preset"),
    )


def _gravity_tui_preset_lines(
    *,
    focus: int,
    active_slot: int | None = None,
) -> list[str]:
    lines: list[str] = []
    focus_slot = max(0, min(_GRAVITY_TUI_MENU_FOCUS_MAX, int(focus)))
    active = int(active_slot) if active_slot is not None else None
    for slot in range(len(_GRAVITY_KEYPAD_NUMERIC_KEYS)):
        preset_id = _gravity_preset_id(slot)
        label = _gravity_preset_tui_short_label(slot)
        if slot == focus_slot:
            marker = ">"
        elif active is not None and slot == active:
            marker = "*"
        else:
            marker = " "
        lines.append(f"{marker} {preset_id} - {label}")
    return lines


def _gravity_tui_status_label(
    active_slot: int,
    *,
    status_label: str | None = None,
    key_metrics: dict[str, float | int | str | None] | None = None,
) -> str:
    if status_label:
        return status_label
    if key_metrics:
        phase = key_metrics.get("phase")
        if phase == "once":
            return "ANIMATE — PLAYING"
        if phase == "loop":
            return "ANIMATE — LOOP"
        frame_idx = key_metrics.get("frame_idx")
        total_frames = key_metrics.get("total_frames")
        if frame_idx is not None and total_frames:
            return f"ANIMATE — FRAME {int(frame_idx)}/{int(total_frames)}"
        return "ANIMATE"
    preset_id = _gravity_preset_id(active_slot)
    return f"PRESET {preset_id} — {_gravity_preset_tui_short_label(active_slot)}"


def _gravity_keypad_btn_classes(key: str, *, active_numeric: str = "", active_nav: str = "") -> list[str]:
    classes = ["vqc-receiver-preset", "myst-gravity-keypad-btn"]
    if key in _GRAVITY_KEYPAD_NUMERIC_KEYS:
        classes.append("myst-gravity-keypad-num")
        if key == active_numeric:
            classes.append("active")
    else:
        classes.append("myst-gravity-keypad-nav")
        if key == "enter":
            classes.append("myst-gravity-keypad-enter")
        elif key == "stop":
            classes.append("myst-gravity-keypad-stop")
        else:
            classes.append("myst-gravity-keypad-arrow")
        if key == active_nav:
            classes.append("active")
    return classes


def _gravity_keypad_btn_updates(
    *,
    active_numeric: str = "",
    active_nav: str = "",
) -> tuple:
    return tuple(
        gr.update(
            elem_classes=_gravity_keypad_btn_classes(
                key,
                active_numeric=active_numeric,
                active_nav=active_nav,
            ),
            variant="secondary",
        )
        for key in _GRAVITY_KEYPAD_ALL_KEYS
    )


def _gravity_child_nav_btn_classes(letter: str, active_slot: int) -> list[str]:
    classes = ["vqc-source-tab", "demo-btn", "myst-status-preset-btn", "myst-gravity-preset-btn"]
    slot = ord(letter) - ord("A")
    if 0 <= int(active_slot) < len(_GRAVITY_CHILD_NAV_LETTERS) and slot == int(active_slot):
        classes.append("active")
    return classes


def _gravity_child_nav_btn_updates(active_slot: int = -1) -> tuple:
    active = int(active_slot)
    return tuple(
        gr.update(
            elem_classes=_gravity_child_nav_btn_classes(letter, active),
            # Demo tabs stay clickable — A must relaunch breathing when re-selected.
            interactive=True,
            variant="secondary",
        )
        for letter in _GRAVITY_CHILD_NAV_LETTERS
    )


def _gravity_child_nav_output_updates(active_slot: int = -1) -> tuple:
    """Wired preset outputs — skip legacy back slot, then A–I updates."""
    return (gr.skip(), *_gravity_child_nav_btn_updates(active_slot))


def _demo_active_tab_updates(active_letter: str) -> tuple:
    """Orange active styling for Demo A–I — no back button in demo outputs."""
    letter = str(active_letter).strip().upper()
    if letter not in _GRAVITY_CHILD_NAV_LETTERS:
        letter = "A"
    slot = ord(letter) - ord("A")
    return _gravity_child_nav_btn_updates(slot)


_GRAVITY_DEMO_VIDEO_CACHE: dict[str, str] = {}
_BREATHING_DEMO_VIDEO_CACHE: str | None = None
_BUNDLED_BREATHING_VIDEO = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "assets",
    "demo_a_breathing.gif",
)


def _gravity_demo_letter_slot(letter: str) -> int:
    letter = str(letter).strip().upper()
    if letter not in _GRAVITY_CHILD_NAV_LETTERS:
        letter = "A"
    return ord(letter) - ord("A")


def _gravity_demo_video_html(video_path: str, *, letter: str, title: str, deform_display: str) -> str:
    url = f"/gradio_api/file={video_path}"
    return (
        f'<div class="myst-gravity-viewport-inner myst-gravity-demo-{letter.lower()}">'
        f'<div class="myst-gravity-viewport-title">Demo {letter} — {title}</div>'
        f'<div class="myst-gravity-viewport-sub">{deform_display}</div>'
        '<video class="myst-gravity-demo-video" autoplay loop muted playsinline '
        'preload="auto">'
        f'<source src="{url}" type="video/mp4" />'
        "</video></div>"
    )


def _get_gravity_demo_static_html(letter: str) -> str:
    """Fast static frame for a demo letter (used before video encode)."""
    letter = str(letter).strip().upper()
    slot = _gravity_demo_letter_slot(letter)
    meta = _render_preset_shape_meta(slot)
    dials = _render_preset_dials_for_slot(slot)
    try:
        _metrics, _header, fig = run_residual_explorer(
            dials["phi"],
            dials["e"],
            dials["pi"],
            dials["kappa"],
            dials["dz"],
            dials["alpha"],
            dials["beta"],
            dials["pressure"],
            dials["elev"],
            dials["azim"],
        )
        body = figure_to_viewport_cached_html(fig, dpi=_UNIT_CELL_IMAGE_DPI)
    except Exception as exc:
        logger.exception("gravity demo static frame failed for %s", letter)
        body = unit_cell_error_placeholder_html()
        body = f'<div class="myst-gravity-viewport-error">Demo {letter} error: {exc}</div>{body}'
    return (
        f'<div class="myst-gravity-viewport-inner myst-gravity-demo-{letter.lower()}">'
        f'<div class="myst-gravity-viewport-title">Demo {letter} — {meta["title"]}</div>'
        f'<div class="myst-gravity-viewport-sub">{meta["deform_display"]} · {meta["shape_type"]}</div>'
        f'<div class="myst-gravity-viewport-frame">{body}</div></div>'
    )


def _get_gravity_animation_html(letter: str) -> str:
    """Return looping deformation video HTML for the selected Demo letter."""
    letter = str(letter).strip().upper()
    if letter not in _GRAVITY_CHILD_NAV_LETTERS:
        letter = "A"
    slot = _gravity_demo_letter_slot(letter)
    meta = _render_preset_shape_meta(slot)
    dials = _render_preset_dials_for_slot(slot)
    if letter not in _GRAVITY_DEMO_VIDEO_CACHE:
        try:
            _GRAVITY_DEMO_VIDEO_CACHE[letter] = render_gravity_demo_animation_video(
                dials["phi"],
                dials["e"],
                dials["pi"],
                dials["kappa"],
                dials["dz"],
                dials["alpha"],
                dials["beta"],
                dials["pressure"],
                dials["elev"],
                dials["azim"],
            )
        except Exception as exc:
            logger.exception("gravity demo video failed for %s", letter)
            return _get_gravity_demo_static_html(letter).replace(
                "</div></div>",
                f'<div class="myst-gravity-viewport-error">Video encode failed: {exc}</div></div></div>',
                1,
            )
    return _gravity_demo_video_html(
        _GRAVITY_DEMO_VIDEO_CACHE[letter],
        letter=letter,
        title=meta["title"],
        deform_display=f'{meta["deform_display"]} · {meta["shape_type"]}',
    )


def _create_breathing_animation(*, fresh: bool = False):
    """Looping breathing Plotly figure for Demo A — ready to animate on load."""
    return create_breathing_animation(fresh=fresh)


def _cache_media_for_gradio(src_path: str) -> str:
    """Copy temp media into Gradio cache so /gradio_api/file= URLs work on HF."""
    from gradio.processing_utils import save_file_to_cache
    from gradio.utils import get_upload_folder

    served = save_file_to_cache(src_path, get_upload_folder())
    print(f"[breathing] cached media: {src_path} -> {served}", flush=True)
    return served


def _get_breathing_demo_video_path() -> str:
    """Gradio-served path to looping breathing GIF/MP4 (bundled asset preferred)."""
    global _BREATHING_DEMO_VIDEO_CACHE
    if _BREATHING_DEMO_VIDEO_CACHE is None:
        if os.path.isfile(_BUNDLED_BREATHING_VIDEO):
            raw_path = _BUNDLED_BREATHING_VIDEO
            print(f"[breathing] using bundled asset: {raw_path}", flush=True)
        else:
            raw_path = render_breathing_demo_video(n_per_segment=8, fps=10, dpi=80)
        _BREATHING_DEMO_VIDEO_CACHE = _cache_media_for_gradio(raw_path)
    return _BREATHING_DEMO_VIDEO_CACHE


def _get_rigid_preset_plotly_figure():
    """Preset 05 rigid cube — fast placeholder while breathing video encodes."""
    dials = _render_preset_dials_for_slot(4)
    fig = run_residual_explorer_plotly(
        dials["phi"],
        dials["e"],
        dials["pi"],
        dials["kappa"],
        dials["dz"],
        dials["alpha"],
        dials["beta"],
        dials["pressure"],
        dials["elev"],
        dials["azim"],
    )
    fig.update_layout(
        height=620,
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        uirevision="mystery-demo-rigid",
    )
    return fig


def _demo_viewport_show_plot(fig) -> tuple:
    """Show interactive Plotly preset (B–I)."""
    return (
        gr.update(value=fig, visible=True),
        gr.update(value=None, visible=False),
    )


def _demo_viewport_show_breathing_video() -> tuple:
    """Show looping breathing GIF/MP4 via gr.Video (HF-safe cached path)."""
    video_path = _get_breathing_demo_video_path()
    return (
        gr.update(visible=False),
        gr.update(value=video_path, visible=True, autoplay=True, loop=True),
    )


def _launch_demo_a() -> tuple:
    """Demo A — breathing MP4; fall back to rigid Plotly if encode fails."""
    try:
        viewport = _demo_viewport_show_breathing_video()
    except Exception as exc:
        logger.exception("breathing demo video failed")
        viewport = _demo_viewport_show_plot(_get_rigid_preset_plotly_figure())
    return (
        *viewport,
        *_demo_active_tab_updates("A"),
        "A",
    )


def _get_gravity_demo_plotly_figure(letter: str):
    """Static Plotly unit-cell figure for Demo letters B–I."""
    slot = _gravity_demo_letter_slot(letter)
    dials = _render_preset_dials_for_slot(slot)
    fig = run_residual_explorer_plotly(
        dials["phi"],
        dials["e"],
        dials["pi"],
        dials["kappa"],
        dials["dz"],
        dials["alpha"],
        dials["beta"],
        dials["pressure"],
        dials["elev"],
        dials["azim"],
    )
    fig.update_layout(
        height=620,
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        uirevision=f"mystery-demo-{letter.lower()}",
    )
    return fig


def _switch_gravity_demo(letter: str) -> tuple:
    """Switch the Home viewport to the demo for the selected letter (B–I)."""
    letter = str(letter).strip().upper()
    slot = _gravity_demo_letter_slot(letter)
    fig = _get_gravity_demo_plotly_figure(letter)
    return (
        *_demo_viewport_show_plot(fig),
        *_demo_active_tab_updates(letter),
        letter,
    )


def _gravity_tui_viewport_open(scroll_px: int) -> str:
    return (
        '<div class="myst-preset-tui-viewport" '
        f'style="--tui-scroll:{max(0, int(scroll_px))}px">'
    )


def _format_gravity_main_menu_html(*, tui_state: dict[str, object] | None = None) -> str:
    state = _coerce_gravity_tui_state(tui_state)
    focus = int(state["focus"])
    scroll_px = int(state["scroll"])
    lines: list[str] = ["MAIN MENU", ""]
    for index, (_action, label) in enumerate(_GRAVITY_MAIN_MENU_ITEMS):
        marker = ">" if index == focus else " "
        lines.append(f"{marker} {index + 1} - {label}")
    message = str(state.get("message", "") or "").strip()
    if message:
        lines.extend(["", message])
    lines.extend(["", "↑↓ move · number jump · Green confirm · Red back"])
    body = "\n".join(lines).rstrip()
    return (
        f'{_gravity_tui_viewport_open(scroll_px)}'
        '<div class="myst-preset-tui-serial myst-preset-tui-menu">'
        '<div class="myst-preset-tui-status">'
        "<u>ACTIVE STATUS: GRAVITY MENU</u>"
        "</div>"
        f'<pre class="myst-preset-tui-lines">{body}</pre>'
        "</div></div>"
    )


def _format_gravity_preset_list_html(
    *,
    tui_state: dict[str, object] | None = None,
    active_slot: int | None = None,
) -> str:
    state = _coerce_gravity_tui_state(tui_state)
    focus = int(state["focus"])
    scroll_px = int(state["scroll"])
    body = "\n".join(
        _gravity_tui_preset_lines(focus=focus, active_slot=active_slot)
    ).rstrip()
    message = str(state.get("message", "") or "").strip()
    if message:
        body = f"{body}\n\n{message}"
    return (
        f'{_gravity_tui_viewport_open(scroll_px)}'
        '<div class="myst-preset-tui-serial myst-preset-tui-menu">'
        '<div class="myst-preset-tui-status">'
        "<u>ACTIVE STATUS: PRESET CATALOG</u>"
        "</div>"
        f'<pre class="myst-preset-tui-lines">{body}</pre>'
        "</div></div>"
    )


def _format_gravity_pipeline_menu_html(*, tui_state: dict[str, object] | None = None) -> str:
    state = _coerce_gravity_tui_state(tui_state)
    scroll_px = int(state["scroll"])
    pipeline = list(state.get("pipeline", []))
    seq = (
        " → ".join(_gravity_preset_id(int(slot)) for slot in pipeline)
        if pipeline
        else "(empty)"
    )
    pending = str(state.get("pending", "") or "").strip()
    pending_line = f"Pending digit: {pending}" if pending else "Pending digit: —"
    message = str(state.get("message", "") or "").strip() or (
        "Enter preset number + Green to add.\n"
        "Green (no pending) = finish pipeline.\n"
        "Red = cancel and return to main menu."
    )
    body = "\n".join(
        [
            "PIPELINE ANIMATION",
            "",
            f"Sequence: {seq}",
            pending_line,
            "",
            message,
        ]
    ).rstrip()
    return (
        f'{_gravity_tui_viewport_open(scroll_px)}'
        '<div class="myst-preset-tui-serial myst-preset-tui-menu">'
        '<div class="myst-preset-tui-status">'
        "<u>ACTIVE STATUS: PIPELINE BUILDER</u>"
        "</div>"
        f'<pre class="myst-preset-tui-lines">{body}</pre>'
        "</div></div>"
    )


def _format_gravity_menu_tui_html(
    *,
    tui_state: dict[str, object] | None = None,
    active_slot: int | None = None,
) -> str:
    state = _coerce_gravity_tui_state(tui_state)
    menu = str(state["menu"])
    if menu == "pipeline":
        return _format_gravity_pipeline_menu_html(tui_state=state)
    if menu == "preset_list":
        return _format_gravity_preset_list_html(
            tui_state=state,
            active_slot=active_slot,
        )
    return _format_gravity_main_menu_html(tui_state=state)


def _format_gravity_control_panel_html(
    dials: dict[str, float],
    active_slot: int,
) -> str:
    if active_slot == 0:
        return (
            '<div class="myst-gravity-level-panel myst-gravity-level-menu-mode">'
            '<div class="myst-gravity-level-title">PARAMETER LEVELS</div>'
            '<hr class="myst-gravity-level-rule" />'
            '<p class="myst-gravity-level-hint">'
            "PRESET 01 — menu loaded in TUI. Select <b>02</b> rigid cube or <b>03</b> full bowl."
            "</p>"
            "</div>"
        )
    rows: list[str] = []
    for spec in _GRAVITY_PARAM_CATALOG:
        val = float(dials[str(spec["key"])])
        blocks, val_cls = _gravity_level_blocks(val, spec)
        display = _gravity_param_display(spec, val)
        rows.append(
            '<div class="myst-gravity-level-row">'
            f'<span class="myst-gravity-level-id">{spec["id"]} -</span>'
            f'<span class="myst-gravity-level-bar">{blocks}</span>'
            '<span class="myst-gravity-level-sep"> | </span>'
            f'<span class="myst-gravity-level-val {val_cls}">{display}</span>'
            "</div>"
        )
    preset_id = _gravity_preset_id(active_slot)
    return (
        '<div class="myst-gravity-level-panel">'
        '<div class="myst-gravity-level-title">PARAMETER LEVELS</div>'
        '<hr class="myst-gravity-level-rule" />'
        f"{''.join(rows)}"
        f'<div class="myst-gravity-level-foot">PRESET {preset_id} · live dial readout</div>'
        "</div>"
    )


def _format_gravity_status_catalog_notes(slot: int) -> str:
    """Outlined Notes box with preset-specific configuration guidance."""
    note = _GRAVITY_PRESET_STATUS_NOTES.get(
        int(slot),
        "Programmed preset configuration notes for this Status catalog panel.",
    )
    return (
        '<div class="myst-status-notes-wrap">'
        '<div class="myst-status-notes-label">Notes</div>'
        f'<div class="myst-status-notes-box">{html.escape(note)}</div>'
        "</div>"
    )


def _format_gravity_status_catalog_header(*, zoom: bool = False) -> str:
    """Column labels for Status preset catalog tables."""
    zoom_cls = " myst-status-zoom-level-row" if zoom else ""
    return (
        f'<div class="myst-gravity-level-row myst-status-level-row myst-status-catalog-header{zoom_cls}">'
        '<span class="myst-gravity-level-id">#</span>'
        '<span class="myst-gravity-level-desc">Description</span>'
        '<span class="myst-gravity-level-range">Range</span>'
        '<span class="myst-gravity-level-bar"></span>'
        '<span class="myst-gravity-level-val">Value</span>'
        "</div>"
    )


def _format_gravity_status_catalog_rows(
    dials: dict[str, float],
    *,
    slot: int,
    zoom: bool = False,
) -> str:
    """Status preset catalog lines with a blank row after each numbered entry."""
    rows: list[str] = [_format_gravity_status_catalog_header(zoom=zoom)]
    catalog = _GRAVITY_PARAM_CATALOG
    zoom_cls = " myst-status-zoom-level-row" if zoom else ""
    rows.append('<div class="myst-status-level-spacer" aria-hidden="true"></div>')
    for index, spec in enumerate(catalog):
        val = float(dials[str(spec["key"])])
        blocks, val_cls = _gravity_level_blocks(val, spec)
        display = _gravity_param_display(spec, val)
        range_text = _gravity_param_range_parens(spec)
        rows.append(
            f'<div class="myst-gravity-level-row myst-status-level-row{zoom_cls}">'
            f'<span class="myst-gravity-level-id">{spec["id"]}</span>'
            f'<span class="myst-gravity-level-desc">{spec["label"]}</span>'
            f'<span class="myst-gravity-level-range">{range_text}</span>'
            f'<span class="myst-gravity-level-bar">{blocks}</span>'
            f'<span class="myst-gravity-level-val {val_cls}">{display}</span>'
            "</div>"
        )
        if index < len(catalog) - 1:
            rows.append('<div class="myst-status-level-spacer" aria-hidden="true"></div>')
    rows.append('<div class="myst-status-level-spacer" aria-hidden="true"></div>')
    rows.append(_format_gravity_status_catalog_notes(slot))
    return "".join(rows)


def _format_gravity_status_cell_html(slot: int, *, active: bool = False) -> str:
    """Compact parameter levels for one programmed preset (status grid cell)."""
    dials = _gravity_preset_dials_for_slot(slot)
    preset_id = _gravity_preset_id(slot)
    profile = _GRAVITY_PRESET_SLOT_LABELS.get(slot)
    subtitle = f" · {profile}" if profile else ""
    active_cls = " myst-status-grid-cell-active" if active else ""
    panel_index = slot + 1
    return (
        f'<div class="myst-status-grid-cell myst-status-panel-{panel_index}{active_cls}">'
        '<div class="myst-gravity-level-panel myst-status-preset-panel">'
        f'<div class="myst-gravity-level-title">PRESET {preset_id}{subtitle}</div>'
        '<hr class="myst-gravity-level-rule" />'
        f"{_format_gravity_status_catalog_rows(dials, slot=slot)}"
        "</div>"
        "</div>"
    )


def _status_panel_html(
    zoom_slot: int,
    *,
    grid_active_slot: int | None = None,
    dials: dict[str, float] | None = None,
) -> str:
    """Single Status content host — 3×3 grid when zoom_slot < 0, else full-page preset."""
    zs = int(zoom_slot)
    if zs >= 0:
        return _format_gravity_status_zoom_html(zs, dials)
    return _format_gravity_status_grid_html(active_slot=grid_active_slot)


def _status_panels_host_update(*, edit_active: bool) -> gr.Update:
    classes = ["myst-status-panels-host"]
    if edit_active:
        classes.append("myst-status-edit-active")
    return gr.update(elem_classes=classes)


def _status_catalog_updates(
    zoom_slot: int,
    *,
    grid_active_slot: int | None = None,
    dials: dict[str, float] | None = None,
    visible: bool = True,
) -> tuple[gr.Update, gr.Update]:
    """Refresh catalog HTML and show/hide the catalog column during manual edit."""
    html = _status_panel_html(
        zoom_slot,
        grid_active_slot=grid_active_slot,
        dials=dials,
    )
    show = bool(visible)
    return (
        gr.update(visible=show),
        gr.update(value=html),
    )


def _status_panel_levels_update(
    zoom_slot: int,
    *,
    grid_active_slot: int | None = None,
    dials: dict[str, float] | None = None,
    visible: bool = True,
) -> tuple[gr.Update, gr.Update, gr.Update]:
    """Refresh Status panels — catalog column, HTML value, and panels-host edit class."""
    catalog_col, panel_html = _status_catalog_updates(
        zoom_slot,
        grid_active_slot=grid_active_slot,
        dials=dials,
        visible=visible,
    )
    return (
        catalog_col,
        panel_html,
        _status_panels_host_update(edit_active=not visible),
    )


def _format_gravity_status_grid_html(active_slot: int | None = None) -> str:
    """3×3 status page grid — status_panel_1 … status_panel_9 programmed preset readouts."""
    active = int(active_slot) if active_slot is not None else None
    cells = [
        _format_gravity_status_cell_html(slot, active=(active == slot))
        for slot in range(_STATUS_GRID_PRESET_COUNT)
    ]
    return (
        '<div class="myst-status-grid-wrap">'
        '<div class="myst-status-grid">'
        f"{''.join(cells)}"
        "</div>"
        "</div>"
    )


def _dials_to_explorer_args(dials: dict[str, float]) -> tuple[float, ...]:
    return (
        dials["phi"],
        dials["e"],
        dials["pi"],
        dials["kappa"],
        dials["dz"],
        dials["alpha"],
        dials["beta"],
        dials["pressure"],
        dials["elev"],
        dials["azim"],
    )


def _render_preset_plot_html(slot: int, *, dpi: int = _RENDER_GRID_IMAGE_DPI) -> str:
    """Render one preset's unit-cell plot as stretch-filled grid cell HTML."""
    dials = _render_preset_dials_for_slot(slot)
    _metrics, _header, fig = run_residual_explorer(*_dials_to_explorer_args(dials))
    return _gravity_fig_to_render_grid_file_html(fig, dpi=dpi)


def _render_preset_detail_plot_html(slot: int) -> str:
    """Interactive Plotly plot for the Render preset detail view."""
    dials = _render_preset_dials_for_slot(slot)
    fig = run_residual_explorer_plotly(*_dials_to_explorer_args(dials))
    return plotly_figure_to_render_detail_html(fig)


def _render_detail_plot_fallback(slot: int, error: Exception):
    """Informative Plotly figure when WebGL / 3D rendering fails in the browser."""
    import plotly.graph_objects as go

    preset_id = _gravity_preset_id(int(slot))
    fig = go.Figure()
    fig.add_annotation(
        text=(
            "3D rendering failed in this browser.<br>"
            "Please try Firefox or disable Brave Shields.<br>"
            f"Preset {preset_id}<br>"
            f"Error: {str(error)[:100]}"
        ),
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        align="center",
        font=dict(size=16, color="#e8a040"),
    )
    fig.update_layout(
        height=500,
        margin=dict(l=24, r=24, t=24, b=24),
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        uirevision="constant",
    )
    return fig


def _generate_render_detail_plot(slot: int):
    """Large interactive Plotly 3D figure for the Render preset detail view."""
    slot = int(slot)
    try:
        dials = _render_preset_dials_for_slot(slot)
        fig = run_residual_explorer_plotly(*_dials_to_explorer_args(dials))
        fig.update_layout(
            height=620,
            margin=dict(l=0, r=0, t=8, b=0),
            paper_bgcolor="#000000",
            plot_bgcolor="#000000",
            uirevision="constant",
        )
        fig.update_layout(
            modebar=dict(orientation="v", bgcolor="rgba(0, 0, 0, 0.55)"),
        )
        return fig
    except Exception as exc:
        return _render_detail_plot_fallback(slot, exc)


def _format_render_detail_description(slot: int) -> str:
    """Markdown description panel for a Render preset detail view."""
    slot = int(slot)
    meta = RENDER_PRESET_META.get(slot, {})
    return (
        f"### {meta.get('title', f'Preset {_gravity_preset_id(slot)}')}\n\n"
        f"**Description**  \n"
        f"{meta.get('description', 'No description available.')}\n\n"
        f"**Current Parameters**\n\n"
        f"```\n{meta.get('params', 'N/A')}\n```\n\n"
        f"**Notes**  \n"
        f"{meta.get('notes', 'No additional notes.')}"
    )


def _format_render_cell_html(
    slot: int,
    *,
    plot_html: str | None = None,
    active: bool = False,
    loading: bool = False,
) -> str:
    """Single Render grid cell — preset label plus plot or placeholder."""
    preset_id = _gravity_preset_id(slot)
    profile = _RENDER_PRESET_LABELS.get(slot)
    subtitle = f" · {profile}" if profile else ""
    active_cls = " myst-render-grid-cell-active" if active else ""
    panel_index = slot + 1
    if plot_html:
        body = f'<div class="myst-render-plot-host">{plot_html}</div>'
    elif loading:
        body = (
            '<div class="myst-render-plot-placeholder myst-render-plot-loading">'
            f'Rendering preset <span class="myst-render-accent">{preset_id}</span>…'
            "</div>"
        )
    else:
        body = (
            '<div class="myst-render-plot-placeholder">'
            'Click <span class="myst-render-accent">Render</span> to load'
            "</div>"
        )
    return (
        f'<div class="myst-render-grid-cell myst-render-cell-clickable myst-render-panel-{panel_index}{active_cls}" '
        f'data-slot="{slot}" role="button" tabindex="0" '
        f'aria-label="Open PRESET {preset_id} detail view">'
        '<div class="myst-gravity-level-panel myst-render-preset-panel">'
        '<div class="myst-render-preset-header">'
        f'<div class="myst-gravity-level-title">PRESET {preset_id}{subtitle}</div>'
        '<hr class="myst-gravity-level-rule" />'
        '</div>'
        f"{body}"
        "</div>"
        "</div>"
    )


def _format_render_grid_html(
    plot_htmls: list[str | None] | None = None,
    *,
    active_slot: int | None = None,
    render_in_progress: bool = False,
) -> str:
    """3×3 Render page grid — preset plots or placeholders."""
    cells = [
        _format_render_cell_html(
            slot,
            plot_html=None if plot_htmls is None else plot_htmls[slot],
            active=(active_slot is not None and active_slot == slot),
            loading=bool(
                render_in_progress
                and plot_htmls is not None
                and not plot_htmls[slot]
            ),
        )
        for slot in range(_STATUS_GRID_PRESET_COUNT)
    ]
    return (
        '<div class="myst-render-grid-wrap">'
        '<div class="myst-render-grid">'
        f"{''.join(cells)}"
        "</div>"
        "</div>"
    )


def _format_render_detail_html(slot: int, *, plot_html: str | None = None) -> str:
    """Full-page preset detail — title plus large unit-cell plot."""
    slot = int(slot)
    preset_id = _gravity_preset_id(slot)
    profile = _GRAVITY_PRESET_SLOT_LABELS.get(slot)
    subtitle = f" · {profile}" if profile else ""
    plot = plot_html or _render_preset_detail_plot_html(slot)
    return (
        f'<div class="myst-render-detail-wrap myst-render-panel-{slot + 1}">'
        '<div class="myst-gravity-level-panel myst-render-detail-panel">'
        f'<div class="myst-render-detail-title myst-gravity-level-title">'
        f"PRESET {preset_id}{subtitle}</div>"
        '<hr class="myst-gravity-level-rule" />'
        f'<div class="myst-render-detail-plot-host">{plot}</div>'
        "</div>"
        "</div>"
    )


def _render_panel_html(
    zoom_slot: int,
    plot_cache: list[str | None] | None = None,
    *,
    grid_active_slot: int | None = None,
) -> str:
    """Render tab grid host HTML (detail view uses gr.Plot in a separate column)."""
    _ = zoom_slot
    has_plots = bool(plot_cache) and any(plot_cache)
    return _format_render_grid_html(
        plot_cache if has_plots else None,
        active_slot=grid_active_slot,
    )


def _render_sub_nav_btn_classes(slot: int, active_slot: int) -> list[str]:
    classes = ["vqc-source-tab", "myst-status-preset-btn", "myst-render-preset-btn"]
    if slot == active_slot:
        classes.append("active")
    return classes


def _render_sub_nav_btn_updates(active_slot: int) -> tuple:
    active = int(active_slot)
    return tuple(
        gr.update(
            interactive=(i != active),
            elem_classes=_render_sub_nav_btn_classes(i, active),
            variant="secondary",
        )
        for i in range(_STATUS_ZOOM_PRESET_COUNT)
    )


def _render_sub_nav_render_btn_update(
    *,
    rendering: bool = False,
    on_grid: bool = True,
) -> gr.Update:
    classes = [
        "vqc-source-tab",
        "demo-btn",
        "myst-status-preset-btn",
        "myst-render-nav-render-btn",
        "full-width-btn",
    ]
    if rendering:
        classes.append("active")
    return gr.update(
        value="Render",
        visible=on_grid,
        elem_classes=classes,
        variant="secondary",
    )


def _place_gravity_child_nav_row() -> dict[str, gr.Button]:
    """Demo navigation row for Home — no Back button; label aligns with Mystery:."""
    buttons: dict[str, gr.Button] = {}
    with gr.Row(
        elem_id="myst-gravity-child-nav",
        elem_classes=[
            "myst-secondary-nav",
            "myst-nav-bar-row",
            "myst-gravity-child-nav-row",
            "myst-gravity-demo-nav-wrap",
        ],
    ):
        gr.HTML(
            '<span class="vqc-source-label vqc-nav-row-label myst-gravity-child-nav-label">'
            "Demo:</span>"
        )
        with gr.Row(elem_classes=["nav-button-grid"]):
            for letter in _GRAVITY_CHILD_NAV_LETTERS:
                buttons[letter] = _nav_theme_button(
                    letter,
                    elem_id=f"myst-gravity-preset-btn-{letter}",
                    elem_classes=[
                        "vqc-source-tab",
                        "demo-btn",
                        "myst-status-preset-btn",
                        "myst-gravity-preset-btn",
                    ],
                )
    if not buttons:
        raise RuntimeError("_place_gravity_child_nav_row produced no Demo buttons")
    return buttons


def _place_render_sub_nav_row(
    active_slot: int = -1,
    *,
    zoom_slot: int = -1,
) -> dict[str, gr.Button]:
    """Render sub-nav — Demo: label and nine presets (01 … 09) only."""
    _ = zoom_slot
    buttons: dict[str, gr.Button] = {}
    active = int(active_slot)
    with gr.Row(
        elem_id="myst-render-sub-nav",
        elem_classes=[
            "myst-secondary-nav",
            "myst-nav-bar-row",
            "myst-render-preset-nav-wrap",
            "myst-demo-preset-nav-row",
            "vqc-status-preset-nav-row",
        ],
    ):
        gr.HTML(
            '<span class="vqc-source-label vqc-nav-row-label myst-gravity-child-nav-label">'
            "Demo:</span>"
        )
        with gr.Row(elem_classes=["nav-button-grid"]):
            for slot in range(_STATUS_ZOOM_PRESET_COUNT):
                preset_id = _gravity_preset_id(slot)
                is_active = slot == active
                classes = ["vqc-source-tab", "demo-btn", "myst-status-preset-btn", "myst-render-preset-btn"]
                if is_active:
                    classes.append("active")
                buttons[str(slot)] = _nav_theme_button(
                    preset_id,
                    elem_id=f"myst-render-preset-btn-{preset_id}",
                    elem_classes=classes,
                    interactive=not is_active,
                )
    return buttons


def _render_detail_view_updates(slot: int) -> tuple:
    """Show full-viewport interactive detail for one preset."""
    slot = int(slot)
    return (
        slot,
        slot,
        gr.update(visible=False),
        gr.update(visible=True),
        _generate_render_detail_plot(slot),
        _format_render_detail_description(slot),
        slot,
        *_render_sub_nav_btn_updates(slot),
        _render_sub_nav_render_btn_update(rendering=True, on_grid=False),
    )


def _render_grid_view_updates(
    plot_cache: list[str | None] | None,
    active_slot: int,
    *,
    rendering: bool = True,
) -> tuple:
    """Restore the 3×3 overview grid and hide the detail column."""
    nav_active = int(active_slot) if int(active_slot) >= 0 else -1
    highlight = nav_active if nav_active >= 0 else None
    has_plots = bool(plot_cache) and any(plot_cache)
    html = _format_render_grid_html(
        plot_cache if has_plots else None,
        active_slot=highlight,
    )
    return (
        html,
        -1,
        nav_active,
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(value=None),
        "",
        -1,
        *_render_sub_nav_btn_updates(nav_active if nav_active >= 0 else -1),
        _render_sub_nav_render_btn_update(rendering=rendering and has_plots, on_grid=True),
    )


def _render_open_detail(slot: int, plot_cache: list[str | None] | None = None) -> tuple:
    """Open full-viewport detail view for one preset."""
    _ = plot_cache
    return (gr.skip(), *_render_detail_view_updates(int(slot)))


def _render_grid_load_yield(
    html: str,
    plots: list[str | None],
    nav_active: int,
    *,
    rendering: bool,
) -> tuple:
    """One progressive Render-grid update while presets are generated."""
    return (
        html,
        list(plots),
        -1,
        nav_active,
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(value=None),
        "",
        -1,
        *_render_sub_nav_btn_updates(nav_active),
        _render_sub_nav_render_btn_update(rendering=rendering, on_grid=True),
    )


def _render_load_all_presets(active_slot: int, zoom_slot: int):
    """Render all nine preset plots into the Render grid (progressive yields)."""
    plots: list[str | None] = [None] * _STATUS_GRID_PRESET_COUNT
    zs = int(zoom_slot)
    nav_active = int(active_slot) if int(active_slot) >= 0 else -1
    highlight = nav_active if nav_active >= 0 else None
    on_grid = zs < 0
    if on_grid:
        html = _format_render_grid_html(
            plots,
            active_slot=highlight,
            render_in_progress=True,
        )
        yield _render_grid_load_yield(html, plots, nav_active, rendering=True)
    for slot in range(_STATUS_GRID_PRESET_COUNT):
        plots[slot] = _render_preset_plot_html(slot)
        if on_grid:
            html = _format_render_grid_html(
                plots,
                active_slot=highlight,
                render_in_progress=(slot < _STATUS_GRID_PRESET_COUNT - 1),
            )
            yield _render_grid_load_yield(
                html,
                plots,
                nav_active,
                rendering=(slot == _STATUS_GRID_PRESET_COUNT - 1),
            )
    if zs >= 0:
        yield (
            gr.skip(),
            list(plots),
            *_render_detail_view_updates(zs),
        )


def _format_gravity_status_zoom_html(
    slot: int,
    dials: dict[str, float] | None = None,
) -> str:
    """Full-page preset readout for Status/01 … Status/09 zoom view."""
    slot = int(slot)
    dials = dials or _gravity_preset_dials_for_slot(slot)
    preset_id = _gravity_preset_id(slot)
    profile = _GRAVITY_PRESET_SLOT_LABELS.get(slot)
    subtitle = f" · {profile}" if profile else ""
    return (
        f'<div class="myst-status-zoom-wrap myst-status-panel-{slot + 1}">'
        '<div class="myst-gravity-level-panel myst-status-preset-panel myst-status-zoom-panel">'
        f'<div class="myst-gravity-level-title">PRESET {preset_id}{subtitle}</div>'
        '<hr class="myst-gravity-level-rule" />'
        f"{_format_gravity_status_catalog_rows(dials, slot=slot, zoom=True)}"
        f'<div class="myst-gravity-level-foot">PRESET {preset_id} · parameter levels</div>'
        "</div>"
        "</div>"
    )


def _status_zoom_select(slot: int) -> tuple:
    """Latch a Status/ preset zoom button and show the full-page preset readout."""
    slot = int(slot)
    dials = _gravity_preset_dials_for_slot(slot)
    slider_updates = _gravity_slider_control_updates(dials, edit_enabled=False)
    return (
        *_status_panel_levels_update(slot, dials=dials, visible=True),
        *_status_zoom_btn_updates(slot),
        slot,
        False,
        gr.update(visible=False),
        _status_zoom_nav_edit_btn_update(in_zoom=True, edit_open=False),
        *slider_updates,
        _status_zoom_save_btn_active_update(saved=False),
        False,
    )


_STATUS_ZOOM_SAVE_BTN_CLASSES = [
    "vqc-source-tab",
    "myst-status-preset-btn",
    "myst-status-zoom-save-btn",
]


def _status_zoom_save_btn_placeholder_update() -> gr.Update:
    """Grid view — visible Save placeholder (non-interactive)."""
    return gr.update(
        value="Save",
        interactive=False,
        variant="secondary",
        elem_classes=[
            "save-btn",
            "placeholder-btn",
            *_STATUS_ZOOM_SAVE_BTN_CLASSES,
        ],
    )


def _latch_save_button() -> tuple:
    """Save clicked — red latched styling (detail/edit view only)."""
    return (
        gr.update(
            value="Save",
            interactive=True,
            variant="secondary",
            elem_classes=["save-btn", "saved", *_STATUS_ZOOM_SAVE_BTN_CLASSES],
        ),
        True,
    )


def _unlatch_save_button() -> tuple:
    """Reset Save — white text, global default border (detail/edit view)."""
    return (
        gr.update(
            value="Save",
            interactive=True,
            variant="secondary",
            elem_classes=["save-btn", *_STATUS_ZOOM_SAVE_BTN_CLASSES],
        ),
        False,
    )


def _status_zoom_save_btn_active_update(*, saved: bool = False) -> gr.Update:
    btn_update, _ = _latch_save_button() if saved else _unlatch_save_button()
    return btn_update


def _status_zoom_save_btn_update(
    *,
    saved: bool = False,
    on_grid: bool = False,
) -> gr.Update:
    if on_grid:
        return _status_zoom_save_btn_placeholder_update()
    return _status_zoom_save_btn_active_update(saved=saved)


def _status_zoom_edit_toggle(
    is_open: bool,
    zoom_slot: int,
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
    deform_pressure: float,
    view_elev: float,
    view_azim: float,
) -> tuple:
    """Toggle Status zoom Edit drawer (drop-up) and latch the Edit button."""
    show = not bool(is_open)
    if show:
        dials = _gravity_dial_bundle(
            phi_sq_scale,
            e_sq_scale,
            pi_sq_scale,
            kappa,
            delta_z,
            alpha,
            beta,
            deform_pressure,
            view_elev,
            view_azim,
        )
    else:
        dials = _gravity_preset_dials_for_slot(int(zoom_slot))
    slider_updates = _gravity_slider_control_updates(dials, edit_enabled=show)
    edit_btn = _status_zoom_nav_edit_btn_update(in_zoom=True, edit_open=show)
    slot = int(zoom_slot)
    save_btn = (
        _status_zoom_save_btn_active_update(saved=False)
        if slot >= 0
        else _status_zoom_save_btn_placeholder_update()
    )
    return (
        show,
        gr.update(visible=show),
        edit_btn,
        *slider_updates,
        *_status_panel_levels_update(slot, dials=dials, visible=not show),
        save_btn,
        False,
    )


def _status_zoom_save_preset(
    zoom_slot: int,
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
    deform_pressure: float,
    view_elev: float,
    view_azim: float,
) -> tuple:
    """Persist edited dial values, then collapse the edit drawer back into the Edit tab."""
    slot = int(zoom_slot)
    if slot < 0:
        return tuple(gr.skip() for _ in range(18))
    dials = _gravity_dial_bundle(
        phi_sq_scale,
        e_sq_scale,
        pi_sq_scale,
        kappa,
        delta_z,
        alpha,
        beta,
        deform_pressure,
        view_elev,
        view_azim,
    )
    _GRAVITY_PRESET_PROFILES[slot] = dict(dials)
    slider_updates = _gravity_slider_control_updates(dials, edit_enabled=False)
    saved_btn = _status_zoom_save_btn_active_update(saved=True)
    return (
        *_status_panel_levels_update(slot, dials=dials, visible=True),
        saved_btn,
        False,
        gr.update(visible=False),
        _status_zoom_nav_edit_btn_update(in_zoom=True, edit_open=False),
        *slider_updates,
        True,
    )


def _status_zoom_manual_refresh(
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
    deform_pressure: float,
    view_elev: float,
    view_azim: float,
    zoom_slot: int,
    edit_open: bool,
) -> tuple:
    if not edit_open:
        return gr.skip(), gr.skip(), gr.skip(), *_unlatch_save_button()
    dials = _gravity_dial_bundle(
        phi_sq_scale,
        e_sq_scale,
        pi_sq_scale,
        kappa,
        delta_z,
        alpha,
        beta,
        deform_pressure,
        view_elev,
        view_azim,
    )
    return (
        *_status_panel_levels_update(int(zoom_slot), dials=dials, visible=False),
        *_unlatch_save_button(),
    )


def _format_gravity_preset_tui_html(
    active_slot: int,
    dials: dict[str, float],
    *,
    status_label: str | None = None,
    key_metrics: dict[str, float | int | str | None] | None = None,
    tui_state: dict[str, object] | None = None,
) -> str:
    if active_slot == 0 and key_metrics is None and status_label is None:
        return _format_gravity_menu_tui_html(tui_state=tui_state, active_slot=0)
    state = _coerce_gravity_tui_state(tui_state)
    focus = state["focus"]
    scroll_px = state["scroll"]
    status = _gravity_tui_status_label(
        active_slot,
        status_label=status_label,
        key_metrics=key_metrics,
    )
    body = "\n".join(
        _gravity_tui_preset_lines(focus=focus, active_slot=active_slot)
    ).rstrip()
    return (
        f'{_gravity_tui_viewport_open(scroll_px)}'
        '<div class="myst-preset-tui-serial">'
        f'<div class="myst-preset-tui-status"><u>ACTIVE STATUS: {status}</u></div>'
        f'<pre class="myst-preset-tui-lines">{body}</pre>'
        "</div></div>"
    )


def _gravity_tui_for_preset(
    active_slot: int,
    dials: dict[str, float],
    *,
    status_label: str | None = None,
    key_metrics: dict[str, float | int | str | None] | None = None,
    tui_state: dict[str, object] | None = None,
) -> str:
    state = _coerce_gravity_tui_state(tui_state)
    if key_metrics is not None or status_label is not None:
        return _format_gravity_preset_tui_html(
            active_slot,
            dials,
            status_label=status_label,
            key_metrics=key_metrics,
            tui_state=state,
        )
    if int(active_slot) > 0 and str(state.get("menu")) != "pipeline":
        return _format_gravity_preset_tui_html(active_slot, dials, tui_state=state)
    return _format_gravity_menu_tui_html(tui_state=state, active_slot=active_slot)


def _gravity_tui_nav_apply(
    direction: str,
    tui_state: dict[str, object] | None,
    *,
    active_slot: int,
    dials: dict[str, float],
    active_nav: str,
) -> tuple[str, dict[str, object], tuple]:
    state = _coerce_gravity_tui_state(tui_state)
    menu = str(state["menu"])
    focus = int(state["focus"])
    if direction in {"up", "left"}:
        focus = max(0, focus - 1)
    elif direction in {"down", "right"}:
        focus_max = (
            _GRAVITY_MAIN_MENU_FOCUS_MAX
            if menu == "main"
            else _GRAVITY_TUI_MENU_FOCUS_MAX
        )
        focus = min(focus_max, focus + 1)
    state["focus"] = focus
    tui = _gravity_tui_for_preset(int(active_slot), dials, tui_state=state)
    return tui, state, _gravity_keypad_btn_updates(active_numeric=str(active_slot), active_nav=active_nav)


def figure_to_viewport_file_html(path: str, *, png_bytes: int | None = None) -> str:
    """Clean gr.HTML with Gradio-served /gradio_api/file= image path."""
    if not path or not os.path.exists(path):
        return "<div style='color:red;padding:20px;'>Image file not found</div>"
    size = png_bytes if png_bytes is not None else os.path.getsize(path)
    html = (
        '<div id="unit-cell-main-view" class="myst-unit-cell-viewport-inner" '
        'style="height:100% !important;width:100% !important;max-width:100% !important;'
        'min-height:100% !important;background:#000000;display:flex !important;'
        'align-items:center !important;justify-content:center !important;'
        'overflow:hidden !important;box-sizing:border-box !important;">'
        f'<img src="/gradio_api/file={path}" '
        'style="max-width:100% !important;max-height:100% !important;'
        'object-fit:contain !important;display:block !important;" '
        'alt="Unit cell viewport" loading="eager" decoding="sync" />'
        "</div>"
    )
    print(
        f"[DEBUG] Returning HTML len={len(html)} png_bytes={size} path={path}",
        flush=True,
    )
    return html


def figure_to_render_grid_viewport_html(path: str, *, png_bytes: int | None = None) -> str:
    """Stretch-filled viewport img for Render tab 3×3 grid cells (no centering)."""
    if not path or not os.path.exists(path):
        return "<div style='color:red;padding:20px;'>Image file not found</div>"
    size = png_bytes if png_bytes is not None else os.path.getsize(path)
    html = (
        '<div class="myst-unit-cell-viewport-inner myst-render-grid-viewport" '
        'style="height:100% !important;width:100% !important;max-width:100% !important;'
        'min-height:9rem !important;background:#000000;display:block !important;'
        'overflow:hidden !important;box-sizing:border-box !important;margin:0 !important;'
        'padding:0 !important;">'
        f'<img src="/gradio_api/file={path}" '
        'style="width:100% !important;height:100% !important;min-height:8rem !important;'
        'max-width:100% !important;max-height:100% !important;'
        'object-fit:contain !important;display:block !important;margin:0 !important;" '
        'alt="Unit cell viewport" loading="eager" />'
        "</div>"
    )
    print(
        f"[DEBUG] Returning render grid HTML len={len(html)} png_bytes={size} path={path}",
        flush=True,
    )
    return html


def _gravity_fig_to_viewport_file_html(fig: plt.Figure, *, dpi: int) -> str:
    """savefig → save_file_to_cache → gr.HTML img (HF Spaces-safe)."""
    from gradio.processing_utils import save_file_to_cache
    from gradio.utils import get_upload_folder

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir="/tmp") as tmp:
        tmp_path = tmp.name
    try:
        fig.savefig(
            tmp_path,
            format="png",
            dpi=dpi,
            facecolor="#000000",
            bbox_inches="tight",
            pad_inches=0.05,
        )
    finally:
        plt.close(fig)
    png_bytes = os.path.getsize(tmp_path)
    print(
        f"[DEBUG] Saved PNG: {tmp_path} (exists={os.path.exists(tmp_path)}, "
        f"bytes={png_bytes})",
        flush=True,
    )
    served_path = save_file_to_cache(tmp_path, get_upload_folder())
    return figure_to_viewport_file_html(served_path, png_bytes=png_bytes)


def _gravity_fig_to_render_grid_file_html(fig: plt.Figure, *, dpi: int) -> str:
    """savefig → cache → stretch-filled grid cell img (Render tab 3×3)."""
    from gradio.processing_utils import save_file_to_cache
    from gradio.utils import get_upload_folder

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir="/tmp") as tmp:
        tmp_path = tmp.name
    try:
        fig.savefig(
            tmp_path,
            format="png",
            dpi=dpi,
            facecolor="#000000",
            bbox_inches="tight",
            pad_inches=0.02,
        )
    finally:
        plt.close(fig)
    png_bytes = os.path.getsize(tmp_path)
    served_path = save_file_to_cache(tmp_path, get_upload_folder())
    return figure_to_render_grid_viewport_html(served_path, png_bytes=png_bytes)


def _gravity_static_image_update(fig: object) -> object:
    """gr.HTML + /gradio_api/file= PNG (HF and local)."""
    if fig is gr.skip():
        print("[DEBUG] _gravity_static_image_update: gr.skip()", flush=True)
        return gr.skip()
    return _gravity_fig_to_viewport_file_html(fig, dpi=_UNIT_CELL_IMAGE_DPI)


def _gravity_viewport_error_placeholder() -> object:
    if is_hf_space():
        return (
            '<div class="myst-unit-cell-viewport-inner myst-unit-cell-viewport-error" '
            'style="width:100%;max-width:550px;height:550px;background:#b40000;'
            'display:flex;align-items:center;justify-content:center;color:#fff;">'
            "Viewport render error"
            "</div>"
        )
    return unit_cell_error_placeholder_html()


def _gravity_clear_video_update() -> dict:
    return gr.update(value=None)


def _gravity_load_video_update(video_path: str) -> dict:
    return gr.update(value=video_path, autoplay=True, loop=True)


def _run_residual_explorer_ui(
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
    deform_pressure: float,
    view_elev: float,
    view_azim: float,
    active_preset: int,
    status_zoom_slot: int,
) -> tuple:
    metrics, header, fig = run_residual_explorer(
        phi_sq_scale,
        e_sq_scale,
        pi_sq_scale,
        kappa,
        delta_z,
        alpha,
        beta,
        deform_pressure,
        view_elev,
        view_azim,
    )
    dials = _gravity_dial_bundle(
        phi_sq_scale,
        e_sq_scale,
        pi_sq_scale,
        kappa,
        delta_z,
        alpha,
        beta,
        deform_pressure,
        view_elev,
        view_azim,
    )
    slot = int(active_preset)
    tui = _gravity_tui_for_preset(slot, dials)
    control_levels = _format_gravity_control_panel_html(dials, slot)
    zoom_slot = int(status_zoom_slot)
    status_panel = _status_panel_html(
        zoom_slot,
        grid_active_slot=slot,
        dials=_gravity_preset_dials_for_slot(zoom_slot) if zoom_slot >= 0 else None,
    )
    print(f"[DEBUG] _run_residual_explorer_ui: preset={slot}", flush=True)
    return (
        metrics,
        metrics,
        header,
        *_demo_viewport_show_breathing_video(),
        _gravity_clear_video_update(),
        control_levels,
        gr.skip(),
        gr.update(value=status_panel),
        gr.skip(),
        tui,
    )


def _run_residual_explorer_ui_manual(
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
    deform_pressure: float,
    view_elev: float,
    view_azim: float,
    active_preset: int,
    status_zoom_slot: int,
    edit_params_enabled: bool,
) -> tuple:
    """Manual dial refresh — only when Manual Edit is latched (avoids preset cascade)."""
    if not edit_params_enabled:
        return tuple(gr.skip() for _ in range(11))
    print("[DEBUG] _run_residual_explorer_ui_manual: manual dial release", flush=True)
    return _run_residual_explorer_ui(
        phi_sq_scale,
        e_sq_scale,
        pi_sq_scale,
        kappa,
        delta_z,
        alpha,
        beta,
        deform_pressure,
        view_elev,
        view_azim,
        active_preset,
        status_zoom_slot,
    )


def _gravity_preset_btn_classes(key: str, active: str) -> list[str]:
    classes = ["vqc-receiver-preset", "myst-gravity-quick-preset"]
    if key == active:
        classes.append("active")
    return classes


def _gravity_preset_btn_updates(active: str = "") -> tuple:
    return _gravity_keypad_btn_updates(active_numeric=active)


def _gravity_preset_btn_immediate_active(active_key: str) -> tuple:
    """Flash matrix-green active state on the clicked preset before heavy work."""
    return _gravity_preset_btn_updates(active_key)


def _gravity_preset_click_immediate(slot: int) -> tuple:
    print(f"[DEBUG] preset_click_immediate: slot={slot}", flush=True)
    return (
        *_gravity_preset_btn_immediate_active(str(slot)),
        gr.skip(),
        _gravity_clear_video_update(),
    )


def _gravity_animate_btn_immediate() -> tuple:
    return (
        *_gravity_preset_btn_updates(),
        gr.skip(),
        _gravity_clear_video_update(),
    )


def _gravity_edit_params_btn_update(enabled: bool) -> dict:
    classes = [
        "vqc-receiver-preset",
        "myst-gravity-edit-params-btn",
        "vqc-full-width",
    ]
    if enabled:
        classes.append("active")
    return gr.update(elem_classes=classes, variant="secondary")


def _gravity_slider_control_updates(
    dials: dict[str, float] | None,
    *,
    edit_enabled: bool,
) -> tuple:
    keys = ("phi", "e", "pi", "kappa", "dz", "alpha", "beta", "pressure", "elev", "azim")
    if dials is None:
        return tuple(gr.update(interactive=edit_enabled) for _ in keys)
    return tuple(
        gr.update(value=float(dials[key]), interactive=edit_enabled) for key in keys
    )


def _gravity_edit_params_toggle(enabled: bool) -> tuple:
    new_state = not bool(enabled)
    btn_update = _gravity_edit_params_btn_update(new_state)
    slider_updates = _gravity_slider_control_updates(None, edit_enabled=new_state)
    return (
        new_state,
        btn_update,
        *slider_updates,
        btn_update,
        *slider_updates,
    )


def _gravity_explorer_outputs(
    active_key: str,
    dials: dict[str, float],
    metrics: str,
    header: str,
    fig: object,
    video_update: dict,
    tui: str,
    active_slot: int,
    status_zoom_slot: int,
    *,
    edit_params_enabled: bool = False,
    update_image: bool = True,
) -> tuple:
    image_out = _gravity_static_image_update(fig) if update_image else gr.skip()
    edit_btn = _gravity_edit_params_btn_update(edit_params_enabled)
    slider_updates = _gravity_slider_control_updates(
        dials, edit_enabled=edit_params_enabled
    )
    control_levels = _format_gravity_control_panel_html(dials, active_slot)
    zoom_slot = int(status_zoom_slot)
    status_panel = _status_panel_html(
        zoom_slot,
        grid_active_slot=active_slot,
        dials=_gravity_preset_dials_for_slot(zoom_slot) if zoom_slot >= 0 else None,
    )
    child_active = int(active_slot) if 0 <= int(active_slot) < len(_GRAVITY_CHILD_NAV_LETTERS) else -1
    return (
        *_gravity_preset_btn_updates(active_key),
        *_gravity_child_nav_output_updates(child_active),
        edit_btn,
        edit_btn,
        *slider_updates,
        *slider_updates,
        metrics,
        metrics,
        header,
        image_out,
        video_update,
        control_levels,
        gr.skip(),
        gr.update(value=status_panel),
        gr.skip(),
        tui,
        active_slot,
    )


def _gravity_animation_render_outputs(
    active_key: str,
    dials: dict[str, float],
    metrics: str,
    header: str,
    video_update: dict,
    tui: str,
    active_slot: int,
    status_zoom_slot: int,
    *,
    edit_params_enabled: bool = False,
) -> tuple:
    return _gravity_explorer_outputs(
        active_key,
        dials,
        metrics,
        header,
        gr.skip(),
        video_update,
        tui,
        active_slot,
        status_zoom_slot,
        edit_params_enabled=edit_params_enabled,
        update_image=False,
    )


def _gravity_animate_toggle_click(
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
    deform_pressure: float,
    view_elev: float,
    view_azim: float,
    active_preset: int,
    edit_params_enabled: bool,
    status_zoom_slot: int,
    progress: gr.Progress = gr.Progress(track_tqdm=False),
) -> tuple:
    dials = _gravity_dial_bundle(
        phi_sq_scale,
        e_sq_scale,
        pi_sq_scale,
        kappa,
        delta_z,
        alpha,
        beta,
        deform_pressure,
        view_elev,
        view_azim,
    )
    slot = int(active_preset)
    try:
        video_path, metrics, header, fig, key_metrics = render_unit_cell_deformation_video(
            phi_sq_scale,
            e_sq_scale,
            pi_sq_scale,
            kappa,
            delta_z,
            alpha,
            beta,
            deform_pressure,
            view_elev,
            view_azim,
            progress=progress,
        )
        plt.close(fig)
        dials["pressure"] = float(key_metrics["pressure"])
        tui = _gravity_tui_for_preset(slot, dials, key_metrics=key_metrics)
        anim_state = _coerce_gravity_tui_state(None)
        anim_state["menu"] = "preset_list"
        anim_state["focus"] = slot
        return _gravity_preset_handler_outputs(
            _gravity_animation_render_outputs(
                str(slot),
                dials,
                metrics,
                header,
                _gravity_load_video_update(video_path),
                tui,
                slot,
                status_zoom_slot,
                edit_params_enabled=bool(edit_params_enabled),
            ),
            menu_state=anim_state,
        )
    except Exception as exc:
        logger.exception("gravity animate render failed")
        err_tui = _gravity_tui_for_preset(slot, dials, status_label="ANIMATE ERROR")
        err_state = _coerce_gravity_tui_state(None)
        err_state["menu"] = "preset_list"
        err_state["focus"] = slot
        return _gravity_preset_handler_outputs(
            _gravity_animation_render_outputs(
                str(slot),
                dials,
                f"Animation error: {exc}",
                gr.skip(),
                _gravity_clear_video_update(),
                err_tui,
                slot,
                status_zoom_slot,
                edit_params_enabled=bool(edit_params_enabled),
            ),
            menu_state=err_state,
        )


def _gravity_pipeline_message(state: dict[str, object]) -> str:
    pipeline = list(state.get("pipeline", []))
    seq = (
        " → ".join(_gravity_preset_id(int(slot)) for slot in pipeline)
        if pipeline
        else "(empty)"
    )
    message = f"Sequence: {seq}"
    if len(pipeline) >= _GRAVITY_PIPELINE_SOFT_LIMIT:
        message += (
            f"\n(Soft limit {_GRAVITY_PIPELINE_SOFT_LIMIT} reached — "
            "continue or Green to finish)"
        )
    return message


def _gravity_menu_to_preset_outputs(
    tui: str,
    menu_state: dict[str, object],
    active_preset: int,
    *,
    active_numeric: str = "",
    active_nav: str = "",
) -> tuple:
    """Menu-only TUI refresh packed into gravity_preset_outputs shape."""
    child_active = (
        int(active_preset)
        if 0 <= int(active_preset) < len(_GRAVITY_CHILD_NAV_LETTERS)
        else -1
    )
    return _gravity_preset_handler_outputs(
        (
            *_gravity_keypad_btn_updates(
                active_numeric=active_numeric,
                active_nav=active_nav,
            ),
            *_gravity_child_nav_output_updates(child_active),
            gr.skip(),
            gr.skip(),
            *([gr.skip()] * 20),
            gr.skip(),
            gr.skip(),
            gr.skip(),
            gr.skip(),
            gr.skip(),
            gr.skip(),
            gr.skip(),
            gr.skip(),
            gr.skip(),
            tui,
            int(active_preset),
        ),
        menu_state=menu_state,
    )


def _gravity_keypad_enter_apply(
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
    deform_pressure: float,
    view_elev: float,
    view_azim: float,
    active_preset: int,
    edit_params_enabled: bool,
    status_zoom_slot: int,
    tui_state: object,
) -> tuple:
    """Green circle — confirm menu choice, preset, or pipeline digit."""
    state = _coerce_gravity_tui_state(tui_state)
    menu = str(state["menu"])
    dials = _gravity_dial_bundle(
        phi_sq_scale,
        e_sq_scale,
        pi_sq_scale,
        kappa,
        delta_z,
        alpha,
        beta,
        deform_pressure,
        view_elev,
        view_azim,
    )

    if menu == "main":
        action = _GRAVITY_MAIN_MENU_ITEMS[int(state["focus"])][0]
        if action == "preset_list":
            state["menu"] = "preset_list"
            state["focus"] = max(0, int(active_preset))
            state["message"] = "Select preset · Green loads · Red = main menu"
            tui = _format_gravity_preset_list_html(
                tui_state=state,
                active_slot=int(active_preset),
            )
            return _gravity_menu_to_preset_outputs(
                tui, state, int(active_preset), active_nav="enter"
            )
        if action == "animate":
            return _gravity_animate_toggle_click(
                phi_sq_scale,
                e_sq_scale,
                pi_sq_scale,
                kappa,
                delta_z,
                alpha,
                beta,
                deform_pressure,
                view_elev,
                view_azim,
                int(active_preset),
                edit_params_enabled,
                status_zoom_slot,
            )
        if action == "pipeline":
            state["menu"] = "pipeline"
            state["pipeline"] = []
            state["pending"] = ""
            state["message"] = (
                "Enter preset number + Green to add.\n"
                "Green (no pending) = finish. Red = cancel."
            )
            tui = _format_gravity_pipeline_menu_html(tui_state=state)
            return _gravity_menu_to_preset_outputs(
                tui, state, int(active_preset), active_nav="enter"
            )
        if action == "catalog":
            state["menu"] = "preset_list"
            state["focus"] = 0
            return _make_gravity_quick_preset_click(0, menu_state=state)(
                phi_sq_scale,
                e_sq_scale,
                pi_sq_scale,
                kappa,
                delta_z,
                alpha,
                beta,
                deform_pressure,
                view_elev,
                view_azim,
                active_preset,
                edit_params_enabled,
                status_zoom_slot,
            )

    if menu == "preset_list":
        slot = int(state["focus"])
        state["menu"] = "preset_list"
        return _make_gravity_quick_preset_click(slot, menu_state=state)(
            phi_sq_scale,
            e_sq_scale,
            pi_sq_scale,
            kappa,
            delta_z,
            alpha,
            beta,
            deform_pressure,
            view_elev,
            view_azim,
            active_preset,
            edit_params_enabled,
            status_zoom_slot,
        )

    if menu == "pipeline":
        pending = str(state.get("pending", "") or "").strip()
        if pending:
            try:
                slot = max(0, min(_GRAVITY_TUI_MENU_FOCUS_MAX, int(pending)))
            except ValueError:
                state["message"] = f"Invalid preset digit: {pending!r}"
                tui = _format_gravity_pipeline_menu_html(tui_state=state)
                return _gravity_menu_to_preset_outputs(
                    tui, state, int(active_preset), active_nav="enter"
                )
            pipeline = list(state.get("pipeline", []))
            pipeline.append(slot)
            state["pipeline"] = pipeline
            state["pending"] = ""
            state["message"] = _gravity_pipeline_message(state)
            tui = _format_gravity_pipeline_menu_html(tui_state=state)
            return _gravity_menu_to_preset_outputs(
                tui, state, int(active_preset), active_nav="enter"
            )
        pipeline = list(state.get("pipeline", []))
        if pipeline:
            state["message"] = (
                f"Pipeline ready ({len(pipeline)} presets) — "
                f"{' → '.join(_gravity_preset_id(int(s)) for s in pipeline)}\n"
                "(Stitched animation render — coming soon)"
            )
            tui = _format_gravity_pipeline_menu_html(tui_state=state)
            return _gravity_menu_to_preset_outputs(
                tui, state, int(active_preset), active_nav="enter"
            )
        state["message"] = "Add at least one preset before finishing."
        tui = _format_gravity_pipeline_menu_html(tui_state=state)
        return _gravity_menu_to_preset_outputs(
            tui, state, int(active_preset), active_nav="enter"
        )

    slot = int(state["focus"])
    return _make_gravity_quick_preset_click(slot, menu_state=state)(
        phi_sq_scale,
        e_sq_scale,
        pi_sq_scale,
        kappa,
        delta_z,
        alpha,
        beta,
        deform_pressure,
        view_elev,
        view_azim,
        active_preset,
        edit_params_enabled,
        status_zoom_slot,
    )


def _make_gravity_keypad_nav_click(direction: str):
    def handler(
        phi_sq_scale: float,
        e_sq_scale: float,
        pi_sq_scale: float,
        kappa: float,
        delta_z: float,
        alpha: float,
        beta: float,
        deform_pressure: float,
        view_elev: float,
        view_azim: float,
        active_preset: object,
        tui_state: object,
    ) -> tuple:
        preset_slot = _coerce_active_preset(active_preset)
        dials = _gravity_dial_bundle(
            phi_sq_scale,
            e_sq_scale,
            pi_sq_scale,
            kappa,
            delta_z,
            alpha,
            beta,
            deform_pressure,
            view_elev,
            view_azim,
        )
        tui, state, keypad_updates = _gravity_tui_nav_apply(
            direction,
            tui_state,
            active_slot=preset_slot,
            dials=dials,
            active_nav=direction,
        )
        return _gravity_menu_to_preset_outputs(
            tui,
            state,
            preset_slot,
            active_nav=direction,
        )

    return handler


def _gravity_keypad_stop_apply(
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
    deform_pressure: float,
    view_elev: float,
    view_azim: float,
    active_preset: int,
    edit_params_enabled: bool,
    status_zoom_slot: int,
    tui_state: object,
) -> tuple:
    """Red circle — cancel pipeline / back to main / stop animation."""
    state = _coerce_gravity_tui_state(tui_state)
    menu = str(state["menu"])

    if menu == "pipeline":
        state = _default_gravity_tui_state()
        state["message"] = "Pipeline cancelled."
        tui = _format_gravity_main_menu_html(tui_state=state)
        return _gravity_menu_to_preset_outputs(
            tui, state, int(active_preset), active_nav="stop"
        )

    if menu == "preset_list":
        state = _default_gravity_tui_state()
        state["message"] = "Returned to main menu."
        tui = _format_gravity_main_menu_html(tui_state=state)
        return _gravity_menu_to_preset_outputs(
            tui, state, int(active_preset), active_nav="stop"
        )

    dials, metrics, header, fig, tui, active_slot = _gravity_quick_preset_apply(
        0,
        phi_sq_scale,
        e_sq_scale,
        pi_sq_scale,
        kappa,
        delta_z,
        alpha,
        beta,
        deform_pressure,
        view_elev,
        view_azim,
    )
    reset_state = _default_gravity_tui_state()
    reset_state["message"] = "Animation stopped · catalog reset."
    tui = _format_gravity_main_menu_html(tui_state=reset_state)
    outputs = list(
        _gravity_explorer_outputs(
            "0",
            dials,
            metrics,
            header,
            fig,
            _gravity_clear_video_update(),
            tui,
            active_slot,
            status_zoom_slot,
            edit_params_enabled=edit_params_enabled,
            update_image=fig is not None,
        )
    )
    keypad_len = len(_GRAVITY_KEYPAD_ALL_KEYS)
    outputs[:keypad_len] = list(
        _gravity_keypad_btn_updates(active_numeric="0", active_nav="stop")
    )
    return _gravity_preset_handler_outputs(tuple(outputs), menu_state=reset_state)


def _gravity_quick_preset_apply(
    slot: int,
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
    deform_pressure: float,
    view_elev: float,
    view_azim: float,
) -> tuple[dict[str, float], str, str, object, str, int]:
    if 0 <= slot < _STATUS_GRID_PRESET_COUNT:
        dials = _render_preset_dials_for_slot(slot)
    elif slot in _GRAVITY_PRESET_PROFILES:
        dials = dict(_GRAVITY_PRESET_PROFILES[slot])
    else:
        dials = _gravity_dial_bundle(
            phi_sq_scale,
            e_sq_scale,
            pi_sq_scale,
            kappa,
            delta_z,
            alpha,
            beta,
            deform_pressure,
            view_elev,
            view_azim,
        )
    metrics, header, fig = run_residual_explorer(
        dials["phi"],
        dials["e"],
        dials["pi"],
        dials["kappa"],
        dials["dz"],
        dials["alpha"],
        dials["beta"],
        dials["pressure"],
        dials["elev"],
        dials["azim"],
    )
    tui = _gravity_tui_for_preset(slot, dials)
    return dials, metrics, header, fig, tui, slot


def _make_gravity_keypad_digit_click(digit: int):
    """Numeric keypad — menu navigation, pipeline pending digit, or preset focus."""

    def handler(
        phi_sq_scale: float,
        e_sq_scale: float,
        pi_sq_scale: float,
        kappa: float,
        delta_z: float,
        alpha: float,
        beta: float,
        deform_pressure: float,
        view_elev: float,
        view_azim: float,
        active_preset: int,
        edit_params_enabled: bool,
        status_zoom_slot: int,
        tui_state: object,
    ) -> tuple:
        state = _coerce_gravity_tui_state(tui_state)
        menu = str(state["menu"])
        key = str(int(digit))
        dials = _gravity_dial_bundle(
            phi_sq_scale,
            e_sq_scale,
            pi_sq_scale,
            kappa,
            delta_z,
            alpha,
            beta,
            deform_pressure,
            view_elev,
            view_azim,
        )

        if menu == "pipeline":
            state["pending"] = key
            state["message"] = f"Pending: {key} — press Green to add to pipeline"
            tui = _format_gravity_pipeline_menu_html(tui_state=state)
            return _gravity_menu_to_preset_outputs(
                tui,
                state,
                int(active_preset),
                active_numeric=key,
            )

        if menu == "main":
            if key in {"1", "2", "3", "4"}:
                state["focus"] = int(key) - 1
            tui = _format_gravity_main_menu_html(tui_state=state)
            return _gravity_menu_to_preset_outputs(
                tui,
                state,
                int(active_preset),
                active_numeric=key,
            )

        state["menu"] = "preset_list"
        state["focus"] = max(0, min(_GRAVITY_TUI_MENU_FOCUS_MAX, int(digit)))
        tui = _format_gravity_preset_list_html(
            tui_state=state,
            active_slot=int(active_preset),
        )
        return _gravity_menu_to_preset_outputs(
            tui,
            state,
            int(active_preset),
            active_numeric=key,
        )

    return handler


def _make_gravity_quick_preset_click(
    slot: int,
    *,
    menu_state: dict[str, object] | None = None,
):
    """Single-step preset handler — updates buttons, sliders, metrics, image, TUI."""

    def handler(
        phi_sq_scale: float,
        e_sq_scale: float,
        pi_sq_scale: float,
        kappa: float,
        delta_z: float,
        alpha: float,
        beta: float,
        deform_pressure: float,
        view_elev: float,
        view_azim: float,
        _active_preset: int,
        edit_params_enabled: bool,
        status_zoom_slot: int,
    ):
        print(f"[DEBUG] preset_click_unified ENTER slot={slot}", flush=True)
        print(
            f"[DEBUG] preset_click_unified inputs: elev={view_elev} azim={view_azim} "
            f"active_preset={_active_preset}",
            flush=True,
        )
        try:
            dials, metrics, header, fig, tui, active_slot = _gravity_quick_preset_apply(
                slot,
                phi_sq_scale,
                e_sq_scale,
                pi_sq_scale,
                kappa,
                delta_z,
                alpha,
                beta,
                deform_pressure,
                view_elev,
                view_azim,
            )
            print("[DEBUG] preset_click_unified: run_residual_explorer ok", flush=True)
        except Exception as exc:
            print(f"[ERROR] preset_click_unified: apply failed: {exc}", flush=True)
            traceback.print_exc()
            logger.exception("gravity preset apply failed for slot=%s", slot)
            dials = dict(_GRAVITY_HOME_DIALS)
            metrics = f"Preset error: {exc}"
            header = gr.skip()
            fig = None
            tui = _gravity_tui_for_preset(slot, dials, status_label="PRESET ERROR")
            active_slot = slot
        outputs = _gravity_explorer_outputs(
            str(active_slot),
            dials,
            metrics,
            header,
            fig,
            _gravity_clear_video_update(),
            tui,
            active_slot,
            status_zoom_slot,
            edit_params_enabled=edit_params_enabled,
            update_image=fig is not None,
        )
        if fig is None:
            outputs = list(outputs)
            outputs[_GRAVITY_PRESET_IMAGE_OUT_INDEX] = _gravity_viewport_error_placeholder()
        image_out = outputs[_GRAVITY_PRESET_IMAGE_OUT_INDEX]
        if hasattr(image_out, "shape"):
            print(
                f"[DEBUG] preset_click_unified: Returning numpy shape={image_out.shape}",
                flush=True,
            )
        elif hasattr(image_out, "size"):
            print(
                f"[DEBUG] preset_click_unified: Returning PIL size={image_out.size}",
                flush=True,
            )
        elif isinstance(image_out, str):
            print(
                f"[DEBUG] preset_click_unified: Returning html len={len(image_out)}",
                flush=True,
            )
        else:
            print(
                f"[DEBUG] preset_click_unified: image_out={image_out!r}",
                flush=True,
            )
        print(f"[DEBUG] preset_click_unified EXIT slot={slot}", flush=True)
        resolved_state = _coerce_gravity_tui_state(menu_state)
        resolved_state["menu"] = "preset_list"
        resolved_state["focus"] = int(active_slot)
        return _gravity_preset_handler_outputs(
            tuple(outputs) if isinstance(outputs, list) else outputs,
            menu_state=resolved_state,
        )

    return handler


def build_app() -> gr.Blocks:
    for static_dir in wallpaper_static_paths():
        gr.set_static_paths(paths=[str(static_dir)])
    with gr.Blocks(
        title="Mystery — φ · e · π Emergent Signature",
        analytics_enabled=False,
        theme=_build_vqc_theme(),
        head=WALLPAPER_HEAD,
        css=HFB_CSS,
        fill_width=True,
        fill_height=True,
    ) as demo:
        current_page = gr.State("home")
        newhere_open = gr.State(False)
        claims_open = gr.State(False)
        with gr.Column(visible=False, elem_classes=["vqc-links-panel"]) as panel_claims:
            with gr.Row(elem_classes=["vqc-panel-header-row"]):
                gr.Markdown("### How this maps to Mystery probes")
                claims_minimize_btn = gr.Button(
                    "▲",
                    elem_classes=["vqc-panel-minimize"],
                    scale=0,
                    variant="secondary",
                )
            gr.Markdown(CLAIMS_MD)
        with gr.Column(visible=False, elem_classes=["vqc-links-panel"]) as panel_newhere:
            with gr.Row(elem_classes=["vqc-panel-header-row"]):
                gr.Markdown("### New here? 60-second guide (φ-e-π emergent signature)")
                newhere_minimize_btn = gr.Button(
                    "▲",
                    elem_classes=["vqc-panel-minimize"],
                    scale=0,
                    variant="secondary",
                )
            gr.Markdown(ONBOARDING_MD)
        with gr.Column(visible=False, elem_classes=["myst-gravity-wired-hidden"]):
            tab_claims_btn = gr.Button(
                "Claims",
                elem_classes=["vqc-source-tab"],
                variant="secondary",
            )
            tab_newhere_btn = gr.Button(
                "New here?",
                elem_classes=["vqc-source-tab"],
                variant="secondary",
            )

        active_shape = gr.State(_DEFAULT_ACTIVE_SHAPE)
        with gr.Column(elem_classes=["myst-unified-nav-host"], scale=0):
            unified_nav = _place_unified_main_nav(
                active_page="home",
                default_shape=_DEFAULT_ACTIVE_SHAPE,
            )
            _add_gap_row(slot="after-main-nav")
            with gr.Column(
                visible=True,
                elem_id="myst-home-demo-nav-section",
                elem_classes=["myst-home-demo-nav-section", "myst-force-visible"],
            ) as home_demo_nav_section:
                gravity_child_nav = _place_gravity_child_nav_row()

        _init_re_metrics, _init_unit_cell_header, _init_unit_cell_fig = run_residual_explorer(
            1.0, 1.0, 1.0, KAPPA_DOC, 0.1, 1.0, 1.0, 0.35, 22.0, 45.0
        )
        _init_unit_cell_html = _gravity_fig_to_viewport_file_html(
            _init_unit_cell_fig,
            dpi=_UNIT_CELL_IMAGE_DPI,
        )
        _init_preset_tui = _format_gravity_menu_tui_html()
        _init_control_levels = _format_gravity_control_panel_html(_GRAVITY_HOME_DIALS, 0)
        _init_status_panel = _format_gravity_status_grid_html(active_slot=None)
        _init_render_panel = _format_render_grid_html()

        readme_return_page = gr.State("home")
        with gr.Column(visible=False, elem_classes=["myst-readme-page"]) as page_readme:
            _add_gap_row(slot="before-docs-content")
            with gr.Row(elem_classes=["myst-readme-back-row"]):
                readme_back_btn = _place_back_button("← Back to App", min_width=110)
            with gr.Column(
                elem_classes=[
                    "myst-readme-body",
                    "myst-readme-scrollable-content",
                    "myst-scrollable-panel",
                ],
                elem_id="readme-scroll-container",
            ):
                gr.HTML(build_readme_full_page_html())

        render_active_slot = gr.State(-1)
        render_zoom_slot = gr.State(-1)
        render_plot_cache = gr.State([None] * _STATUS_GRID_PRESET_COUNT)
        with gr.Column(visible=False, elem_classes=["myst-render-page"]) as page_render:
            with gr.Column(visible=True, elem_classes=["myst-render-stack"]) as render_content_col:
                _render_sub_nav = _place_render_sub_nav_row(
                    active_slot=-1,
                    zoom_slot=-1,
                )
                _add_gap_row(slot="before-render-btn")
                with gr.Row(elem_classes=["myst-render-action-row"]):
                    render_all_btn = _nav_theme_button(
                        "Render",
                        elem_id="myst-render-nav-render-btn",
                        elem_classes=[
                            "vqc-source-tab",
                            "demo-btn",
                            "myst-status-preset-btn",
                            "myst-render-nav-render-btn",
                            "full-width-btn",
                        ],
                    )
                _add_gap_row(slot="after-render-btn")
                render_sub_nav_btns = [
                    _render_sub_nav[str(i)] for i in range(_STATUS_ZOOM_PRESET_COUNT)
                ]
                with gr.Column(visible=False, elem_classes=["myst-gravity-wired-hidden"]):
                    render_cell_btns = [
                        gr.Button(
                            f"open_{slot}",
                            elem_id=f"myst-render-cell-btn-{slot}",
                            visible=False,
                        )
                        for slot in range(_STATUS_ZOOM_PRESET_COUNT)
                    ]
                with gr.Column(
                    visible=True,
                    elem_classes=["myst-render-catalog-host"],
                ) as render_catalog_col:
                    render_panel_html = gr.HTML(
                        _init_render_panel,
                        elem_id="myst-render-grid-host",
                        elem_classes=[
                            "myst-gravity-control-levels-wrap",
                            "myst-render-panel-host",
                            "myst-render-grid-host",
                        ],
                    )
                render_detail_slot = gr.State(-1)
                with gr.Column(
                    visible=False,
                    elem_id="myst-render-detail-wrapper",
                    elem_classes=["myst-render-detail-wrapper", "myst-render-detail-view"],
                ) as render_detail_col:
                    with gr.Row(
                        elem_classes=["myst-render-split-row"],
                        equal_height=True,
                    ):
                        with gr.Column(
                            scale=1,
                            min_width=280,
                            elem_classes=["myst-render-left-panel"],
                        ):
                            gr.HTML(
                                "<div class='myst-render-panel-header'>Preset Details</div>"
                            )
                            render_detail_description = gr.Markdown(
                                elem_classes=["myst-render-verbose-desc"],
                                container=True,
                            )
                        with gr.Column(
                            scale=2,
                            min_width=560,
                            elem_classes=["myst-render-right-panel"],
                        ):
                            render_detail_plot = gr.Plot(
                                label="",
                                show_label=False,
                                container=True,
                                elem_id="myst-render-detail-plot",
                                elem_classes=["myst-render-detail-plot"],
                            )
                    with gr.Row(elem_classes=["myst-render-detail-actions"]):
                        render_detail_zoom_in_btn = gr.Button(
                            "Zoom +",
                            scale=0,
                            elem_id="myst-render-detail-zoom-in",
                        )
                        render_detail_zoom_out_btn = gr.Button(
                            "Zoom −",
                            scale=0,
                            elem_id="myst-render-detail-zoom-out",
                        )
                        render_detail_reset_btn = gr.Button(
                            "Reset View",
                            scale=0,
                            elem_id="myst-render-detail-reset",
                        )
                        render_detail_download_btn = gr.Button(
                            "Download PNG",
                            scale=0,
                            elem_id="myst-render-detail-download",
                        )
                        render_detail_fullscreen_btn = gr.Button(
                            "Fullscreen",
                            scale=0,
                            elem_id="myst-render-detail-fullscreen",
                        )

        status_content_open = gr.State(True)
        with gr.Column(visible=False, elem_classes=["myst-status-page"]) as page_status:
            status_zoom_slot = gr.State(-1)
            status_zoom_edit_open = gr.State(False)
            save_button_state = gr.State(False)
            with gr.Column(visible=True, elem_classes=["myst-status-stack"]) as status_content_col:
                _status_zoom_nav = _place_status_zoom_nav_row(active_slot=-1)
                _add_gap_row(slot="after-demo-nav")
                status_zoom_save_btn, status_zoom_edit_btn = _place_status_save_edit_row()
                _add_gap_row(slot="after-save-edit")
                status_zoom_btns = [
                    _status_zoom_nav[str(i)] for i in range(_STATUS_ZOOM_PRESET_COUNT)
                ]
                with gr.Column(elem_classes=["myst-status-panels-host"]) as status_panels_host:
                    with gr.Column(
                        visible=False,
                        elem_classes=[
                            "myst-status-zoom-edit-drawer",
                            "myst-gravity-control-panel",
                        ],
                        ) as status_zoom_edit_drawer:
                        with gr.Column(
                            elem_classes=[
                                "myst-status-zoom-edit-col",
                                "vqc-optics-panel",
                            ],
                        ):
                            with gr.Row(elem_classes=["slider-row"]):
                                sz_pressure = gr.Slider(
                                    0.0,
                                    1.0,
                                    value=0.35,
                                    step=0.01,
                                    label="01 · Deformation pressure",
                                    elem_classes=["vqc-optics-dial-wrap"],
                                    interactive=True,
                                )
                            with gr.Row(elem_classes=["slider-row"]):
                                sz_phi_scale = gr.Slider(
                                    0.90,
                                    1.10,
                                    value=1.0,
                                    step=0.001,
                                    label="02 · Φ² scale",
                                    elem_id="myst-status-slider-02",
                                    elem_classes=["vqc-optics-dial-wrap"],
                                    interactive=True,
                                )
                            with gr.Row(elem_classes=["slider-row"]):
                                sz_e_scale = gr.Slider(
                                    0.90,
                                    1.10,
                                    value=1.0,
                                    step=0.001,
                                    label="03 · e² scale",
                                    elem_id="myst-status-slider-03",
                                    elem_classes=["vqc-optics-dial-wrap"],
                                    interactive=True,
                                )
                            with gr.Row(elem_classes=["slider-row"]):
                                sz_pi_scale = gr.Slider(
                                    0.90,
                                    1.10,
                                    value=1.0,
                                    step=0.001,
                                    label="04 · π² scale",
                                    elem_classes=["vqc-optics-dial-wrap"],
                                    interactive=True,
                                )
                            with gr.Row(elem_classes=["slider-row"]):
                                sz_kappa = gr.Slider(
                                    0.70,
                                    0.95,
                                    value=KAPPA_DOC,
                                    step=0.001,
                                    label="05 · κ (holonomy-gap parameter)",
                                    elem_classes=["vqc-optics-dial-wrap"],
                                    interactive=True,
                                )
                            with gr.Row(elem_classes=["slider-row"]):
                                sz_delta_z = gr.Slider(
                                    0.0,
                                    0.5,
                                    value=0.1,
                                    step=0.01,
                                    label="06 · δ_z (primary push)",
                                    elem_classes=["vqc-optics-dial-wrap"],
                                    interactive=True,
                                )
                            with gr.Row(elem_classes=["slider-row"]):
                                sz_alpha = gr.Slider(
                                    0.0,
                                    2.0,
                                    value=1.0,
                                    step=0.05,
                                    label="07 · α (geometry factor)",
                                    elem_classes=["vqc-optics-dial-wrap"],
                                    interactive=True,
                                )
                            with gr.Row(elem_classes=["slider-row"]):
                                sz_beta = gr.Slider(
                                    0.0,
                                    2.0,
                                    value=1.0,
                                    step=0.05,
                                    label="08 · β (residual coupling)",
                                    elem_classes=["vqc-optics-dial-wrap"],
                                    interactive=True,
                                )
                            with gr.Row(elem_classes=["slider-row"]):
                                sz_view_elev = gr.Slider(
                                    5.0,
                                    75.0,
                                    value=22.0,
                                    step=1.0,
                                    label="09 · View elevation (°)",
                                    elem_classes=["vqc-optics-dial-wrap"],
                                    interactive=True,
                                )
                            with gr.Row(elem_classes=["slider-row"]):
                                sz_view_azim = gr.Slider(
                                    0.0,
                                    360.0,
                                    value=45.0,
                                    step=5.0,
                                    label="10 · View azimuth (°)",
                                    elem_classes=["vqc-optics-dial-wrap"],
                                    interactive=True,
                                )
                with gr.Column(
                    visible=True,
                    elem_classes=["myst-status-catalog-host"],
                ) as status_catalog_col:
                    status_panel_levels = gr.HTML(
                        _init_status_panel,
                        elem_id="myst-status-panel-host",
                        elem_classes=[
                            "myst-gravity-control-levels-wrap",
                            "myst-status-panel-host",
                            "myst-status-grid-host",
                        ],
                    )

        with gr.Column(visible=False, elem_classes=["myst-edit-page"]) as page_edit:
            with gr.Column(
                elem_classes=[
                    "vqc-optics-panel",
                    "vqc-gravity-panel",
                    "myst-gravity-left-frame",
                    "myst-gravity-panel-window",
                    "myst-gravity-control-panel",
                    "myst-edit-panel",
                ],
            ):
                with gr.Accordion(
                    "Manual Edit",
                    open=True,
                    elem_classes=[
                        "myst-gravity-controls-accordion",
                        "myst-gravity-manual-edit-accordion",
                    ],
                ):
                    gr.HTML(CONTROL_PANEL_HEADER_HTML)
                    edit_edit_params_btn = gr.Button(
                        "Manual Edit",
                        variant="secondary",
                        elem_classes=[
                            "vqc-receiver-preset",
                            "myst-gravity-edit-params-btn",
                            "vqc-full-width",
                        ],
                    )
                    with gr.Row(elem_classes=["vqc-optics-dial-row"]):
                        edit_re_pressure = gr.Slider(
                            0.0,
                            1.0,
                            value=0.35,
                            step=0.01,
                            label="Deformation pressure",
                            info="0 = rigid cube · 1 = full π bowl + φ/e concave pinch",
                            elem_classes=["vqc-optics-dial-wrap"],
                            interactive=False,
                        )
                    with gr.Row(elem_classes=["vqc-optics-dial-row"]):
                        edit_re_view_elev = gr.Slider(
                            5.0,
                            75.0,
                            value=22.0,
                            step=1.0,
                            label="View elevation (°)",
                            elem_classes=["vqc-optics-dial-wrap"],
                            interactive=False,
                        )
                        edit_re_view_azim = gr.Slider(
                            0.0,
                            360.0,
                            value=45.0,
                            step=5.0,
                            label="View azimuth (°)",
                            elem_classes=["vqc-optics-dial-wrap"],
                            interactive=False,
                        )
                    with gr.Row(elem_classes=["vqc-optics-dial-row"]):
                        edit_re_phi_scale = gr.Slider(
                            0.90,
                            1.10,
                            value=1.0,
                            step=0.001,
                            label="φ² scale",
                            elem_classes=["vqc-optics-dial-wrap"],
                            interactive=False,
                        )
                        edit_re_e_scale = gr.Slider(
                            0.90,
                            1.10,
                            value=1.0,
                            step=0.001,
                            label="e² scale",
                            elem_classes=["vqc-optics-dial-wrap"],
                            interactive=False,
                        )
                        edit_re_pi_scale = gr.Slider(
                            0.90,
                            1.10,
                            value=1.0,
                            step=0.001,
                            label="π² scale",
                            elem_classes=["vqc-optics-dial-wrap"],
                            interactive=False,
                        )
                    with gr.Row(elem_classes=["vqc-optics-dial-row"]):
                        edit_re_kappa = gr.Slider(
                            0.70,
                            0.95,
                            value=KAPPA_DOC,
                            step=0.001,
                            label="κ (holonomy-gap parameter)",
                            info=f"κ_doc = {KAPPA_DOC} · κ* nulls B(κ)−R",
                            elem_classes=["vqc-optics-dial-wrap"],
                            interactive=False,
                        )
                        edit_re_delta_z = gr.Slider(
                            0.0,
                            0.5,
                            value=0.1,
                            step=0.01,
                            label="δ_z (primary push)",
                            elem_classes=["vqc-optics-dial-wrap"],
                            interactive=False,
                        )
                    with gr.Row(elem_classes=["vqc-optics-dial-row"]):
                        edit_re_alpha = gr.Slider(
                            0.0,
                            2.0,
                            value=1.0,
                            step=0.05,
                            label="α (geometry factor)",
                            elem_classes=["vqc-optics-dial-wrap"],
                            interactive=False,
                        )
                        edit_re_beta = gr.Slider(
                            0.0,
                            2.0,
                            value=1.0,
                            step=0.05,
                            label="β (residual coupling)",
                            elem_classes=["vqc-optics-dial-wrap"],
                            interactive=False,
                        )
                    with gr.Column(elem_classes=["myst-gravity-metrics-inner"]):
                        edit_re_metrics = gr.Textbox(
                            label="Residual explorer",
                            lines=9,
                            interactive=False,
                            value=_init_re_metrics,
                        )

        with gr.Column(visible=True, elem_classes=["myst-gravity-page"], scale=1) as page_gravity:
            _add_gap_row(slot="after-demo-nav")
            gravity_letter_btns = {
                letter: gravity_child_nav[letter] for letter in _GRAVITY_CHILD_NAV_LETTERS
            }
            gravity_active_letter = gr.State("A")
            with gr.Column(
                elem_classes=["myst-gravity-single-viewport"],
                elem_id="myst-gravity-viewport-wrapper",
            ) as viewport_col:
                gravity_viewport_plot = gr.Plot(
                    value=_get_rigid_preset_plotly_figure(),
                    label="",
                    show_label=False,
                    container=True,
                    visible=True,
                    elem_id="myst-gravity-viewport-plot",
                    elem_classes=["myst-gravity-viewport-plot"],
                    scale=1,
                )
                gravity_viewport_video = gr.Video(
                    label="",
                    show_label=False,
                    visible=False,
                    autoplay=True,
                    loop=True,
                    height=620,
                    elem_id="myst-gravity-viewport",
                    elem_classes=["myst-gravity-viewport", "myst-gravity-demo-video"],
                    container=True,
                )
            with gr.Column(visible=False, elem_classes=["myst-gravity-wired-hidden"]):
                re_active_preset = gr.State(0)
                re_edit_params = gr.State(False)
                re_control_levels = gr.HTML(
                    _init_control_levels,
                    elem_classes=["myst-gravity-control-levels-wrap"],
                )
                re_preset_tui = gr.HTML(
                    _init_preset_tui,
                    elem_classes=["myst-gravity-preset-tui-wrap"],
                )
                unit_cell_header = gr.HTML(
                    _init_unit_cell_header,
                    elem_classes=["myst-cube-viewport-header-slot"],
                )
                unit_cell_video = gr.Video(
                    visible=False,
                    elem_id="unit-cell-animation",
                    elem_classes=["myst-unit-cell-animation"],
                )
                re_pressure = gr.Slider(-1.0, 1.0, value=0.35, step=0.01, visible=False)
                re_view_elev = gr.Slider(5.0, 75.0, value=22.0, step=1.0, visible=False)
                re_view_azim = gr.Slider(0.0, 360.0, value=45.0, step=5.0, visible=False)
                re_phi_scale = gr.Slider(0.90, 1.10, value=1.0, step=0.001, visible=False)
                re_e_scale = gr.Slider(0.90, 1.10, value=1.0, step=0.001, visible=False)
                re_pi_scale = gr.Slider(0.90, 1.10, value=1.0, step=0.001, visible=False)
                re_kappa = gr.Slider(0.70, 0.95, value=KAPPA_DOC, step=0.001, visible=False)
                re_delta_z = gr.Slider(0.0, 0.5, value=0.1, step=0.01, visible=False)
                re_alpha = gr.Slider(0.0, 2.0, value=1.0, step=0.05, visible=False)
                re_beta = gr.Slider(0.0, 2.0, value=1.0, step=0.05, visible=False)
                re_metrics = gr.Textbox(value=_init_re_metrics, visible=False)
            re_inputs = [
                re_phi_scale,
                re_e_scale,
                re_pi_scale,
                re_kappa,
                re_delta_z,
                re_alpha,
                re_beta,
                re_pressure,
                re_view_elev,
                re_view_azim,
            ]
            edit_re_inputs = [
                edit_re_phi_scale,
                edit_re_e_scale,
                edit_re_pi_scale,
                edit_re_kappa,
                edit_re_delta_z,
                edit_re_alpha,
                edit_re_beta,
                edit_re_pressure,
                edit_re_view_elev,
                edit_re_view_azim,
            ]
            re_outputs = [
                re_metrics,
                edit_re_metrics,
                unit_cell_header,
                gravity_viewport_plot,
                gravity_viewport_video,
                unit_cell_video,
                re_control_levels,
                status_catalog_col,
                status_panel_levels,
                status_panels_host,
                re_preset_tui,
            ]
            gravity_dial_inputs = [*re_inputs, re_active_preset, status_zoom_slot]
            gravity_demo_outputs = [
                gravity_viewport_plot,
                gravity_viewport_video,
                *[gravity_letter_btns[letter] for letter in _GRAVITY_CHILD_NAV_LETTERS],
                gravity_active_letter,
            ]
            for letter in _GRAVITY_CHILD_NAV_LETTERS:
                btn = gravity_letter_btns[letter]
                if letter == "A":
                    btn.click(
                        _launch_demo_a,
                        outputs=gravity_demo_outputs,
                        show_progress="hidden",
                    )
                else:
                    btn.click(
                        lambda l=letter: _switch_gravity_demo(l),
                        outputs=gravity_demo_outputs,
                        show_progress="hidden",
                    )

            sz_inputs = [
                sz_phi_scale,
                sz_e_scale,
                sz_pi_scale,
                sz_kappa,
                sz_delta_z,
                sz_alpha,
                sz_beta,
                sz_pressure,
                sz_view_elev,
                sz_view_azim,
            ]
            status_zoom_save_outputs = [
                status_catalog_col,
                status_panel_levels,
                status_panels_host,
                status_zoom_save_btn,
                status_zoom_edit_open,
                status_zoom_edit_drawer,
                status_zoom_edit_btn,
                *sz_inputs,
                save_button_state,
            ]
            status_zoom_select_outputs = [
                status_catalog_col,
                status_panel_levels,
                status_panels_host,
                *status_zoom_btns,
                status_zoom_slot,
                status_zoom_edit_open,
                status_zoom_edit_drawer,
                status_zoom_edit_btn,
                *sz_inputs,
                status_zoom_save_btn,
                save_button_state,
            ]
            save_unlatch_outputs = [status_zoom_save_btn, save_button_state]
            for slot, zoom_btn in enumerate(status_zoom_btns):
                zoom_btn.click(
                    lambda s=slot: _status_zoom_select(s),
                    outputs=status_zoom_select_outputs,
                    show_progress="hidden",
                )
            status_zoom_edit_outputs = [
                status_zoom_edit_open,
                status_zoom_edit_drawer,
                status_zoom_edit_btn,
                *sz_inputs,
                status_catalog_col,
                status_panel_levels,
                status_panels_host,
                status_zoom_save_btn,
                save_button_state,
            ]
            status_zoom_edit_inputs = [
                status_zoom_edit_open,
                status_zoom_slot,
                *sz_inputs,
            ]
            status_zoom_edit_btn.click(
                _status_zoom_edit_toggle,
                inputs=status_zoom_edit_inputs,
                outputs=status_zoom_edit_outputs,
                show_progress="hidden",
            )
            sz_manual_inputs = [*sz_inputs, status_zoom_slot, status_zoom_edit_open]
            for slider in sz_inputs:
                slider.change(
                    _unlatch_save_button,
                    outputs=save_unlatch_outputs,
                    show_progress="hidden",
                )
                slider.release(
                    _status_zoom_manual_refresh,
                    inputs=sz_manual_inputs,
                    outputs=[
                        status_catalog_col,
                        status_panel_levels,
                        status_panels_host,
                        *save_unlatch_outputs,
                    ],
                    show_progress="hidden",
                )
            status_zoom_save_inputs = [status_zoom_slot, *sz_inputs]
            status_zoom_save_btn.click(
                _status_zoom_save_preset,
                inputs=status_zoom_save_inputs,
                outputs=status_zoom_save_outputs,
                show_progress="hidden",
            )
            status_zoom_back_outputs = [
                status_catalog_col,
                status_panel_levels,
                status_panels_host,
                *status_zoom_btns,
                status_zoom_slot,
                status_zoom_edit_open,
                status_zoom_edit_drawer,
                status_zoom_edit_btn,
                *sz_inputs,
                status_zoom_save_btn,
                save_button_state,
            ]

        newhere_outputs = [panel_newhere, tab_newhere_btn, newhere_open, panel_claims, tab_claims_btn, claims_open]
        claims_outputs = [panel_claims, tab_claims_btn, claims_open, panel_newhere, tab_newhere_btn, newhere_open]
        shape_outputs = [
            active_shape,
            *[unified_nav[shape_id] for shape_id in _SHAPE_NAV_IDS],
        ]
        nav_outputs = [
            page_gravity,
            page_render,
            page_readme,
            page_status,
            page_edit,
            unified_nav["home"],
            unified_nav["render"],
            unified_nav["readme"],
            unified_nav["status"],
            panel_newhere,
            tab_newhere_btn,
            newhere_open,
            panel_claims,
            tab_claims_btn,
            claims_open,
            current_page,
        ]
        readme_nav_outputs = [*nav_outputs, readme_return_page]

        status_nav_outputs = [
            *nav_outputs,
            status_content_col,
            status_content_open,
            *status_zoom_back_outputs,
        ]

        def _bind_nav(
            btn: gr.Button,
            page: str,
            *,
            show_home_demo: bool | None = None,
            refresh_gravity: bool = False,
            reset_save: bool = False,
        ) -> None:
            chain = btn.click(lambda: _nav_to_page(page), outputs=nav_outputs)
            if show_home_demo is not None:
                chain = chain.then(
                    lambda visible=show_home_demo: _home_demo_nav_visible(visible),
                    outputs=[home_demo_nav_section],
                )
            if reset_save:
                chain = chain.then(_unlatch_save_button, outputs=save_unlatch_outputs)
            if refresh_gravity:
                chain = chain.then(
                    _run_residual_explorer_ui,
                    inputs=gravity_dial_inputs,
                    outputs=re_outputs,
                )

        def _bind_readme_nav(btn: gr.Button) -> None:
            btn.click(_open_readme_page, inputs=[current_page], outputs=readme_nav_outputs).then(
                lambda: _home_demo_nav_visible(False),
                outputs=[home_demo_nav_section],
            ).then(
                _unlatch_save_button,
                outputs=save_unlatch_outputs,
            )

        def _bind_status_nav(btn: gr.Button) -> None:
            btn.click(
                _nav_to_status_page,
                inputs=[current_page, status_content_open],
                outputs=status_nav_outputs,
            ).then(
                lambda: _home_demo_nav_visible(False),
                outputs=[home_demo_nav_section],
            ).then(
                _run_residual_explorer_ui,
                inputs=gravity_dial_inputs,
                outputs=re_outputs,
                show_progress="hidden",
            )

        render_panel_outputs = [
            render_panel_html,
            render_zoom_slot,
            render_active_slot,
            render_catalog_col,
            render_detail_col,
            render_detail_plot,
            render_detail_description,
            render_detail_slot,
            *render_sub_nav_btns,
            render_all_btn,
        ]
        render_load_outputs = [
            render_panel_html,
            render_plot_cache,
            render_zoom_slot,
            render_active_slot,
            render_catalog_col,
            render_detail_col,
            render_detail_plot,
            render_detail_description,
            render_detail_slot,
            *render_sub_nav_btns,
            render_all_btn,
        ]

        def _make_render_open_detail(slot: int):
            def _handler(plot_cache: list[str | None]):
                return _render_open_detail(slot, plot_cache)

            return _handler

        render_all_btn.click(
            _render_load_all_presets,
            inputs=[render_active_slot, render_zoom_slot],
            outputs=render_load_outputs,
            show_progress="hidden",
        )
        for slot, btn in enumerate(render_sub_nav_btns):
            btn.click(
                _make_render_open_detail(slot),
                inputs=[render_plot_cache],
                outputs=render_panel_outputs,
                show_progress="hidden",
            )
        for slot, btn in enumerate(render_cell_btns):
            btn.click(
                _make_render_open_detail(slot),
                inputs=[render_plot_cache],
                outputs=render_panel_outputs,
                show_progress="hidden",
            )

        for shape_id in _SHAPE_NAV_IDS:
            unified_nav[shape_id].click(
                lambda s=shape_id: _set_active_shape(s),
                outputs=shape_outputs,
                show_progress="hidden",
            ).then(_unlatch_save_button, outputs=save_unlatch_outputs)

        _bind_nav(
            unified_nav["home"],
            "home",
            show_home_demo=True,
            refresh_gravity=True,
            reset_save=True,
        )
        unified_nav["home"].click(
            lambda: _home_demo_nav_visible(True),
            outputs=[home_demo_nav_section],
        )
        _bind_nav(unified_nav["render"], "render", show_home_demo=False, reset_save=True)
        unified_nav["render"].click(
            lambda: _home_demo_nav_visible(False),
            outputs=[home_demo_nav_section],
        )
        _bind_readme_nav(unified_nav["readme"])
        unified_nav["readme"].click(
            lambda: _home_demo_nav_visible(False),
            outputs=[home_demo_nav_section],
        )
        _bind_status_nav(unified_nav["status"])
        unified_nav["status"].click(
            lambda: _home_demo_nav_visible(False),
            outputs=[home_demo_nav_section],
        )
        readme_back_btn.click(
            _readme_back_to_app,
            inputs=[readme_return_page],
            outputs=[*nav_outputs, home_demo_nav_section],
        ).then(
            _unlatch_save_button,
            outputs=save_unlatch_outputs,
        ).then(
            _run_residual_explorer_ui,
            inputs=gravity_dial_inputs,
            outputs=re_outputs,
            show_progress="hidden",
        )

        tab_newhere_btn.click(_toggle_newhere, inputs=[newhere_open], outputs=newhere_outputs)
        tab_claims_btn.click(_toggle_claims, inputs=[claims_open], outputs=claims_outputs)
        newhere_minimize_btn.click(_minimize_newhere, outputs=newhere_outputs[:3])
        claims_minimize_btn.click(_minimize_claims, outputs=claims_outputs[:3])
        def _app_boot() -> tuple:
            """Fast boot — rigid plot first so HF health checks pass quickly."""
            viewport = _demo_viewport_show_plot(_get_rigid_preset_plotly_figure())
            return (
                *_nav_to_page("home"),
                *viewport,
                *_demo_active_tab_updates("A"),
                "A",
                *_set_active_shape(_DEFAULT_ACTIVE_SHAPE),
            )

        def _app_boot_deferred_video() -> tuple:
            """Load Demo A breathing video after the UI is live (HF encodes on first boot)."""
            try:
                return _demo_viewport_show_breathing_video()
            except Exception:
                logger.exception("app boot breathing video failed")
                return _demo_viewport_show_plot(_get_rigid_preset_plotly_figure())

        demo.load(
            lambda: _home_demo_nav_visible(True),
            outputs=[home_demo_nav_section],
            show_progress="hidden",
        ).then(
            _app_boot,
            outputs=[
                *nav_outputs,
                gravity_viewport_plot,
                gravity_viewport_video,
                *[gravity_letter_btns[letter] for letter in _GRAVITY_CHILD_NAV_LETTERS],
                gravity_active_letter,
                *shape_outputs,
            ],
            show_progress="hidden",
        ).then(
            lambda: _home_demo_nav_visible(True),
            outputs=[home_demo_nav_section],
            show_progress="hidden",
        ).then(
            _app_boot_deferred_video,
            outputs=[gravity_viewport_plot, gravity_viewport_video],
            show_progress="hidden",
        )

        gr.Markdown(
            "Research notebook — emergent signature, not forced identity · "
            f"[Mystery repo]({GITHUB_URL}) · [TOE parent]({TOE_URL})",
            elem_classes=["myst-app-footer"],
        )
    return demo


demo = build_app()


def _pick_local_server_port(preferred: int, *, max_tries: int = 10) -> int:
    """Return the first free TCP port in [preferred, preferred + max_tries)."""
    import socket

    for port in range(preferred, preferred + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("0.0.0.0", port))
            except OSError:
                continue
            return port
    return preferred


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    try:
        from build_info import BUILD_COMMIT, BUILD_UPDATED_UTC

        logger.info("Mystery build %s (%s)", BUILD_COMMIT, BUILD_UPDATED_UTC)
    except ImportError:
        logger.info("Mystery build (dev — run scripts/sync_hf_space.sh to stamp)")
    logger.info("Wallpaper URL: %s", WALLPAPER_URL)

    try:
        demo.get_api_info()
        logger.info("Gradio API info check passed")
    except Exception:
        logger.exception("Gradio API info check failed")

    on_hf = bool(os.environ.get("SPACE_ID"))
    preferred_port = int(os.environ.get("GRADIO_SERVER_PORT", "7860"))
    port = preferred_port if on_hf else _pick_local_server_port(preferred_port)
    if not on_hf and port != preferred_port:
        logger.warning(
            "Port %s is busy; launching on http://127.0.0.1:%s instead",
            preferred_port,
            port,
        )
    share_env = os.environ.get("GRADIO_SHARE", "").strip().lower()
    share_local = share_env in {"1", "true", "yes", "on"}

    launch_kwargs: dict = {
        "server_name": "0.0.0.0",
        "server_port": port,
        "show_error": True,
        "show_api": False,
        "inbrowser": False,
        "share": share_local if not on_hf else False,
        # SSR can swallow button .click() events on HF Spaces — disable for reliable presets.
        "ssr_mode": False,
    }
    gradio_root = os.environ.get("GRADIO_ROOT_PATH", "").strip()
    if on_hf and gradio_root:
        launch_kwargs["root_path"] = gradio_root

    if not on_hf:
        logger.info("Open http://127.0.0.1:%s (close other local app.py instances to avoid stale ports)", port)
    demo.queue(default_concurrency_limit=2).launch(**launch_kwargs)


if __name__ == "__main__":
    main()