from diagrams import Diagram, Cluster, Edge
from diagrams.generic.blank import Blank

with Diagram(
    filename="project_definition",
    direction="LR",
    show=False,
    node_attr={"fontsize": "16"},
    graph_attr={"fontsize": "18", "bgcolor": "transparent", "ranksep": "1.0", "nodesep": "0.5"},
):
    with Cluster("Project", graph_attr={"bgcolor": "#EDEDED", "fontsize": "18"}):
        
        # First row of deployments
        with Cluster("Deployment", graph_attr={"bgcolor": "#D3E9F5", "fontsize": "18"}):
            with Cluster("Group", graph_attr={"bgcolor": "#F5E6D3"}):
                m1 = Blank(label="Module", shape="box", width="1.5", height="0.5", fillcolor="white", style="rounded,filled", labelloc="c")
            with Cluster("Group ", graph_attr={"bgcolor": "#F5E6D3", "fontsize": "18"}):
                m2 = Blank(label="Module", shape="box", width="1.5", height="0.5", fillcolor="white", style="rounded,filled", labelloc="c")
            with Cluster("Group  ", graph_attr={"bgcolor": "#F5E6D3", "fontsize": "18"}):
                m3 = Blank(label="Module", shape="box", width="1.5", height="0.5", fillcolor="white", style="rounded,filled", labelloc="c")
            with Cluster("Group   ", graph_attr={"bgcolor": "#F5E6D3", "fontsize": "18"}):
                m4 = Blank(label="Module", shape="box", width="1.5", height="0.5", fillcolor="white", style="rounded,filled", labelloc="c")

        with Cluster("Deployment ", graph_attr={"bgcolor": "#D3E9F5", "fontsize": "18"}):
            with Cluster("Group    ", graph_attr={"bgcolor": "#F5E6D3", "fontsize": "18"}):
                m5 = Blank(label="Module", shape="box", width="1.5", height="0.5",fillcolor="white", style="rounded,filled", labelloc="c")
            with Cluster("Group     ", graph_attr={"bgcolor": "#F5E6D3", "fontsize": "18"}):
                m6 = Blank(label="Module", shape="box", width="1.5", height="0.5",fillcolor="white", style="rounded,filled", labelloc="c")
            with Cluster("Group      ", graph_attr={"bgcolor": "#F5E6D3", "fontsize": "18"}):
                m7 = Blank(label="Module", shape="box", width="1.5", height="0.5",fillcolor="white", style="rounded,filled", labelloc="c")
            with Cluster("Group       ", graph_attr={"bgcolor": "#F5E6D3", "fontsize": "18"}):
                m8 = Blank(label="Module", shape="box", width="1.5", height="0.5",fillcolor="white", style="rounded,filled", labelloc="c")

        # Second row of deployments
        with Cluster("Deployment  ", graph_attr={"bgcolor": "#D3E9F5", "fontsize": "18"}):
            with Cluster("Group        ", graph_attr={"bgcolor": "#F5E6D3", "fontsize": "18"}):
                m9 = Blank(label="Module", shape="box", width="1.5", height="0.5",fillcolor="white", style="rounded,filled", labelloc="c")
            with Cluster("Group         ", graph_attr={"bgcolor": "#F5E6D3", "fontsize": "18"}):
                m10 = Blank(label="Module", shape="box", width="1.5", height="0.5",fillcolor="white", style="rounded,filled", labelloc="c")
            with Cluster("Group          ", graph_attr={"bgcolor": "#F5E6D3", "fontsize": "18"}):
                m11 = Blank(label="Module", shape="box", width="1.5", height="0.5",fillcolor="white", style="rounded,filled", labelloc="c")
            with Cluster("Group           ", graph_attr={"bgcolor": "#F5E6D3", "fontsize": "18"}):
                m12 = Blank(label="Module", shape="box", width="1.5", height="0.5",fillcolor="white", style="rounded,filled", labelloc="c")

        with Cluster("Deployment   ", graph_attr={"bgcolor": "#D3E9F5", "fontsize": "18"}):
            with Cluster("Group            ", graph_attr={"bgcolor": "#F5E6D3", "fontsize": "18"}):
                m13 = Blank(label="Module", shape="box", width="1.5", height="0.5",fillcolor="white", style="rounded,filled", labelloc="c")
            with Cluster("Group             ", graph_attr={"bgcolor": "#F5E6D3", "fontsize": "18"}):
                m14 = Blank(label="Module", shape="box", width="1.5", height="0.5",fillcolor="white", style="rounded,filled", labelloc="c")
            with Cluster("Group              ", graph_attr={"bgcolor": "#F5E6D3", "fontsize": "18"}):
                m15 = Blank(label="Module", shape="box", width="1.5", height="0.5",fillcolor="white", style="rounded,filled", labelloc="c")
            with Cluster("Group               ", graph_attr={"bgcolor": "#F5E6D3", "fontsize": "18"}):
                m16 = Blank(label="Module", shape="box", width="1.5", height="0.5",fillcolor="white", style="rounded,filled", labelloc="c")
    
    # Invisible edges to force grid layout
    m1 - Edge(style="invis") - m5
    m5 - Edge(style="invis") - m9
    m9 - Edge(style="invis") - m13
