"""
UI component for Current Scan box (Section 2 Left).
"""

from __future__ import annotations

import qt

from ..methods.current_scan_box import (
    on_dataset_text_changed,
    on_next_scan_clicked,
    on_prev_scan_clicked,
)
from ..styles import (
    BUTTON_PRIMARY_STYLE,
    BUTTON_SECONDARY_STYLE,
    LINE_EDIT_STYLE,
    PROGRESS_BAR_STYLE,
)


class CurrentScanBox:
    def __init__(self, main_widget=None, parent=None):
        self.main_widget = main_widget
        self.widget = qt.QGroupBox("Current Scan", parent)
        self.widget.setStyleSheet("QGroupBox { font-size: 11px; font-weight: bold; color: #aaa; }")
        self._setup_ui()

    def _setup_ui(self):
        scanLayout = qt.QVBoxLayout(self.widget)
        scanLayout.setSpacing(6)
        scanLayout.setContentsMargins(8, 12, 8, 8)

        # Row 1: Progress bar + scan count label
        progressRow = qt.QHBoxLayout()
        progressRow.setSpacing(8)

        self.progressBar = qt.QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setStyleSheet(PROGRESS_BAR_STYLE)
        progressRow.addWidget(self.progressBar, 1)

        self.scanCountLabel = qt.QLabel("0 / 0")
        self.scanCountLabel.setStyleSheet(
            "font-weight: bold; font-size: 11px; color: #90caf9; min-width: 55px;"
        )
        self.scanCountLabel.setAlignment(qt.Qt.AlignRight | qt.Qt.AlignVCenter)
        progressRow.addWidget(self.scanCountLabel)
        scanLayout.addLayout(progressRow)

        # Row 2: Clean image name
        self.imageNameLabel = qt.QLabel("Scan: No queue loaded")
        self.imageNameLabel.setStyleSheet(
            "font-size: 11px; font-weight: bold; color: #ffffff; margin-top: 1px;"
        )
        scanLayout.addWidget(self.imageNameLabel)

        # Row 3: Dataset textbox
        datasetRow = qt.QHBoxLayout()
        datasetRow.setSpacing(6)
        datasetLabel = qt.QLabel("Dataset:")
        datasetLabel.setStyleSheet("font-size: 10px; color: #aaa;")
        self.datasetLineEdit = qt.QLineEdit()
        self.datasetLineEdit.setPlaceholderText("e.g. TotalSegmentator, Verse...")
        self.datasetLineEdit.setStyleSheet(LINE_EDIT_STYLE)
        datasetRow.addWidget(datasetLabel)
        datasetRow.addWidget(self.datasetLineEdit)
        scanLayout.addLayout(datasetRow)

        # Row 4: Stacked navigation buttons (Prev on top, Save & Next below)
        navCol = qt.QVBoxLayout()
        navCol.setSpacing(4)

        self.prevScanButton = qt.QPushButton("<< Previous Scan  [ B ]")
        self.prevScanButton.setStyleSheet(BUTTON_SECONDARY_STYLE)
        navCol.addWidget(self.prevScanButton)

        self.nextScanButton = qt.QPushButton("Save && Next Scan  [ Space ] >>")
        self.nextScanButton.setStyleSheet(BUTTON_PRIMARY_STYLE)
        navCol.addWidget(self.nextScanButton)
        scanLayout.addLayout(navCol)

        # Row 5: Unreviewed count anchored at the very bottom
        scanLayout.addStretch(1)
        self.unreviewedCountLabel = qt.QLabel("⏳ Unreviewed: 0")
        self.unreviewedCountLabel.setStyleSheet("font-size: 10px; color: #ffb74d; margin-top: 2px;")
        scanLayout.addWidget(self.unreviewedCountLabel)

        if self.main_widget:
            self.datasetLineEdit.textChanged.connect(
                lambda text: on_dataset_text_changed(self.main_widget, text)
            )
            self.prevScanButton.clicked.connect(
                lambda *args: on_prev_scan_clicked(self.main_widget)
            )
            self.nextScanButton.clicked.connect(
                lambda *args: on_next_scan_clicked(self.main_widget)
            )

    def update_progress(self, current_index: int, total_count: int):
        if total_count > 0:
            pct = int(((current_index + 1) / total_count) * 100)
            self.progressBar.setValue(pct)
            self.scanCountLabel.setText(f"{current_index + 1} / {total_count}")
        else:
            self.progressBar.setValue(0)
            self.scanCountLabel.setText("0 / 0")

    def set_scan_id(self, scan_id: str):
        self.imageNameLabel.setText(f"Scan: {scan_id}")

    def set_dataset(self, dataset: str):
        self.datasetLineEdit.blockSignals(True)
        self.datasetLineEdit.setText(dataset or "")
        self.datasetLineEdit.blockSignals(False)

    def set_unreviewed_count(self, count: int):
        self.unreviewedCountLabel.setText(f"⏳ Unreviewed: {count}")
