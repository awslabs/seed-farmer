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
    filename="simple_account_setup",
    direction="LR",
    show=False,
    node_attr={"fontsize": "20"}, 
    graph_attr={"fontsize": "20", 
                "bgcolor": "transparent"
                }
):
    with Cluster("",graph_attr={"bgcolor": "#EDEDED"}):

        user = User()

        with Cluster("AWS\nAccount\n(123456789012)", graph_attr={"fontsize": "20","bgcolor":"#D3E9F5"}):

            with Cluster("us-west-2", graph_attr={"fontsize": "20"}):

                with Cluster("SeedFarmer\nToolchain\nAccount", graph_attr={"fontsize": "20", "pencolor": "red", "penwidth": "1.5"}):
                    blank1 = Blank(label="", width="1", height="1", shape="box", style="invis")

                with Cluster("SeedFarmer\nTarget\nAccount", graph_attr={"fontsize": "20"}):
                    blank2 = Blank(label="", width="1", height="1", shape="box", style="invis")

        user >> Edge(penwidth="3.5") >> blank1
        blank1 >> Edge(penwidth="3.5") >> blank2



   