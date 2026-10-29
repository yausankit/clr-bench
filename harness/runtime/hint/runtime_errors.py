"""Separate errors in the arguments of declared agent API calls from host infrastructure faults, so that only the
former are reported back to the agent.

Part of harness/runtime/hint: the practice harness with the lesson appended to every update input (+ lesson)."""
class InfrastructureFailure(BaseException):
    pass

class APIArgumentError(ValueError):
    pass
