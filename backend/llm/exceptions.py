class AuthenticationError(Exception):
    pass

class RateLimitError(Exception):
    pass

class ProviderUnavailableError(Exception):
    pass

class PromptTooLargeError(Exception):
    pass

class GenerationError(Exception):
    pass
