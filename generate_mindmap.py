"""
generate_mindmap_columnar.py

Draws the medical‑topics mind‑map with a *multipartite* (columnar) layout
instead of a force‑directed spring layout.  Each “tier” is determined by how
many colons ‘:’ a node name contains:

    tier 0 →  root          (“Medizin”)
    tier 1 →  category      (“Neurologie” …)
    tier 2 →  topic         (“Radiologie” …)
    tier 3 →  bullet        (“Radiologie: CT hat …”)
    tier 4 →  sub‑bullet    (“Radiologie: CT hat …: Dosisreduktion”)

The code below is self‑contained; install the two pure‑Python libraries once:

    pip install networkx matplotlib
"""

import os
import re

try:
    import networkx as nx
    import matplotlib.pyplot as plt
except ImportError:  # graceful import guard
    nx = None
    plt = None


# ──────────────────────────────────────────────────────── helpers ────
def extract_bullets(path: str, max_bullets: int = 20) -> list[str]:
    """Grab bullet‑like lines (•, –, –, *) from a UTF‑8 text file."""
    bullets: list[str] = []
    bullet_re = re.compile(r'^\s*(?:\u2022|-|\u2013|\*)\s*(.*)')
    with open(path, encoding="utf‑8") as fh:
        for line in fh:
            m = bullet_re.match(line)
            if m and (txt := m.group(1).strip()):
                bullets.append(txt)
                if len(bullets) >= max_bullets:
                    break
    return bullets


def extract_subpoints(text: str, max_subpoints: int = 3) -> list[str]:
    """Break a bullet into 0‑3 shorter phrases to deepen the tree."""
    text = text.split(":", 1)[1] if ":" in text else text
    parts = re.split(r"[.,;()]", text)
    return [p.strip() for p in parts if p.strip()][:max_subpoints]


def extract_sentences(path: str, max_sentences: int = 20) -> list[str]:
    """Fallback: split whole file into sentences if no bullets present."""
    with open(path, encoding="utf‑8") as fh:
        text = fh.read()
    sentences = re.split(r"[.!?]\s+", text)
    return [s.strip() for s in sentences if len(s.split()) > 3][:max_sentences]


# ─────────────────────────────────────────────────── data definition ───
TOPICS = {                 # (exactly the dictionary from your earlier code)
    "Notfallmedizin": {
        "Anästhesie und Notfallmedizin": "Anästhesie-und-Notfallmedizin.txt",
    },
    "Neurologie": {
        "Neurowissenschaften": "Neurowissenschaften.txt",
        "Tiefe Hirnstimulation": "Tiefe-Hirnstimulation.txt",
        "Schädelhirntrauma in der Neurochirurgie":
            "Schädelhirntrauma---in-der-Neurochirurgie.txt",
        "Neurochirurgie – Hirntumorchirurgie":
            "Neurochirurgie–Hirntumorchirurgie.txt",
        "Spinale Navigation": "Spinale-Navigation.txt",
    },
    "Imaging und Onkologie": {
        "Radiologie": "Radiologie.txt",
        "Computertomographie": "Computertomogtaphie.txt",
        "Strahlentherapie": "Strahlentherapie-2.txt",
        "Einführung in die Strahlentherapie": "Einführung-in-die-Strahlentherapie.txt",
        "Intra- und extrakranielle stereotaktische Strahlentherapie":
            "Intra-und-extrakranielle-stereotaktische-Strahlentherapie.txt",
        "Radiomics": "Radiomics-2.txt",
        "Radionomics": "Radionomics.txt",
        "NCT Datenbanken": "NCT-Datenbanken.txt",
    },
    "Innere Medizin": {
        "Diarrhö und chronisch entzündliche Darmerkrankungen":
            "Diarrhö-und-Chronisch-Entzündliche-Darmerkrankungen.txt",
        "Hämatologie": "Hämatologie.txt",
        "Pharmakologie": "Pharmakologie.txt",
    },
    "HNO und MKG": {
        "HNO": "HNO.txt",
        "MKG": "MKG.txt",
    },
}

