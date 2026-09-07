"""
Method handlers for Section 3: Findings.
Includes finding table management, 3D slice navigation, Pass/Fail scoring,
interactive ROI/Landmark drawing and editing, and undo functionality.
"""

from __future__ import annotations

import copy
import logging

import qt
import slicer

from .current_scan_box import save_evaluations, update_stats_label


def clear_markup_nodes(widget):
    """Removes all active markup nodes from the MRML scene."""
    for node in widget.current_markup_nodes:
        if node and slicer.mrmlScene.GetNodeByID(node.GetID()):
            slicer.mrmlScene.RemoveNode(node)
    widget.current_markup_nodes = []


def refresh_boxes_table(widget):
    """Refreshes the QTableWidget with findings of the current scan."""
    if widget.current_scan_index < 0 or widget.current_scan_index >= len(widget.scans_data):
        widget.findingsBox.populate_table([])
        return

    scan_item = widget.scans_data[widget.current_scan_index]
    widget.findingsBox.populate_table(scan_item["boxes"])


def on_table_item_changed(widget, item):
    """Updates finding metadata when user edits the Type or Details cells."""
    if widget.current_scan_index < 0 or widget.current_scan_index >= len(widget.scans_data):
        return

    row = item.row()
    col = item.column()
    scan_item = widget.scans_data[widget.current_scan_index]
    if row < 0 or row >= len(scan_item["boxes"]):
        return

    box = scan_item["boxes"][row]
    new_text = item.text().strip()

    if col == 1:
        box["type"] = new_text or "error"
    elif col == 2:
        box["description"] = new_text

    save_evaluations(widget, show_message=False)


def on_table_selection_changed(widget):
    """Jumps slice views when user selects a finding in the table."""
    jump_to_selected_box(widget)


def jump_to_selected_box(widget):
    """Centers Red, Green, and Yellow slice viewers on the selected finding."""
    row = widget.findingsBox.get_selected_row()
    if row < 0 or row >= len(widget.current_markup_nodes):
        return

    node = widget.current_markup_nodes[row]
    if not node:
        return

    center = [0.0, 0.0, 0.0]
    if hasattr(node, "GetCenter"):
        node.GetCenter(center)
    elif hasattr(node, "GetNthControlPointPosition"):
        if node.GetNumberOfControlPoints() > 0:
            node.GetNthControlPointPosition(0, center)
        else:
            return
    else:
        return

    for sliceViewName in ["Red", "Green", "Yellow"]:
        sliceWidget = slicer.app.layoutManager().sliceWidget(sliceViewName)
        if sliceWidget:
            sliceNode = sliceWidget.mrmlSliceNode()
            sliceNode.JumpSliceByCentering(center[0], center[1], center[2])


def set_eval_for_selected(widget, eval_val: int):
    """
    Applies evaluation score (1=PASS, 0=FAIL) to selected finding or whole scan.
    Updates markup colors, refreshes table, auto-advances if enabled.
    """
    if widget.current_scan_index < 0 or widget.current_scan_index >= len(widget.scans_data):
        return

    scan_item = widget.scans_data[widget.current_scan_index]
    has_findings = len(scan_item["boxes"]) > 0

    if not has_findings or widget.findingsBox.evaluateWholeImageCheckbox.isChecked():
        if not widget.findingsBox.evaluateWholeImageCheckbox.isChecked() and not has_findings:
            proceed = prompt_whole_image_evaluation(widget)
            if not proceed:
                return

        evaluate_whole_scan(widget, eval_val)
        return

    row = widget.findingsBox.get_selected_row()
    if row < 0:
        for r, b in enumerate(scan_item["boxes"]):
            if b.get("eval") is None:
                widget.findingsBox.select_row(r)
                row = r
                break

    if row < 0:
        return

    box = scan_item["boxes"][row]
    box["eval"] = eval_val

    if row < len(widget.current_markup_nodes):
        node = widget.current_markup_nodes[row]
        widget.logic.apply_markup_color(node, eval_val)

    refresh_boxes_table(widget)
    update_stats_label(widget)
    save_evaluations(widget, show_message=False)

    if widget.findingsBox.autoAdvanceCheckbox.isChecked():
        next_row = -1
        for r in range(row + 1, len(scan_item["boxes"])):
            if scan_item["boxes"][r].get("eval") is None:
                next_row = r
                break
        if next_row == -1 and row + 1 < len(scan_item["boxes"]):
            next_row = row + 1

        if next_row != -1:
            widget.findingsBox.select_row(next_row)
            jump_to_selected_box(widget)


