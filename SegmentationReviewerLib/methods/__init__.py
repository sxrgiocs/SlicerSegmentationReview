"""
Methods package for SegmentationReviewer.
Modular handlers per UI box:
- setup_box.py: Review queue building, directory validation, and loading.
- current_scan_box.py: Scan navigation, dataset metadata, progress, and auto-saving.
- label_editor_box.py: Segment visibility, opacity slider, 3D surface, and dual segmentation switcher.
- findings_box.py: Finding table interaction, manual box/point placement, editing, scoring, and undo.
"""

from __future__ import annotations
