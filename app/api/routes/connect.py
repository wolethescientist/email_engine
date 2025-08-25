import logging
from fastapi import APIRouter, HTTPException, status

from ...schemas.user import ConnectValidateRequest, ConnectValidateResponse
from ...services.connection_service import validate_connection
from ...core.config import get_settings

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["connect"])
settings = get_settings()


@router.post("/connect", response_model=ConnectValidateResponse, status_code=status.HTTP_200_OK)
def connect(body: ConnectValidateRequest):
    """Validate IMAP/SMTP connectivity and credentials without saving or returning tokens."""
    try:
        if body.password is None and not body.access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either password or access_token",
            )

        validate_connection(
            email=str(body.email),
            password=body.password.get_secret_value() if body.password else None,
            imap_host=body.imap_host,
            imap_port=body.imap_port,
            smtp_host=body.smtp_host,
            smtp_port=body.smtp_port,
            access_token=body.access_token,
        )

        return ConnectValidateResponse(success=True, message="Connection validated")

    except ValueError as e:
        logger.warning(f"Connection validation failed for {body.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred during connection validation for {body.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal error occurred.",
        )