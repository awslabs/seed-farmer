from diagrams import Diagram, Cluster, Edge
from diagrams.aws.security import IAMRole, SecretsManager, KMS
from diagrams.aws.management import SystemsManagerParameterStore
from diagrams.aws.storage import S3
from diagrams.aws.devtools import Codebuild
from diagrams.aws.general import User

node_attr = {
    "fontsize": "20",
    #"bgcolor": "transparent"
}

graph_attr = {
    "fontsize": "32",
    #"bgcolor": "transparent"
}

with Diagram(
    filename="role_assumption",
    direction="LR",
    show=False,
    node_attr={"fontsize": "20"}, 
    graph_attr={"fontsize": "24", 
                "bgcolor": "transparent"
                }
):
    with Cluster("",graph_attr={"bgcolor": "#EDEDED"}):

        user = User("\nTrusted\nPrincipal", fontsize="24")

        with Cluster("Toolchain\nAccount\n(123456789012)", graph_attr={"fontsize": "20","bgcolor":"#D3E9F5"}):
            toolchain_role = IAMRole("SeedFarmer\nToolchain Role")

        with Cluster("Deployment\nAccount \n(333333333333)", graph_attr={"fontsize": "20","bgcolor":"#D3E9F5"}):
            deployment_role_c = IAMRole("SeedFarmer\nDeployment\nRole")
            codebuild_c = Codebuild("\nCodeBuild")
            module_role_c = IAMRole("SeedFarmer\nModule\nRole")

        with Cluster("Deployment\nAccount \n(222222222222)", graph_attr={"fontsize": "20","bgcolor":"#D3E9F5"}):
            deployment_role_b = IAMRole("SeedFarmer\nDeployment\nRole")
            codebuild_b = Codebuild("\nCodeBuild")
            module_role_b = IAMRole("SeedFarmer\nModule\nRole")

        with Cluster("Deployment\nAccount \n(111111111111)", graph_attr={"fontsize": "20","bgcolor":"#D3E9F5"}):
            deployment_role_a = IAMRole("SeedFarmer\nDeployment\nRole")
            codebuild_a = Codebuild("\nCodeBuild")
            module_role_a = IAMRole("SeedFarmer\nModule\nRole")



    # Connections
    user >> Edge(label="Assume\nRole",penwidth="3.5",style="dotted", fontsize="20") >> toolchain_role
    toolchain_role >> Edge(color="red",penwidth="3.5", fontsize="20") >> [ deployment_role_a, deployment_role_b, deployment_role_c]

    deployment_role_a >> Edge(style="dotted",penwidth="3.5",label="Starts", fontsize="20") >> codebuild_a << Edge(penwidth="3.5",label="Attached", fontsize="20") << module_role_a

    deployment_role_b >> Edge(style="dotted",penwidth="3.5",label="Starts", fontsize="20") >> codebuild_b << Edge(penwidth="3.5",label="Attached", fontsize="20") << module_role_b

    deployment_role_c >> Edge(style="dotted",penwidth="3.5",label="Starts", fontsize="20") >> codebuild_c << Edge(penwidth="3.5",label="Attached", fontsize="20") << module_role_c

