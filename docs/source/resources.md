## Resources

The resources section/directory of the [project stucture](project_structure.md) contains resources (policies) that can be applied to all the roles created for [AWS CodeSeeder](https://aws-codeseeder.readthedocs.io/en/latest/) to use.

(project_policy)=
### Project Policy
`SeedFarmer` expects a policy located at `resources/projectpolicy.yaml`.  This provided by default when using the [project initialization](cookiecutter_new_project).  This can be used as-is, modified, or you can provide your own - but this policy contains the MINIMUM permissions `SeedFarmer` needs to operate.

(permission_boundary)=
### Permission Boundary Support
`SeedFarmer` supports the concept of a [permission boundary](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html).  This should already be deployed in your AWS account prior to use.


Please see the [deployment manifest](deployment_manifest) definition for details of configuring `SeedFarmer` to use your customized resources.

