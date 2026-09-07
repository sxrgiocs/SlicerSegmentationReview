"""
SegmentationReviewer - 3D Slicer Scripted Loadable Module

Main entry point registering module metadata, widget, logic, and self-tests.
Modular components are located in SegmentationReviewerLib/.
"""

from __future__ import annotations
from SegmentationReviewerLib import SegmentationReviewerLogic, SegmentationReviewerWidget

import os
import sys

from slicer.ScriptedLoadableModule import (
    ScriptedLoadableModule,
    ScriptedLoadableModuleTest,
)
import slicer

# Ensure library package is importable relative to this file
module_dir = os.path.dirname(os.path.abspath(__file__))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)


# ==============================================================================
# Module Registration
# ==============================================================================
class SegmentationReviewer(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Segmentation Reviewer"
        self.parent.categories = ["Quality Assurance", "Segmentation"]
        self.parent.dependencies = []
        self.parent.contributors = ["Sergio Carreras (IGT Research Group, UC3M)", "Antigravity Team"]
        self.parent.helpText = (
            "Review medical image segmentations (predictions and ground truth), "
            "evaluate automated quality control bounding boxes and landmarks, "
            "assign Pass (1) / Fail (0) scores, and mark missed errors."
        )
        self.parent.acknowledgementText = (
            "Designed for validation of automated quality control methods "
            "and deep learning segmentation predictions."
        )


# ==============================================================================
# Self Test
# ==============================================================================
class SegmentationReviewerTest(ScriptedLoadableModuleTest):
    def setUp(self):
        slicer.mrmlScene.Clear()

    def runTest(self):
        self.setUp()
        self.test_SegmentationReviewer1()

    def test_SegmentationReviewer1(self):
        self.delayDisplay("Starting the test")
        logic = SegmentationReviewerLogic()
        self.assertIsNotNone(logic)
        self.delayDisplay("Test passed!")
