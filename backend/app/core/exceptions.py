from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


class VisionForensicsError(Exception):
    """Base application exception."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class UnsupportedFileTypeError(VisionForensicsError):
    def __init__(self, file_type: str):
        super().__init__(f"Unsupported file type: '{file_type}'", status_code=415)


class FileTooLargeError(VisionForensicsError):
    def __init__(self, max_mb: int):
        super().__init__(f"File exceeds maximum allowed size of {max_mb} MB", status_code=413)


class DocumentNotFoundError(VisionForensicsError):
    def __init__(self, document_id: str):
        super().__init__(f"Document '{document_id}' not found", status_code=404)


class StorageError(VisionForensicsError):
    def __init__(self, detail: str):
        super().__init__(f"Storage error: {detail}", status_code=500)


class PipelineError(VisionForensicsError):
    """Raised when the pipeline cannot continue due to an unrecoverable failure."""
    def __init__(self, stage: str, detail: str):
        self.stage = stage
        super().__init__(f"Pipeline failed at stage '{stage}': {detail}", status_code=500)


class StageError(Exception):
    """
    Raised inside a stage to signal a recoverable failure.
    The pipeline records the error on the context and continues.
    """
    def __init__(self, stage: str, detail: str):
        self.stage = stage
        self.detail = detail
        super().__init__(f"[{stage}] {detail}")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(VisionForensicsError)
    async def app_exception_handler(request: Request, exc: VisionForensicsError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message, "status_code": exc.status_code},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "Validation error", "details": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "An unexpected error occurred"},
        )
