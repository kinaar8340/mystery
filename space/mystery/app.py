#!/usr/bin/env python3
"""Lightweight Gradio web demo for the Mystery φ-e-π probe."""

from __future__ import annotations

import logging
import os
import re
import time
import traceback
from collections.abc import Callable, Iterator

import gradio as gr

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
    run_analysis,
    run_residual_explorer,
    stream_unit_cell_deformation,
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

CUBE_VIEWPORT_HEADER_HTML = """
<div class="myst-cube-viewport-header" role="img" aria-label="Unit cell viewport">
  <span class="myst-cube-viewport-brand">MYSTERY</span>
  <span class="myst-cube-viewport-title">Unit Cell Viewport</span>
  <span class="myst-cube-viewport-sub">π bowl · φ/e concave · live curvature</span>
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
    """Animations tab — orange only when that page is open; otherwise green."""
    if active:
        return gr.update(interactive=False, elem_classes=["vqc-source-tab", "active"])
    return gr.update(interactive=True, elem_classes=["vqc-source-tab"], variant="secondary")


def _home_tab_update(*, on_demo_page: bool) -> gr.Update:
    """Live demo tab: orange on demo page, green link back from Animations."""
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
</script>
"""

HFB_CSS = f"""
:root, :root .dark {{
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
    background: transparent !important;
    background-color: transparent !important;
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
    min-height: 2.05rem !important;
    height: auto !important;
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
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: linear-gradient(180deg, #ea580c 0%, #9a3412 100%) !important;
    border-color: #7c2d12 !important;
    text-decoration: none !important;
    cursor: default !important;
    opacity: 1 !important;
    box-shadow: 0 0 10px rgba(234, 88, 12, 0.35), inset 0 1px 0 rgba(255, 220, 150, 0.2) !important;
}}
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.active:disabled,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.active[disabled],
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.active:disabled span,
.gradio-container .vqc-source-tabs-row button.vqc-source-tab.active[disabled] span {{
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: linear-gradient(180deg, #ea580c 0%, #9a3412 100%) !important;
    border-color: #7c2d12 !important;
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
    color: #f5e6c8 !important;
    border-radius: 8px !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.04em !important;
    box-shadow: inset 0 1px 0 rgba(255, 220, 150, 0.15), 0 2px 4px rgba(0, 0, 0, 0.4) !important;
}}
.gradio-container .vqc-optics-panel button.vqc-receiver-preset:hover {{
    background: linear-gradient(180deg, #6b4f1d 0%, #3d2e14 100%) !important;
    color: #fff8e8 !important;
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
.gradio-container .myst-gravity-page .vqc-plot3d-panel,
.gradio-container .myst-gravity-page .vqc-plot3d-panel .block,
.gradio-container .myst-gravity-page .vqc-plot3d-panel img {{
    background-color: #000000 !important;
}}
.gradio-container .myst-gravity-split {{
    align-items: stretch !important;
    gap: 0.85rem !important;
    width: 100% !important;
}}
.gradio-container .myst-gravity-split > .column,
.gradio-container .myst-gravity-split > .block,
.gradio-container .myst-gravity-split > .form {{
    min-width: 0 !important;
}}
.gradio-container .myst-gravity-controls-col {{
    flex: 1 1 22rem !important;
    max-width: 28rem !important;
}}
.gradio-container .myst-gravity-visuals-col {{
    flex: 1 1 24rem !important;
    max-width: 34rem !important;
    align-items: center !important;
}}
.gradio-container .myst-gravity-page .myst-cube-viewport-frame.vqc-optics-panel {{
    width: 100% !important;
    max-width: 32rem !important;
    margin: 0 auto !important;
    padding: 0 0.75rem 0.85rem !important;
}}
.gradio-container .myst-gravity-page .myst-cube-viewport-header {{
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 0.08rem !important;
    width: 100% !important;
    margin: 0 0 0.55rem 0 !important;
    padding: 0.65rem 0.75rem 0.75rem !important;
    border-bottom: 1px solid rgba(74, 56, 24, 0.65) !important;
    border-radius: 10px 10px 0 0 !important;
    background: linear-gradient(180deg, #1f140a 0%, #0f0a06 100%) !important;
    box-shadow: inset 0 0 14px rgba(0, 0, 0, 0.55) !important;
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
.gradio-container .myst-cube-viewport-sub {{
    font-size: 0.64rem !important;
    letter-spacing: 0.18em !important;
    color: #9a8458 !important;
}}
.gradio-container .myst-gravity-page .myst-cube-viewport-frame .myst-cube-plot-inner,
.gradio-container .myst-gravity-page .myst-cube-viewport-frame .myst-cube-plot-inner.block {{
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0.45rem 0.55rem 0.55rem !important;
    background: rgba(0, 0, 0, 0.22) !important;
    border: 1px solid #4a3818 !important;
    border-radius: 10px !important;
}}
.gradio-container .myst-gravity-page .myst-cube-viewport-frame .myst-cube-plot-inner .label-wrap span {{
    color: #e8d4a8 !important;
    font-size: 0.76rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    font-weight: 700 !important;
}}
.gradio-container .myst-gravity-page .myst-cube-viewport-frame .plot-container {{
    min-height: 280px !important;
    max-height: 340px !important;
    border: 2px inset #5c4a1f !important;
    border-radius: 8px !important;
    background-color: #000000 !important;
    padding: 0.25rem !important;
    box-shadow: inset 0 0 18px rgba(0, 0, 0, 0.75) !important;
}}
.gradio-container .myst-gravity-page .myst-cube-viewport-frame .plot-container img,
.gradio-container .myst-gravity-page .myst-cube-viewport-frame .plot-container canvas {{
    max-height: 320px !important;
    width: auto !important;
    max-width: 100% !important;
    margin: 0 auto !important;
    display: block !important;
    object-fit: contain !important;
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
    color: #f5e6c8 !important;
}}
.gradio-container .myst-gravity-page .vqc-gravity-panel button.vqc-receiver-preset:hover {{
    background: linear-gradient(180deg, #6b4f1d 0%, #3d2e14 100%) !important;
    color: #fff8e8 !important;
}}
.gradio-container .myst-gravity-page .vqc-gravity-panel button.primary {{
    background: linear-gradient(180deg, #ea580c 0%, #9a3412 100%) !important;
    border: 2px solid #7c2d12 !important;
    color: #fff8e8 !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em !important;
}}
.gradio-container .myst-gravity-page .vqc-gravity-panel textarea {{
    background: #120c06 !important;
    border: 2px inset #5c4a1f !important;
    color: #ffb347 !important;
    font-family: "Courier New", Courier, monospace !important;
}}

.gradio-container .myst-gravity-visuals-col .markdown.prose {{
    font-size: 0.92rem !important;
    line-height: 1.45 !important;
}}
.gradio-container .myst-readme-page {{
    width: 100% !important;
}}
.gradio-container .myst-readme-page .markdown.prose {{
    font-size: 0.94rem !important;
    line-height: 1.5 !important;
}}
@media (max-width: 900px) {{
    .gradio-container .myst-gravity-controls-col,
    .gradio-container .myst-gravity-visuals-col {{
        max-width: 100% !important;
        flex: 1 1 100% !important;
    }}
}}
@media (max-width: 640px) {{
    .gradio-container .vqc-nav-spreadsheet-row {{
        grid-template-columns: 3.5rem repeat(6, minmax(2.8rem, 1fr)) !important;
        gap: 0.15rem 0.25rem !important;
    }}
    .gradio-container .vqc-source-tab,
    .gradio-container .vqc-source-tabs-row button.vqc-source-tab {{
        font-size: 0.78rem !important;
    }}
    .gradio-container .myst-gravity-page .myst-cube-viewport-frame {{
        max-width: 100% !important;
    }}
    .gradio-container .myst-gravity-page .myst-cube-viewport-frame .plot-container {{
        min-height: 240px !important;
        max-height: 300px !important;
    }}
}}
"""


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

        _init_re_metrics, _init_unit_cell = run_residual_explorer(
            1.0, 1.0, 1.0, KAPPA_DOC, 0.1, 1.0, 1.0, 0.35, 22.0, 45.0
        )

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

        with gr.Column(visible=True, elem_classes=["myst-gravity-page"]) as page_gravity:
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
            with gr.Row(elem_classes=["myst-gravity-split"], equal_height=False):
                with gr.Column(
                    scale=2,
                    min_width=300,
                    elem_classes=["myst-gravity-controls-col"],
                ):
                    with gr.Group(elem_classes=["vqc-optics-panel", "vqc-gravity-panel"]):
                        with gr.Row(elem_classes=["vqc-optics-panel-header"]):
                            gr.HTML(GRAVITY_OPTICS_LOGO_HTML)
                        gr.HTML(
                            '<p class="vqc-optics-presets-label">'
                            "Deformation &amp; view — drag dials, animate curvature sweep"
                            "</p>"
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
                            )
                        with gr.Row(elem_classes=["vqc-optics-dial-row"]):
                            re_view_elev = gr.Slider(
                                5.0,
                                75.0,
                                value=22.0,
                                step=1.0,
                                label="View elevation (°)",
                                elem_classes=["vqc-optics-dial-wrap"],
                            )
                            re_view_azim = gr.Slider(
                                0.0,
                                360.0,
                                value=45.0,
                                step=5.0,
                                label="View azimuth (°)",
                                elem_classes=["vqc-optics-dial-wrap"],
                            )
                        gr.HTML(
                            '<p class="vqc-optics-presets-label">'
                            "Residual explorer — φ² · e² · π² · κ · δ_z"
                            "</p>"
                        )
                        with gr.Row(elem_classes=["vqc-optics-dial-row"]):
                            re_phi_scale = gr.Slider(
                                0.90,
                                1.10,
                                value=1.0,
                                step=0.001,
                                label="φ² scale",
                                elem_classes=["vqc-optics-dial-wrap"],
                            )
                            re_e_scale = gr.Slider(
                                0.90,
                                1.10,
                                value=1.0,
                                step=0.001,
                                label="e² scale",
                                elem_classes=["vqc-optics-dial-wrap"],
                            )
                            re_pi_scale = gr.Slider(
                                0.90,
                                1.10,
                                value=1.0,
                                step=0.001,
                                label="π² scale",
                                elem_classes=["vqc-optics-dial-wrap"],
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
                            )
                            re_delta_z = gr.Slider(
                                0.0,
                                0.5,
                                value=0.1,
                                step=0.01,
                                label="δ_z (primary push)",
                                elem_classes=["vqc-optics-dial-wrap"],
                            )
                        with gr.Row(elem_classes=["vqc-optics-dial-row"]):
                            re_alpha = gr.Slider(
                                0.0,
                                2.0,
                                value=1.0,
                                step=0.05,
                                label="α (geometry factor)",
                                elem_classes=["vqc-optics-dial-wrap"],
                            )
                            re_beta = gr.Slider(
                                0.0,
                                2.0,
                                value=1.0,
                                step=0.05,
                                label="β (residual coupling)",
                                elem_classes=["vqc-optics-dial-wrap"],
                            )
                        gr.HTML(
                            '<p class="vqc-optics-presets-label">'
                            "Quick presets — one click sets dials"
                            "</p>"
                        )
                        with gr.Row():
                            re_preset_rigid = gr.Button(
                                "Rigid cube",
                                variant="secondary",
                                size="sm",
                                elem_classes=["vqc-receiver-preset"],
                            )
                            re_preset_full = gr.Button(
                                "Full deform",
                                variant="secondary",
                                size="sm",
                                elem_classes=["vqc-receiver-preset"],
                            )
                            re_preset_kappa_doc = gr.Button(
                                "κ_doc = 0.85",
                                variant="secondary",
                                size="sm",
                                elem_classes=["vqc-receiver-preset"],
                            )
                            re_preset_kappa_star = gr.Button(
                                "κ* null",
                                variant="secondary",
                                size="sm",
                                elem_classes=["vqc-receiver-preset"],
                            )
                        animate_deform_btn = gr.Button(
                            "Animate deformation",
                            variant="primary",
                            elem_classes=["vqc-full-width"],
                        )
                        re_metrics = gr.Textbox(
                            label="Explorer metrics",
                            lines=14,
                            interactive=False,
                            value=_init_re_metrics,
                        )
                with gr.Column(
                    scale=3,
                    elem_classes=["myst-gravity-visuals-col"],
                ):
                    with gr.Group(
                        elem_classes=[
                            "vqc-optics-panel",
                            "vqc-gravity-panel",
                            "myst-cube-viewport-frame",
                        ]
                    ):
                        gr.HTML(CUBE_VIEWPORT_HEADER_HTML)
                        unit_cell_plot = gr.Plot(
                            label="Deformable unit cell (no WebGL)",
                            value=_init_unit_cell,
                            elem_classes=["vqc-plot3d-panel", "myst-cube-plot-inner"],
                        )
            re_inputs = [
                re_phi_scale, re_e_scale, re_pi_scale,
                re_kappa, re_delta_z, re_alpha, re_beta, re_pressure,
                re_view_elev, re_view_azim,
            ]
            re_outputs = [re_metrics, unit_cell_plot]
            for slider in re_inputs:
                slider.change(run_residual_explorer, inputs=re_inputs, outputs=re_outputs)
            animate_deform_btn.click(
                stream_unit_cell_deformation,
                inputs=re_inputs,
                outputs=re_outputs,
            )
            re_preset_rigid.click(lambda: 0.0, outputs=[re_pressure]).then(
                run_residual_explorer, inputs=re_inputs, outputs=re_outputs
            )
            re_preset_full.click(lambda: 1.0, outputs=[re_pressure]).then(
                run_residual_explorer, inputs=re_inputs, outputs=re_outputs
            )
            re_preset_kappa_doc.click(load_kappa_doc, outputs=[re_kappa]).then(
                run_residual_explorer, inputs=re_inputs, outputs=re_outputs
            )
            re_preset_kappa_star.click(load_kappa_star, outputs=[re_kappa]).then(
                run_residual_explorer, inputs=re_inputs, outputs=re_outputs
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
                    run_residual_explorer, inputs=re_inputs, outputs=re_outputs
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

        gr.Markdown(
            "Research notebook — emergent signature, not forced identity · "
            f"[Mystery repo]({GITHUB_URL}) · [TOE parent]({TOE_URL})"
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

    launch_kwargs: dict = {
        "server_name": "0.0.0.0",
        "server_port": port,
        "show_error": True,
        "show_api": False,
        "inbrowser": False,
        "share": False if on_hf else True,
    }

    demo.queue(default_concurrency_limit=2).launch(**launch_kwargs)


if __name__ == "__main__":
    main()