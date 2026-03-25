class AiAgentError(Exception):
    """Base application exception."""


class ConfigurationError(AiAgentError):
    pass


class ProviderError(AiAgentError):
    pass


class AuthenticationError(ProviderError):
    pass


class TransportError(ProviderError):
    pass


class AgentError(AiAgentError):
    pass
