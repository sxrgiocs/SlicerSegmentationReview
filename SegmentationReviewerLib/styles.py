"""
Styles, themes, and UI widget styling for SpineQCReviewer.
"""

from __future__ import annotations

import qt


PROGRESS_BAR_STYLE = """
QProgressBar {
    border: 1px solid #373e48;
    border-radius: 4px;
    height: 20px;
    background-color: #1b1e22;
}
QProgressBar::chunk {
    background-color: #204566;
    border-radius: 3px;
}
"""

LINE_EDIT_STYLE = """
QLineEdit {
    background-color: #1b1e22;
    color: #e0e0e0;
    border: 1px solid #373e48;
    border-radius: 3px;
    padding: 3px 5px;
    font-size: 11px;
}
QLineEdit:focus {
    border-color: #1976d2;
}
"""

BUTTON_PRIMARY_STYLE = """
QPushButton {
    padding: 6px 10px;
    font-weight: bold;
    font-size: 10px;
    background-color: #172a3e;
    color: #90caf9;
    border: 1px solid #234768;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #1f3752;
    color: #bbdefb;
}
"""

BUTTON_SECONDARY_STYLE = """
QPushButton {
    padding: 6px 10px;
    font-weight: bold;
    font-size: 10px;
    background-color: #24272c;
    color: #bbb;
    border: 1px solid #3c424a;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #2e333a;
    color: #fff;
}
"""

BUTTON_FAIL_STYLE = """
QPushButton {
    font-size: 11px;
    font-weight: bold;
    padding: 8px 6px;
    background-color: #281c1e;
    color: #ef9a9a;
    border: 1px solid #5a2225;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #352326;
    border-color: #c62828;
    color: #ffcdd2;
}
"""

BUTTON_PASS_STYLE = """
QPushButton {
    font-size: 11px;
    font-weight: bold;
    padding: 8px 6px;
    background-color: #18261b;
    color: #a5d6a7;
    border: 1px solid #264a2b;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #203324;
    border-color: #2e7d32;
    color: #c8e6c9;
}
"""

BUTTON_TOOL_BOX_STYLE = """
QPushButton {
    font-size: 11px;
    font-weight: bold;
    padding: 6px 4px;
    background-color: #1a2530;
    color: #90caf9;
    border: 1px solid #284059;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #233342;
}
"""

BUTTON_TOOL_POINT_STYLE = """
QPushButton {
    font-size: 11px;
    font-weight: bold;
    padding: 6px 4px;
    background-color: #231c2d;
    color: #ce93d8;
    border: 1px solid #432b59;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #2d233a;
}
"""

BUTTON_LABEL_EDITOR_STYLE = """
QPushButton {
    background-color: #25282c;
    color: #cfd8dc;
    border: 1px solid #3d4249;
    border-radius: 3px;
    padding: 2px 6px;
    height: 22px;
    min-height: 22px;
    font-size: 10px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #2e3338;
    color: #ffffff;
}
"""

BUTTON_DELETE_LABEL_STYLE = """
QPushButton {
    background-color: #25282c;
    color: #ef9a9a;
    border: 1px solid #3d4249;
    border-radius: 3px;
    padding: 2px 8px;
    height: 22px;
    min-height: 22px;
    font-size: 10px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #382528;
}
"""

TABLE_STYLE = """
QTableWidget {
    background-color: #1e2126;
    alternate-background-color: #23272d;
    gridline-color: #2b2f36;
    border: 1px solid #333842;
    border-radius: 4px;
    selection-background-color: #25384d;
    selection-color: #ffffff;
    font-size: 11px;
}
QTableWidget::item {
    padding: 4px 6px;
    border-bottom: 1px solid #282c33;
}
QHeaderView::section {
    background-color: #272b32;
    color: #a0a6b0;
    padding: 4px 6px;
    border: 1px solid #30343c;
    font-weight: bold;
    font-size: 11px;
}
"""

SEGMENTS_TABLE_STYLE = """
qMRMLSegmentsTableView {
    background-color: #1e2126;
    border: 1px solid #333842;
    border-radius: 3px;
    font-size: 10px;
}
"""


def create_verdict_badge(eval_val: int | None) -> qt.QLabel:
    """
    Creates a solid color badge widget that maintains its background
    even when the row is selected in QTableWidget.
    - PASS: 1 (Green)
    - FAIL: 0 (Red)
    - UNREVIEWED: None (Gold/Yellow)
    """
    verdict_text = "UNREVIEWED"
    bg_hex = "#c68400"
    text_hex = "#ffffff"

    if eval_val == 1:
        verdict_text = "PASS"
        bg_hex = "#2e7d32"
        text_hex = "#ffffff"
    elif eval_val == 0:
        verdict_text = "FAIL"
        bg_hex = "#c62828"
        text_hex = "#ffffff"

    badge = qt.QLabel(verdict_text)
    badge.setAlignment(qt.Qt.AlignCenter)
    badge.setStyleSheet(f"""
        QLabel {{
            background-color: {bg_hex};
            color: {text_hex};
            font-weight: bold;
            font-size: 11px;
            border-radius: 3px;
            margin: 2px 4px;
        }}
    """)
    return badge
