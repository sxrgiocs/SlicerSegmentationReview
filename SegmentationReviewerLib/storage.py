"""
Storage and persistence helpers: parsing QC JSONs, schema preservation, and atomic saves.
"""

from __future__ import annotations

import copy
import json
import logging
from pathlib import Path


def parse_qc_jsons(qc_path: str) -> tuple[dict, dict]:
    """
    Parses pre-computed QC JSONs (single file or folder) into:
    - by_scan: mapping scan_id -> { scan_id, dataset, boxes }
    - qc_source_files: mapping file_stem -> original JSON list (for schema preservation)
    """
    qc_files = []
    path = Path(qc_path)
    if path.is_file():
        qc_files.append(path)
    elif path.is_dir():
        qc_files.extend(sorted(path.glob("*.json")))

    by_scan = {}
    qc_source_files = {}

    for f in qc_files:
        try:
            with open(f, "r") as fp:
                raw_list = json.load(fp)
        except Exception as e:
            logging.warning(f"Could not read QC file {f}: {e}")
            continue

        if not isinstance(raw_list, list):
            continue

        qc_source_files[f.stem] = raw_list

        for item in raw_list:
            if not isinstance(item, dict) or "scan_id" not in item:
                continue

            scan_id = item["scan_id"]
            dataset = item.get("dataset", "")

            if scan_id not in by_scan:
                by_scan[scan_id] = {
                    "scan_id": scan_id,
                    "dataset": dataset,
                    "boxes": [],
                }

            # 1. Label Invasions
            if "invasions" in item and isinstance(item["invasions"], list):
                for inv in item["invasions"]:
                    bbox = inv.get("bbox")
                    if not bbox or len(bbox) != 6:
                        continue
                    pair = inv.get("pair", [])
                    cnt = inv.get("contact_voxels", 0)
                    cx = (bbox[0] + bbox[1]) // 2
                    cy = (bbox[2] + bbox[3]) // 2
                    cz = (bbox[4] + bbox[5]) // 2
                    by_scan[scan_id]["boxes"].append({
                        "source": "automated",
                        "type": "invasions",
                        "description": f"Pair {pair} ({cnt} voxels)",
                        "bbox": bbox,
                        "landmark": inv.get("landmark", [cx, cy, cz]),
                        "eval": inv.get("eval", None),
                        "raw_ref": inv,
                        "source_file_stem": f.stem,
                    })

            # 2. Island Invasions
            if "islands" in item and isinstance(item["islands"], list):
                for isl in item["islands"]:
                    bbox = isl.get("bbox")
                    if not bbox or len(bbox) != 6:
                        continue
                    gh = isl.get("guest_on_host", [])
                    vol = isl.get("vol_mm3", 0)
                    pct = isl.get("vol_frac_pct", 0)
                    cx = (bbox[0] + bbox[1]) // 2
                    cy = (bbox[2] + bbox[3]) // 2
                    cz = (bbox[4] + bbox[5]) // 2
                    by_scan[scan_id]["boxes"].append({
                        "source": "automated",
                        "type": "islands",
                        "description": f"Guest/Host {gh} ({vol:.1f} mm³, {pct:.1f}%)",
                        "bbox": bbox,
                        "landmark": isl.get("landmark", [cx, cy, cz]),
                        "eval": isl.get("eval", None),
                        "raw_ref": isl,
                        "source_file_stem": f.stem,
                    })

            # 3. Dynamic error keys
            for key, val in item.items():
                if key in ["scan_id", "dataset", "islands", "invasions"]:
                    continue
                if isinstance(val, list):
                    for entry in val:
                        if not isinstance(entry, dict):
                            continue
                        bbox = entry.get("bbox")
                        landmark = entry.get("landmark")
                        if not bbox and not landmark:
                            continue
                        by_scan[scan_id]["boxes"].append({
                            "source": entry.get("source", "automated"),
                            "type": key,
                            "description": entry.get("description", str(entry.get("label", ""))),
                            "bbox": bbox,
                            "landmark": landmark,
                            "eval": entry.get("eval", None),
                            "raw_ref": entry,
                            "source_file_stem": f.stem,
                        })

    return by_scan, qc_source_files


