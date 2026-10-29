"""Separate errors in the arguments of declared agent API calls from host infrastructure faults, so that only the
former are reported back to the agent.

Part of harness/runtime/self: the practice harness for learning from feedback alone (self)."""
class InfrastructureFailure(BaseException):
    pass

class APIArgumentError(ValueError):
    pass
