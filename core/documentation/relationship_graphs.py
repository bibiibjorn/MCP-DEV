"""Relationship graph visualization for Power BI models."""

from __future__ import annotations

import math
import os
from typing import Any, Dict, List, Optional, Tuple

from .utils import ensure_dir, now_iso, safe_filename, GRAPH_SIZE


def generate_relationship_graph(
    relationships: List[Dict[str, Any]], output_dir: Optional[str] = None
) -> Tuple[Optional[str], List[str]]:
    """Generate a static PNG relationship graph using matplotlib and networkx.

    Args:
        relationships: List of relationship dictionaries
        output_dir: Optional output directory for the graph

    Returns:
        Tuple of (graph_path, error_notes)
    """
    if not relationships:
        return None, []
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import networkx as nx
    except Exception as exc:
        return None, [f"Graph generation unavailable: {exc}"]

    graph_dir = ensure_dir(output_dir)
    graph_path = (
        os.path.join(graph_dir, safe_filename("relationships", f"graph_{now_iso()}"))
        + ".png"
    )
    graph = nx.DiGraph()
    for rel in relationships:
        frm = rel.get("from_table")
        to = rel.get("to_table")
        if frm:
            graph.add_node(frm)
        if to:
            graph.add_node(to)
        if frm and to:
            graph.add_edge(
                frm,
                to,
                active=rel.get("is_active"),
                cardinality=rel.get("cardinality"),
                direction=rel.get("direction"),
                weight=1.0,
            )
    try:
        plt.figure(figsize=GRAPH_SIZE)
        if graph.number_of_nodes() == 0:
            return None, []
        k = 1 / math.sqrt(max(graph.number_of_nodes(), 1))
        layout = nx.spring_layout(graph, k=k, seed=42)
        node_colors = ["#1f77b4" for _ in graph.nodes]
        edge_colors = [
            "#2ca02c" if data.get("active") else "#d62728"
            for _, _, data in graph.edges(data=True)
        ]
        nx.draw_networkx_nodes(graph, layout, node_size=1400, node_color=node_colors)
        nx.draw_networkx_labels(graph, layout, font_size=9)
        nx.draw_networkx_edges(
            graph,
            layout,
            edge_color=edge_colors,
            arrows=True,
            arrowstyle="-|>",
            arrowsize=14,
        )
        try:
            active_edges = sum(
                1 for _, _, data in graph.edges(data=True) if data.get("active")
            )
            inactive_edges = graph.number_of_edges() - active_edges
            plt.title(
                f"Model Relationships (Active: {active_edges}, Inactive: {inactive_edges})"
            )
        except Exception:
            pass
        plt.tight_layout()
        plt.savefig(graph_path, dpi=220)
        plt.close()
        return graph_path, []
    except Exception as exc:
        return None, [f"Failed to render graph: {exc}"]