def prompt_whole_image_evaluation(widget) -> bool:
    """Prompts confirmation when scoring an image without individual findings."""
    msgBox = qt.QMessageBox(slicer.util.mainWindow())
    msgBox.setIcon(qt.QMessageBox.Question)
    msgBox.setWindowTitle("Evaluate Whole Image")
    msgBox.setText("Segmentation will be evaluated completely, do you want to proceed?")

    yesAllBtn = msgBox.addButton("Yes (for every sample)", qt.QMessageBox.AcceptRole)
    yesBtn = msgBox.addButton("Yes", qt.QMessageBox.AcceptRole)
    cancelBtn = msgBox.addButton("Cancel", qt.QMessageBox.RejectRole)
    msgBox.setDefaultButton(yesBtn)

    msgBox.exec_()
    clicked = msgBox.clickedButton()

    if clicked == cancelBtn:
        return False
    elif clicked == yesAllBtn:
        widget.findingsBox.evaluateWholeImageCheckbox.setChecked(True)
        return True
    elif clicked == yesBtn:
        return True
    return False


def evaluate_whole_scan(widget, eval_val: int):
    """Sets whole-scan evaluation score and advances if auto-advance is on."""
    from .current_scan_box import load_scan_at_index

    scan_item = widget.scans_data[widget.current_scan_index]
    scan_item["scan_eval"] = eval_val
    update_stats_label(widget)
    save_evaluations(widget, show_message=False)

    if widget.findingsBox.autoAdvanceCheckbox.isChecked():
        if widget.current_scan_index + 1 < len(widget.scans_data):
            load_scan_at_index(widget, widget.current_scan_index + 1)


def on_mark_fail_clicked(widget):
    """Scores selected finding or scan as FAIL (eval: 0)."""
    set_eval_for_selected(widget, 0)


def on_mark_pass_clicked(widget):
    """Scores selected finding or scan as PASS (eval: 1)."""
    set_eval_for_selected(widget, 1)


def on_add_missed_box_clicked(widget):
    """Activates interactive 3D bounding box drawing."""
    start_placement(widget, mode="roi")


def on_add_landmark_clicked(widget):
    """Activates interactive point landmark placement."""
    start_placement(widget, mode="landmark")


def start_placement(widget, mode: str):
    """
    Initializes ROI or Fiducial placement mode in 3D Slicer.
    Attaches banner text and interaction observer.
    """
    if widget.current_scan_index < 0:
        return

    volume_node = widget.logic.current_ref_volume
    if not volume_node:
        slicer.util.errorDisplay("No volume loaded.")
        return

    scan_item = widget.scans_data[widget.current_scan_index]
    next_id = len(scan_item["boxes"]) + 1
    widget.active_placement_mode = mode

    if mode == "roi":
        roi_name = f"#{next_id} (Manual Box)"
        node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsROINode", roi_name)
        node.CreateDefaultDisplayNodes()
        disp = node.GetDisplayNode()
        disp.SetFillVisibility(False)
        disp.SetFillOpacity(0.0)
        disp.SetOutlineVisibility(True)
        disp.SetOutlineOpacity(1.0)
        disp.SetSliceIntersectionThickness(2)
        disp.SetPointLabelsVisibility(True)
        disp.SetPropertiesLabelVisibility(False)
        disp.SetHandlesInteractive(True)
        widget.logic.apply_markup_color(node, 0)
        banner_text = "📍 DRAWING BOX: Click & drag on any slice to draw the box. Click 'Done' when finished."
    else:
        fid_name = f"#{next_id} (Manual Point)"
        node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", fid_name)
        node.CreateDefaultDisplayNodes()
        disp = node.GetDisplayNode()
        disp.SetPointLabelsVisibility(True)
        disp.SetPropertiesLabelVisibility(False)
        disp.SetGlyphScale(3.0)
        widget.logic.apply_markup_color(node, 0)
        banner_text = "📍 PLACING LANDMARK: Click on any slice to place a point. Click 'Done' when finished."

    widget.active_manual_node = node

    selection_node = slicer.app.applicationLogic().GetSelectionNode()
    selection_node.SetActivePlaceNodeID(node.GetID())
    interaction_node = slicer.app.applicationLogic().GetInteractionNode()
    interaction_node.SetCurrentInteractionMode(slicer.vtkMRMLInteractionNode.Place)

    widget.findingsBox.show_banner(banner_text)

    if widget.manual_placement_observer_tag:
        interaction_node.RemoveObserver(widget.manual_placement_observer_tag)
    widget.manual_placement_observer_tag = interaction_node.AddObserver(
        slicer.vtkMRMLInteractionNode.InteractionModeChangedEvent,
        lambda caller, event: on_interaction_mode_changed(widget, caller, event),
    )