CROSS_EDGES = [
    ("Radiomics", "Radiologie"),
    ("Radionomics", "Radiologie"),
    ("Strahlentherapie", "Radiologie"),
    ("NCT Datenbanken", "Radiomics"),
    ("NCT Datenbanken", "Strahlentherapie"),
    ("Neurochirurgie – Hirntumorchirurgie", "Radiologie"),
    ("Neurochirurgie – Hirntumorchirurgie", "Strahlentherapie"),
    ("Schädelhirntrauma in der Neurochirurgie",
     "Neurochirurgie – Hirntumorchirurgie"),
    ("Tiefe Hirnstimulation", "Neurochirurgie – Hirntumorchirurgie"),
    ("Spinale Navigation", "Neurochirurgie – Hirntumorchirurgie"),
    ("Hämatologie", "Pharmakologie"),
    ("Diarrhö und chronisch entzündliche Darmerkrankungen", "Pharmakologie"),
    ("MKG", "HNO"),
    ("Computertomographie", "Radiologie"),
    ("Computertomographie", "Strahlentherapie"),
    ("Computertomographie", "Radiomics"),
    ("Computertomographie", "Radionomics"),
    ("Einführung in die Strahlentherapie", "Strahlentherapie"),
    ("Intra- und extrakranielle stereotaktische Strahlentherapie",
     "Strahlentherapie"),
    ("Intra- und extrakranielle stereotaktische Strahlentherapie",
     "Radiologie"),
    ("Intra- und extrakranielle stereotaktische Strahlentherapie",
     "Computertomographie"),
    ("HNO", "Radiologie"),
    ("MKG", "Computertomographie"),
    ("MKG", "Strahlentherapie"),
    ("Anästhesie und Notfallmedizin",
     "Schädelhirntrauma in der Neurochirurgie"),
    ("Anästhesie und Notfallmedizin", "Radiologie"),
    ("Anästhesie und Notfallmedizin", "Computertomographie"),
    ("Pharmakologie", "Radiologie"),
    ("Pharmakologie", "Strahlentherapie"),
    ("Hämatologie", "Strahlentherapie"),
    ("Neurochirurgie – Hirntumorchirurgie", "Computertomographie"),
    ("Neurowissenschaften", "Tiefe Hirnstimulation"),
    ("Neurowissenschaften", "Schädelhirntrauma in der Neurochirurgie"),
    ("Neurowissenschaften", "Radiologie"),
    ("NCT Datenbanken", "Computertomographie"),
    ("NCT Datenbanken", "Radionomics"),
    ("Radiomics", "Radionomics"),
    ("Radiomics", "Tiefe Hirnstimulation"),
    ("Radionomics", "Tiefe Hirnstimulation"),
    ("Spinale Navigation", "Computertomographie"),
    ("Spinale Navigation", "Radiologie"),
    ("Spinale Navigation", "Strahlentherapie"),
    ("Schädelhirntrauma in der Neurochirurgie", "Radiologie"),
    ("Schädelhirntrauma in der Neurochirurgie", "Computertomographie"),
    ("Radiologie", "Neurowissenschaften"),
]


# ───────────────────────────────────────────────────── graph builder ───
def build_graph(include_bullets: bool = True,
                include_subpoints: bool = False) -> "nx.Graph":
    if nx is None:
        raise RuntimeError("networkx is required")

    g = nx.Graph()
    g.add_node("Medizin")
    nodes_present = {"Medizin"}

    for category, subtopics in TOPICS.items():
        g.add_node(category)
        g.add_edge("Medizin", category)
        nodes_present.add(category)

        for topic, filename in subtopics.items():
            g.add_node(topic)
            g.add_edge(category, topic)
            nodes_present.add(topic)

            if not include_bullets:
                continue

            path = os.path.join(os.path.dirname(__file__), filename)
            if not os.path.exists(path):
                continue

            bullets = extract_bullets(path, max_bullets=10)
            if len(bullets) < 5:
                bullets.extend(extract_sentences(path, 5 - len(bullets)))

            for bullet in bullets:
                bullet_node = f"{topic}: {bullet}"
                g.add_node(bullet_node)
                g.add_edge(topic, bullet_node)
                nodes_present.add(bullet_node)

                if not include_subpoints:
                    continue

                for sub in extract_subpoints(bullet, max_subpoints=3):
                    sub_node = f"{bullet_node}: {sub}"
                    g.add_node(sub_node)
                    g.add_edge(bullet_node, sub_node)
                    nodes_present.add(sub_node)

    for a, b in CROSS_EDGES:
        if a in nodes_present and b in nodes_present:
            g.add_edge(a, b)

    return g


# ──────────────────────────────────────────────────────────── main ───
def main() -> None:
    if nx is None or plt is None:
        raise RuntimeError("networkx and matplotlib are required")

    # Pick your depth here
    graph = build_graph(include_bullets=True, include_subpoints=False)

    # ── NEW: mark each node with its tier (number of ':') ────────────
    for n in graph:
        graph.nodes[n]["tier"] = n.count(":")  # 0=root, 1=category, …

    # multipartite_layout now just needs the *attribute name*
    pos = nx.multipartite_layout(graph, subset_key="tier", align="horizontal")
    # ─────────────────────────────────────────────────────────────────

    plt.figure(figsize=(18, 14))
    nx.draw_networkx(graph,
                     pos,
                     node_size=50,
                     font_size=6,
                     with_labels=True,
                     edge_color="#888888")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig("mindmap_columnar.pdf")
    print("Saved mindmap_columnar.pdf")


if __name__ == "__main__":
    main()
