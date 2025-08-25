from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from app.services.email_service import UserLike
from app.core.auth import header_query_user
from app.services.idle_service import start_idle

router = APIRouter()

@router.websocket('/ws/idle')
async def websocket_idle_endpoint(
    websocket: WebSocket,
    user: UserLike = Depends(header_query_user)
):
    await websocket.accept()
    # The `user` dependency is now resolved by FastAPI. If it fails,
    # it will raise an HTTPException which we don't need to handle here,
    # as FastAPI's WebSocket support doesn't handle HTTPExceptions gracefully.
    # The connection will simply fail, which is acceptable for an auth failure.
    try:
        
        # Start the IDLE loop
        await start_idle(user, websocket)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user: {user.email if user else 'Unknown'}")
    except Exception as e:
        print(f"Error in WebSocket for user {user.email if user else 'Unknown'}: {e}")
        await websocket.close(code=1011, reason="Internal server error")
