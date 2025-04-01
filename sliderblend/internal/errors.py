class IBMStorageError(Exception):
    """Custom exception for IBM Cloud Storage errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
