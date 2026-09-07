"""
UI component for Label Editor box (Section 2 Right).
Includes segment opacity slider, 3D model toggle, segment deletion,
and dual-segmentation switching (Predictions vs Ground Truth).
"""

from __future__ import annotations

import qt
import slicer

from ..methods.label_editor_box import (
    on_delete_selected_segment_clicked,
    on_fill_opacity_changed,
    on_segmentation_choice_changed,
    on_show_3d_surface_clicked,
    on_toggle_fill_clicked,
    on_toggle_gt_overlay_clicked,
)
from ..styles import (
    BUTTON_DELETE_LABEL_STYLE,
    BUTTON_LABEL_EDITOR_STYLE,
    SEGMENTS_TABLE_STYLE,
)


class LabelEditorBox:
    def __init__(self, main_widget=None, parent=None):
        self.main_widget = main_widget
        self.widget = qt.QGroupBox("Label Editor", parent)
        self.widget.setStyleSheet("QGroupBox { font-size: 11px; font-weight: bold; color: #aaa; }")
        self._setup_ui()

    def _setup_ui(self):
        layout = qt.QVBoxLayout(self.widget)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 12, 8, 8)

        # Row 0: Dual Segmentation Switcher (Predictions vs Ground Truth)
        self.dualSegRow = qt.QHBoxLayout()
        self.dualSegRow.setSpacing(6)

        segLabel = qt.QLabel("Active Seg:")
        segLabel.setStyleSheet("font-size: 10px; color: #aaa;")
        self.dualSegRow.addWidget(segLabel)

        self.segSelectorCombo = qt.QComboBox()
        self.segSelectorCombo.addItems(["Predictions", "Ground Truth"])
        self.segSelectorCombo.setStyleSheet("""
            QComboBox {
                font-size: 10px;
                padding: 2px 6px;
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 3px;
                min-height: 20px;
            }
        """)
        self.dualSegRow.addWidget(self.segSelectorCombo, 1)

        self.toggleGtOverlayButton = qt.QPushButton("GT Overlay")
        self.toggleGtOverlayButton.setStyleSheet(BUTTON_LABEL_EDITOR_STYLE)
        self.toggleGtOverlayButton.setToolTip("Toggle visibility of Ground Truth reference segmentation")
        self.dualSegRow.addWidget(self.toggleGtOverlayButton)

        # Initially hidden until a scan with GT is loaded
        self.dualSegContainer = qt.QWidget()
        self.dualSegContainer.setLayout(self.dualSegRow)
        self.dualSegContainer.setVisible(False)
        layout.addWidget(self.dualSegContainer)

        # Row 1: Fill slider, Fill toggle, 3D toggle
        controlsRow = qt.QHBoxLayout()
        controlsRow.setSpacing(5)

        self.fillOpacityLabel = qt.QLabel("Fill: 25%")
        self.fillOpacityLabel.setStyleSheet("font-size: 10px; color: #bbb; min-width: 50px;")
        controlsRow.addWidget(self.fillOpacityLabel)

        self.fillOpacitySlider = qt.QSlider(qt.Qt.Horizontal)
        self.fillOpacitySlider.setRange(0, 100)
        self.fillOpacitySlider.setValue(25)
        self.fillOpacitySlider.setTickPosition(qt.QSlider.TicksBelow)
        self.fillOpacitySlider.setTickInterval(20)
        controlsRow.addWidget(self.fillOpacitySlider)

        self.toggleFillButton = qt.QPushButton("Fill")
        self.toggleFillButton.setStyleSheet(BUTTON_LABEL_EDITOR_STYLE)
        controlsRow.addWidget(self.toggleFillButton)

        self.show3DSurfaceButton = qt.QPushButton("3D")
        self.show3DSurfaceButton.setIcon(qt.QIcon(":/Icons/MakeModel.png"))
        self.show3DSurfaceButton.setStyleSheet(BUTTON_LABEL_EDITOR_STYLE)
        controlsRow.addWidget(self.show3DSurfaceButton)
        layout.addLayout(controlsRow)

        # Row 2: Segments Table
        if hasattr(slicer, "qMRMLSegmentsTableView"):
            self.segmentsTable = slicer.qMRMLSegmentsTableView()
            self.segmentsTable.setMRMLScene(slicer.mrmlScene)
            self.segmentsTable.headerVisible = True
            self.segmentsTable.visibilityColumnVisible = True
            self.segmentsTable.colorColumnVisible = True
            self.segmentsTable.opacityColumnVisible = False
            self.segmentsTable.filterBarVisible = True
            self.segmentsTable.setMinimumHeight(115)
            self.segmentsTable.setMaximumHeight(150)
            self.segmentsTable.setStyleSheet(SEGMENTS_TABLE_STYLE)
            layout.addWidget(self.segmentsTable)

            # Row 3: Delete / Remove segment button
            actionRow = qt.QHBoxLayout()
            self.deleteSegmentButton = qt.QPushButton("Remove")
            self.deleteSegmentButton.setIcon(qt.QIcon(":/Icons/Remove.png"))
            self.deleteSegmentButton.setStyleSheet(BUTTON_DELETE_LABEL_STYLE)
            actionRow.addWidget(self.deleteSegmentButton)
            actionRow.addStretch(1)
            layout.addLayout(actionRow)
        else:
            self.segmentsTable = None
            self.deleteSegmentButton = None

        layout.addStretch(1)

        if self.main_widget:
            self.fillOpacitySlider.valueChanged.connect(
                lambda val: on_fill_opacity_changed(self.main_widget, val)
            )
            self.toggleFillButton.clicked.connect(
                lambda *args: on_toggle_fill_clicked(self.main_widget)
            )
            self.show3DSurfaceButton.clicked.connect(
                lambda *args: on_show_3d_surface_clicked(self.main_widget)
            )
            if self.deleteSegmentButton:
                self.deleteSegmentButton.clicked.connect(
                    lambda *args: on_delete_selected_segment_clicked(self.main_widget)
                )
            self.segSelectorCombo.currentIndexChanged.connect(
                lambda idx: on_segmentation_choice_changed(self.main_widget, idx)
            )
            self.toggleGtOverlayButton.clicked.connect(
                lambda *args: on_toggle_gt_overlay_clicked(self.main_widget)
            )

    def update_segmentation_nodes(self, pred_node, gt_node):
        """Updates the table and displays switcher if both nodes exist."""
        has_both = (pred_node is not None) and (gt_node is not None)
        self.dualSegContainer.setVisible(has_both)

        active_node = pred_node or gt_node
        if self.segmentsTable and active_node:
            self.segmentsTable.setSegmentationNode(active_node)

        self.segSelectorCombo.blockSignals(True)
        self.segSelectorCombo.setCurrentIndex(0)
        self.segSelectorCombo.blockSignals(False)

    def set_fill_opacity_label(self, value: int):
        self.fillOpacityLabel.setText(f"Fill: {value}%")

    def set_3d_active(self, is_active: bool):
        if is_active:
            self.show3DSurfaceButton.setStyleSheet("""
                QPushButton {
                    background-color: #1b2e20;
                    color: #a5d6a7;
                    border: 1px solid #264a2b;
                    border-radius: 3px;
                    padding: 2px 6px;
                    height: 22px;
                    min-height: 22px;
                    font-size: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #223c28;
                }
            """)
        else:
            self.show3DSurfaceButton.setStyleSheet(BUTTON_LABEL_EDITOR_STYLE)

    def set_gt_overlay_active(self, is_active: bool):
        if is_active:
            self.toggleGtOverlayButton.setStyleSheet("""
                QPushButton {
                    background-color: #1b2836;
                    color: #90caf9;
                    border: 1px solid #28425d;
                    border-radius: 3px;
                    padding: 2px 6px;
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
        else:
            self.toggleGtOverlayButton.setStyleSheet(BUTTON_LABEL_EDITOR_STYLE)
