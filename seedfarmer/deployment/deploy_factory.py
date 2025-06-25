#    Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License").
#    You may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from __future__ import annotations

from typing import Type

import seedfarmer.errors
from seedfarmer.deployment.deploy_base import DeployModule
from seedfarmer.deployment.deploy_local import DeployLocalModule
from seedfarmer.deployment.deploy_remote import DeployRemoteModule
from seedfarmer.models.transfer import ModuleDeployObject
from seedfarmer.services.session_manager import (
    ISessionManager,
    SessionManager,
    SessionManagerLocalImpl,
    SessionManagerRemoteImpl,
)


class DeployModuleFactory:
    @staticmethod
    def create(mdo: ModuleDeployObject) -> DeployModule:
        session_instance = SessionManager()
        session_type: Type[ISessionManager] = type(session_instance)
        if session_type is SessionManagerRemoteImpl:
            return DeployRemoteModule(mdo)
        elif session_type is SessionManagerLocalImpl:
            return DeployLocalModule(mdo)
        else:
            raise seedfarmer.errors.InvalidConfigurationError(f"Unsupported session type: {session_type}")

    @staticmethod
    def is_local() -> bool:
        session_instance = SessionManager()
        session_type: Type[ISessionManager] = type(session_instance)
        if session_type is SessionManagerRemoteImpl:
            return False
        else:
            return True
