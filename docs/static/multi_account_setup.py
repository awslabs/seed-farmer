from diagrams import Diagram, Cluster, Edge
from diagrams.aws.security import IAMRole, SecretsManager, KMS
from diagrams.aws.management import SystemsManagerParameterStore
from diagrams.aws.storage import S3
from diagrams.aws.devtools import Codebuild
from diagrams.aws.general import User
from diagrams.generic.blank import Blank

node_attr = {
    "fontsize": "20",
    #"bgcolor": "transparent"
}

graph_attr = {
    "fontsize": "32",
    #"bgcolor": "transparent"
}

with Diagram(
    filename="multi_account_setup",
    direction="TB",
    show=False,
    node_attr={"fontsize": "20"}, 
    graph_attr={"fontsize": "20", 
                "bgcolor": "transparent",
                "splines": "polyline",
                "concentrate": "true"
                },
    edge_attr={"concentrate": "true"}
):
    with Cluster("",graph_attr={"bgcolor": "#EDEDED"}):

        user = User()

        with Cluster("AWS\nAccount\n(98765432109)", graph_attr={"fontsize": "20","bgcolor":"#D3E9F5","labelloc": "b"}):

            with Cluster("us-west-2", graph_attr={"fontsize": "20", "labelloc": "b"}):

                with Cluster("SeedFarmer\nTarget\nAccount", graph_attr={"fontsize": "20", "labelloc": "b"}):
                    blankuswest2backwards = Blank(label="", width="1", height="1", shape="box", style="invis")


            with Cluster("us-east-1", graph_attr={"fontsize": "20", "labelloc": "b"}):
                
                with Cluster("SeedFarmer\nTarget\nAccount", graph_attr={"fontsize": "20", "labelloc": "b"}):
                    blankeast1backwards = Blank(label="", width="1", height="1", shape="box", style="invis")

        with Cluster("AWS\nAccount\n(123456789012)", graph_attr={"fontsize": "20","bgcolor":"#D3E9F5", "labelloc": "b"}):

            with Cluster("us-west-2", graph_attr={"fontsize": "20", "labelloc": "b"}):

                with Cluster("SeedFarmer\nToolchain\nAccount", graph_attr={"fontsize": "20", "pencolor": "red", "penwidth": "1.5", "labelloc": "t"}):
                    blanktoolchain = Blank(label="", width="1", height="1", shape="box", style="invis")

                with Cluster("SeedFarmer\nTarget\nAccount", graph_attr={"fontsize": "20", "labelloc": "b"}):
                    blank2 = Blank(label="", width="1", height="1", shape="box", style="invis")

            with Cluster("eu-west-2", graph_attr={"fontsize": "20","labelloc": "b"}):
                
                with Cluster("SeedFarmer\nTarget\nAccount", graph_attr={"fontsize": "20", "labelloc": "b"}):
                    blankwest2 = Blank(label="", width="1", height="1", shape="box", style="invis")

            with Cluster("us-east-1", graph_attr={"fontsize": "20","labelloc": "b"}):
                
                with Cluster("SeedFarmer\nTarget\nAccount", graph_attr={"fontsize": "20", "labelloc": "b"}):
                    blankeast1 = Blank(label="", width="1", height="1", shape="box", style="invis")









        user >> Edge(penwidth="3.5", style="dotted") >> blanktoolchain
        blanktoolchain >> Edge(penwidth="3.5") >> [blank2, blankwest2,blankeast1 , blankuswest2backwards, blankeast1backwards]
        # blanktoolchain >> Edge(penwidth="3.5") >> blankwest2
        # blanktoolchain >> Edge(penwidth="3.5") >> blankeast1




   