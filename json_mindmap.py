import json
import sys
import os

try:
    import networkx as nx
    import matplotlib.pyplot as plt
except ImportError:
    nx = None
    plt = None


def build_graph(node, graph, parent=None, tier=0):
    name = node.get("name")
    graph.add_node(name, tier=tier)
    if parent:
        graph.add_edge(parent, name)
    for child in node.get("children", []):
        build_graph(child, graph, name, tier + 1)


def radial_positions(graph):
    tiers = {}
    for n, data in graph.nodes(data=True):
        t = data.get("tier", 0)
        tiers.setdefault(t, []).append(n)
    shells = [tiers[k] for k in sorted(tiers)]
    return nx.shell_layout(graph, nlist=shells)


def main(path):
    if nx is None or plt is None:
        raise RuntimeError("networkx and matplotlib are required")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    g = nx.Graph()
    build_graph(data, g)
    pos = radial_positions(g)
    plt.figure(figsize=(18, 14))
    nx.draw_networkx(g, pos, node_size=50, font_size=6, edge_color="#888888")
    plt.axis("off")
    plt.tight_layout()
    out_pdf = os.path.splitext(os.path.basename(path))[0] + ".pdf"
    plt.savefig(out_pdf)
    print(f"Saved {out_pdf}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python json_mindmap.py <json_file>")
        sys.exit(1)
    main(sys.argv[1])
