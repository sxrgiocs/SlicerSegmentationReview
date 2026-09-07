"""
Markups helpers: ROI bounding boxes, Fiducial landmark points, and coordinate transforms.
"""

from __future__ import annotations

import math
import slicer
import vtk


def create_contour_roi(box: dict, volume_node):
    """
    Creates an outline-only vtkMRMLMarkupsROINode from voxel bbox coords.
    """
    bbox = box["bbox"]
    ijkToRas = vtk.vtkMatrix4x4()
    volume_node.GetIJKToRASMatrix(ijkToRas)

    corners_ijk = [
        [bbox[0], bbox[2], bbox[4], 1.0],
        [bbox[1], bbox[2], bbox[4], 1.0],
        [bbox[0], bbox[3], bbox[4], 1.0],
        [bbox[1], bbox[3], bbox[4], 1.0],
        [bbox[0], bbox[2], bbox[5], 1.0],
        [bbox[1], bbox[2], bbox[5], 1.0],
        [bbox[0], bbox[3], bbox[5], 1.0],
        [bbox[1], bbox[3], bbox[5], 1.0],
    ]
    corners_ras = []
    for pt in corners_ijk:
        out = [0.0, 0.0, 0.0, 1.0]
        ijkToRas.MultiplyPoint(pt, out)
        corners_ras.append(out[:3])

    min_ras = [min(pt[d] for pt in corners_ras) for d in range(3)]
    max_ras = [max(pt[d] for pt in corners_ras) for d in range(3)]

    center_ras = [(min_ras[d] + max_ras[d]) / 2.0 for d in range(3)]
    size_ras = [max(abs(max_ras[d] - min_ras[d]), 4.0) for d in range(3)]

    num_label = f"#{box['box_id']}"
    roi_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsROINode", num_label)
    roi_node.SetCenter(center_ras)
    roi_node.SetSize(size_ras)

    roi_node.CreateDefaultDisplayNodes()
    disp = roi_node.GetDisplayNode()
    disp.SetFillVisibility(False)
    disp.SetFillOpacity(0.0)
    disp.SetOutlineVisibility(True)
    disp.SetOutlineOpacity(1.0)
    disp.SetSliceIntersectionThickness(2)
    disp.SetPointLabelsVisibility(True)
    disp.SetPropertiesLabelVisibility(False)
    disp.SetHandlesInteractive(False)

    apply_markup_color(roi_node, box.get("eval"))
    return roi_node


def create_landmark_node(box: dict, volume_node):
    """
    Creates a single-point vtkMRMLMarkupsFiducialNode from voxel coords.
    """
    l_voxel = box["landmark"]
    ijkToRas = vtk.vtkMatrix4x4()
    volume_node.GetIJKToRASMatrix(ijkToRas)
    out_ras = [0.0, 0.0, 0.0, 1.0]
    ijkToRas.MultiplyPoint([l_voxel[0], l_voxel[1], l_voxel[2], 1.0], out_ras)

    num_label = f"#{box['box_id']}"
    fid_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", num_label)
    fid_node.AddControlPoint(out_ras[:3], num_label)

    fid_node.CreateDefaultDisplayNodes()
    disp = fid_node.GetDisplayNode()
    disp.SetPointLabelsVisibility(True)
    disp.SetPropertiesLabelVisibility(False)
    disp.SetGlyphScale(3.0)

    apply_markup_color(fid_node, box.get("eval"))
    return fid_node


def apply_markup_color(node, eval_val: int | None):
    """
    Sets the outline or fiducial color based on review state:
    - PASS (1): Green
    - FAIL (0): Red
    - Unreviewed (None): Yellow
    """
    if not node:
        return
    disp = node.GetDisplayNode()
    if not disp:
        return

    if eval_val == 1:
        color = (0.15, 0.85, 0.25)  # Green (Pass)
    elif eval_val == 0:
        color = (0.9, 0.15, 0.15)   # Red (Fail)
    else:
        color = (0.95, 0.8, 0.1)    # Yellow (Unreviewed)

    disp.SetColor(color)
    disp.SetSelectedColor(color)


def convert_ras_roi_to_voxel_bbox(roi_node, volume_node) -> list[int]:
    """
    Transforms RAS bounds of an ROI to integer voxel coordinate bounding box.
    """
    bounds_ras = [0.0] * 6
    roi_node.GetRASBounds(bounds_ras)

    rasToIjk = vtk.vtkMatrix4x4()
    volume_node.GetRASToIJKMatrix(rasToIjk)

    corners_ras = [
        [bounds_ras[0], bounds_ras[2], bounds_ras[4], 1.0],
        [bounds_ras[1], bounds_ras[2], bounds_ras[4], 1.0],
        [bounds_ras[0], bounds_ras[3], bounds_ras[4], 1.0],
        [bounds_ras[1], bounds_ras[3], bounds_ras[4], 1.0],
        [bounds_ras[0], bounds_ras[2], bounds_ras[5], 1.0],
        [bounds_ras[1], bounds_ras[2], bounds_ras[5], 1.0],
        [bounds_ras[0], bounds_ras[3], bounds_ras[5], 1.0],
        [bounds_ras[1], bounds_ras[3], bounds_ras[5], 1.0],
    ]
    corners_ijk = []
    for pt in corners_ras:
        out = [0.0, 0.0, 0.0, 1.0]
        rasToIjk.MultiplyPoint(pt, out)
        corners_ijk.append(out[:3])

    dims = volume_node.GetImageData().GetDimensions()
    x_min = int(max(0, math.floor(min(pt[0] for pt in corners_ijk))))
    x_max = int(min(dims[0], math.ceil(max(pt[0] for pt in corners_ijk))))
    y_min = int(max(0, math.floor(min(pt[1] for pt in corners_ijk))))
    y_max = int(min(dims[1], math.ceil(max(pt[1] for pt in corners_ijk))))
    z_min = int(max(0, math.floor(min(pt[2] for pt in corners_ijk))))
    z_max = int(min(dims[2], math.ceil(max(pt[2] for pt in corners_ijk))))

    return [x_min, x_max, y_min, y_max, z_min, z_max]


def convert_ras_point_to_voxel(ras_pt: list[float], volume_node) -> list[int]:
    """
    Transforms a 3D RAS position to voxel coordinate [x, y, z].
    """
    rasToIjk = vtk.vtkMatrix4x4()
    volume_node.GetRASToIJKMatrix(rasToIjk)
    out = [0.0, 0.0, 0.0, 1.0]
    rasToIjk.MultiplyPoint([ras_pt[0], ras_pt[1], ras_pt[2], 1.0], out)
    dims = volume_node.GetImageData().GetDimensions()
    vx = int(max(0, min(dims[0] - 1, round(out[0]))))
    vy = int(max(0, min(dims[1] - 1, round(out[1]))))
    vz = int(max(0, min(dims[2] - 1, round(out[2]))))
    return [vx, vy, vz]
