from typing import Optional


def no_deployment_found(deployment_name: Optional[str] = None) -> str:
    msg = "We found no deployments with your active session."
    if deployment_name:
        msg = f"We found no deployments named {deployment_name} with your active session."

    checklist = """  Be sure to check:
            1. The session that you are executing the CLI from matches the ACCOUNT and REGION
            where your toolchain is configured
            2. The session has permissions to access the proper toolchain role
            """

    return msg + checklist


def git_error_support() -> str:
    return """
    1. Make sure your path to the repo is correct and valid (check your module manifests!)
    2. The credentials used to call SeedFarmer have access to the repo
    3. The credentials used to call SeedFarmer have not expired
    """
