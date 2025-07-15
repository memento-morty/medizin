import os
import re

try:
    import networkx as nx
    import matplotlib.pyplot as plt
except ImportError:
    # Placeholders so script can be imported without the libs
    nx = None
    plt = None


def extract_bullets(path, max_bullets=20):
    """Extract up to max_bullets bullet-like lines from a text file."""
    bullets = []
    bullet_re = re.compile(r'^\s*(?:\u2022|-|\u2013|\*)\s*(.*)')
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            m = bullet_re.match(line)
            if m:
                text = m.group(1).strip()
                if text:
                    bullets.append(text)
                if len(bullets) >= max_bullets:
                    break
    return bullets


def extract_subpoints(text, max_subpoints=3):
    """Split a bullet text into subpoints to increase mindmap depth."""
    # Use part after the first colon if present
    if ':' in text:
        text = text.split(':', 1)[1]
    parts = re.split(r'[.,;()]', text)
    subpoints = [p.strip() for p in parts if p.strip()]
    return subpoints[:max_subpoints]


def extract_sentences(path, max_sentences=20):
    """Fallback extraction splitting the text into sentences."""
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    # Split by ., !, ? while keeping words together
    sentences = re.split(r'[.!?]\s+', text)
    cleaned = [s.strip() for s in sentences if len(s.split()) > 3]
    return cleaned[:max_sentences]


# Define hierarchical structure for the mindmap
TOPICS = {
    "Notfallmedizin": {
        "Anästhesie und Notfallmedizin": "Anästhesie-und-Notfallmedizin.txt",
    },
    "Neurologie": {
        "Neurowissenschaften": "Neurowissenschaften.txt",
        "Tiefe Hirnstimulation": "Tiefe-Hirnstimulation.txt",
        "Schädelhirntrauma in der Neurochirurgie": "Schädelhirntrauma---in-der-Neurochirurgie.txt",
        "Neurochirurgie – Hirntumorchirurgie": "Neurochirurgie–Hirntumorchirurgie.txt",
        "Spinale Navigation": "Spinale-Navigation.txt",
    },
    "Imaging und Onkologie": {
        "Radiologie": "Radiologie.txt",
        "Computertomographie": "Computertomogtaphie.txt",
        "Strahlentherapie": "Strahlentherapie-2.txt",
        "Einführung in die Strahlentherapie": "Einführung-in-die-Strahlentherapie.txt",
        "Intra- und extrakranielle stereotaktische Strahlentherapie": "Intra-und-extrakranielle-stereotaktische-Strahlentherapie.txt",
        "Radiomics": "Radiomics-2.txt",
        "Radionomics": "Radionomics.txt",
        "NCT Datenbanken": "NCT-Datenbanken.txt",
    },
    "Innere Medizin": {
        "Diarrhö und chronisch entzündliche Darmerkrankungen": "Diarrhö-und-Chronisch-Entzündliche-Darmerkrankungen.txt",
        "Hämatologie": "Hämatologie.txt",
        "Pharmakologie": "Pharmakologie.txt",
    },
    "HNO und MKG": {
        "HNO": "HNO.txt",
        "MKG": "MKG.txt",
    },
}

# Cross-topic connections (will become additional edges)
CROSS_EDGES = [
    ("Radiomics", "Radiologie"),
    ("Radionomics", "Radiologie"),
    ("Strahlentherapie", "Radiologie"),
    ("NCT Datenbanken", "Radiomics"),
    ("NCT Datenbanken", "Strahlentherapie"),
    ("Neurochirurgie – Hirntumorchirurgie", "Radiologie"),
    ("Neurochirurgie – Hirntumorchirurgie", "Strahlentherapie"),
    ("Schädelhirntrauma in der Neurochirurgie", "Neurochirurgie – Hirntumorchirurgie"),
    ("Tiefe Hirnstimulation", "Neurochirurgie – Hirntumorchirurgie"),
    ("Spinale Navigation", "Neurochirurgie – Hirntumorchirurgie"),
    ("Hämatologie", "Pharmakologie"),
    ("Diarrhö und chronisch entzündliche Darmerkrankungen", "Pharmakologie"),
    ("MKG", "HNO"),
    # Additional cross links to enrich the graph
    ("Computertomographie", "Radiologie"),
    ("Computertomographie", "Strahlentherapie"),
    ("Computertomographie", "Radiomics"),
    ("Computertomographie", "Radionomics"),
    ("Einführung in die Strahlentherapie", "Strahlentherapie"),
    ("Intra- und extrakranielle stereotaktische Strahlentherapie", "Strahlentherapie"),
    ("Intra- und extrakranielle stereotaktische Strahlentherapie", "Radiologie"),
    ("Intra- und extrakranielle stereotaktische Strahlentherapie", "Computertomographie"),
    ("HNO", "Radiologie"),
    ("MKG", "Computertomographie"),
    ("MKG", "Strahlentherapie"),
    ("Anästhesie und Notfallmedizin", "Schädelhirntrauma in der Neurochirurgie"),
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


def build_graph():
    if nx is None:
        raise RuntimeError("networkx is required to build the mindmap")

    g = nx.Graph()
    g.add_node("Medizin")  # root

    # Track which nodes exist so cross edges can be added conditionally
    nodes = {"Medizin"}

    for category, subtopics in TOPICS.items():
        g.add_node(category)
        g.add_edge("Medizin", category)
        nodes.add(category)

        for topic, filename in subtopics.items():
            g.add_node(topic)
            g.add_edge(category, topic)
            nodes.add(topic)

            path = os.path.join(os.path.dirname(__file__), filename)
            if os.path.exists(path):
                bullets = extract_bullets(path)
                if len(bullets) < 10:
                    bullets.extend(extract_sentences(path, 20 - len(bullets)))

                for bullet in bullets:
                    bullet_node = f"{topic}: {bullet}"
                    g.add_node(bullet_node)
                    g.add_edge(topic, bullet_node)
                    nodes.add(bullet_node)

                    subpoints = extract_subpoints(bullet)
                    for sub in subpoints:
                        sub_node = f"{bullet_node}: {sub}"
                        g.add_node(sub_node)
                        g.add_edge(bullet_node, sub_node)
                        nodes.add(sub_node)

    # Add cross-topic edges
    for a, b in CROSS_EDGES:
        if a in nodes and b in nodes:
            g.add_edge(a, b)

    return g


def main():
    graph = build_graph()

    if nx is None or plt is None:
        raise RuntimeError("networkx and matplotlib are required to render the mindmap")

    # Arrange nodes in columns based on colon depth so labels rarely overlap
    # Root, categories and topics share the first tier; bullet points and
    # subpoints appear in subsequent tiers.
    pos = nx.multipartite_layout(graph, subset_key=lambda n: n.count(':'))
    plt.figure(figsize=(20, 20))
    nx.draw(graph, pos, with_labels=True, node_size=50, font_size=6)
    plt.savefig("mindmap.pdf")


if __name__ == "__main__":
    main()
