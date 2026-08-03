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

class FeedAlreadyExists(ResourceAlreadyExists):
    pass

class FeedNotFound(Exception):
    pass