def generate_interactive_relationship_graph(
    relationships: List[Dict[str, Any]], output_dir: Optional[str] = None
) -> Tuple[Optional[str], List[str]]:
    """Generate an interactive HTML relationship graph using Plotly.

    Args:
        relationships: List of relationship dictionaries
        output_dir: Optional output directory for the graph

    Returns:
        Tuple of (graph_path, error_notes)
    """
    if not relationships:
        return None, []

    try:
        import plotly.graph_objects as go
        import networkx as nx
    except Exception as exc:
        return None, [
            f"Interactive graph generation unavailable: {exc}. Install plotly and networkx."
        ]

    graph_dir = ensure_dir(output_dir)
    graph_path = (
        os.path.join(
            graph_dir, safe_filename("relationships", f"interactive_graph_{now_iso()}")
        )
        + ".html"
    )

    # Build networkx graph
    G = nx.DiGraph()
    for rel in relationships:
        frm = rel.get("from_table")
        to = rel.get("to_table")
        if frm and to:
            G.add_edge(
                frm,
                to,
                active=rel.get("is_active"),
                cardinality=rel.get("cardinality"),
                direction=rel.get("direction"),
                from_col=rel.get("from_column"),
                to_col=rel.get("to_column"),
            )

    if G.number_of_nodes() == 0:
        return None, []

    # Create layout with improved handling of disconnected components
    try:
        # Identify connected components
        if G.is_directed():
            components = list(nx.weakly_connected_components(G))
        else:
            components = list(nx.connected_components(G))

        # Sort components by size (largest first)
        components = sorted(components, key=len, reverse=True)

        # Layout the main component with more space
        main_component = components[0]
        main_subgraph = G.subgraph(main_component)

        # Use spring layout for main component with tighter spacing
        k_value = 0.8 / math.sqrt(len(main_component))  # Reduced from 2
        main_pos = nx.spring_layout(
            main_subgraph, k=k_value, iterations=50, seed=42, scale=2.0
        )

        # Initialize final positions with main component
        pos = dict(main_pos)

        # Place disconnected components in a compact ring around the main component
        if len(components) > 1:
            # Calculate bounding box of main component
            main_x = [coord[0] for coord in main_pos.values()]
            main_y = [coord[1] for coord in main_pos.values()]
            main_center_x = sum(main_x) / len(main_x)
            main_center_y = sum(main_y) / len(main_y)
            main_radius = max(
                max(abs(x - main_center_x) for x in main_x),
                max(abs(y - main_center_y) for y in main_y),
            )

            # Place disconnected nodes/components closer to main component
            ring_radius = main_radius + 1.5  # Reduced from default separation
            angle_step = (2 * math.pi) / sum(len(comp) for comp in components[1:])
            current_angle = 0

            for component in components[1:]:
                component_subgraph = G.subgraph(component)

                if len(component) == 1:
                    # Single disconnected node - place on ring
                    node = list(component)[0]
                    pos[node] = (
                        main_center_x + ring_radius * math.cos(current_angle),
                        main_center_y + ring_radius * math.sin(current_angle),
                    )
                    current_angle += angle_step
                else:
                    # Small subgraph - layout internally then place as group
                    comp_k = 0.5 / math.sqrt(len(component))
                    comp_pos = nx.spring_layout(
                        component_subgraph, k=comp_k, iterations=30, seed=42, scale=0.5
                    )

                    # Calculate group center angle
                    group_angle = current_angle + (angle_step * len(component) / 2)
                    group_x = main_center_x + ring_radius * math.cos(group_angle)
                    group_y = main_center_y + ring_radius * math.sin(group_angle)

                    # Place nodes relative to group center
                    for node, (x, y) in comp_pos.items():
                        pos[node] = (group_x + x, group_y + y)

                    current_angle += angle_step * len(component)
    except Exception:
        # Fallback to basic spring layout if component handling fails
        try:
            pos = nx.spring_layout(G, k=1.0, iterations=50, seed=42)
        except Exception:
            pos = nx.random_layout(G, seed=42)

    # Prepare edge traces with separate traces for active and inactive
    active_edge_x = []
    active_edge_y = []
    active_edge_text = []

    inactive_edge_x = []
    inactive_edge_y = []
    inactive_edge_text = []

    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        is_active = edge[2].get("active", False)

        hover_text = (
            f"<b>Relationship</b><br>"
            f"From: {edge[0]}<br>"
            f"  Column: {edge[2].get('from_col', 'N/A')}<br>"
            f"To: {edge[1]}<br>"
            f"  Column: {edge[2].get('to_col', 'N/A')}<br>"
            f"Cardinality: {edge[2].get('cardinality', 'N/A')}<br>"
            f"Direction: {edge[2].get('direction', 'N/A')}<br>"
            f"Status: <b>{'Active' if is_active else 'Inactive'}</b>"
        )

        if is_active:
            active_edge_x.extend([x0, x1, None])
            active_edge_y.extend([y0, y1, None])
            active_edge_text.append(hover_text)
        else:
            inactive_edge_x.extend([x0, x1, None])
            inactive_edge_y.extend([y0, y1, None])
            inactive_edge_text.append(hover_text)

    # Create edge traces
    traces = []

    if active_edge_x:
        active_edge_trace = go.Scatter(
            x=active_edge_x,
            y=active_edge_y,
            mode="lines",
            line=dict(width=2.5, color="#2ecc71"),  # Green
            hoverinfo="text",
            text=active_edge_text,
            name="Active Relationships",
            showlegend=True,
        )
        traces.append(active_edge_trace)

    if inactive_edge_x:
        inactive_edge_trace = go.Scatter(
            x=inactive_edge_x,
            y=inactive_edge_y,
            mode="lines",
            line=dict(width=1.5, color="#e74c3c", dash="dash"),  # Red dashed
            hoverinfo="text",
            text=inactive_edge_text,
            name="Inactive Relationships",
            showlegend=True,
        )
        traces.append(inactive_edge_trace)

    # Prepare node trace with better styling
    node_x = []
    node_y = []
    node_text = []
    node_hover = []
    node_colors = []
    node_sizes = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

        in_degree = G.in_degree(node)
        out_degree = G.out_degree(node)
        total_degree = in_degree + out_degree

        # Color based on connectivity (disconnected nodes are different color)
        if total_degree == 0:
            node_colors.append("#95a5a6")  # Gray for disconnected
            node_sizes.append(15)
        else:
            node_colors.append("#3498db")  # Blue for connected
            # Size based on degree (more connections = bigger)
            node_sizes.append(20 + min(total_degree * 3, 30))

        node_hover.append(
            f"<b>{node}</b><br>"
            f"Incoming: {in_degree}<br>"
            f"Outgoing: {out_degree}<br>"
            f"Total connections: {total_degree}"
        )

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="top center",
        textfont=dict(size=10, color="#2c3e50", family="Arial Black"),
        hoverinfo="text",
        hovertext=node_hover,
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=2, color="#2c3e50"),
            opacity=0.9,
        ),
        name="Tables",
        showlegend=True,
    )
    traces.append(node_trace)

    # Create figure with improved layout
    fig = go.Figure(data=traces)

    # Count relationships for title
    active_count = sum(1 for _, _, d in G.edges(data=True) if d.get("active"))
    inactive_count = G.number_of_edges() - active_count

    fig.update_layout(
        title={
            "text": f"<b>Power BI Model Relationships</b><br>"
            f"<sup>Tables: {G.number_of_nodes()} | "
            f"Active: {active_count} | Inactive: {inactive_count}</sup>",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 18, "color": "#2c3e50"},
        },
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#2c3e50",
            borderwidth=1,
        ),
        hovermode="closest",
        margin=dict(b=20, l=20, r=20, t=80),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="white",
        font=dict(family="Arial", size=12, color="#2c3e50"),
        height=800,
    )

    # Save to HTML
    try:
        fig.write_html(graph_path)
        return graph_path, []
    except Exception as exc:
        return None, [f"Failed to save interactive graph: {exc}"]
