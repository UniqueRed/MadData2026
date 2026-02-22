"""
Comorbidity Network Processor

Parses all 16 Chronic GEXF files (8 age groups x 2 sexes) from
ComorbidityNetworksData into a single JSON file for the simulation engine.

Usage:
    cd backend && python -m app.data.comorbidity_processor
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

_GEXF_DIR = Path(__file__).resolve().parent.parent.parent.parent / (
    "data/ComorbidityNetworksData/4.Graphs-gexffiles"
)
_OUTPUT_DIR = Path(__file__).resolve().parent / "processed"

# GEXF namespace
_NS = {"gexf": "http://www.gexf.net/1.3"}

# Map GEXF node labels → internal condition keys
LABEL_TO_KEY = {
    "Hypertension": "hypertension",
    "Lipid metabolism disorders8": "high_cholesterol",
    "Chronic low back pain": "back_pain",
    "Severe vision reduction": "vision_loss",
    "Joint arthrosis": "arthrosis",
    "Diabetes mellitus": "diabetes",
    "Chronic ischemic heart disease": "cad",
    "Thyroid diseases": "thyroid_disease",
    "Cardiac arrhythmias": "arrhythmia",
    "Obesity": "obesity",
    "Hyperuricemia/gout": "gout",
    "Prostatic hyperplasia": "prostatic_hyperplasia",
    "Lower limb varicosis": "varicosis",
    "Liver disease": "liver_disease",
    "Depression": "depression",
    "Asthma/COPD": "asthma_copd",
    "Gynecological problems": "gynecological",
    "Atherosclerosis/PAOD": "atherosclerosis",
    "Osteoporosis": "osteoporosis",
    "Renal insufficiency": "ckd",
    "Cerebral ischemia/chronic stroke": "stroke",
    "Cardiac insufficiency": "heart_failure",
    "Severe hearing loss": "hearing_loss",
    "Chronic cholecystitis/gallstones": "gallstones",
    "Somatoform disorders": "somatoform",
    "Hemorrhoids": "hemorrhoids",
    "Intestinal diverticulosis": "diverticulosis",
    "Rheumatoid arthritis/chronic polyarthritis": "arthritis",
    "Cardiac valve disorders": "valve_disorder",
    "Neuropathies": "neuropathy",
    "Dizziness": "dizziness",
    "Dementia": "dementia",
    "Urinary incontinence": "urinary_incontinence",
    "Urinary tract calculi": "kidney_stones",
    "Anemia": "anemia",
    "Anxiety": "anxiety",
    "Psoriasis": "psoriasis",
    "Migraine/chronic headache": "migraine",
    "Parkinson's disease": "parkinsons",
    "Cancer": "cancer",
    "Allergy": "allergy",
    "Chronic gastritis/GERD": "gerd",
    "Sexual dysfunction": "sexual_dysfunction",
    "Insomnia": "insomnia",
    "Tobacco abuse": "tobacco_use",
    "Hypotension": "hypotension",
}

# Internal key → display label
KEY_TO_LABEL = {v: k for k, v in LABEL_TO_KEY.items()}
# Override some labels for cleaner display
KEY_TO_LABEL.update({
    "high_cholesterol": "High Cholesterol",
    "back_pain": "Chronic Low Back Pain",
    "vision_loss": "Severe Vision Loss",
    "arthrosis": "Joint Arthrosis",
    "diabetes": "Diabetes Mellitus",
    "cad": "Coronary Artery Disease",
    "thyroid_disease": "Thyroid Disease",
    "arrhythmia": "Cardiac Arrhythmia",
    "obesity": "Obesity",
    "gout": "Gout",
    "prostatic_hyperplasia": "Prostatic Hyperplasia",
    "varicosis": "Varicose Veins",
    "liver_disease": "Liver Disease",
    "depression": "Depression",
    "asthma_copd": "Asthma / COPD",
    "gynecological": "Gynecological Problems",
    "atherosclerosis": "Atherosclerosis / PAOD",
    "osteoporosis": "Osteoporosis",
    "ckd": "Chronic Kidney Disease",
    "stroke": "Stroke",
    "heart_failure": "Heart Failure",
    "hearing_loss": "Hearing Loss",
    "gallstones": "Gallstones",
    "somatoform": "Somatoform Disorder",
    "hemorrhoids": "Hemorrhoids",
    "diverticulosis": "Diverticulosis",
    "arthritis": "Rheumatoid Arthritis",
    "valve_disorder": "Cardiac Valve Disorder",
    "neuropathy": "Neuropathy",
    "dizziness": "Dizziness / Vertigo",
    "dementia": "Dementia",
    "urinary_incontinence": "Urinary Incontinence",
    "kidney_stones": "Kidney Stones",
    "anemia": "Anemia",
    "anxiety": "Anxiety",
    "psoriasis": "Psoriasis",
    "migraine": "Migraine",
    "parkinsons": "Parkinson's Disease",
    "cancer": "Cancer",
    "allergy": "Allergy",
    "gerd": "GERD / Gastritis",
    "sexual_dysfunction": "Sexual Dysfunction",
    "insomnia": "Insomnia",
    "tobacco_use": "Tobacco Use Disorder",
    "hypotension": "Hypotension",
    "hypertension": "Hypertension",
})

# Sex mapping for filenames
SEX_MAP = {"M": "Male", "F": "Female"}


def parse_gexf(filepath: Path) -> dict:
    """
    Parse a single GEXF file and return:
        {"nodes": {node_id: {"label": ..., "icd": ...}},
         "edges": [(source_key, target_key, weight), ...]}
    """
    tree = ET.parse(filepath)
    root = tree.getroot()

    graph = root.find("gexf:graph", _NS)
    nodes_el = graph.find("gexf:nodes", _NS)
    edges_el = graph.find("gexf:edges", _NS)

    # Parse nodes: id -> {label, icd_code}
    id_to_info = {}
    for node in nodes_el.findall("gexf:node", _NS):
        node_id = node.get("id")
        label = node.get("label")
        icd_code = ""
        attvalues = node.find("gexf:attvalues", _NS)
        if attvalues is not None:
            for av in attvalues.findall("gexf:attvalue", _NS):
                if av.get("for") == "att2":
                    icd_code = av.get("value", "")
        id_to_info[node_id] = {"label": label, "icd": icd_code}

    # Parse edges: source_id, target_id, weight
    edges = []
    for edge in edges_el.findall("gexf:edge", _NS):
        source_id = edge.get("source")
        target_id = edge.get("target")
        weight = float(edge.get("weight", "1.0"))

        source_label = id_to_info.get(source_id, {}).get("label")
        target_label = id_to_info.get(target_id, {}).get("label")

        source_key = LABEL_TO_KEY.get(source_label)
        target_key = LABEL_TO_KEY.get(target_label)

        if source_key and target_key:
            edges.append((source_key, target_key, weight))

    return {"nodes": id_to_info, "edges": edges}


def process_all() -> dict:
    """
    Process all 16 Chronic GEXF files and build the combined JSON structure.
    """
    # Collect condition metadata from any file (they all have the same 46 nodes)
    conditions = {}
    networks = {}

    for sex_code, sex_name in SEX_MAP.items():
        for age_group in range(1, 9):
            filename = f"Graph_{sex_name}_Chronic_Age_{age_group}.gexf"
            filepath = _GEXF_DIR / filename

            if not filepath.exists():
                print(f"  WARNING: {filename} not found, skipping")
                continue

            result = parse_gexf(filepath)

            # Build conditions metadata (from first file parsed)
            if not conditions:
                for node_info in result["nodes"].values():
                    label = node_info["label"]
                    key = LABEL_TO_KEY.get(label)
                    if key:
                        conditions[key] = {
                            "label": KEY_TO_LABEL.get(key, label),
                            "icd": node_info["icd"],
                        }

            # Build adjacency dict for this sex + age_group
            network_key = f"{sex_code}_{age_group}"
            adj = {}
            for source_key, target_key, weight in result["edges"]:
                if source_key not in adj:
                    adj[source_key] = {}
                adj[source_key][target_key] = round(weight, 4)

                # Ensure bidirectional (undirected graph)
                if target_key not in adj:
                    adj[target_key] = {}
                if source_key not in adj[target_key]:
                    adj[target_key][source_key] = round(weight, 4)

            networks[network_key] = adj
            edge_count = len(result["edges"])
            print(f"  Parsed {filename}: {edge_count} edges")

    return {"conditions": conditions, "networks": networks}


def main():
    print("Comorbidity Network Processor")
    print(f"  GEXF directory: {_GEXF_DIR}")
    print(f"  Output directory: {_OUTPUT_DIR}")
    print()

    if not _GEXF_DIR.exists():
        print(f"ERROR: GEXF directory not found: {_GEXF_DIR}")
        return

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    data = process_all()

    output_path = _OUTPUT_DIR / "comorbidity_network.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    n_conditions = len(data["conditions"])
    n_networks = len(data["networks"])
    print(f"\nDone! {n_conditions} conditions, {n_networks} networks")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
