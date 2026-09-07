"""
Business logic and MRML data management for SegmentationReviewer.
Supports dual segmentation review (Deep Learning Predictions & Ground Truth).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import slicer
from slicer.ScriptedLoadableModule import ScriptedLoadableModuleLogic

from .markups import (
    apply_markup_color,
    convert_ras_point_to_voxel,
    convert_ras_roi_to_voxel_bbox,
    create_contour_roi,
    create_landmark_node,
)
from .storage import (
    parse_qc_jsons,
    restore_evaluations_from_dir,
    save_all_evaluations,
)


class SegmentationReviewerLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        ScriptedLoadableModuleLogic.__init__(self)
        self.current_ct_node = None
        self.current_pred_seg_node = None
        self.current_gt_seg_node = None
        self.current_seg_node = None
        self.current_ref_volume = None
        self.qc_source_files = {}

    def build_review_queue(
        self,
        pred_segs_dir: str = None,
        gt_segs_dir: str = None,
        segs_dir: str = None,
        scans_dir: str = None,
        qc_path: str = None,
        output_dir: str = None,
    ) -> list:
        """
        Builds review queue matching scans across predictions, ground truth,
        and volume directories.
        """
        if not pred_segs_dir and segs_dir:
            pred_segs_dir = segs_dir

        pred_file_map = {}
        if pred_segs_dir and os.path.isdir(pred_segs_dir):
            p_path = Path(pred_segs_dir)
            for p in p_path.rglob("*.nii.gz"):
                pred_file_map[p.name] = str(p)
            for p in p_path.rglob("*.nii"):
                if p.name not in pred_file_map:
                    pred_file_map[p.name] = str(p)

        gt_file_map = {}
        if gt_segs_dir and os.path.isdir(gt_segs_dir):
            g_path = Path(gt_segs_dir)
            for p in g_path.rglob("*.nii.gz"):
                gt_file_map[p.name] = str(p)
            for p in g_path.rglob("*.nii"):
                if p.name not in gt_file_map:
                    gt_file_map[p.name] = str(p)

        all_scan_names = sorted(set(pred_file_map.keys()) | set(gt_file_map.keys()))

        ct_file_map = {}
        if scans_dir and os.path.isdir(scans_dir):
            scans_path = Path(scans_dir)
            for p in scans_path.rglob("*.nii.gz"):
                ct_file_map[p.name] = str(p)
            for p in scans_path.rglob("*.nii"):
                if p.name not in ct_file_map:
                    ct_file_map[p.name] = str(p)

        qc_data_by_scan = {}
        self.qc_source_files = {}
        if qc_path and os.path.exists(qc_path):
            qc_data_by_scan, self.qc_source_files = parse_qc_jsons(qc_path)

        queue = []
        for scan_id in all_scan_names:
            pred_file = pred_file_map.get(scan_id)
            gt_file = gt_file_map.get(scan_id)
            primary_seg = pred_file or gt_file
            ct_file = ct_file_map.get(scan_id)

            boxes = []
            dataset = ""
            if scan_id in qc_data_by_scan:
                info = qc_data_by_scan[scan_id]
                dataset = info.get("dataset", "")
                boxes = info.get("boxes", [])

            queue.append({
                "scan_id": scan_id,
                "dataset": dataset,
                "pred_seg_path": pred_file,
                "gt_seg_path": gt_file,
                "seg_path": primary_seg,
                "ct_path": ct_file,
                "boxes": boxes,
                "scan_eval": None,
            })

        for q_item in queue:
            for idx, box in enumerate(q_item["boxes"], start=1):
                box["box_id"] = idx

        if output_dir and os.path.isdir(output_dir):
            restore_evaluations_from_dir(output_dir, self.qc_source_files, queue)

        return queue

    def is_scan_completed(self, scan_item: dict) -> bool:
        if scan_item.get("scan_eval") is not None:
            return True
        boxes = scan_item.get("boxes", [])
        if not boxes:
            return False
        return all(b.get("eval") is not None for b in boxes)

    def _load_seg_file(self, seg_path: str, node_name: str):
        seg_node = None
        try:
            seg_node = slicer.util.loadSegmentation(seg_path)
            if seg_node:
                seg_node.SetName(node_name)
        except Exception:
            try:
                label_vol = slicer.util.loadLabelVolume(seg_path)
                if label_vol:
                    seg_node = slicer.mrmlScene.AddNewNodeByClass(
                        "vtkMRMLSegmentationNode", node_name
                    )
                    slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(
                        label_vol, seg_node
                    )
                    slicer.mrmlScene.RemoveNode(label_vol)
            except Exception as e:
                logging.exception(e)

        if seg_node:
            disp_node = seg_node.GetDisplayNode()
            if disp_node:
                disp_node.SetOpacity2DOutline(1.0)
                disp_node.SetSliceIntersectionThickness(2)
        return seg_node

    def load_scan_and_seg(
        self,
        seg_path: str = None,
        ct_path: str = None,
        pred_seg_path: str = None,
        gt_seg_path: str = None,
    ):
        """
        Loads CT volume and both predictions & ground truth segmentations.
        """
        if not pred_seg_path and not gt_seg_path and seg_path:
            pred_seg_path = seg_path

        # Unload previous nodes
        for node in [
            self.current_ct_node,
            self.current_pred_seg_node,
            self.current_gt_seg_node,
        ]:
            if node and slicer.mrmlScene.GetNodeByID(node.GetID()):
                slicer.mrmlScene.RemoveNode(node)

        self.current_ct_node = None
        self.current_pred_seg_node = None
        self.current_gt_seg_node = None
        self.current_seg_node = None
        self.current_ref_volume = None

        # 1. Load Volume / CT
        ct_node = None
        if ct_path and os.path.exists(ct_path):
            try:
                ct_node = slicer.util.loadVolume(ct_path)
                self.current_ct_node = ct_node
            except Exception as e:
                logging.warning(f"Could not load volume from {ct_path}: {e}")

        # 2. Load Predictions Segmentation
        if pred_seg_path and os.path.exists(pred_seg_path):
            name = f"[Pred] {Path(pred_seg_path).name}"
            self.current_pred_seg_node = self._load_seg_file(pred_seg_path, name)

        # 3. Load Ground Truth Segmentation
        if gt_seg_path and os.path.exists(gt_seg_path):
            name = f"[GT] {Path(gt_seg_path).name}"
            self.current_gt_seg_node = self._load_seg_file(gt_seg_path, name)
            if self.current_gt_seg_node:
                disp = self.current_gt_seg_node.GetDisplayNode()
                if disp:
                    # Slightly thinner outline for GT reference so both can be seen if overlaid
                    disp.SetSliceIntersectionThickness(2)
                    disp.SetOpacity2DFill(0.15)

        self.current_seg_node = self.current_pred_seg_node or self.current_gt_seg_node

        if not self.current_seg_node:
            ref_path = pred_seg_path or gt_seg_path or seg_path
            raise RuntimeError(f"Could not load segmentation from {ref_path}")

        if ct_node:
            self.current_ref_volume = ct_node
        else:
            try:
                primary_path = pred_seg_path or gt_seg_path or seg_path
                ref_vol = slicer.util.loadVolume(primary_path)
                self.current_ct_node = ref_vol
                self.current_ref_volume = ref_vol
            except Exception:
                self.current_ref_volume = ct_node

        slicer.util.resetSliceViews()
        return self.current_ref_volume, self.current_seg_node

    def set_active_segmentation_node(self, node):
        """Switches the active segmentation node for editing and inspection."""
        if node:
            self.current_seg_node = node

    def set_segmentation_fill_opacity(self, opacity: float, node=None):
        target_nodes = [node] if node else [self.current_pred_seg_node, self.current_gt_seg_node]
        for n in target_nodes:
            if n:
                disp = n.GetDisplayNode()
                if disp:
                    disp.SetOpacity2DFill(opacity)

    def toggle_segmentation_visibility(self, node, visible: bool):
        if node:
            disp = node.GetDisplayNode()
            if disp:
                disp.SetVisibility2D(visible)
                disp.SetVisibility3D(visible)

    def toggle_3d_surface_visibility(self, node=None) -> bool:
        target = node or self.current_seg_node
        if not target:
            return False

        disp = target.GetDisplayNode()
        if not disp:
            return False

        is_visible = disp.GetVisibility3D()
        if not is_visible:
            target.CreateClosedSurfaceRepresentation()
            disp.SetVisibility3D(True)
            return True
        else:
            disp.SetVisibility3D(False)
            return False

    def convert_ras_roi_to_voxel_bbox(self, roi_node, volume_node) -> list[int]:
        return convert_ras_roi_to_voxel_bbox(roi_node, volume_node)

    def convert_ras_point_to_voxel(self, ras_point, volume_node) -> list[int]:
        return convert_ras_point_to_voxel(ras_point, volume_node)

    def create_contour_roi(self, box: dict, volume_node):
        return create_contour_roi(box, volume_node)

    def create_landmark_node(self, box: dict, volume_node):
        return create_landmark_node(box, volume_node)

    def apply_markup_color(self, node, eval_val: int | None):
        return apply_markup_color(node, eval_val)

    def save_all_evaluations(self, output_dir: str, scans_data: list[dict]) -> list[Path]:
        return save_all_evaluations(output_dir, scans_data, self.qc_source_files)
