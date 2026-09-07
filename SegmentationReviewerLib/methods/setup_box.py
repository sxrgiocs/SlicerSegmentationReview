"""
Method handlers for Section 1: Setup / Input Directories.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import slicer

from .current_scan_box import load_scan_at_index


def on_load_queue_clicked(widget):
    """
    Validates directories, builds review queue with predictions and/or ground truth,
    collapses setup box, and loads the first unreviewed scan.
    """
    pred_dir = widget.setupBox.predSegsDirSelector.currentPath.strip() or None
    gt_dir = widget.setupBox.gtSegsDirSelector.currentPath.strip() or None
    scans_dir = widget.setupBox.scansDirSelector.currentPath.strip() or None
    qc_path = widget.setupBox.qcJsonSelector.currentPath.strip() or None
    out_dir = widget.setupBox.outputDirSelector.currentPath.strip()

    if not pred_dir and not gt_dir:
        slicer.util.errorDisplay(
            "Please select at least one Segmentations Directory:\n"
            "- Predictions (Deep Learning output)\n"
            "- Ground Truth (Reference masks)"
        )
        return

    if pred_dir and not os.path.isdir(pred_dir):
        slicer.util.errorDisplay(f"Predictions directory not found:\n{pred_dir}")
        return

    if gt_dir and not os.path.isdir(gt_dir):
        slicer.util.errorDisplay(f"Ground Truth directory not found:\n{gt_dir}")
        return

    if not out_dir or not os.path.isdir(out_dir):
        slicer.util.errorDisplay("Please select a valid Output Directory.")
        return

    try:
        widget.scans_data = widget.logic.build_review_queue(
            pred_segs_dir=pred_dir,
            gt_segs_dir=gt_dir,
            scans_dir=scans_dir,
            qc_path=qc_path,
            output_dir=out_dir,
        )
    except Exception as e:
        slicer.util.errorDisplay(f"Failed to load review queue:\n{e}")
        logging.exception(e)
        return

    if not widget.scans_data:
        slicer.util.warningDisplay(
            "No segmentation files (.nii, .nii.gz) found matching the criteria."
        )
        return

    widget.setupBox.widget.collapsed = True
    widget.scanAndLabelsCollapsible.collapsed = False
    widget.findingsBox.widget.collapsed = False

    start_idx = 0
    for i, item in enumerate(widget.scans_data):
        if not widget.logic.is_scan_completed(item):
            start_idx = i
            break

    widget.current_scan_index = start_idx
    load_scan_at_index(widget, widget.current_scan_index)
    slicer.util.infoDisplay(
        f"Loaded {len(widget.scans_data)} scans into review queue.\n"
        f"Resuming at scan #{start_idx + 1}."
    )
