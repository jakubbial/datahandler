class BdlError(Exception):
    """Base class for errors raised while talking to the BDL API."""


class BdlRateLimitError(BdlError):
    """BDL rejected the request because the rate limit was exceeded (HTTP 429)."""


class BdlUpstreamError(BdlError):
    """BDL failed, timed out, was unreachable, or returned an unusable response."""


class BdlNotFoundError(BdlError):
    """BDL reported that the requested resource does not exist (HTTP 404)."""
