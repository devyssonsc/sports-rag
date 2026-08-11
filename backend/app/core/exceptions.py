class DomainException(Exception):
    """Base exception for domain errors."""


class ResourceNotFound(DomainException):
    pass


class ResourceAlreadyExists(DomainException):
    pass

class ArticleAlreadyExists(ResourceAlreadyExists):
    pass


class ArticleNotFound(ResourceNotFound):
    pass

class NewsSourceAlreadyExists(ResourceAlreadyExists):
    pass


class NewsSourceNotFound(ResourceNotFound):
    pass


class UnsupportedNewsSourceType(DomainException):
    pass


class DiscoveryError(DomainException):
    """Raised when a discovery strategy fails to fetch or parse a source."""
    pass
