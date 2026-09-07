"""
Method handlers for Label Editor box (Section 2 Right).
Includes controls for segment transparency, 3D model generation,
segment deletion, and switching between Predictions and Ground Truth.
"""

from __future__ import annotations

import slicer


def on_fill_opacity_changed(widget, value: int):
    """Adjusts 2D segmentation fill opacity."""
    opacity = value / 100.0
    widget.labelEditorBox.set_fill_opacity_label(value)
    if value > 0:
        widget.last_non_zero_fill_opacity = value
    widget.logic.set_segmentation_fill_opacity(opacity)


def on_toggle_fill_clicked(widget):
    """Toggles opacity between 0% and last non-zero percentage."""
    current_val = widget.labelEditorBox.fillOpacitySlider.value
    if current_val > 0:
        widget.labelEditorBox.fillOpacitySlider.setValue(0)
    else:
        widget.labelEditorBox.fillOpacitySlider.setValue(
            widget.last_non_zero_fill_opacity or 25
        )


def on_show_3d_surface_clicked(widget):
    """Toggles 3D surface model rendering for the active segmentation."""
    is_now_visible = widget.logic.toggle_3d_surface_visibility()
    widget.labelEditorBox.set_3d_active(is_now_visible)


def onDeleteSelectedSegmentClicked(widget):
    """Deletes selected segment(s) from the active segmentation."""
    on_delete_selected_segment_clicked(widget)


def on_delete_selected_segment_clicked(widget):
    """Deletes selected segment(s) from the active segmentation."""
    active_node = widget.logic.current_seg_node
    table = widget.labelEditorBox.segmentsTable
    if not active_node or not table:
        return

    selected_ids = table.selectedSegmentIDs()
    if not selected_ids:
        slicer.util.warningDisplay("Please select a label from the table to delete.")
        return

    confirm = slicer.util.confirmYesNoDisplay(
        f"Are you sure you want to delete {len(selected_ids)} selected label(s) from {active_node.GetName()}?"
    )
    if confirm:
        segmentation = active_node.GetSegmentation()
        for seg_id in selected_ids:
            segmentation.RemoveSegment(seg_id)


def on_segmentation_choice_changed(widget, index: int):
    """
    Switches the active segmentation in the table view and editor
    between Predictions (index 0) and Ground Truth (index 1).
    """
    if index == 0:
        target_node = widget.logic.current_pred_seg_node
    else:
        target_node = widget.logic.current_gt_seg_node or widget.logic.current_pred_seg_node

    if target_node and widget.labelEditorBox.segmentsTable:
        widget.logic.set_active_segmentation_node(target_node)
        widget.labelEditorBox.segmentsTable.setSegmentationNode(target_node)


def on_toggle_gt_overlay_clicked(widget):
    """Toggles 2D/3D visibility of Ground Truth reference segmentation."""
    gt_node = widget.logic.current_gt_seg_node
    if not gt_node:
        return

    disp = gt_node.GetDisplayNode()
    if not disp:
        return

    currently_visible = disp.GetVisibility2D()
    new_visible = not currently_visible
    disp.SetVisibility2D(new_visible)
    disp.SetVisibility3D(new_visible)
    widget.labelEditorBox.set_gt_overlay_active(new_visible)
