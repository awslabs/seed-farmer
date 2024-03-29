from typing import Optional

checklist = """  Be sure to check:
        1. The session that you are executing the CLI from matches the ACCOUNT and REGION
           where your toolchain is configured
        2. The session has permissions to access the proper toolchain role
        """


def no_deployment_found(deployment_name: Optional[str] = None) -> str:
    msg = "We found no deployments with yout active session."
    if deployment_name:
        msg = f"We found no deployments named {deployment_name} with your active session."

    return msg + checklist