def on_edit_finding_clicked(widget):
    """Enables interactive resize and position handles on the selected finding."""
    row = widget.findingsBox.get_selected_row()
    if row < 0 or row >= len(widget.current_markup_nodes):
        slicer.util.warningDisplay("Please select a finding from the table to edit.")
        return

    node = widget.current_markup_nodes[row]
    if not node:
        return

    widget.active_manual_node = node
    widget.active_placement_mode = "edit"

    disp = node.GetDisplayNode()
    if disp and hasattr(disp, "SetHandlesInteractive"):
        disp.SetHandlesInteractive(True)

    jump_to_selected_box(widget)

    interaction_node = slicer.app.applicationLogic().GetInteractionNode()
    interaction_node.SetCurrentInteractionMode(slicer.vtkMRMLInteractionNode.ViewTransform)

    widget.findingsBox.show_banner(
        f"📍 EDITING FINDING #{row + 1}: Drag handles on slice views. Click 'Done' when finished."
    )


def on_remove_finding_clicked(widget):
    """Deletes selected finding and pushes state to undo stack."""
    row = widget.findingsBox.get_selected_row()
    if row < 0:
        return

    scan_item = widget.scans_data[widget.current_scan_index]
    if row >= len(scan_item["boxes"]):
        return

    widget.deleted_findings_history.append({
        "scan_index": widget.current_scan_index,
        "row": row,
        "box_data": copy.deepcopy(scan_item["boxes"][row]),
    })

    if row < len(widget.current_markup_nodes):
        node = widget.current_markup_nodes.pop(row)
        if node and slicer.mrmlScene.GetNodeByID(node.GetID()):
            slicer.mrmlScene.RemoveNode(node)

    scan_item["boxes"].pop(row)

    for idx, b in enumerate(scan_item["boxes"], start=1):
        b["box_id"] = idx

    refresh_boxes_table(widget)
    update_stats_label(widget)
    save_evaluations(widget, show_message=False)


def on_undo_clicked(widget):
    """Restores the last deleted finding from history."""
    if not widget.deleted_findings_history:
        return

    last_item = widget.deleted_findings_history.pop()
    if last_item["scan_index"] != widget.current_scan_index:
        return

    box_data = last_item["box_data"]
    scan_item = widget.scans_data[widget.current_scan_index]
    insert_idx = min(last_item["row"], len(scan_item["boxes"]))

    scan_item["boxes"].insert(insert_idx, box_data)
    for idx, b in enumerate(scan_item["boxes"], start=1):
        b["box_id"] = idx

    volume_node = widget.logic.current_ref_volume
    if volume_node:
        if "bbox" in box_data and box_data["bbox"]:
            node = widget.logic.create_contour_roi(box_data, volume_node)
        elif "landmark" in box_data and box_data["landmark"]:
            node = widget.logic.create_landmark_node(box_data, volume_node)
        else:
            node = None
        widget.current_markup_nodes.insert(insert_idx, node)

    refresh_boxes_table(widget)
    update_stats_label(widget)
    widget.findingsBox.select_row(insert_idx)
    jump_to_selected_box(widget)
    save_evaluations(widget, show_message=False)
    logging.info(f"Undid deletion of finding #{box_data['box_id']}")


