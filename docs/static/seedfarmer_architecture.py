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
    filename="seedfarmer_architecture",
    direction="TB",
    show=True,
    node_attr={"fontsize": "20"}, 
    graph_attr={"fontsize": "32", 
                "bgcolor": "transparent"
                }
):


    with Cluster("",graph_attr={"bgcolor": "#EDEDED"}):

        user = User("\nUser", fontsize="32")

        with Cluster("AWS",graph_attr={"fontsize": "32"}):
            with Cluster("Toolchain\nAccount \nus-east-1", graph_attr={"fontsize": "24"}):
                toolchain_role = IAMRole("SeedFarmer\nToolchain Role")
                ssm_toolchain = SystemsManagerParameterStore("\nSSM\nParameters")
                secrets_toolchain = SecretsManager("\nSecrets\nManager")

            with Cluster("Deployment\nAccount A\nus-east-1", graph_attr={"fontsize": "24"}):
                role_a = IAMRole("SeedFarmer\nModule Role")
                codebuild_a = Codebuild("\nCodeBuild")
                s3_a = S3("\nS3\nBucket")
                ssm_a = SystemsManagerParameterStore("\nSSM\nParameters")
                secrets_a = SecretsManager("\nSecrets\nManager")
                kms_a = KMS("\nKMS")
                deployment_role_a = IAMRole("SeedFarmer\nDeployment Role")

            with Cluster("Deployment\nAccount B\nus-west-2", graph_attr={"fontsize": "24"}):
                role_b = IAMRole("SeedFarmer\nModule Role")
                codebuild_b = Codebuild("\nCodeBuild")
                s3_b = S3("\nS3\nBucket")
                ssm_b = SystemsManagerParameterStore("\nSSM\nParameters")
                secrets_b = SecretsManager("\nSecrets\nManager")
                kms_b = KMS("\nKMS")
                deployment_role_b = IAMRole("SeedFarmer\nDeployment Role")


    # Connections
    user >> Edge(color="red",penwidth="3.5") >> toolchain_role
    toolchain_role >> Edge(color="red",penwidth="3.5") >> [ deployment_role_a, deployment_role_b]
    toolchain_role >>  Edge(penwidth="3.5") >> [ssm_toolchain, secrets_toolchain]

    deployment_role_a >> Edge(penwidth="3.5") >> codebuild_a >> Edge(penwidth="3.5") >> [s3_a, ssm_a, secrets_a]
    role_a >> Edge(color="red",penwidth="3.5", style="dotted")>> codebuild_a
    s3_a >> kms_a

    deployment_role_b >> Edge(penwidth="3.5") >> codebuild_b >> Edge(penwidth="3.5") >> [s3_b, ssm_b, secrets_b]
    role_b >> Edge(color="red",penwidth="3.5", style="dotted")>> codebuild_b
    s3_b >> Edge(penwidth="3.5") >> kms_b