def restore_evaluations_from_dir(output_dir: str, qc_source_files: dict, queue: list):
    """
    Scans the output directory for previous evaluations and restores verdicts and manual additions.
    """
    out_path = Path(output_dir)
    eval_files = list(out_path.glob("*_evaluated.json")) + list(out_path.glob("manual_*.json"))
    if isinstance(qc_source_files, dict):
        for stem in qc_source_files.keys():
            candidate = out_path / f"{stem}.json"
            if candidate.exists() and candidate not in eval_files:
                eval_files.append(candidate)

    for ef in eval_files:
        try:
            with open(ef, "r") as fp:
                data = json.load(fp)
        except Exception:
            continue

        if not isinstance(data, list):
            continue

        saved_map = {item["scan_id"]: item for item in data if isinstance(item, dict) and "scan_id" in item}
        for q_item in queue:
            if q_item["scan_id"] in saved_map:
                saved_item = saved_map[q_item["scan_id"]]
                if "scan_eval" in saved_item:
                    q_item["scan_eval"] = saved_item["scan_eval"]
                elif "eval" in saved_item and not saved_item.get("boxes"):
                    q_item["scan_eval"] = saved_item["eval"]

                for key, val in saved_item.items():
                    if key in ["scan_id", "dataset", "scan_eval", "eval"] or not isinstance(val, list):
                        continue
                    for entry in val:
                        if not isinstance(entry, dict):
                            continue
                        bbox = entry.get("bbox")
                        landmark = entry.get("landmark")
                        eval_v = entry.get("eval")

                        matched = False
                        for b in q_item["boxes"]:
                            if (bbox and b.get("bbox") == bbox) or (landmark and b.get("landmark") == landmark):
                                if eval_v is not None:
                                    b["eval"] = eval_v
                                if "type" in entry:
                                    b["type"] = entry["type"]
                                matched = True
                                break

                        if not matched and eval_v is not None:
                            next_id = len(q_item["boxes"]) + 1
                            q_item["boxes"].append({
                                "box_id": next_id,
                                "source": "manual",
                                "type": key,
                                "description": entry.get("description", f"Saved {key}"),
                                "bbox": bbox,
                                "landmark": landmark,
                                "eval": eval_v,
                                "raw_ref": entry,
                            })


def save_all_evaluations(
    output_dir: str,
    scans_data: list,
    qc_source_files: dict | None = None,
) -> list[Path]:
    """
    Saves evaluations atomically to disk.
    If qc_source_files is provided, preserves original JSON schema.
    If no QC JSONs were used, exports a clean generic evaluations JSON.
    """
    # Defensive check in case caller passed (output_dir, qc_source_files, scans_data)
    if isinstance(scans_data, dict) and isinstance(qc_source_files, list):
        scans_data, qc_source_files = qc_source_files, scans_data

    if not isinstance(qc_source_files, dict):
        qc_source_files = {}

    out_dir_path = Path(output_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)
    saved_paths = []

    if qc_source_files:
        for file_stem, original_list in qc_source_files.items():
            evaluated_list = copy.deepcopy(original_list)
            scan_boxes_map = {s["scan_id"]: s for s in scans_data}

            for item in evaluated_list:
                scan_id = item.get("scan_id")
                if scan_id not in scan_boxes_map:
                    continue

                scan_info = scan_boxes_map[scan_id]
                if scan_info.get("dataset"):
                    item["dataset"] = scan_info["dataset"]
                if scan_info.get("scan_eval") is not None:
                    item["scan_eval"] = scan_info["scan_eval"]

                current_boxes = scan_info["boxes"]

                for b in current_boxes:
                    category_key = str(b.get("type", "islands")).strip()
                    if category_key not in item or not isinstance(item[category_key], list):
                        item[category_key] = []

                    matched_entry = None
                    for entry in item[category_key]:
                        if ("bbox" in b and entry.get("bbox") == b["bbox"]) or (
                            "landmark" in b and entry.get("landmark") == b["landmark"]
                        ):
                            matched_entry = entry
                            break

                    if matched_entry is not None:
                        matched_entry["eval"] = b.get("eval")
                        if "landmark" in b and b["landmark"]:
                            matched_entry["landmark"] = b["landmark"]
                    else:
                        new_finding = {"eval": b.get("eval")}
                        if "bbox" in b and b["bbox"]:
                            new_finding["bbox"] = b["bbox"]
                        if "landmark" in b and b["landmark"]:
                            new_finding["landmark"] = b["landmark"]
                        if b.get("description"):
                            new_finding["description"] = b["description"]
                        item[category_key].append(new_finding)

            out_file = out_dir_path / f"{file_stem}_evaluated.json"
            temp_file = out_file.with_suffix(".tmp")
            with open(temp_file, "w") as fp:
                json.dump(evaluated_list, fp, indent=2)
            temp_file.replace(out_file)
            saved_paths.append(out_file)
    else:
        generic_list = []
        for s in scans_data:
            scan_dict = {
                "scan_id": s["scan_id"],
                "dataset": s.get("dataset", ""),
            }
            if s.get("scan_eval") is not None:
                scan_dict["scan_eval"] = s["scan_eval"]

            for b in s["boxes"]:
                cat_key = str(b.get("type", "manual_findings")).strip()
                if cat_key not in scan_dict:
                    scan_dict[cat_key] = []

                finding = {
                    "eval": b.get("eval"),
                    "description": b.get("description", ""),
                }
                if "bbox" in b and b["bbox"]:
                    finding["bbox"] = b["bbox"]
                if "landmark" in b and b["landmark"]:
                    finding["landmark"] = b["landmark"]

                scan_dict[cat_key].append(finding)

            generic_list.append(scan_dict)

        out_file = out_dir_path / "manual_segmentation_evaluations.json"
        temp_file = out_file.with_suffix(".tmp")
        with open(temp_file, "w") as fp:
            json.dump(generic_list, fp, indent=2)
        temp_file.replace(out_file)
        saved_paths.append(out_file)

    return saved_paths
