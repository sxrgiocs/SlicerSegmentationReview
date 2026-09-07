"""
Main UI orchestrator for SegmentationReviewerWidget.
Composes modular boxes (SetupBox, CurrentScanBox, LabelEditorBox, FindingsBox)
and configures global application shortcuts.
"""

from __future__ import annotations

import ctk
import qt
import slicer
from slicer.ScriptedLoadableModule import ScriptedLoadableModuleWidget

from ..logic import SegmentationReviewerLogic
from ..methods.current_scan_box import (
    load_scan_at_index,
    on_next_scan_clicked,
    on_prev_scan_clicked,
    save_evaluations,
    update_stats_label,
)
from ..methods.findings_box import (
    clear_markup_nodes,
    on_add_landmark_clicked,
    on_add_missed_box_clicked,
    on_edit_finding_clicked,
    on_mark_fail_clicked,
    on_mark_pass_clicked,
    on_remove_finding_clicked,
    on_undo_clicked,
    refresh_boxes_table,
)
from .current_scan_box import CurrentScanBox
from .findings_box import FindingsBox
from .label_editor_box import LabelEditorBox
from .setup_box import SetupBox


class SegmentationReviewerWidget(ScriptedLoadableModuleWidget):
    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        self.logic = None
        self.current_scan_index = -1
        self.scans_data = []
        self.current_markup_nodes = []
        self.deleted_findings_history = []
        self.manual_placement_observer_tag = None
        self.active_manual_node = None
        self.active_placement_mode = None
        self.shortcuts = []
        self.last_non_zero_fill_opacity = 25

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        self.logic = SegmentationReviewerLogic()

        # ----------------------------------------------------------------------
        # 1. Setup / Input Directories (Predictions & Ground Truth)
        # ----------------------------------------------------------------------
        self.setupBox = SetupBox(main_widget=self)
        self.layout.addWidget(self.setupBox.widget)

        # ----------------------------------------------------------------------
        # 2. Current Scan & Label Editor (SIDE-BY-SIDE)
        # ----------------------------------------------------------------------
        self.scanAndLabelsCollapsible = ctk.ctkCollapsibleButton()
        self.scanAndLabelsCollapsible.text = "2. Current Scan && Label Editor"
        self.layout.addWidget(self.scanAndLabelsCollapsible)

        scanAndLabelsLayout = qt.QHBoxLayout(self.scanAndLabelsCollapsible)
        scanAndLabelsLayout.setSpacing(10)
        scanAndLabelsLayout.setContentsMargins(6, 6, 6, 6)

        # Left Box: Current Scan
        self.currentScanBox = CurrentScanBox(main_widget=self)
        scanAndLabelsLayout.addWidget(self.currentScanBox.widget, 1)

        # Right Box: Label Editor & Dual-Segmentation Switcher
        self.labelEditorBox = LabelEditorBox(main_widget=self)
        scanAndLabelsLayout.addWidget(self.labelEditorBox.widget, 1)

        # ----------------------------------------------------------------------
        # 3. Findings (75% Table / 25% Action Buttons)
        # ----------------------------------------------------------------------
        self.findingsBox = FindingsBox(main_widget=self)
        self.layout.addWidget(self.findingsBox.widget)

        # ----------------------------------------------------------------------
        # Keyboard Shortcuts
        # ----------------------------------------------------------------------
        self._setupShortcuts()
        self.layout.addStretch(1)

    def _setupShortcuts(self):
        main_win = slicer.util.mainWindow()
        if not main_win:
            return

        self._addShortcut("1", lambda: on_mark_fail_clicked(self))
        self._addShortcut("f", lambda: on_mark_fail_clicked(self))
        self._addShortcut("F", lambda: on_mark_fail_clicked(self))

        self._addShortcut("2", lambda: on_mark_pass_clicked(self))
        self._addShortcut("p", lambda: on_mark_pass_clicked(self))
        self._addShortcut("P", lambda: on_mark_pass_clicked(self))

        self._addShortcut("a", lambda: on_add_missed_box_clicked(self))
        self._addShortcut("A", lambda: on_add_missed_box_clicked(self))

        self._addShortcut("l", lambda: on_add_landmark_clicked(self))
        self._addShortcut("L", lambda: on_add_landmark_clicked(self))

        self._addShortcut("e", lambda: on_edit_finding_clicked(self))
        self._addShortcut("E", lambda: on_edit_finding_clicked(self))

        self._addShortcut("Delete", lambda: on_remove_finding_clicked(self))
        self._addShortcut("Backspace", lambda: on_remove_finding_clicked(self))

        self._addShortcut("Ctrl+z", lambda: on_undo_clicked(self))
        self._addShortcut("Ctrl+Z", lambda: on_undo_clicked(self))
        self._addShortcut("Meta+z", lambda: on_undo_clicked(self))
        self._addShortcut("Meta+Z", lambda: on_undo_clicked(self))

        self._addShortcut("Space", lambda: on_next_scan_clicked(self))
        self._addShortcut("n", lambda: on_next_scan_clicked(self))
        self._addShortcut("N", lambda: on_next_scan_clicked(self))

        self._addShortcut("b", lambda: on_prev_scan_clicked(self))
        self._addShortcut("B", lambda: on_prev_scan_clicked(self))

    def _addShortcut(self, keySeq, slot):
        main_win = slicer.util.mainWindow()
        if main_win:
            shortcut = qt.QShortcut(qt.QKeySequence(keySeq), main_win)
            shortcut.activated.connect(slot)
            self.shortcuts.append(shortcut)

    def cleanup(self):
        for s in self.shortcuts:
            s.disconnect("activated()")
        self.shortcuts = []
        clear_markup_nodes(self)

    # --------------------------------------------------------------------------
    # API Compatibility Delegators
    # --------------------------------------------------------------------------
    def loadScanAtIndex(self, index: int):
        return load_scan_at_index(self, index)

    def saveEvaluations(self, show_message: bool = False):
        return save_evaluations(self, show_message=show_message)

    def refreshBoxesTable(self):
        return refresh_boxes_table(self)

    def clearMarkupNodes(self):
        return clear_markup_nodes(self)

    def updateStatsLabel(self):
        return update_stats_label(self)
