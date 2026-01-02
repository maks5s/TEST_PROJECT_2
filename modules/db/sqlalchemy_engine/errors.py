class DbConnectionError(Exception):
    "Custom DB Connection Error"
    pass


class DatabaseUpdateParamsEventError(Exception):
    """Error that happened during update of database params for sqlalchemy `do_connect` event."""
    pass


class MissingSessionError(Exception):
    """Missing Session Error."""

    def __init__(self):
        """Set error message."""
        super().__init__("Missing session in current context.")


class SessionMakerNotInitializedError(Exception):
    """Session Maker Not Initialized Error."""

    def __init__(self):
        """Set error message."""
        super().__init__("Session Maker is not initialized. Check if `Database` was initialized.")
