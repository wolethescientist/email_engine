from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...schemas.user import ConnectionRequest, ConnectionResponse, UserRole
from ...services.connection_service import validate_connection
from ...db.session import get_db
from ...db.models.user import User
from ...core.security import encrypt_secret, create_access_token
from ...core.config import get_settings

router = APIRouter(prefix="", tags=["connect"]) 
settings = get_settings()


@router.post("/connect", response_model=ConnectionResponse, status_code=status.HTTP_200_OK)
def connect(body: ConnectionRequest, db: Session = Depends(get_db)):
    # Validate IMAP & SMTP with TLS
    try:
        validate_connection(
            email=str(body.email),
            password=body.password.get_secret_value(),
            imap_host=body.imap_host,
            imap_port=body.imap_port,
            smtp_host=body.smtp_host,
            smtp_port=body.smtp_port,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Upsert user and store encrypted password
    user = db.query(User).filter(User.email == str(body.email)).first()
    encrypted = encrypt_secret(body.password.get_secret_value())

    if user is None:
        user = User(
            email=str(body.email),
            encrypted_password=encrypted,
            imap_host=body.imap_host,
            imap_port=body.imap_port,
            smtp_host=body.smtp_host,
            smtp_port=body.smtp_port,
            role=UserRole.user,
        )
        db.add(user)
        db.flush()  # ensures user.id is available
    else:
        user.encrypted_password = encrypted
        user.imap_host = body.imap_host
        user.imap_port = body.imap_port
        user.smtp_host = body.smtp_host
        user.smtp_port = body.smtp_port
        db.flush()

    # Commit the transaction to ensure fresh user data
    db.commit()

    # Issue JWT access token (send via Authorization: Bearer <token>)
    access_token = create_access_token(subject=user.id, role=user.role.value if hasattr(user.role, 'value') else str(user.role))

    return ConnectionResponse(access_token=access_token, role=user.role)