#!/usr/bin/env python3
"""Lightweight Gradio web demo for the Mystery φ-e-π probe."""

from __future__ import annotations

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
    FIGURE_URLS,
    FIGURES_INTRO_MD,
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
    build_unit_cell_viewport_header_html,
    unit_cell_error_placeholder_html,
    render_unit_cell_deformation_video,
    residual_from_scales,
    run_analysis,
    run_residual_explorer,

    terminal_directory_help,
    terminal_figures_index,
    terminal_keypad_map,
    terminal_probe_catalog,
    terminal_probe_scope,
    terminal_results_snapshot,
    terminal_toe_linkage,
    terminal_vortex369_readout,
)


def _figures_grid_html() -> str:
    """2×2 grid of reference figures on the Figures page."""
    labels = ("φ-e-π triangle", "κ sweep", "3-6-9 clock", "Conduit angular")
    imgs = "".join(
        f'<figure class="vqc-screencast-video-wrap">'
        f'<img class="vqc-screencast-video" src="{url}" alt="{label}" loading="lazy" />'
        f'<figcaption>{label}</figcaption></figure>'
        for url, label in zip(FIGURE_URLS, labels, strict=True)
    )
    return f'<div class="vqc-screencast-wrap">{imgs}</div>'


def _figures_links_md() -> str:
    links = " · ".join(
        f"[{label}]({url})" for label, url in zip(
            ("Triangle", "κ sweep", "369 clock", "Conduit"),
            FIGURE_URLS,
            strict=True,
        )
    )
    return f"{links} · same plots as **Run analysis** on the **Live Probe** tab."

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
_VQC_MATRIX_GREEN_BG = "#0a1f12"
_VQC_LOGO_GOLD = "#c9a227"
_VQC_HOME_KEY_BG = "#000000"

FIGURES_INTRO_MD_LOCAL = FIGURES_INTRO_MD

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


def _source_tab_btn_update(*, active: bool) -> gr.Update:
    """Source tab — matrix-green label when active; default brown body either way."""
    if active:
        return gr.update(
            interactive=False,
            elem_classes=["vqc-source-tab", "active"],
            variant="secondary",
        )
    return gr.update(interactive=True, elem_classes=["vqc-source-tab"], variant="secondary")


def _home_tab_update(*, on_demo_page: bool) -> gr.Update:
    """Live demo tab — matrix-green label when on demo page."""
    if on_demo_page:
        return gr.update(interactive=False, elem_classes=["vqc-source-tab", "active"], variant="secondary")
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


