"""
Method handlers for Current Scan box (Section 2 Left) and queue navigation.
"""

from __future__ import annotations

import datetime
import logging
import os

import slicer


def on_dataset_text_changed(widget, text: str):
    """Updates the dataset metadata for the active scan."""
    if 0 <= widget.current_scan_index < len(widget.scans_data):
        widget.scans_data[widget.current_scan_index]["dataset"] = text.strip()
        save_evaluations(widget, show_message=False)


def update_stats_label(widget):
    """Refreshes the unreviewed findings counter in CurrentScanBox."""
    if widget.current_scan_index < 0 or widget.current_scan_index >= len(widget.scans_data):
        return
    scan_item = widget.scans_data[widget.current_scan_index]
    boxes = scan_item["boxes"]
    unrev = sum(1 for b in boxes if b.get("eval") is None)
    widget.currentScanBox.set_unreviewed_count(unrev)


def load_scan_at_index(widget, index: int):
    """
    Loads volume, prediction, and ground truth segmentations for scan at index.
    Creates 3D Slicer markup nodes and refreshes findings table.
    """
    from .findings_box import clear_markup_nodes, jump_to_selected_box, refresh_boxes_table

    if index < 0 or index >= len(widget.scans_data):
        return

    widget.current_scan_index = index
    scan_item = widget.scans_data[index]

    clear_markup_nodes(widget)

    # Update Current Scan Box UI
    widget.currentScanBox.update_progress(index, len(widget.scans_data))
    widget.currentScanBox.set_scan_id(scan_item["scan_id"])
    widget.currentScanBox.set_dataset(scan_item.get("dataset", ""))

    try:
        volume_node, seg_node = widget.logic.load_scan_and_seg(
            pred_seg_path=scan_item.get("pred_seg_path"),
            gt_seg_path=scan_item.get("gt_seg_path"),
            seg_path=scan_item.get("seg_path"),
            ct_path=scan_item.get("ct_path"),
        )
    except Exception as e:
        slicer.util.errorDisplay(f"Failed to load scan {scan_item['scan_id']}:\n{e}")
        logging.exception(e)
        return

    # Update Label Editor with both Pred and GT segmentations
    widget.labelEditorBox.update_segmentation_nodes(
        pred_node=widget.logic.current_pred_seg_node,
        gt_node=widget.logic.current_gt_seg_node,
    )

    widget.logic.set_segmentation_fill_opacity(
        widget.labelEditorBox.fillOpacitySlider.value / 100.0
    )
    widget.labelEditorBox.set_3d_active(False)

    # Recreate markup nodes for findings
    widget.current_markup_nodes = []
    for box in scan_item["boxes"]:
        if "bbox" in box and box["bbox"]:
            node = widget.logic.create_contour_roi(box, volume_node)
        elif "landmark" in box and box["landmark"]:
            node = widget.logic.create_landmark_node(box, volume_node)
        else:
            node = None
        widget.current_markup_nodes.append(node)

    refresh_boxes_table(widget)
    update_stats_label(widget)

    if scan_item["boxes"]:
        widget.findingsBox.select_row(0)
        jump_to_selected_box(widget)


def save_evaluations(widget, show_message: bool = False):
    """Persists all review decisions to the output directory."""
    out_dir = widget.setupBox.outputDirSelector.currentPath.strip()
    if not out_dir or not os.path.isdir(out_dir):
        if show_message:
            slicer.util.errorDisplay("Please select a valid Output Directory.")
        return

    try:
        saved_paths = widget.logic.save_all_evaluations(out_dir, widget.scans_data)
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        if show_message:
            slicer.util.infoDisplay(
                f"Saved evaluations successfully at {now_str} to directory:\n{out_dir}\n"
                f"Files: {', '.join(p.name for p in saved_paths)}"
            )
    except Exception as e:
        slicer.util.errorDisplay(f"Failed to save evaluations:\n{e}")
        logging.exception(e)


def on_next_scan_clicked(widget):
    """Advances to next scan after confirming completeness."""
    if widget.current_scan_index < 0 or widget.current_scan_index >= len(widget.scans_data):
        return

    scan_item = widget.scans_data[widget.current_scan_index]
    unreviewed = [b for b in scan_item["boxes"] if b.get("eval") is None]
    has_whole_eval = scan_item.get("scan_eval") is not None

    if unreviewed and not has_whole_eval:
        confirm = slicer.util.confirmYesNoDisplay(
            f"There are {len(unreviewed)} unreviewed finding(s) in this scan.\n"
            f"Do you want to proceed to the next scan anyway?"
        )
        if not confirm:
            return

    save_evaluations(widget, show_message=False)

    if widget.current_scan_index + 1 < len(widget.scans_data):
        load_scan_at_index(widget, widget.current_scan_index + 1)
    else:
        slicer.util.infoDisplay(
            "Congratulations! You have completed all scans in the queue."
        )


def on_prev_scan_clicked(widget):
    """Steps back to previous scan in queue."""
    if widget.current_scan_index > 0:
        save_evaluations(widget, show_message=False)
        load_scan_at_index(widget, widget.current_scan_index - 1)
