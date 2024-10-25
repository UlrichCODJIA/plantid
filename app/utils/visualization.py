import io

import matplotlib.pyplot as plt
import networkx as nx
from app.extensions import knowledge_graph


def generate_knowledge_graph_visualization():
    kg = knowledge_graph

    # Create NetworkX graph
    G = nx.Graph()

    # Query all relationships from Neo4j
    with kg.driver.session() as session:
        result = session.run(
            """
        MATCH (start)-[r]->(end)
        RETURN start.name as start_name,
               labels(start)[0] as start_label,
               type(r) as relationship,
               end.name as end_name,
               labels(end)[0] as end_label
        """
        )

        # Process results and build NetworkX graph
        for record in result:
            start_node = f"{record['start_label']}: {record['start_name']}"
            end_node = f"{record['end_label']}: {record['end_name']}"
            G.add_edge(start_node, end_node, relationship=record["relationship"])

    # Generate visualization
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, k=1, iterations=50)

    # Draw nodes
    nx.draw(G, pos, with_labels=True, node_color="lightblue", node_size=2000, font_size=8, font_weight="bold")

    # Draw edge labels
    edge_labels = nx.get_edge_attributes(G, "relationship")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=6)

    # Save plot to bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=300)
    buf.seek(0)
    plt.close()  # Close the figure to free memory

    return buf
