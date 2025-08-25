import asyncio
import imaplib
from fastapi import WebSocket
from app.services.email_service import UserLike
from app.services.email_service import _make_imap

async def start_idle(user: UserLike, websocket: WebSocket):
    """
    Starts an IMAP IDLE session to listen for new emails and notifies via WebSocket.
    """
    imap = None
    try:
        # Use a longer timeout for IDLE connection, e.g., 29 minutes
        imap = _make_imap(user, timeout_seconds=29 * 60)
        
        status, _ = imap.select('INBOX', readonly=True)
        if status != 'OK':
            await websocket.send_json({"error": "Failed to select INBOX"})
            return

        print(f"User {user.email} started IMAP IDLE session.")

        while True:
            # Check for client disconnect before blocking
            if websocket.client_state.name != 'CONNECTED':
                print(f"WebSocket disconnected for {user.email}. Ending IDLE.")
                break

            imap.send(b'IDLE\r\n')
            
            # Wait for the server's continuation response
            if 'idling' in imap.readline().decode():
                # Wait for updates from the server, with a timeout
                # Most servers will timeout IDLE after ~30 mins. We'll refresh it sooner.
                responses = imap.idle_check(timeout=15 * 60)

                imap.send(b'DONE\r\n')
                imap.readline()

                for response in responses:
                    if b'EXISTS' in response:
                        print(f"New mail detected for {user.email}. Notifying client.")
                        await websocket.send_json({"event": "new_mail"})

            # Small sleep to prevent tight looping if something goes wrong
            await asyncio.sleep(5)

    except (ConnectionAbortedError, asyncio.CancelledError):
        print(f"WebSocket connection closed for {user.email}.")
    except Exception as e:
        print(f"IMAP IDLE error for {user.email}: {e}")
        try:
            await websocket.send_json({"error": f"An IDLE error occurred: {e}"})
        except Exception as ws_e:
            print(f"Could not send error to disconnected websocket: {ws_e}")
    finally:
        if imap:
            try:
                imap.close()
            except Exception:
                pass
            try:
                imap.logout()
            except Exception:
                pass
        print(f"IMAP IDLE session ended for {user.email}.")