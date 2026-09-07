"""
UI component for Section 1: Setup / Input Directories.
Provides separate inputs for Predictions (DL) and Ground Truth segmentations.
"""

from __future__ import annotations

import os
import ctk
import qt

from ..methods.setup_box import on_load_queue_clicked


class SetupBox:
    def __init__(self, main_widget=None, parent=None):
        self.main_widget = main_widget
        self.widget = ctk.ctkCollapsibleButton(parent)
        self.widget.text = "1. Setup / Input Directories"
        self._setup_ui()

    def _setup_ui(self):
        formLayout = qt.QFormLayout(self.widget)
        formLayout.setSpacing(6)
        formLayout.setContentsMargins(6, 6, 6, 6)

        # 1. Predictions directory (DL model outputs)
        self.predSegsDirSelector = ctk.ctkPathLineEdit()
        self.predSegsDirSelector.filters = ctk.ctkPathLineEdit.Dirs
        self.predSegsDirSelector.settingKey = "SegmentationReviewer/PredSegsDir"
        default_pred_dir = "/home/scarreras/Projects/predictions_ts_fast"
        if os.path.exists(default_pred_dir):
            self.predSegsDirSelector.setCurrentPath(default_pred_dir)
        formLayout.addRow("Predictions (DL) *:", self.predSegsDirSelector)

        # 2. Ground Truth directory (Reference masks - OPTIONAL)
        self.gtSegsDirSelector = ctk.ctkPathLineEdit()
        self.gtSegsDirSelector.filters = ctk.ctkPathLineEdit.Dirs
        self.gtSegsDirSelector.settingKey = "SegmentationReviewer/GTSegsDir"
        formLayout.addRow("Ground Truth:", self.gtSegsDirSelector)

        # 3. Volume / CT directory (OPTIONAL)
        self.scansDirSelector = ctk.ctkPathLineEdit()
        self.scansDirSelector.filters = ctk.ctkPathLineEdit.Dirs
        self.scansDirSelector.settingKey = "SegmentationReviewer/ScansDir"
        formLayout.addRow("Volume:", self.scansDirSelector)

        # 4. QC JSONs path (OPTIONAL: file or directory)
        self.qcJsonSelector = ctk.ctkPathLineEdit()
        self.qcJsonSelector.filters = ctk.ctkPathLineEdit.Files | ctk.ctkPathLineEdit.Dirs
        self.qcJsonSelector.settingKey = "SegmentationReviewer/QCJsonPath"
        default_qc_dir = "/home/scarreras/Projects/Spine/data/qc"
        if os.path.exists(default_qc_dir):
            self.qcJsonSelector.setCurrentPath(default_qc_dir)
        formLayout.addRow("QC JSONs:", self.qcJsonSelector)

        # 5. Output Directory (MANDATORY)
        self.outputDirSelector = ctk.ctkPathLineEdit()
        self.outputDirSelector.filters = ctk.ctkPathLineEdit.Dirs
        self.outputDirSelector.settingKey = "SegmentationReviewer/OutputDir"
        default_out_dir = "/home/scarreras/Projects/Spine/data/qc"
        if os.path.exists(default_out_dir):
            self.outputDirSelector.setCurrentPath(default_out_dir)
        formLayout.addRow("Output Folder *:", self.outputDirSelector)

        # 6. Load Queue Button
        self.loadQueueButton = qt.QPushButton("Load Queue && Start Review")
        self.loadQueueButton.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 12px;
                padding: 7px 12px;
                background-color: #1b2836;
                color: #90caf9;
                border: 1px solid #28425d;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #223547;
                color: #bbdefb;
            }
        """)
        formLayout.addRow(self.loadQueueButton)

        if self.main_widget:
            self.loadQueueButton.clicked.connect(
                lambda *args: on_load_queue_clicked(self.main_widget)
            )