def on_interaction_mode_changed(widget, caller=None, event=None):
    """Triggered when user exits placement mode (e.g. by right-click or ESC)."""
    interaction_node = slicer.app.applicationLogic().GetInteractionNode()
    if (
        interaction_node.GetCurrentInteractionMode()
        != slicer.vtkMRMLInteractionNode.Place
    ):
        on_finish_placement_clicked(widget)


def on_finish_placement_clicked(widget):
    """
    Finalizes ROI or Landmark drawing/editing.
    Computes voxel coordinates and updates finding dictionary.
    """
    interaction_node = slicer.app.applicationLogic().GetInteractionNode()
    if widget.manual_placement_observer_tag:
        interaction_node.RemoveObserver(widget.manual_placement_observer_tag)
        widget.manual_placement_observer_tag = None

    interaction_node.SetCurrentInteractionMode(
        slicer.vtkMRMLInteractionNode.ViewTransform
    )

    widget.findingsBox.hide_banner()

    node = widget.active_manual_node
    mode = widget.active_placement_mode
    widget.active_manual_node = None
    widget.active_placement_mode = None

    if not node:
        return

    volume_node = widget.logic.current_ref_volume
    scan_item = widget.scans_data[widget.current_scan_index]

    if mode == "edit":
        row = widget.findingsBox.get_selected_row()
        if 0 <= row < len(scan_item["boxes"]):
            box = scan_item["boxes"][row]
            if hasattr(node, "GetRASBounds"):
                bbox = widget.logic.convert_ras_roi_to_voxel_bbox(node, volume_node)
                box["bbox"] = bbox
                cx = (bbox[0] + bbox[1]) // 2
                cy = (bbox[2] + bbox[3]) // 2
                cz = (bbox[4] + bbox[5]) // 2
                box["landmark"] = [cx, cy, cz]
            elif hasattr(node, "GetNthControlPointPosition") and node.GetNumberOfControlPoints() > 0:
                ras_pt = [0.0, 0.0, 0.0]
                node.GetNthControlPointPosition(0, ras_pt)
                box["landmark"] = widget.logic.convert_ras_point_to_voxel(ras_pt, volume_node)
        refresh_boxes_table(widget)
        save_evaluations(widget, show_message=False)
        return

    next_id = len(scan_item["boxes"]) + 1

    if mode == "roi":
        bbox = widget.logic.convert_ras_roi_to_voxel_bbox(node, volume_node)
        if (bbox[1] - bbox[0] <= 0) or (bbox[3] - bbox[2] <= 0) or (bbox[5] - bbox[4] <= 0):
            logging.info("Placed ROI has zero volume, discarding.")
            slicer.mrmlScene.RemoveNode(node)
            return

        cx = (bbox[0] + bbox[1]) // 2
        cy = (bbox[2] + bbox[3]) // 2
        cz = (bbox[4] + bbox[5]) // 2

        new_item = {
            "box_id": next_id,
            "source": "manual",
            "type": "manual_box",
            "description": f"ROI [{bbox[0]}..{bbox[1]}, {bbox[2]}..{bbox[3]}, {bbox[4]}..{bbox[5]}]",
            "bbox": bbox,
            "landmark": [cx, cy, cz],
            "eval": 0,
        }
    else:
        if node.GetNumberOfControlPoints() == 0:
            slicer.mrmlScene.RemoveNode(node)
            return
        ras_pt = [0.0, 0.0, 0.0]
        node.GetNthControlPointPosition(0, ras_pt)
        l_voxel = widget.logic.convert_ras_point_to_voxel(ras_pt, volume_node)

        new_item = {
            "box_id": next_id,
            "source": "manual",
            "type": "manual_landmark",
            "description": f"Point {l_voxel}",
            "landmark": l_voxel,
            "eval": 0,
        }

    scan_item["boxes"].append(new_item)
    widget.current_markup_nodes.append(node)

    refresh_boxes_table(widget)
    update_stats_label(widget)
    widget.findingsBox.select_row(len(scan_item["boxes"]) - 1)
    jump_to_selected_box(widget)
    save_evaluations(widget, show_message=False)


def on_manual_save_clicked(widget):
    """Triggers manual evaluation save with user confirmation message."""
    save_evaluations(widget, show_message=True)
