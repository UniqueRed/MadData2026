"""
ICD Mapping Processor

Parses an ICD GEXF file to extract the mapping from matrix index (0-1079)
to ICD-10 code and description.  Saves as processed/icd_mapping.json.

Usage:
    cd backend && python -m app.data.icd_processor
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

_GEXF_DIR = Path(__file__).resolve().parent.parent.parent.parent / (
    "data/ComorbidityNetworksData/4.Graphs-gexffiles"
)
_OUTPUT_DIR = Path(__file__).resolve().parent / "processed"

_NS = {"gexf": "http://www.gexf.net/1.3"}

# Use any ICD GEXF file — they all have the same 1080 nodes
_REFERENCE_FILE = "Graph_Female_ICD_Age_1.gexf"


def extract_icd_mapping() -> list[dict]:
    """
    Parse an ICD GEXF file and return a list of 1080 entries:
        [{"index": 0, "icd_code": "A00", "description": "Cholera"}, ...]
    Sorted by index (0-based, matching CSV column order).
    """
    filepath = _GEXF_DIR / _REFERENCE_FILE
    tree = ET.parse(filepath)
    root = tree.getroot()

    nodes = root.findall(".//gexf:node", _NS)
    mapping = []
    for node in nodes:
        idx = int(node.get("id")) - 1  # GEXF ids are 1-based, CSV columns are 0-based
        label = node.get("label")
        atts = {}
        for av in node.findall(".//gexf:attvalue", _NS):
            atts[av.get("for")] = av.get("value")
        mapping.append({
            "index": idx,
            "icd_code": label,
            "description": atts.get("att4") or atts.get("att5") or label,
        })

    mapping.sort(key=lambda x: x["index"])
    return mapping


def main():
    print("ICD Mapping Processor")
    print(f"  GEXF directory: {_GEXF_DIR}")
    print(f"  Reference file: {_REFERENCE_FILE}")
    print()

    if not (_GEXF_DIR / _REFERENCE_FILE).exists():
        print(f"ERROR: {_REFERENCE_FILE} not found in {_GEXF_DIR}")
        return

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    mapping = extract_icd_mapping()

    output_path = _OUTPUT_DIR / "icd_mapping.json"
    with open(output_path, "w") as f:
        json.dump(mapping, f, indent=2)

    print(f"Extracted {len(mapping)} ICD codes")
    print(f"Range: {mapping[0]['icd_code']} – {mapping[-1]['icd_code']}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