def _nav_to_page(page: str) -> tuple:
    """Switch between demo, figures, gravity, and readme; refresh Source tab highlights."""
    on_demo = page == "demo"
    on_anim = page == "animations"
    on_gravity = page == "gravity"
    on_readme = page == "readme"
    closed = _close_links_panels()
    tab_gravity = _source_tab_btn_update(active=on_gravity)
    tab_readme = _source_tab_btn_update(active=on_readme)
    tab_demo = _home_tab_update(on_demo_page=on_demo)
    tab_anim = _source_tab_btn_update(active=on_anim)
    page_tabs = (tab_gravity, tab_readme, tab_demo, tab_anim)
    return (
        gr.update(visible=on_demo),
        gr.update(visible=on_anim),
        gr.update(visible=on_gravity),
        gr.update(visible=on_readme),
        *page_tabs,
        *closed,
        *page_tabs,
        *page_tabs,
        *page_tabs,
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
        if (window.mystOnHf) return;
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
    function mystReflowViewport() {{
        var vp = document.getElementById('unit-cell-main-view');
        var row = document.querySelector('.myst-unit-cell-image-row');
        if (vp) void vp.offsetHeight;
        if (row) void row.offsetHeight;
        window.dispatchEvent(new Event('resize'));
    }}
    function bootViewportReflow() {{
        mystReflowViewport();
        requestAnimationFrame(mystReflowViewport);
        if (window.__mystViewportReflowObs) return;
        window.__mystViewportReflowObs = new MutationObserver(function() {{
            requestAnimationFrame(mystReflowViewport);
        }});
        var root = document.querySelector('.myst-unit-cell-image-row');
        if (root) {{
            window.__mystViewportReflowObs.observe(root, {{
                subtree: true, childList: true, attributes: true, attributeFilter: ['style', 'class']
            }});
        }}
    }}
    if (document.body) bootViewportReflow();
    document.addEventListener('DOMContentLoaded', bootViewportReflow);
    window.addEventListener('load', bootViewportReflow);
}})();
</script>
"""

HFB_CSS = f"""
:root, :root .dark {{
    --myst-control-bar-height: 1.54rem;
    --myst-button-height: 26px;
    --myst-viewport-min-height: 18rem;
    --myst-viewport-plot-height: 700px;
    --myst-viewport-aspect: 7 / 5;
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
.gradio-container .vqc-source-label {{
    color: #ffffff !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    margin-right: 0.35rem !important;
    line-height: 1.2 !important;
}}
.gradio-container .vqc-source-tab,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab span,
.gradio-container .vqc-nav-cell a.vqc-source-tab {{
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0.34rem 0.78rem !important;
    border: 2px solid #6b4f1d !important;
    border-radius: 8px !important;
    background: linear-gradient(180deg, #3d2e14 0%, #1f1608 100%) !important;
    background-color: #2a1f10 !important;
    box-shadow: inset 0 1px 0 rgba(255, 220, 150, 0.12), 0 2px 4px rgba(0, 0, 0, 0.35) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    text-decoration: none !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    line-height: 1.2 !important;
    letter-spacing: 0.03em !important;
    text-transform: none !important;
    white-space: nowrap !important;
    min-height: var(--myst-control-bar-height, 2.05rem) !important;
    height: var(--myst-control-bar-height, 2.05rem) !important;
    box-sizing: border-box !important;
    width: auto !important;
    margin: 0 !important;
    opacity: 1 !important;
    text-shadow: none !important;
    transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
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
.gradio-container .vqc-source-tab.active,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.active,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.active span,
.gradio-container .vqc-source-tab.active:hover,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.active:hover,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.active:hover span,
.gradio-container a.vqc-source-tab.active {{
    color: {_VQC_MATRIX_GREEN} !important;
    -webkit-text-fill-color: {_VQC_MATRIX_GREEN} !important;
    background: linear-gradient(180deg, #3d2e14 0%, #1f1608 100%) !important;
    border-color: #6b4f1d !important;
    text-decoration: none !important;
    cursor: default !important;
    opacity: 1 !important;
    box-shadow: inset 0 1px 0 rgba(255, 220, 150, 0.12), 0 2px 4px rgba(0, 0, 0, 0.35) !important;
}}
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.active:disabled,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.active[disabled],
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.active:disabled span,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.active[disabled] span {{
    color: {_VQC_MATRIX_GREEN} !important;
    -webkit-text-fill-color: {_VQC_MATRIX_GREEN} !important;
    background: linear-gradient(180deg, #3d2e14 0%, #1f1608 100%) !important;
    border-color: #6b4f1d !important;
    text-decoration: none !important;
    cursor: default !important;
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
.gradio-container .vqc-nav-spreadsheet-row {{
    display: grid !important;
    grid-template-columns: 4.75rem repeat(6, minmax(3.8rem, 1fr)) !important;
    gap: 0.2rem 0.45rem !important;
    align-items: center !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
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
    justify-self: end !important;
    align-self: center !important;
    text-align: right !important;
    padding-right: 0.15rem !important;
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
    min-height: 360px !important;
    background-color: #000000 !important;
}}
/* viewport plot sizing: see KNOWN-GOOD block at end of HFB_CSS */
.gradio-container .myst-gravity-page .vqc-plot3d-panel,
.gradio-container .myst-gravity-page .vqc-plot3d-panel .block,
.gradio-container .myst-gravity-page .vqc-plot3d-panel img {{
    background-color: #000000 !important;
}}
.gradio-container:has(.myst-gravity-page) {{
    overflow: hidden !important;
    max-height: 100dvh !important;
    padding: 0.15rem 0.5rem 0 !important;
    display: flex !important;
    flex-direction: column !important;
    min-height: calc(100dvh - 3.5rem) !important;
    box-sizing: border-box !important;
}}
.gradio-container:has(.myst-gravity-page) .main,
.gradio-container:has(.myst-gravity-page) .main > .wrap,
.gradio-container:has(.myst-gravity-page) .contain {{
    flex: 1 1 0 !important;
    min-height: 0 !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
}}
.gradio-container:has(.myst-gravity-page) .myst-app-footer,
.gradio-container:has(.myst-gravity-page) .myst-app-footer.block {{
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    visibility: hidden !important;
}}
.gradio-container .myst-gravity-page {{
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
    grid-template-columns: minmax(220px, 20%) minmax(0, 1fr) !important;
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
    grid-row: 2 !important;
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
    grid-row: 2 !important;
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
.gradio-container .myst-gravity-presets-header {{
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 0.06rem !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0.5rem 0.65rem 0.55rem !important;
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
.gradio-container .myst-gravity-page button.myst-gravity-quick-preset,
.gradio-container .myst-gravity-page button.myst-gravity-quick-preset span,
.gradio-container .myst-gravity-presets-panel button.myst-gravity-quick-preset,
.gradio-container .myst-gravity-presets-panel button.myst-gravity-quick-preset span,
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
    min-height: var(--myst-control-bar-height, 2.05rem) !important;
    height: var(--myst-control-bar-height, 2.05rem) !important;
    box-sizing: border-box !important;
    padding: 0.34rem 0.5rem !important;
    font-size: 0.82rem !important;
    line-height: 1.2 !important;
}}
.gradio-container .myst-gravity-page button.vqc-receiver-preset.vqc-full-width,
.gradio-container .myst-gravity-presets-panel button.vqc-receiver-preset.vqc-full-width,
.gradio-container .myst-gravity-presets-tui-card button.vqc-receiver-preset.vqc-full-width {{
    margin: 0.1rem 0.45rem 0.35rem !important;
    width: calc(100% - 0.9rem) !important;
    min-height: var(--myst-control-bar-height, 2.05rem) !important;
    height: var(--myst-control-bar-height, 2.05rem) !important;
    box-sizing: border-box !important;
    padding: 0.34rem 0.78rem !important;
    font-size: 0.82rem !important;
    line-height: 1.2 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
}}
.gradio-container .myst-gravity-page .myst-gravity-controls-accordion > .label-wrap {{
    min-height: var(--myst-control-bar-height, 2.05rem) !important;
    height: var(--myst-control-bar-height, 2.05rem) !important;
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
    min-height: 12rem !important;
    height: 100% !important;
    max-height: 100% !important;
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
    gap: 0.05rem !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0.38rem 0.65rem 0.42rem !important;
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
    min-height: 0 !important;
    max-height: 100% !important;
    margin: 0.3rem 0.45rem 0.4rem !important;
    padding: 0.5rem 0.6rem !important;
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
    min-height: 11rem !important;
    font-family: "Courier New", Courier, monospace !important;
    font-size: 0.78rem !important;
    line-height: 1.55 !important;
    color: #ffffff !important;
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
    align-self: stretch !important;
    min-height: 100% !important;
    min-width: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    overflow: visible !important;
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
}}
.gradio-container .myst-gravity-visuals-col {{
    align-items: stretch !important;
    align-self: stretch !important;
    display: flex !important;
    flex-direction: column !important;
    height: auto !important;
    min-height: 0 !important;
    overflow: visible !important;
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
.gradio-container .myst-app-footer.block {{
    margin: 0 !important;
    padding: 0.05rem 0.25rem !important;
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
}}
.gradio-container .myst-readme-page .markdown.prose {{
    font-size: 0.94rem !important;
    line-height: 1.5 !important;
}}
/* === UNIT CELL VIEWPORT header — hidden (plot only) === */
.gradio-container #component-191,
.gradio-container #component-191.block,
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
.gradio-container .myst-unit-cell-image-row,
.gradio-container .row.myst-unit-cell-image-row,
.gradio-container #component-192 {{
    height: 550px !important;
    min-height: 550px !important;
    max-height: 550px !important;
    flex: 0 0 550px !important;
    flex-shrink: 0 !important;
    width: 100% !important;
    min-width: 0 !important;
    align-items: stretch !important;
    align-self: stretch !important;
    box-sizing: border-box !important;
    overflow: visible !important;
}}
.gradio-container .myst-unit-cell-video-row,
.gradio-container .row.myst-unit-cell-video-row,
.gradio-container #component-194 {{
    align-items: stretch !important;
    align-self: stretch !important;
    box-sizing: border-box !important;
    overflow: visible !important;
}}
.gradio-container .myst-unit-cell-video-row,
.gradio-container .row.myst-unit-cell-video-row,
.gradio-container #component-194 {{
    height: 320px !important;
    min-height: 320px !important;
    max-height: 320px !important;
    flex: 0 0 320px !important;
}}
.gradio-container .myst-unit-cell-image-row > .form,
.gradio-container .myst-unit-cell-image-row > .form > .block,
.gradio-container .myst-unit-cell-image-row .gradio-html,
.gradio-container .myst-unit-cell-image-row .myst-unit-cell-viewport-image,
.gradio-container .myst-unit-cell-image-row .html-container,
.gradio-container .myst-unit-cell-image-row .prose,
.gradio-container #component-192 .gradio-html,
.gradio-container #component-192 .html-container {{
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
.gradio-container .myst-unit-cell-image-row .wrap.center.full,
.gradio-container .myst-unit-cell-image-row .wrap.center.hidden,
.gradio-container .myst-unit-cell-image-row .wrap.default.hidden,
.gradio-container #component-192 .wrap.center.full,
.gradio-container #component-192 .wrap.center.hidden {{
    display: none !important;
    opacity: 0 !important;
    pointer-events: none !important;
    visibility: hidden !important;
}}
.gradio-container #unit-cell-main-view,
.gradio-container #unit-cell-main-view.myst-unit-cell-viewport-inner {{
    height: 550px !important;
    min-height: 550px !important;
    max-height: 550px !important;
    width: 100% !important;
    max-width: 550px !important;
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
.gradio-container #unit-cell-animation,
.gradio-container #unit-cell-animation .wrap,
.gradio-container #unit-cell-animation .video-container,
.gradio-container #unit-cell-animation video {{
    width: 100% !important;
    height: 320px !important;
    min-height: 320px !important;
    object-fit: contain !important;
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

_HF_VIEWPORT_CSS = ""
if is_hf_space():
    _HF_VIEWPORT_CSS = """
/* HF Space — no wallpaper; body fallback only */
body::before,
#vqc-wallpaper {{
    display: none !important;
}}
body {{
    background: #0a0818 !important;
}}
"""

HFB_CSS = HFB_CSS + _HF_VIEWPORT_CSS


def run_probe(
    kappa: float,
    progress: gr.Progress = gr.Progress(track_tqdm=False),
) -> tuple[str, str | None, str | None]:
    try:
        progress(0.1, desc="Computing φ-e-π triangle…")
        progress(0.5, desc="Rendering κ sweep…")
        metrics, tri_path, sweep_path = run_analysis(float(kappa))
        progress(1.0, desc="Done")
        return metrics, tri_path, sweep_path
    except Exception as exc:
        logger.exception("run_probe failed for kappa=%r", kappa)
        err = f"Error: {exc}\n\n{traceback.format_exc()}"
        return err, None, None


_GRAVITY_QUICK_PRESET_KEYS = tuple(str(i) for i in range(8))
_GRAVITY_PRESET_BTN_KEYS = _GRAVITY_QUICK_PRESET_KEYS
_UNIT_CELL_IMAGE_DPI = 100
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
}
_GRAVITY_PARAM_CATALOG: tuple[dict[str, object], ...] = (
    {
        "id": "01",
        "key": "pressure",
        "label": "deformation pressure",
        "kind": "percent",
        "min": 0.0,
        "max": 1.0,
        "default": 0.35,
        "desc": "0 = rigid cube · 1 = full π bowl + φ/e concave pinch",
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


def _format_gravity_menu_tui_html() -> str:
    lines: list[str] = []
    for spec in _GRAVITY_PARAM_CATALOG:
        kind = str(spec["kind"])
        lines.append(
            f"{spec['id']}  {spec['label']:<22} {kind:<8} "
            f"{_gravity_param_range_label(spec):<12} default {_gravity_param_default_display(spec)}"
        )
        lines.append(f"    {spec['desc']}")
        lines.append("")
    body = "\n".join(lines).rstrip()
    return (
        '<div class="myst-preset-tui-serial myst-preset-tui-menu">'
        '<div class="myst-preset-tui-status">'
        "<u>ACTIVE STATUS: PRESET 01 — MENU · PARAMETER CATALOG</u>"
        "</div>"
        '<div class="myst-preset-tui-key-label">Preset menu description — table of contents</div>'
        f'<pre class="myst-preset-tui-lines">{body}</pre>'
        "</div>"
    )


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


def _format_gravity_preset_tui_html(
    active_slot: int,
    dials: dict[str, float],
    *,
    status_label: str | None = None,
    key_metrics: dict[str, float | int | str | None] | None = None,
) -> str:
    if active_slot == 0 and key_metrics is None and status_label is None:
        return _format_gravity_menu_tui_html()
    preset_id = _gravity_preset_id(active_slot)
    profile = _GRAVITY_PRESET_SLOT_LABELS.get(active_slot)
    if key_metrics:
        phase = key_metrics.get("phase")
        if phase == "once":
            status = "PLAYING — DEFORMATION (once)"
        elif phase == "loop":
            status = "LOOP — DEFORMATION VIDEO"
        else:
            frame_idx = key_metrics.get("frame_idx")
            total_frames = key_metrics.get("total_frames")
            if frame_idx is not None and total_frames:
                status = f"ANIMATE — FRAME {int(frame_idx)}/{int(total_frames)}"
            else:
                status = status_label or "ANIMATE"
    elif status_label:
        status = status_label
    elif profile:
        status = f"PRESET {preset_id} — {profile}"
    else:
        status = f"PRESET {preset_id}"
    dial_lines = tuple(
        f"{spec['label']:<26} {_gravity_param_display(spec, float(dials[str(spec['key'])]))}"
        for spec in _GRAVITY_PARAM_CATALOG
    )
    dial_body = "\n".join(dial_lines)
    key_section = ""
    if key_metrics:
        km = key_metrics
        key_body = "\n".join(
            (
                f"pressure (live)           {float(km['pressure_pct']):.1f}%",
                f"R (residual)              {float(km['r']):+.6f}",
                f"δ_side (contraction)      {float(km['delta_side']):.6f}",
                f"B(κ) − R                  {float(km['b_minus_r']):+.6f}",
                f"W_g (350/π gravity)       {float(km['w_g']):.4f}",
                f"deform mode               {km['deform_hint']}",
            )
        )
        key_section = (
            '<div class="myst-preset-tui-key-label">Key metrics — live frame</div>'
            f'<pre class="myst-preset-tui-key-metrics">{key_body}</pre>'
            '<div class="myst-preset-tui-key-label">Control panel snapshot</div>'
        )
    return (
        '<div class="myst-preset-tui-serial">'
        f'<div class="myst-preset-tui-status"><u>ACTIVE STATUS: {status}</u></div>'
        f"{key_section}"
        f'<pre class="myst-preset-tui-lines">{dial_body}</pre>'
        "</div>"
    )


def _gravity_tui_for_preset(
    active_slot: int,
    dials: dict[str, float],
    *,
    status_label: str | None = None,
    key_metrics: dict[str, float | int | str | None] | None = None,
) -> str:
    if key_metrics is not None or status_label is not None:
        return _format_gravity_preset_tui_html(
            active_slot,
            dials,
            status_label=status_label,
            key_metrics=key_metrics,
        )
    if active_slot == 0:
        return _format_gravity_menu_tui_html()
    return _format_gravity_preset_tui_html(active_slot, dials)


def figure_to_viewport_file_html(path: str, *, png_bytes: int | None = None) -> str:
    """Clean gr.HTML with Gradio-served /gradio_api/file= image path."""
    if not path or not os.path.exists(path):
        return "<div style='color:red;padding:20px;'>Image file not found</div>"
    size = png_bytes if png_bytes is not None else os.path.getsize(path)
    html = (
        '<div id="unit-cell-main-view" class="myst-unit-cell-viewport-inner" '
        'style="height:550px !important;width:100% !important;max-width:550px !important;'
        'min-height:550px !important;background:#000000;display:flex !important;'
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
) -> tuple[str, str, str | object, dict, str, str]:
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
    print(f"[DEBUG] _run_residual_explorer_ui: preset={slot}", flush=True)
    return (
        metrics,
        header,
        _gravity_static_image_update(fig),
        _gravity_clear_video_update(),
        control_levels,
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
    edit_params_enabled: bool,
) -> tuple:
    """Manual dial refresh — only when Manual Edit is latched (avoids preset cascade)."""
    if not edit_params_enabled:
        return tuple(gr.skip() for _ in range(6))
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
    )


def _gravity_preset_btn_classes(key: str, active: str) -> list[str]:
    classes = ["vqc-receiver-preset", "myst-gravity-quick-preset"]
    if key == active:
        classes.append("active")
    return classes


def _gravity_preset_btn_updates(active: str = "") -> tuple:
    return tuple(
        gr.update(
            elem_classes=_gravity_preset_btn_classes(key, active),
            variant="secondary",
        )
        for key in _GRAVITY_PRESET_BTN_KEYS
    )


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
    return (
        new_state,
        _gravity_edit_params_btn_update(new_state),
        *_gravity_slider_control_updates(None, edit_enabled=new_state),
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
    *,
    edit_params_enabled: bool = False,
    update_image: bool = True,
) -> tuple:
    image_out = _gravity_static_image_update(fig) if update_image else gr.skip()
    return (
        *_gravity_preset_btn_updates(active_key),
        _gravity_edit_params_btn_update(edit_params_enabled),
        *_gravity_slider_control_updates(dials, edit_enabled=edit_params_enabled),
        metrics,
        header,
        image_out,
        video_update,
        _format_gravity_control_panel_html(dials, active_slot),
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
        return _gravity_animation_render_outputs(
            str(slot),
            dials,
            metrics,
            header,
            _gravity_load_video_update(video_path),
            tui,
            slot,
            edit_params_enabled=bool(edit_params_enabled),
        )
    except Exception as exc:
        logger.exception("gravity animate render failed")
        err_tui = _gravity_tui_for_preset(slot, dials, status_label="ANIMATE ERROR")
        return _gravity_animation_render_outputs(
            str(slot),
            dials,
            f"Animation error: {exc}",
            gr.skip(),
            _gravity_clear_video_update(),
            err_tui,
            slot,
            edit_params_enabled=bool(edit_params_enabled),
        )


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
    if slot == 0:
        dials = dict(_GRAVITY_HOME_DIALS)
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


def _make_gravity_quick_preset_click(slot: int):
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
            edit_params_enabled=edit_params_enabled,
            update_image=fig is not None,
        )
        if fig is None:
            outputs = list(outputs)
            outputs[21] = _gravity_viewport_error_placeholder()
        image_out = outputs[21]
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
        return tuple(outputs)

    return handler


def load_kappa_doc() -> float:
    return KAPPA_DOC


def load_kappa_star() -> float:
    from demo_core import kappa_star

    return kappa_star()


def build_app() -> gr.Blocks:
    with gr.Blocks(
        title="Mystery — φ · e · π Emergent Signature",
        analytics_enabled=False,
        theme=_build_vqc_theme(),
        head=WALLPAPER_HEAD,
        css=HFB_CSS,
        fill_width=True,
        fill_height=True,
    ) as demo:
        current_page = gr.State("gravity")
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
        with gr.Column(visible=False) as page_demo:
            with gr.Group(elem_classes=["vqc-optics-panel"]):
                with gr.Row(elem_classes=["vqc-optics-panel-header"]):
                    gr.HTML(OPTICS_LOGO_HTML)
                    with gr.Column(elem_classes=["vqc-optics-panel-nav"], scale=1):
                        with gr.Row(elem_classes=["vqc-nav-spreadsheet-row"]):
                            gr.HTML('<span class="vqc-source-label vqc-nav-row-label">Source:</span>')
                            with gr.Column(elem_classes=["vqc-nav-cell"], scale=1, min_width=72):
                                tab_gravity_btn = gr.Button(
                                    "Gravity",
                                    elem_classes=["vqc-source-tab", "active"],
                                    interactive=False,
                                    scale=0,
                                    variant="secondary",
                                )
                            with gr.Column(elem_classes=["vqc-nav-cell"], scale=1, min_width=72):
                                tab_readme_btn = gr.Button(
                                    "README",
                                    elem_classes=["vqc-source-tab"],
                                    scale=0,
                                    variant="secondary",
                                )
                            with gr.Column(elem_classes=["vqc-nav-cell"], scale=1, min_width=72):
                                tab_demo_btn = gr.Button(
                                    "Live Probe",
                                    elem_classes=["vqc-source-tab"],
                                    scale=0,
                                    variant="secondary",
                                )
                            with gr.Column(elem_classes=["vqc-nav-cell"], scale=1, min_width=72):
                                tab_anim_btn = gr.Button(
                                    "Figures",
                                    elem_classes=["vqc-source-tab"],
                                    scale=0,
                                    variant="secondary",
                                )
                            with gr.Column(elem_classes=["vqc-nav-cell"], scale=1, min_width=72):
                                tab_claims_btn = gr.Button(
                                    "Claims",
                                    elem_classes=["vqc-source-tab"],
                                    scale=0,
                                    variant="secondary",
                                )
                            with gr.Column(elem_classes=["vqc-nav-cell"], scale=1, min_width=72):
                                tab_newhere_btn = gr.Button(
                                    "New here?",
                                    elem_classes=["vqc-source-tab"],
                                    scale=0,
                                    variant="secondary",
                                )
                        with gr.Row(elem_classes=["vqc-nav-spreadsheet-row"]):
                            gr.HTML('<span class="vqc-source-label vqc-nav-row-label">Links:</span>')
                            with gr.Column(elem_classes=["vqc-nav-cell"], scale=1, min_width=72):
                                gr.HTML(_external_tab_html("GitHub", GITHUB_URL, "github"))
                            with gr.Column(elem_classes=["vqc-nav-cell"], scale=1, min_width=72):
                                gr.HTML(_external_tab_html("TOE parent", TOE_URL, "toe"))
                            with gr.Column(elem_classes=["vqc-nav-cell"], scale=1, min_width=72):
                                gr.HTML('<span class="vqc-nav-cell-empty" aria-hidden="true">&nbsp;</span>')
                            with gr.Column(elem_classes=["vqc-nav-cell"], scale=1, min_width=72):
                                gr.HTML('<span class="vqc-nav-cell-empty" aria-hidden="true">&nbsp;</span>')
                            with gr.Column(elem_classes=["vqc-nav-cell"], scale=1, min_width=72):
                                gr.HTML('<span class="vqc-nav-cell-empty" aria-hidden="true">&nbsp;</span>')
                optics_terminal = gr.Textbox(
                    label="Matrix status display — selection menu · d-pad nav",
                    value="",
                    lines=14,
                    max_lines=24,
                    interactive=False,
                    elem_classes=["vqc-optics-terminal-wrap", "vqc-optics-terminal"],
                )
                term_signal_scan = gr.HTML(SIGNAL_SCANNER_HTML, visible=False, elem_classes=["myst-signal-host"])
                term_active_key = gr.State("")
                term_ui_state = gr.State(_default_term_ui_state())
                term_all_btns: dict[str, gr.Button] = {}
                _dpad_row_labels = {
                    "dpad_select": "enter",
                    "dpad_up": "▲",
                    "dpad_down": "▼",
                    "dpad_left": "◀",
                    "dpad_right": "▶",
                    "clear": "clear",
                }

                with gr.Column(elem_classes=["vqc-optics-keypad"]):
                    with gr.Row(elem_classes=["vqc-optics-dpad-row"], equal_height=True):
                        for nav_key in TERM_NAV_KEYS:
                            term_all_btns[nav_key] = gr.Button(
                                _dpad_row_labels[nav_key],
                                elem_classes=_term_key_btn_classes(nav_key, ""),
                                scale=1,
                                variant="secondary",
                            )
                    with gr.Row(elem_classes=["vqc-optics-prog-row"], equal_height=True):
                        for index in range(1, 13):
                            key_id = _term_key_id(index)
                            term_all_btns[key_id] = gr.Button(
                                _term_keypad_label(index),
                                elem_classes=_term_key_btn_classes(key_id, ""),
                                scale=1,
                                variant="secondary",
                            )
                    with gr.Row(elem_classes=["vqc-optics-prog-row"], equal_height=True):
                        for index in range(13, 25):
                            key_id = _term_key_id(index)
                            term_all_btns[key_id] = gr.Button(
                                _term_keypad_label(index),
                                elem_classes=_term_key_btn_classes(key_id, ""),
                                scale=1,
                                variant="secondary",
                            )
                term_keypad_outputs = [
                    optics_terminal,
                    term_signal_scan,
                    *[term_all_btns[key_id] for key_id in TERM_KEYPAD_CONTROL_ORDER],
                    term_active_key,
                    term_ui_state,
                ]
                with gr.Row(elem_classes=["vqc-optics-dial-row"]):
                    kappa = gr.Slider(
                        0.70,
                        0.95,
                        value=KAPPA_DOC,
                        step=0.001,
                        label="κ (holonomy-gap parameter)",
                        info="Documented κ = 0.85 · κ* = e/π − R/π² ≈ 0.8513 nulls B(κ)−R",
                        elem_classes=["vqc-optics-dial-wrap"],
                    )
                gr.HTML(
                    '<p class="vqc-optics-presets-label">'
                    "κ presets — one click sets slider and runs analysis"
                    "</p>"
                )
                with gr.Row():
                    preset_kappa_doc = gr.Button(
                        "κ_doc = 0.85",
                        variant="secondary",
                        size="sm",
                        elem_classes=["vqc-receiver-preset"],
                    )
                    preset_kappa_star = gr.Button(
                        "κ* (exact null)",
                        variant="secondary",
                        size="sm",
                        elem_classes=["vqc-receiver-preset"],
                    )
                    preset_e_over_pi = gr.Button(
                        "e/π",
                        variant="secondary",
                        size="sm",
                        elem_classes=["vqc-receiver-preset"],
                    )
            # Shared cancels list — stops in-flight terminal streams on new keypress.
            term_cancels: list = []

            def _bind_term_event(btn: gr.Button, fn, *, inputs: list) -> None:
                term_cancels.append(
                    btn.click(
                        fn,
                        inputs=inputs,
                        outputs=term_keypad_outputs,
                        cancels=term_cancels,
                    )
                )

            scan_key = _term_key_id(8)
            _bind_term_event(
                term_all_btns[scan_key],
                _make_activate_signal_scan(scan_key),
                inputs=[term_ui_state],
            )
            _bind_term_event(
                term_all_btns["clear"],
                _make_term_clear_click("clear"),
                inputs=[optics_terminal, term_ui_state],
            )
            for hold_key in TERM_DPAD_HOLD_KEYS:
                _bind_term_event(
                    term_all_btns[hold_key],
                    _make_term_dpad_click(hold_key),
                    inputs=[optics_terminal, term_ui_state],
                )
            _bind_term_event(
                term_all_btns[TERM_KEYPAD_HOME_KEY],
                _make_term_home_momentary(),
                inputs=[term_active_key, term_ui_state],
            )
            for index in range(1, TERM_KEYPAD_COUNT + 1):
                key_id = _term_key_id(index)
                if index == 1 or index == 8:
                    continue
                if index in TERM_KEYPAD_DEFINED:
                    action = TERM_KEYPAD_DEFINED[index]
                    _bind_term_event(
                        term_all_btns[key_id],
                        _make_term_stream_click(
                            key_id,
                            TERM_KEYPAD_STREAMERS[action],
                            menu_action=action,
                        ),
                        inputs=[term_ui_state],
                    )
                else:
                    _bind_term_event(
                        term_all_btns[key_id],
                        _make_term_latch_click(key_id),
                        inputs=[optics_terminal, term_ui_state],
                    )

            run_btn = gr.Button("Run analysis", variant="primary", elem_classes=["vqc-full-width"])
            with gr.Row(equal_height=True):
                with gr.Column(scale=1):
                    metrics = gr.Textbox(label="Metrics", lines=18)
                with gr.Column(scale=2):
                    figure_triangle = gr.Image(
                        label="φ-e-π triangle vs 30-60-90",
                        type="filepath",
                        elem_classes=["vqc-figure-panel"],
                    )
            figure_sweep = gr.Image(
                label="κ sweep — B(κ) vs R",
                type="filepath",
                elem_classes=["vqc-figure-panel"],
            )
            run_outputs = [metrics, figure_triangle, figure_sweep]

            run_btn.click(run_probe, inputs=[kappa], outputs=run_outputs)
            preset_kappa_doc.click(load_kappa_doc, outputs=[kappa]).then(
                run_probe, inputs=[kappa], outputs=run_outputs
            )
            preset_kappa_star.click(load_kappa_star, outputs=[kappa]).then(
                run_probe, inputs=[kappa], outputs=run_outputs
            )
            preset_e_over_pi.click(lambda: float(E_OVER_PI), outputs=[kappa]).then(
                run_probe, inputs=[kappa], outputs=run_outputs
            )

        with gr.Column(visible=False, elem_classes=["vqc-animations-page"]) as page_animations:
            with gr.Row(elem_classes=["vqc-source-tabs-row", "vqc-animations-nav-row"]):
                gr.HTML('<span class="vqc-source-label">Source:</span>')
                anim_tab_gravity_btn = gr.Button(
                    "Gravity",
                    elem_classes=["vqc-source-tab"],
                    scale=0,
                    variant="secondary",
                )
                anim_tab_readme_btn = gr.Button(
                    "README",
                    elem_classes=["vqc-source-tab"],
                    scale=0,
                    variant="secondary",
                )
                anim_tab_demo_btn = gr.Button(
                    "Live Probe",
                    elem_classes=["vqc-source-tab"],
                    scale=0,
                    variant="secondary",
                )
                anim_tab_anim_btn = gr.Button(
                    "Figures",
                    elem_classes=["vqc-source-tab", "active"],
                    interactive=False,
                    scale=0,
                    variant="secondary",
                )
            gr.Markdown("## Reference figures")
            gr.Markdown(FIGURES_INTRO_MD_LOCAL)
            gr.HTML(_figures_grid_html())
            gr.Markdown(_figures_links_md())

        _init_re_metrics, _init_unit_cell_header, _init_unit_cell_fig = run_residual_explorer(
            1.0, 1.0, 1.0, KAPPA_DOC, 0.1, 1.0, 1.0, 0.35, 22.0, 45.0
        )
        _init_unit_cell_html = _gravity_fig_to_viewport_file_html(
            _init_unit_cell_fig,
            dpi=_UNIT_CELL_IMAGE_DPI,
        )
        _init_preset_tui = _format_gravity_menu_tui_html()
        _init_control_levels = _format_gravity_control_panel_html(_GRAVITY_HOME_DIALS, 0)

        with gr.Column(visible=False, elem_classes=["myst-readme-page"]) as page_readme:
            with gr.Row(elem_classes=["vqc-source-tabs-row", "vqc-animations-nav-row"]):
                gr.HTML('<span class="vqc-source-label">Source:</span>')
                readme_tab_gravity_btn = gr.Button(
                    "Gravity",
                    elem_classes=["vqc-source-tab"],
                    scale=0,
                    variant="secondary",
                )
                readme_tab_readme_btn = gr.Button(
                    "README",
                    elem_classes=["vqc-source-tab", "active"],
                    interactive=False,
                    scale=0,
                    variant="secondary",
                )
                readme_tab_demo_btn = gr.Button(
                    "Live Probe",
                    elem_classes=["vqc-source-tab"],
                    scale=0,
                    variant="secondary",
                )
                readme_tab_anim_btn = gr.Button(
                    "Figures",
                    elem_classes=["vqc-source-tab"],
                    scale=0,
                    variant="secondary",
                )
            gr.HTML(
                f'<p class="myst-github-banner">Full derivations, probe suite, and JSON outputs: '
                f'<a href="{GITHUB_URL}" target="_blank" rel="noopener noreferrer">'
                f'github.com/kinaar8340/mystery</a> · '
                f'<a href="{GITHUB_URL}#physical-interpretation--emergent-gravity" '
                f'target="_blank" rel="noopener noreferrer">README § Physical Interpretation</a></p>'
            )
            gr.Markdown(PHYSICAL_INTERPRETATION_INTRO_MD)
            gr.Markdown(PHYSICAL_INTERPRETATION_MATH_MD)
            gr.Markdown("### Probe hooks")
            gr.Markdown(PROBE_HOOKS_TABLE_MD)
            for title, script_url, snippet in PROBE_SNIPPETS:
                with gr.Accordion(f"{title} — view snippet", open=False):
                    gr.Markdown(f"Source: [{script_url.split('/')[-1]}]({script_url})")
                    gr.Code(snippet, language="python", lines=10)
            gr.Markdown(EXPLORE_FURTHER_MD)

        with gr.Column(visible=True, elem_classes=["myst-gravity-page"], scale=1) as page_gravity:
            with gr.Row(elem_classes=["vqc-source-tabs-row", "vqc-animations-nav-row"]):
                gr.HTML('<span class="vqc-source-label">Source:</span>')
                grav_tab_gravity_btn = gr.Button(
                    "Gravity",
                    elem_classes=["vqc-source-tab", "active"],
                    interactive=False,
                    scale=0,
                    variant="secondary",
                )
                grav_tab_readme_btn = gr.Button(
                    "README",
                    elem_classes=["vqc-source-tab"],
                    scale=0,
                    variant="secondary",
                )
                grav_tab_demo_btn = gr.Button(
                    "Live Probe",
                    elem_classes=["vqc-source-tab"],
                    scale=0,
                    variant="secondary",
                )
                grav_tab_anim_btn = gr.Button(
                    "Figures",
                    elem_classes=["vqc-source-tab"],
                    scale=0,
                    variant="secondary",
                )
            with gr.Row(elem_classes=["myst-gravity-split"], equal_height=True):
                with gr.Column(
                    scale=2,
                    min_width=220,
                    elem_classes=[
                        "myst-gravity-controls-col",
                        "myst-gravity-left-panel",
                        "myst-gravity-left-stack",
                    ],
                ):
                    with gr.Column(
                        elem_classes=[
                            "vqc-optics-panel",
                            "vqc-gravity-panel",
                            "myst-gravity-left-frame",
                            "myst-gravity-panel-window",
                            "myst-gravity-control-panel",
                            "myst-gravity-left-control-slot",
                            "myst-gravity-control-top-slot",
                        ],
                    ):
                        with gr.Accordion(
                            "Parameter levels",
                            open=False,
                            elem_classes=[
                                "myst-gravity-controls-accordion",
                                "myst-gravity-levels-accordion",
                            ],
                        ):
                            re_control_levels = gr.HTML(
                                _init_control_levels,
                                elem_classes=["myst-gravity-control-levels-wrap"],
                            )
                        with gr.Accordion(
                            "Manual Edit",
                            open=False,
                            elem_classes=[
                                "myst-gravity-controls-accordion",
                                "myst-gravity-manual-edit-accordion",
                            ],
                        ):
                            gr.HTML(CONTROL_PANEL_HEADER_HTML)
                            re_edit_params = gr.State(False)
                            edit_params_btn = gr.Button(
                                "Manual Edit",
                                variant="secondary",
                                elem_classes=[
                                    "vqc-receiver-preset",
                                    "myst-gravity-edit-params-btn",
                                    "vqc-full-width",
                                ],
                            )
                            with gr.Row(elem_classes=["vqc-optics-dial-row"]):
                                re_pressure = gr.Slider(
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
                                re_view_elev = gr.Slider(
                                    5.0,
                                    75.0,
                                    value=22.0,
                                    step=1.0,
                                    label="View elevation (°)",
                                    elem_classes=["vqc-optics-dial-wrap"],
                                    interactive=False,
                                )
                                re_view_azim = gr.Slider(
                                    0.0,
                                    360.0,
                                    value=45.0,
                                    step=5.0,
                                    label="View azimuth (°)",
                                    elem_classes=["vqc-optics-dial-wrap"],
                                    interactive=False,
                                )
                            with gr.Row(elem_classes=["vqc-optics-dial-row"]):
                                re_phi_scale = gr.Slider(
                                    0.90,
                                    1.10,
                                    value=1.0,
                                    step=0.001,
                                    label="φ² scale",
                                    elem_classes=["vqc-optics-dial-wrap"],
                                    interactive=False,
                                )
                                re_e_scale = gr.Slider(
                                    0.90,
                                    1.10,
                                    value=1.0,
                                    step=0.001,
                                    label="e² scale",
                                    elem_classes=["vqc-optics-dial-wrap"],
                                    interactive=False,
                                )
                                re_pi_scale = gr.Slider(
                                    0.90,
                                    1.10,
                                    value=1.0,
                                    step=0.001,
                                    label="π² scale",
                                    elem_classes=["vqc-optics-dial-wrap"],
                                    interactive=False,
                                )
                            with gr.Row(elem_classes=["vqc-optics-dial-row"]):
                                re_kappa = gr.Slider(
                                    0.70,
                                    0.95,
                                    value=KAPPA_DOC,
                                    step=0.001,
                                    label="κ (holonomy-gap parameter)",
                                    info=f"κ_doc = {KAPPA_DOC} · κ* nulls B(κ)−R",
                                    elem_classes=["vqc-optics-dial-wrap"],
                                    interactive=False,
                                )
                                re_delta_z = gr.Slider(
                                    0.0,
                                    0.5,
                                    value=0.1,
                                    step=0.01,
                                    label="δ_z (primary push)",
                                    elem_classes=["vqc-optics-dial-wrap"],
                                    interactive=False,
                                )
                            with gr.Row(elem_classes=["vqc-optics-dial-row"]):
                                re_alpha = gr.Slider(
                                    0.0,
                                    2.0,
                                    value=1.0,
                                    step=0.05,
                                    label="α (geometry factor)",
                                    elem_classes=["vqc-optics-dial-wrap"],
                                    interactive=False,
                                )
                                re_beta = gr.Slider(
                                    0.0,
                                    2.0,
                                    value=1.0,
                                    step=0.05,
                                    label="β (residual coupling)",
                                    elem_classes=["vqc-optics-dial-wrap"],
                                    interactive=False,
                                )
                            with gr.Column(elem_classes=["myst-gravity-metrics-inner"]):
                                re_metrics = gr.Textbox(
                                    label="Residual explorer",
                                    lines=9,
                                    interactive=False,
                                    value=_init_re_metrics,
                                )
                    with gr.Column(
                        elem_classes=[
                            "vqc-optics-panel",
                            "vqc-gravity-panel",
                            "myst-gravity-left-frame",
                            "myst-gravity-panel-window",
                            "myst-gravity-presets-tui-card",
                            "myst-gravity-left-presets-tui-slot",
                        ],
                    ):
                        with gr.Column(
                            elem_classes=[
                                "myst-gravity-presets-panel",
                                "myst-gravity-presets-fixed",
                            ],
                        ):
                            gr.HTML(QUICK_PRESETS_PANEL_HEADER_HTML)
                            re_quick_presets: list[gr.Button] = []
                            for row_start in (0, 4):
                                with gr.Row(elem_classes=["myst-gravity-preset-row"]):
                                    for slot in range(row_start, row_start + 4):
                                        preset_classes = [
                                            "vqc-receiver-preset",
                                            "myst-gravity-quick-preset",
                                        ]
                                        if slot == 0:
                                            preset_classes.append("active")
                                        btn_kwargs: dict = {
                                            "variant": "secondary",
                                            "size": "sm",
                                            "elem_classes": preset_classes,
                                        }
                                        if slot == 0:
                                            btn_kwargs["elem_id"] = "gravity-preset-btn-1"
                                        re_quick_presets.append(
                                            gr.Button(str(slot + 1), **btn_kwargs)
                                        )
                        re_active_preset = gr.State(0)
                        animate_deform_btn = gr.Button(
                            "Animate deformation",
                            variant="secondary",
                            elem_classes=[
                                "vqc-receiver-preset",
                                "myst-gravity-edit-params-btn",
                                "vqc-full-width",
                            ],
                        )
                        with gr.Column(
                            elem_classes=[
                                "myst-gravity-preset-tui-section",
                                "myst-gravity-left-tui",
                                "myst-gravity-left-tui-slot",
                            ],
                        ):
                            gr.HTML(GRAVITY_PRESET_TUI_HEADER_HTML)
                            re_preset_tui = gr.HTML(
                                _init_preset_tui,
                                elem_classes=["myst-gravity-preset-tui-wrap"],
                            )
                with gr.Column(
                    scale=7,
                    elem_classes=["myst-gravity-visuals-col"],
                ):
                    unit_cell_header = gr.HTML(
                        _init_unit_cell_header,
                        elem_classes=["myst-cube-viewport-header-slot"],
                    )
                    with gr.Row(elem_classes=["myst-unit-cell-image-row"]):
                        unit_cell_image = gr.HTML(
                            value="",
                            elem_classes=["myst-unit-cell-viewport-image"],
                            container=False,
                            min_height=550,
                        )
                    with gr.Row(elem_classes=["myst-unit-cell-video-row"]):
                        unit_cell_video = gr.Video(
                            label="Deformation Animation",
                            show_label=True,
                            interactive=False,
                            container=False,
                            autoplay=True,
                            loop=True,
                            height=320,
                            format="mp4",
                            elem_id="unit-cell-animation",
                            elem_classes=["myst-unit-cell-animation", "gradio-video"],
                        )
            re_inputs = [
                re_phi_scale, re_e_scale, re_pi_scale,
                re_kappa, re_delta_z, re_alpha, re_beta, re_pressure,
                re_view_elev, re_view_azim,
            ]
            re_outputs = [
                re_metrics,
                unit_cell_header,
                unit_cell_image,
                unit_cell_video,
                re_control_levels,
                re_preset_tui,
            ]
            gravity_dial_inputs = [*re_inputs, re_active_preset]
            gravity_preset_inputs = [*gravity_dial_inputs, re_edit_params]
            gravity_preset_btn_outputs = list(re_quick_presets)
            gravity_preset_outputs = [
                *gravity_preset_btn_outputs,
                edit_params_btn,
                *re_inputs,
                *re_outputs,
                re_active_preset,
            ]
            edit_params_btn.click(
                _gravity_edit_params_toggle,
                inputs=[re_edit_params],
                outputs=[re_edit_params, edit_params_btn, *re_inputs],
            )
            # .release() not .change() — preset slider gr.update() must not re-fire explorer.
            gravity_manual_inputs = [*gravity_dial_inputs, re_edit_params]
            for slider in re_inputs:
                slider.release(
                    _run_residual_explorer_ui_manual,
                    inputs=gravity_manual_inputs,
                    outputs=re_outputs,
                    show_progress="hidden",
                )
            gravity_immediate_outputs = [
                *gravity_preset_btn_outputs,
                unit_cell_image,
                unit_cell_video,
            ]
            animate_event = animate_deform_btn.click(
                _gravity_animate_btn_immediate,
                outputs=gravity_immediate_outputs,
            ).then(
                _gravity_animate_toggle_click,
                inputs=gravity_preset_inputs,
                outputs=gravity_preset_outputs,
                show_progress="hidden",
            )
            # Unified single-step preset clicks — no immediate/.then() split.
            for slot, preset_btn in enumerate(re_quick_presets):
                preset_btn.click(
                    _make_gravity_quick_preset_click(slot),
                    inputs=gravity_preset_inputs,
                    outputs=gravity_preset_outputs,
                    show_progress="hidden",
                    cancels=[animate_event],
                )
            print(
                f"[DEBUG] wired {len(re_quick_presets)} unified preset handlers",
                flush=True,
            )

        newhere_outputs = [panel_newhere, tab_newhere_btn, newhere_open, panel_claims, tab_claims_btn, claims_open]
        claims_outputs = [panel_claims, tab_claims_btn, claims_open, panel_newhere, tab_newhere_btn, newhere_open]
        nav_outputs = [
            page_demo,
            page_animations,
            page_gravity,
            page_readme,
            tab_gravity_btn,
            tab_readme_btn,
            tab_demo_btn,
            tab_anim_btn,
            panel_newhere,
            tab_newhere_btn,
            newhere_open,
            panel_claims,
            tab_claims_btn,
            claims_open,
            anim_tab_gravity_btn,
            anim_tab_readme_btn,
            anim_tab_demo_btn,
            anim_tab_anim_btn,
            grav_tab_gravity_btn,
            grav_tab_readme_btn,
            grav_tab_demo_btn,
            grav_tab_anim_btn,
            readme_tab_gravity_btn,
            readme_tab_readme_btn,
            readme_tab_demo_btn,
            readme_tab_anim_btn,
            current_page,
        ]

        def _bind_nav(btn: gr.Button, page: str, *, refresh_gravity: bool = False) -> None:
            if refresh_gravity:
                btn.click(lambda: _nav_to_page(page), outputs=nav_outputs).then(
                    _run_residual_explorer_ui,
                    inputs=gravity_dial_inputs,
                    outputs=re_outputs,
                )
            else:
                btn.click(lambda: _nav_to_page(page), outputs=nav_outputs)

        _bind_nav(tab_demo_btn, "demo")
        _bind_nav(tab_anim_btn, "animations")
        _bind_nav(tab_readme_btn, "readme")
        _bind_nav(tab_gravity_btn, "gravity", refresh_gravity=True)
        _bind_nav(anim_tab_demo_btn, "demo")
        _bind_nav(anim_tab_anim_btn, "animations")
        _bind_nav(anim_tab_readme_btn, "readme")
        _bind_nav(anim_tab_gravity_btn, "gravity", refresh_gravity=True)
        _bind_nav(grav_tab_demo_btn, "demo")
        _bind_nav(grav_tab_anim_btn, "animations")
        _bind_nav(grav_tab_readme_btn, "readme")
        _bind_nav(grav_tab_gravity_btn, "gravity", refresh_gravity=True)
        _bind_nav(readme_tab_gravity_btn, "gravity", refresh_gravity=True)
        _bind_nav(readme_tab_demo_btn, "demo")
        _bind_nav(readme_tab_anim_btn, "animations")
        _bind_nav(readme_tab_readme_btn, "readme")
        tab_newhere_btn.click(_toggle_newhere, inputs=[newhere_open], outputs=newhere_outputs)
        tab_claims_btn.click(_toggle_claims, inputs=[claims_open], outputs=claims_outputs)
        newhere_minimize_btn.click(_minimize_newhere, outputs=newhere_outputs[:3])
        claims_minimize_btn.click(_minimize_claims, outputs=claims_outputs[:3])
        demo.load(_stream_term_boot, outputs=term_keypad_outputs)
        demo.load(
            lambda: (
                _init_unit_cell_html
            ),
            outputs=[unit_cell_image],
            show_progress=False,
        )

        gr.Markdown(
            "Research notebook — emergent signature, not forced identity · "
            f"[Mystery repo]({GITHUB_URL}) · [TOE parent]({TOE_URL})",
            elem_classes=["myst-app-footer"],
        )
    return demo


demo = build_app()


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    try:
        demo.get_api_info()
        logger.info("Gradio API info check passed")
    except Exception:
        logger.exception("Gradio API info check failed")

    on_hf = bool(os.environ.get("SPACE_ID"))
    port = int(os.environ.get("GRADIO_SERVER_PORT", "7860"))
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

    demo.queue(default_concurrency_limit=2).launch(**launch_kwargs)


if __name__ == "__main__":
    main()