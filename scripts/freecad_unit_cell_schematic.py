#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mystery φ-e-π unit-cell schematic for FreeCAD.

Matches the HF Space Gravity tab styling:
  • 90% transparent cube faces (blue)
  • Matrix-green (#33ff66) edge lines
  • Red / green / blue leader lines + larger equation labels
  • δ_z and δ_side deformation arrows

How to run
----------
1. Open FreeCAD (0.21+ or 1.0 recommended).
2. Macro → Macros… → create/open this file → Execute
   OR: File → Open → select this .py (if configured as macro)
   OR: paste into the Python console (run line-by-line if imports fail).

Optional: set CREATE_NEW_DOC = False to build into the active document.
"""

from __future__ import annotations

import math

import FreeCAD as App
import Part

try:
    import Draft
except ImportError as exc:  # pragma: no cover - FreeCAD runtime only
    raise ImportError("Draft workbench is required for labels and leader lines.") from exc


def _draft_make_line(p1: App.Vector, p2: App.Vector):
    if hasattr(Draft, "make_line"):
        return Draft.make_line(p1, p2)
    return Draft.makeLine(p1, p2)


def _draft_make_text(text: str, point: App.Vector):
    if hasattr(Draft, "make_text"):
        return Draft.make_text(text, point=point)
    return Draft.makeText([text], point=point)

# ---------------------------------------------------------------------------
# Styling — keep in sync with space/mystery/demo_core.py
# ---------------------------------------------------------------------------
S = 1.0
R_SHOW = 0.137486
DELTA_Z = 0.15
DELTA_SIDE = 0.08

MATRIX_GREEN = "#33ff66"
EQ_RED = "#e63946"
EQ_GREEN = "#22c55e"
EQ_BLUE = "#2563eb"
CAPTION_NEUTRAL = "#e8e0f8"

FACE_TRANSPARENCY = 90  # FreeCAD: 0 = opaque, 100 = fully transparent
LABEL_FONT_MAIN = 22
LABEL_FONT_SMALL = 18
CAPTION_FONT = 17
EDGE_LINE_WIDTH = 3
LEADER_LINE_WIDTH = 2
ARROW_LINE_WIDTH = 3

CREATE_NEW_DOC = True
DOC_NAME = "MysteryUnitCell"


def hex_rgb(hex_color: str) -> tuple[float, float, float]:
    value = hex_color.lstrip("#")
    return tuple(int(value[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def _set_line_style(obj, color_hex: str, width: float) -> None:
    view = obj.ViewObject
    view.LineColor = hex_rgb(color_hex)
    view.LineWidth = width


def _make_text(
    doc: App.Document,
    text: str,
    point: App.Vector,
    color_hex: str,
    font_size: float,
) -> App.DocumentObject:
    """Create a Draft text label at a 3D point."""
    label = _draft_make_text(text, point)
    label.Label = text.replace(" ", "_")[:40]
    view = label.ViewObject
    view.FontSize = font_size
    view.TextColor = hex_rgb(color_hex)
    doc.recompute()
    return label


def _make_leader_label(
    doc: App.Document,
    anchor: tuple[float, float, float],
    label_pos: tuple[float, float, float],
    text: str,
    color_hex: str,
    *,
    font_size: float,
) -> tuple[App.DocumentObject, App.DocumentObject]:
    start = App.Vector(*anchor)
    end = App.Vector(*label_pos)
    leader = _draft_make_line(start, end)
    leader.Label = f"Leader_{text[:12]}"
    _set_line_style(leader, color_hex, LEADER_LINE_WIDTH)
    label = _make_text(doc, text, end, color_hex, font_size)
    doc.recompute()
    return leader, label


def _make_arrow(
    doc: App.Document,
    origin: tuple[float, float, float],
    direction: tuple[float, float, float],
    color_hex: str,
    name: str,
) -> App.DocumentObject:
    start = App.Vector(*origin)
    end = start + App.Vector(*direction)
    shaft = _draft_make_line(start, end)
    shaft.Label = name
    _set_line_style(shaft, color_hex, ARROW_LINE_WIDTH)
    doc.recompute()
    return shaft


def _cube_edges(s: float) -> tuple[tuple[tuple[float, float, float], tuple[float, float, float]], ...]:
    return (
        ((-s, -s, -s), (s, -s, -s)),
        ((s, -s, -s), (s, s, -s)),
        ((s, s, -s), (-s, s, -s)),
        ((-s, s, -s), (-s, -s, -s)),
        ((-s, -s, s), (s, -s, s)),
        ((s, -s, s), (s, s, s)),
        ((s, s, s), (-s, s, s)),
        ((-s, s, s), (-s, -s, s)),
        ((-s, -s, -s), (-s, -s, s)),
        ((s, -s, -s), (s, -s, s)),
        ((s, s, -s), (s, s, s)),
        ((-s, s, -s), (-s, s, s)),
    )


def build_unit_cell(doc: App.Document | None = None) -> App.Document:
    """Build the Mystery unit-cell schematic in a FreeCAD document."""
    if doc is None:
        if CREATE_NEW_DOC or not App.ActiveDocument:
            doc = App.newDocument(DOC_NAME)
        else:
            doc = App.ActiveDocument

    group = doc.addObject("App::DocumentObjectGroup", "MysteryUnitCell")

    # Semi-transparent cube (2×2×2 centered on origin)
    cube = doc.addObject("Part::Box", "UnitCellCube")
    cube.Length = 2 * S
    cube.Width = 2 * S
    cube.Height = 2 * S
    cube.Placement.Base = App.Vector(-S, -S, -S)
    cube_view = cube.ViewObject
    cube_view.ShapeColor = hex_rgb(EQ_BLUE)
    cube_view.Transparency = FACE_TRANSPARENCY
    cube_view.LineColor = hex_rgb(MATRIX_GREEN)
    cube_view.LineWidth = EDGE_LINE_WIDTH
    cube_view.DisplayMode = "Flat Lines"
    group.addObject(cube)

    # Explicit matrix-green edges (crisp on top of shaded faces)
    edges_group = doc.addObject("App::DocumentObjectGroup", "CubeEdges")
    group.addObject(edges_group)
    for idx, (p0, p1) in enumerate(_cube_edges(S), start=1):
        edge = _draft_make_line(App.Vector(*p0), App.Vector(*p1))
        edge.Label = f"Edge_{idx:02d}"
        _set_line_style(edge, MATRIX_GREEN, EDGE_LINE_WIDTH)
        edges_group.addObject(edge)

    # Deformation arrows (δ_z push, δ_side on φ / e faces)
    arrows_group = doc.addObject("App::DocumentObjectGroup", "DeformationArrows")
    group.addObject(arrows_group)
    side = abs(DELTA_SIDE)
    arrow_specs = (
        ("DeltaZ_Push", (0.0, 0.0, S + 0.1), (0.0, 0.0, -DELTA_Z * 2.0), EQ_BLUE),
        ("DeltaSide_Phi", (-S - 0.1, 0.0, 0.0), (side * 2.0, 0.0, 0.0), EQ_RED),
        ("DeltaSide_E", (S + 0.1, 0.0, 0.0), (-side * 2.0, 0.0, 0.0), EQ_GREEN),
    )
    for name, origin, direction, color in arrow_specs:
        arr = _make_arrow(doc, origin, direction, color, name)
        arrows_group.addObject(arr)

    # Leader lines + equation labels (larger text, color-matched)
    labels_group = doc.addObject("App::DocumentObjectGroup", "EquationLabels")
    group.addObject(labels_group)
    label_specs = (
        ((S, 0.0, 0.0), (2.35, 0.45, 0.25), "Tφ ∝ φ²", EQ_RED, LABEL_FONT_MAIN),
        ((0.0, S, 0.0), (0.45, 2.35, 0.25), "Te ∝ e²", EQ_GREEN, LABEL_FONT_MAIN),
        ((0.0, 0.0, S), (0.45, 0.25, 2.35), "Tπ ∝ π²", EQ_BLUE, LABEL_FONT_MAIN),
        ((-S, 0.0, 0.0), (-2.35, -0.55, 0.35), "δside (inward)", EQ_GREEN, LABEL_FONT_SMALL),
        ((0.0, 0.0, S), (-0.55, -2.25, 2.35), "δz (push)", EQ_BLUE, LABEL_FONT_SMALL),
    )
    for anchor, label_pos, text, color, font_size in label_specs:
        leader, label = _make_leader_label(
            doc, anchor, label_pos, text, color, font_size=font_size
        )
        labels_group.addObject(leader)
        labels_group.addObject(label)

    # Residual caption (3D text below the scene)
    caption = (
        f"R = φ² + e² − π² ≈ {R_SHOW:+.3f}  drives net δside contraction"
    )
    caption_obj = _make_text(
        doc,
        caption,
        App.Vector(-2.1, -2.4, -2.2),
        CAPTION_NEUTRAL,
        CAPTION_FONT,
    )
    caption_obj.Label = "ResidualCaption"
    group.addObject(caption_obj)

    # Axis hint labels (φ / e / π faces)
    axes_group = doc.addObject("App::DocumentObjectGroup", "AxisHints")
    group.addObject(axes_group)
    for text, point, color in (
        ("φ-face", App.Vector(2.55, -2.35, -2.15), "#a89ec8"),
        ("e-face", App.Vector(-2.55, 2.55, -2.15), "#a89ec8"),
        ("π-face", App.Vector(-2.55, -2.35, 2.55), "#a89ec8"),
    ):
        hint = _make_text(doc, text, point, color, 12)
        axes_group.addObject(hint)

    doc.recompute()

    try:
        import FreeCADGui as Gui  # noqa: WPS433

        if Gui.ActiveDocument:
            Gui.ActiveDocument.ActiveView.viewIsometric()
            Gui.SendMsgToActiveView("ViewFit")
    except (ImportError, AttributeError):
        pass

    App.Console.PrintMessage(
        "Mystery unit cell built — 90% transparent faces, matrix-green edges.\n"
    )
    return doc


if __name__ == "__main__":
    build_unit_cell()