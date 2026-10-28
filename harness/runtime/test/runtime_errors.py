"""Distinguish declared agent API argument errors from host infrastructure faults."""
class InfrastructureFailure(BaseException):
    pass

class APIArgumentError(ValueError):
    pass
