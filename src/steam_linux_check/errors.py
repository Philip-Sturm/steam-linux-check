class ProviderUnavailableError(RuntimeError):
    """Raised when a provider is unavailable and no cached data can be used."""

    def __init__(
        self,
        provider: str,
        message: str,
    ) -> None:
        super().__init__(message)
        self.provider = provider