from typing import Optional
from types import SimpleNamespace
from fastapi import Depends, Header, HTTPException, Query, status

# Build a user-like object from headers or query params.
# This is used when credentials are not provided in the request body.

def header_query_user(
    # Headers (recommended)
    x_imap_host: Optional[str] = Header(None, alias="X-IMAP-Host"),
    x_imap_port: Optional[int] = Header(None, alias="X-IMAP-Port"),
    x_smtp_host: Optional[str] = Header(None, alias="X-SMTP-Host"),
    x_smtp_port: Optional[int] = Header(None, alias="X-SMTP-Port"),
    x_email: Optional[str] = Header(None, alias="X-Email"),
    x_password: Optional[str] = Header(None, alias="X-Password"),
    x_access_token: Optional[str] = Header(None, alias="X-Access-Token"),
    # Query fallbacks
    imap_host_q: Optional[str] = Query(None, alias="imap_host"),
    imap_port_q: Optional[int] = Query(None, alias="imap_port"),
    smtp_host_q: Optional[str] = Query(None, alias="smtp_host"),
    smtp_port_q: Optional[int] = Query(None, alias="smtp_port"),
    username_q: Optional[str] = Query(None, alias="username"),
    password_q: Optional[str] = Query(None, alias="password"),
    access_token_q: Optional[str] = Query(None, alias="access_token"),
):
    imap_host = x_imap_host or imap_host_q
    imap_port = x_imap_port or imap_port_q
    smtp_host = x_smtp_host or smtp_host_q
    smtp_port = x_smtp_port or smtp_port_q
    email = x_email or username_q
    password = x_password or password_q
    access_token = x_access_token or access_token_q

    # If nothing provided, return 400 so callers know to use body credentials
    if not (imap_host and imap_port and smtp_host and smtp_port and email and (password or access_token)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing credentials (headers or query). Provide headers, query, or include credentials in request body.")

    return SimpleNamespace(
        email=email,
        imap_host=imap_host,
        imap_port=int(imap_port),
        smtp_host=smtp_host,
        smtp_port=int(smtp_port),
        password=password,
        access_token=access_token,
    )