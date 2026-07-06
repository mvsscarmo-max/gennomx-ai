from fastapi import HTTPException, status


class GennomXError(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(GennomXError):
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(f"{resource} not found: {identifier}", code="NOT_FOUND")
        self.resource = resource
        self.identifier = identifier


class ValidationError(GennomXError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="VALIDATION_ERROR")


class AuthenticationError(GennomXError):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message, code="AUTHENTICATION_ERROR")


class AuthorizationError(GennomXError):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message, code="AUTHORIZATION_ERROR")


class IngestionError(GennomXError):
    def __init__(self, source: str, message: str) -> None:
        super().__init__(f"Ingestion failed for {source}: {message}", code="INGESTION_ERROR")
        self.source = source


class MCPError(GennomXError):
    def __init__(self, tool: str, message: str) -> None:
        super().__init__(f"MCP tool {tool} error: {message}", code="MCP_ERROR")
        self.tool = tool


def not_found_exception(resource: str, identifier: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "NOT_FOUND", "resource": resource, "identifier": identifier},
    )


def unauthorized_exception(message: str = "Authentication required") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "AUTHENTICATION_ERROR", "message": message},
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden_exception(message: str = "Insufficient permissions") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": "AUTHORIZATION_ERROR", "message": message},
    )
