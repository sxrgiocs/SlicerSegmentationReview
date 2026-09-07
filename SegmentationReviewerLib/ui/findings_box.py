"""
UI component for Section 3: Findings (75% Table / 25% Action Buttons).
"""

from __future__ import annotations

import ctk
import qt

from ..methods.findings_box import (
    on_add_landmark_clicked,
    on_add_missed_box_clicked,
    on_edit_finding_clicked,
    on_finish_placement_clicked,
    on_manual_save_clicked,
    on_mark_fail_clicked,
    on_mark_pass_clicked,
    on_remove_finding_clicked,
    on_table_item_changed,
    on_table_selection_changed,
)
from ..styles import (
    BUTTON_FAIL_STYLE,
    BUTTON_PASS_STYLE,
    BUTTON_SECONDARY_STYLE,
    BUTTON_TOOL_BOX_STYLE,
    BUTTON_TOOL_POINT_STYLE,
    TABLE_STYLE,
    create_verdict_badge,
)


class FindingsBox:
    def __init__(self, main_widget=None, parent=None):
        self.main_widget = main_widget
        self.widget = ctk.ctkCollapsibleButton(parent)
        self.widget.text = "3. Findings"
        self._setup_ui()

    def _setup_ui(self):
        mainLayout = qt.QVBoxLayout(self.widget)
        mainLayout.setSpacing(4)
        mainLayout.setContentsMargins(6, 6, 6, 6)

        # Drawing / Editing banner across top of section
        self.drawingBanner = qt.QLabel("📍 INTERACTION ACTIVE")
        self.drawingBanner.setStyleSheet(
            "background-color: #ff9800; color: black; font-weight: bold; "
            "padding: 5px; border-radius: 3px; font-size: 11px;"
        )
        self.drawingBanner.setVisible(False)
        mainLayout.addWidget(self.drawingBanner)

        self.finishDrawingButton = qt.QPushButton("✓ Done Editing / Placing")
        self.finishDrawingButton.setStyleSheet(
            "background-color: #2e7d32; color: white; font-weight: bold; "
            "padding: 5px; border-radius: 3px; border: 1px solid #2e7d32;"
        )
        self.finishDrawingButton.setVisible(False)
        mainLayout.addWidget(self.finishDrawingButton)

        # Horizontal layout: 75% Table on Left, 25% Buttons on Right
        rowLayout = qt.QHBoxLayout()
        rowLayout.setSpacing(8)

        # 75% Left: Table
        self.boxesTable = qt.QTableWidget()
        self.boxesTable.setColumnCount(4)
        self.boxesTable.setHorizontalHeaderLabels(["Finding #", "Type", "Details", "Verdict"])
        self.boxesTable.horizontalHeader().setSectionResizeMode(0, qt.QHeaderView.ResizeToContents)
        self.boxesTable.horizontalHeader().setSectionResizeMode(1, qt.QHeaderView.ResizeToContents)
        self.boxesTable.horizontalHeader().setSectionResizeMode(2, qt.QHeaderView.Stretch)
        self.boxesTable.horizontalHeader().setSectionResizeMode(3, qt.QHeaderView.ResizeToContents)
        self.boxesTable.setSelectionBehavior(qt.QAbstractItemView.SelectRows)
        self.boxesTable.setSelectionMode(qt.QAbstractItemView.SingleSelection)
        self.boxesTable.setMinimumHeight(170)
        self.boxesTable.setAlternatingRowColors(True)
        self.boxesTable.setStyleSheet(TABLE_STYLE)
        rowLayout.addWidget(self.boxesTable, 3)

        # 25% Right: Action Buttons Column
        buttonsCol = qt.QVBoxLayout()
        buttonsCol.setSpacing(5)

        self.failButton = qt.QPushButton("FAIL  [ 1 ]")
        self.failButton.setStyleSheet(BUTTON_FAIL_STYLE)
        buttonsCol.addWidget(self.failButton)

        self.passButton = qt.QPushButton("PASS  [ 2 ]")
        self.passButton.setStyleSheet(BUTTON_PASS_STYLE)
        buttonsCol.addWidget(self.passButton)

        buttonsCol.addSpacing(2)

        self.addMissedBoxButton = qt.QPushButton("+ Box  [ A ]")
        self.addMissedBoxButton.setStyleSheet(BUTTON_TOOL_BOX_STYLE)
        buttonsCol.addWidget(self.addMissedBoxButton)

        self.addLandmarkButton = qt.QPushButton("+ Point  [ L ]")
        self.addLandmarkButton.setStyleSheet(BUTTON_TOOL_POINT_STYLE)
        buttonsCol.addWidget(self.addLandmarkButton)

        self.editFindingButton = qt.QPushButton("Edit  [ E ]")
        self.editFindingButton.setStyleSheet(BUTTON_SECONDARY_STYLE)
        buttonsCol.addWidget(self.editFindingButton)

        self.removeFindingButton = qt.QPushButton("Remove  [ Del ]")
        self.removeFindingButton.setStyleSheet(BUTTON_SECONDARY_STYLE)
        buttonsCol.addWidget(self.removeFindingButton)

        buttonsCol.addSpacing(2)

        self.evaluateWholeImageCheckbox = qt.QCheckBox("Whole image")
        self.evaluateWholeImageCheckbox.setStyleSheet("color: #aaa; font-size: 10px;")
        buttonsCol.addWidget(self.evaluateWholeImageCheckbox)

        self.autoAdvanceCheckbox = qt.QCheckBox("Auto-advance")
        self.autoAdvanceCheckbox.setChecked(True)
        self.autoAdvanceCheckbox.setStyleSheet("color: #aaa; font-size: 10px;")
        buttonsCol.addWidget(self.autoAdvanceCheckbox)

        self.manualSaveButton = qt.QPushButton("Save")
        self.manualSaveButton.setStyleSheet(BUTTON_SECONDARY_STYLE)
        buttonsCol.addWidget(self.manualSaveButton)

        buttonsCol.addStretch(1)
        rowLayout.addLayout(buttonsCol, 1)

        mainLayout.addLayout(rowLayout)

        if self.main_widget:
            self.finishDrawingButton.clicked.connect(
                lambda *args: on_finish_placement_clicked(self.main_widget)
            )
            self.boxesTable.itemSelectionChanged.connect(
                lambda *args: on_table_selection_changed(self.main_widget)
            )
            self.boxesTable.itemChanged.connect(
                lambda item: on_table_item_changed(self.main_widget, item)
            )
            self.failButton.clicked.connect(
                lambda *args: on_mark_fail_clicked(self.main_widget)
            )
            self.passButton.clicked.connect(
                lambda *args: on_mark_pass_clicked(self.main_widget)
            )
            self.addMissedBoxButton.clicked.connect(
                lambda *args: on_add_missed_box_clicked(self.main_widget)
            )
            self.addLandmarkButton.clicked.connect(
                lambda *args: on_add_landmark_clicked(self.main_widget)
            )
            self.editFindingButton.clicked.connect(
                lambda *args: on_edit_finding_clicked(self.main_widget)
            )
            self.removeFindingButton.clicked.connect(
                lambda *args: on_remove_finding_clicked(self.main_widget)
            )
            self.manualSaveButton.clicked.connect(
                lambda *args: on_manual_save_clicked(self.main_widget)
            )

    def populate_table(self, boxes: list[dict]):
        self.boxesTable.blockSignals(True)
        self.boxesTable.setRowCount(len(boxes))

        for row, box in enumerate(boxes):
            kind = "Point" if ("landmark" in box and "bbox" not in box) else "Box"
            num_text = f"#{box['box_id']} ({kind})"
            if box.get("source") == "manual":
                num_text += " [M]"
            item_id = qt.QTableWidgetItem(num_text)
            item_id.setFlags(qt.Qt.ItemIsEnabled | qt.Qt.ItemIsSelectable)
            self.boxesTable.setItem(row, 0, item_id)

            item_type = qt.QTableWidgetItem(str(box.get("type", "islands")))
            item_type.setFlags(qt.Qt.ItemIsEnabled | qt.Qt.ItemIsSelectable | qt.Qt.ItemIsEditable)
            self.boxesTable.setItem(row, 1, item_type)

            details = str(box.get("description", ""))
            item_det = qt.QTableWidgetItem(details)
            item_det.setFlags(qt.Qt.ItemIsEnabled | qt.Qt.ItemIsSelectable | qt.Qt.ItemIsEditable)
            self.boxesTable.setItem(row, 2, item_det)

            # Solid color badge widget (persists even when row is selected)
            eval_val = box.get("eval", None)
            badge_widget = create_verdict_badge(eval_val)
            self.boxesTable.setCellWidget(row, 3, badge_widget)

        self.boxesTable.blockSignals(False)

    def show_banner(self, text: str):
        self.drawingBanner.setText(text)
        self.drawingBanner.setVisible(True)
        self.finishDrawingButton.setVisible(True)

    def hide_banner(self):
        self.drawingBanner.setVisible(False)
        self.finishDrawingButton.setVisible(False)

    def get_selected_row(self) -> int:
        selected_rows = self.boxesTable.selectionModel().selectedRows()
        if selected_rows:
            return selected_rows[0].row()
        return -1

    def select_row(self, row: int):
        if 0 <= row < self.boxesTable.rowCount:
            self.boxesTable.selectRow(row)
