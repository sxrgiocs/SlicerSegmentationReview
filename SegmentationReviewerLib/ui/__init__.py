"""
UI package for SegmentationReviewer.
Exposes modular boxes and main widget.
"""

from __future__ import annotations

from .current_scan_box import CurrentScanBox
from .findings_box import FindingsBox
from .label_editor_box import LabelEditorBox
from .main_widget import SegmentationReviewerWidget
from .setup_box import SetupBox

__all__ = [
    "SetupBox",
    "CurrentScanBox",
    "LabelEditorBox",
    "FindingsBox",
    "SegmentationReviewerWidget",
]
