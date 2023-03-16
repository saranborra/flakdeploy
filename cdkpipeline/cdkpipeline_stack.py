import aws_cdk as cdk
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_ecs_patterns as ecs_patterns
import aws_cdk.aws_codecommit as codecommit
import aws_cdk.aws_iam as iam
import aws_cdk.aws_lambda as _lambda
import aws_cdk.aws_lambda_event_sources as event_sources
import aws_cdk.aws_codebuild as codebuild
import aws_cdk.aws_codepipeline as codepipeline
import aws_cdk.aws_codepipeline_actions as codepipeline_actions
import aws_cdk.aws_ecr as ecr
import aws_cdk.aws_elasticloadbalancing as elb
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_ecr_assets as ecr_assets
import aws_cdk.aws_servicediscovery as servicediscovery
from constructs import Construct

class CdkpipelineStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a CodeCommit repository
        # repository = codecommit.Repository(self, 'MyRepository',
        #                                    repository_name='my-repo-name')

        # Create a new CodeCommit repository
        code_repo = codecommit.Repository(self, "pipeline-MyCodeRepo", repository_name = 'pipeline_repo')

        # Create ECR repository
        ecr_repo = ecr.Repository(self, "ECRRepo", repository_name="pipeline-ecr-repo")

        # Output the ECR repository URL
        cdk.CfnOutput(
            self, 'MyECRRepoURL',
            value= ecr_repo.repository_uri
        )

        # Create a new IAM role for CodeBuild
        codebuild_role = iam.Role(self, "CodeBuildRole",
                                  assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"))

        code_repo.grant_read(codebuild_role)
        ecr_repo.grant_pull_push(codebuild_role)

        # Create a CodeBuild project
        codebuild_project = codebuild.Project(
            self,
            "MyCodeBuildProject",
            source=codebuild.Source.code_commit(repository=code_repo),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_4_0,
                privileged=True
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "pre_build": {
                        "commands": [
                            "export REPOSITORY_NAME=pipeline_repo",
                            "export TAG=latest",
                            "echo Logging in to Amazon ECR...",
                            "$(aws ecr get-login --no-include-email --region $AWS_DEFAULT_REGION)"
                            #"$(aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 096721594425.dkr.ecr.us-east-1.amazonaws.com)"
                        ]
                    },
                    "build": {
                        "commands": [
                            "echo Building Docker image...",
                            "docker build -t {} .".format(ecr_repo.repository_uri),
                            "docker push {}".format(ecr_repo.repository_uri)
                        ]
                    }
                }
            })
        )

        # # Create the VPC and subnet
        # vpc = ec2.Vpc(
        #     self, "MyVpc",
        #     ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
        #     max_azs=2,
        #     subnet_configuration=[
        #         ec2.SubnetConfiguration(
        #             name='Public-Subent',
        #             subnet_type=ec2.SubnetType.PUBLIC,
        #             cidr_mask=24
        #         )],
        #     nat_gateways=1
        # )
        #
        # # subnet = ec2.Subnet(
        # #     self, "MySubnet",
        # #     vpc=vpc,
        # #     cidr_block="10.0.0.0/24",
        # # )
        #
        # # Create the ECS cluster
        #
        # cluster = ecs.Cluster(
        #     self, "MyCluster",
        #     vpc=vpc
        #     # default_cloud_map_namespace = namespace.namespace_name
        # )
        # # Add capacity to it
        # cluster.add_capacity("DefaultAutoScalingGroupCapacity",
        #                      instance_type=ec2.InstanceType("t2.micro"),
        #                      desired_capacity=3
        #                      )
        #
        # task_definition = ecs.Ec2TaskDefinition(
        #     self, "pipelineMyTaskDefinition")
        #     #network_mode = ecs.NetworkMode.BRIDGE)
        #
        # pipeliene_container = task_definition.add_container(
        #     "PipelineMyContainer",
        #     image=ecs.ContainerImage.from_ecr_repository(ecr_repo, 'latest'),  # (ecr_repo.repository_uri+":latest"),
        #     memory_reservation_mib=256,
        #     port_mappings = [ecs.PortMapping(container_port=5000)],
        #     essential=True
        # )
        #
        # # Add a port mapping
        # pipeliene_container.add_port_mappings(
        #     ecs.PortMapping(container_port=5000)
        #     #,protocol=ecs.Protocol.TCP
        # )
        #
        # service = ecs.Ec2Service(self, "Service", cluster=cluster, task_definition=task_definition,
        #                          desired_count=1
        #                          #container = pipeliene_container,
        #                          #container_port=5000
        #                          )






