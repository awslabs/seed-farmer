from typing import Optional


class InvalidPathError(RuntimeError):
    def __init__(self, *args: str):
        super().__init__(*args)


class InvalidManifestError(RuntimeError):
    def __init__(self, *args: str, error_file_path: Optional[str] = None):
        super().__init__(*args)


class InvalidConfigurationError(RuntimeError):
    def __init__(self, *args: str):
        super().__init__(*args)


class InvalidSessionError(RuntimeError):
    def __init__(self, *args: str, error_message: Optional[str] = None):
        super().__init__(*args)


class ModuleDeploymentError(RuntimeError):
    def __init__(self, *args: str, error_message: Optional[str] = None):
        super().__init__(*args)


class SeedFarmerException(Exception):
    def __init__(self, *args: str, error_message: Optional[str] = None):
        super().__init__(*args)
