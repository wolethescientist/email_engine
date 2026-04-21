import asyncio
import logging
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from contextlib import asynccontextmanager
import aioimaplib
import aiosmtplib
import ssl
from opentelemetry import trace

from .config import get_settings
from .security import decrypt_secret

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# Timeout for cleanup operations (seconds).
CLEANUP_TIMEOUT = 5


@dataclass
class ConnectionKey:
    """Unique identifier for email connections"""
    email: str
    imap_host: str
    imap_port: int
    smtp_host: str
    smtp_port: int
    
    def __hash__(self):
        return hash((self.email, self.imap_host, self.imap_port, self.smtp_host, self.smtp_port))

@dataclass
class PooledConnection:
    """Wrapper for pooled connections with metadata"""
    imap_client: Optional[aioimaplib.IMAP4_SSL]
    smtp_client: Optional[aiosmtplib.SMTP]
    last_used: float
    in_use: bool = False
    connection_count: int = 0


class ConnectionPool:
    """Connection manager for IMAP/SMTP connections.
    
    IMAP connections are NOT reused between requests due to aioimaplib
    protocol state corruption bugs when commands are issued rapidly on
    a reused connection. Each get_imap_connection() creates a fresh
    connection, and release_connection() destroys it.
    
    SMTP connections ARE pooled since they don't have the same issue.
    """
    
    def __init__(self, max_connections: int = 50, max_idle_time: int = 180):
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        self.pools: Dict[ConnectionKey, PooledConnection] = {}
        self.lock = asyncio.Lock()
        self.settings = get_settings()
        self._active_imap_count = 0
        
    async def get_imap_connection(self, user) -> aioimaplib.IMAP4_SSL:
        """Create a fresh IMAP connection for each request.
        
        We intentionally do NOT reuse IMAP connections because aioimaplib
        has protocol state corruption bugs: the final tagged OK response
        from a FETCH can arrive asynchronously after the connection is
        reused for a new SELECT, causing 'unexpected tagged response' aborts.
        
        The ~200ms login overhead per request is negligible compared to
        random 500 errors from protocol corruption.
        """
        with tracer.start_as_current_span("get_imap_connection") as span:
            span.set_attribute("user.email", user.email)
            span.set_attribute("imap.host", user.imap_host)
            span.set_attribute("connection.reused", False)
            
            imap_client = await self._create_imap_connection(user)
            self._active_imap_count += 1
            span.set_attribute("active.connections", self._active_imap_count)
            
            logger.info(f"Created IMAP connection for {user.email} (active: {self._active_imap_count})")
            return imap_client
    
    async def get_smtp_connection(self, user) -> aiosmtplib.SMTP:
        """Get or create SMTP connection from pool.
        
        SMTP connections are safe to reuse — they don't have the same
        protocol state issues as aioimaplib.
        """
        with tracer.start_as_current_span("get_smtp_connection") as span:
            span.set_attribute("user.email", user.email)
            span.set_attribute("smtp.host", user.smtp_host)
            
            key = ConnectionKey(
                email=user.email,
                imap_host=user.imap_host,
                imap_port=user.imap_port,
                smtp_host=user.smtp_host,
                smtp_port=user.smtp_port
            )
            
            # Try to reuse existing SMTP connection
            candidate = None
            async with self.lock:
                if key in self.pools:
                    conn = self.pools[key]
                    if conn.smtp_client and not conn.in_use:
                        conn.in_use = True
                        candidate = conn
            
            if candidate is not None:
                try:
                    await asyncio.wait_for(
                        candidate.smtp_client.noop(),
                        timeout=CLEANUP_TIMEOUT
                    )
                    candidate.last_used = asyncio.get_event_loop().time()
                    span.set_attribute("connection.reused", True)
                    logger.debug(f"Reusing healthy SMTP connection for {user.email}")
                    return candidate.smtp_client
                except Exception as e:
                    logger.warning(f"Stale SMTP connection for {user.email}: {e}")
                    async with self.lock:
                        await self._cleanup_smtp(key)
            
            # Create new SMTP connection
            span.set_attribute("connection.reused", False)
            smtp_client = await self._create_smtp_connection(user)
            
            async with self.lock:
                if key not in self.pools:
                    self.pools[key] = PooledConnection(
                        imap_client=None,
                        smtp_client=smtp_client,
                        last_used=asyncio.get_event_loop().time(),
                        in_use=True
                    )
                else:
                    self.pools[key].smtp_client = smtp_client
                    self.pools[key].in_use = True
                    self.pools[key].last_used = asyncio.get_event_loop().time()
                
                self.pools[key].connection_count += 1
            
            logger.info(f"Created new SMTP connection for {user.email}")
            return smtp_client
    
    async def release_imap_connection(self, imap_client: aioimaplib.IMAP4_SSL, user):
        """Destroy an IMAP connection after use (no reuse).
        
        We logout and close immediately. This prevents any protocol
        state corruption on reuse.
        """
        with tracer.start_as_current_span("release_imap_connection"):
            try:
                await asyncio.wait_for(
                    imap_client.logout(),
                    timeout=CLEANUP_TIMEOUT
                )
            except Exception as e:
                logger.debug(f"IMAP logout on release: {e}")
            
            self._active_imap_count = max(0, self._active_imap_count - 1)
            logger.debug(f"Destroyed IMAP connection for {user.email} (active: {self._active_imap_count})")
    
    async def release_connection(self, user, connection_type: str = "imap"):
        """Release connection — for backward compatibility.
        
        IMAP connections are destroyed (not returned to pool).
        SMTP connections are returned to the pool.
        """
        key = ConnectionKey(
            email=user.email,
            imap_host=user.imap_host,
            imap_port=user.imap_port,
            smtp_host=user.smtp_host,
            smtp_port=user.smtp_port
        )
        
        if connection_type == "smtp":
            async with self.lock:
                if key in self.pools:
                    conn = self.pools[key]
                    conn.in_use = False
                    conn.last_used = asyncio.get_event_loop().time()
                    logger.debug(f"Released SMTP connection for {user.email}")
    
    async def _create_imap_connection(self, user) -> aioimaplib.IMAP4_SSL:
        """Create new IMAP connection"""
        with tracer.start_as_current_span("create_imap_connection"):
            # Handle both encrypted (database mode) and plain text (stateless mode) passwords
            if hasattr(user, 'encrypted_password') and user.encrypted_password:
                try:
                    password = decrypt_secret(user.encrypted_password)
                except Exception:
                    # Fallback: treat as plain text
                    password = user.encrypted_password
            else:
                # Direct password (stateless mode)
                password = getattr(user, 'password', '')
            
            # Create SSL context
            ssl_context = ssl.create_default_context()
            
            # Create connection
            imap_client = aioimaplib.IMAP4_SSL(
                host=user.imap_host,
                port=user.imap_port,
                ssl_context=ssl_context,
                timeout=self.settings.IMAP_TIMEOUT_SECONDS
            )
            
            await imap_client.wait_hello_from_server()
            await imap_client.login(user.email, password)
            
            return imap_client
    
    async def _create_smtp_connection(self, user) -> aiosmtplib.SMTP:
        """Create new SMTP connection"""
        with tracer.start_as_current_span("create_smtp_connection"):
            # Handle both encrypted (database mode) and plain text (stateless mode) passwords
            if hasattr(user, 'encrypted_password') and user.encrypted_password:
                try:
                    password = decrypt_secret(user.encrypted_password)
                except Exception:
                    # Fallback: treat as plain text
                    password = user.encrypted_password
            else:
                # Direct password (stateless mode)
                password = getattr(user, 'password', '')
            
            # Create connection
            smtp_client = aiosmtplib.SMTP(
                hostname=user.smtp_host,
                port=user.smtp_port,
                use_tls=self.settings.SMTP_USE_SSL,
                timeout=self.settings.SMTP_TIMEOUT_SECONDS
            )
            
            await smtp_client.connect()
            await smtp_client.login(user.email, password)
            
            return smtp_client
    
    async def _cleanup_smtp(self, key: ConnectionKey):
        """Clean up SMTP connection only"""
        if key in self.pools:
            conn = self.pools[key]
            try:
                if conn.smtp_client:
                    await asyncio.wait_for(
                        conn.smtp_client.quit(),
                        timeout=CLEANUP_TIMEOUT
                    )
            except Exception:
                pass
            conn.smtp_client = None
    
    async def cleanup_idle_connections(self):
        """Clean up idle SMTP connections that exceed max_idle_time.
        (IMAP connections are not pooled, so nothing to clean up there.)
        """
        with tracer.start_as_current_span("cleanup_idle_connections"):
            current_time = asyncio.get_event_loop().time()
            keys_to_remove = []
            
            async with self.lock:
                for key, conn in self.pools.items():
                    if (not conn.in_use and 
                        current_time - conn.last_used > self.max_idle_time):
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    await self._cleanup_smtp(key)
                    del self.pools[key]
                    logger.info(f"Cleaned up idle SMTP connection for {key.email}")
    
    # Alias for backward compatibility
    async def keepalive_idle_connections(self):
        await self.cleanup_idle_connections()
    
    async def close_all_connections(self):
        """Close all connections in the pool"""
        with tracer.start_as_current_span("close_all_connections"):
            async with self.lock:
                keys = list(self.pools.keys())
                for key in keys:
                    conn = self.pools[key]
                    try:
                        if conn.smtp_client:
                            await asyncio.wait_for(
                                conn.smtp_client.quit(),
                                timeout=CLEANUP_TIMEOUT
                            )
                    except Exception:
                        pass
                    del self.pools[key]
                logger.info("Closed all connections in pool")

# Global connection pool instance
_connection_pool: Optional[ConnectionPool] = None

def get_connection_pool() -> ConnectionPool:
    """Get the global connection pool instance"""
    global _connection_pool
    if _connection_pool is None:
        settings = get_settings()
        _connection_pool = ConnectionPool(
            max_connections=getattr(settings, 'MAX_CONNECTIONS', 50),
            max_idle_time=getattr(settings, 'MAX_IDLE_TIME', 180)
        )
    return _connection_pool

@asynccontextmanager
async def get_imap_client(user):
    """Context manager for IMAP connections.
    
    Creates a fresh connection each time and destroys it when done.
    This prevents aioimaplib protocol state corruption entirely.
    """
    pool = get_connection_pool()
    client = await pool.get_imap_connection(user)
    try:
        yield client
    finally:
        await pool.release_imap_connection(client, user)

@asynccontextmanager
async def get_smtp_client(user):
    """Context manager for SMTP connections (pooled)"""
    pool = get_connection_pool()
    client = await pool.get_smtp_connection(user)
    try:
        yield client
    finally:
        await pool.release_connection(user, "smtp")
