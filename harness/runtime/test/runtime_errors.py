"""Separate errors in the arguments of declared agent API calls from host infrastructure faults, so that only the
former are reported back to the agent.

Part of harness/runtime/test: the test harness: replay of learned states on the test task, and the frozen agent."""
class InfrastructureFailure(BaseException):
    pass

class APIArgumentError(ValueError):
    pass
