class H1BGraderBlockedError(RuntimeError):
    def __init__(self, message: str, *, url: str | None = None) -> None:
        super().__init__(message)
        self.url = url
