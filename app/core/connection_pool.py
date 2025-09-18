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
    """Async connection pool for IMAP/SMTP connections"""
    
    def __init__(self, max_connections: int = 50, max_idle_time: int = 300):
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        self.pools: Dict[ConnectionKey, PooledConnection] = {}
        self.lock = asyncio.Lock()
        self.settings = get_settings()
        
    async def get_imap_connection(self, user) -> aioimaplib.IMAP4_SSL:
        """Get or create IMAP connection from pool"""
        with tracer.start_as_current_span("get_imap_connection") as span:
            span.set_attribute("user.email", user.email)
            span.set_attribute("imap.host", user.imap_host)
            
            key = ConnectionKey(
                email=user.email,
                imap_host=user.imap_host,
                imap_port=user.imap_port,
                smtp_host=user.smtp_host,
                smtp_port=user.smtp_port
            )
            
            async with self.lock:
                # Check if we have an existing connection
                if key in self.pools:
                    conn = self.pools[key]
                    if conn.imap_client and not conn.in_use:
                        try:
                            # Test connection health
                            await conn.imap_client.noop()
                            
                            # CRITICAL FIX: Reset IMAP state to prevent state corruption
                            # Close any previously selected mailbox to ensure clean state
                            try:
                                await conn.imap_client.close()
                                logger.debug(f"Reset IMAP state for pooled connection - closed previous mailbox")
                            except Exception as close_e:
                                # CLOSE might fail if no mailbox was selected, which is fine
                                logger.debug(f"CLOSE command result (expected if no mailbox selected): {close_e}")
                            
                            conn.in_use = True
                            conn.last_used = asyncio.get_event_loop().time()
                            span.set_attribute("connection.reused", True)
                            logger.debug(f"Reusing IMAP connection for {user.email} with reset state")
                            return conn.imap_client
                        except Exception as e:
                            logger.warning(f"Stale IMAP connection for {user.email}: {e}")
                            await self._cleanup_connection(key)
                
                # Create new connection
                span.set_attribute("connection.reused", False)
                imap_client = await self._create_imap_connection(user)
                
                # Store in pool
                if key not in self.pools:
                    self.pools[key] = PooledConnection(
                        imap_client=imap_client,
                        smtp_client=None,
                        last_used=asyncio.get_event_loop().time(),
                        in_use=True
                    )
                else:
                    self.pools[key].imap_client = imap_client
                    self.pools[key].in_use = True
                    self.pools[key].last_used = asyncio.get_event_loop().time()
                
                self.pools[key].connection_count += 1
                span.set_attribute("connection.count", self.pools[key].connection_count)
                logger.info(f"Created new IMAP connection for {user.email}")
                return imap_client
    
    async def get_smtp_connection(self, user) -> aiosmtplib.SMTP:
        """Get or create SMTP connection from pool"""
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
            
            async with self.lock:
                # Check if we have an existing connection
                if key in self.pools:
                    conn = self.pools[key]
                    if conn.smtp_client and not conn.in_use:
                        try:
                            # Test connection health
                            await conn.smtp_client.noop()
                            conn.in_use = True
                            conn.last_used = asyncio.get_event_loop().time()
                            span.set_attribute("connection.reused", True)
                            logger.debug(f"Reusing SMTP connection for {user.email}")
                            return conn.smtp_client
                        except Exception as e:
                            logger.warning(f"Stale SMTP connection for {user.email}: {e}")
                            await self._cleanup_connection(key)
                
                # Create new connection
                span.set_attribute("connection.reused", False)
                smtp_client = await self._create_smtp_connection(user)
                
                # Store in pool
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
                span.set_attribute("connection.count", self.pools[key].connection_count)
                logger.info(f"Created new SMTP connection for {user.email}")
                return smtp_client
    
    async def release_connection(self, user, connection_type: str = "imap"):
        """Release connection back to pool with proper state cleanup"""
        with tracer.start_as_current_span("release_connection") as span:
            span.set_attribute("user.email", user.email)
            span.set_attribute("connection.type", connection_type)
            
            key = ConnectionKey(
                email=user.email,
                imap_host=user.imap_host,
                imap_port=user.imap_port,
                smtp_host=user.smtp_host,
                smtp_port=user.smtp_port
            )
            
            async with self.lock:
                if key in self.pools:
                    conn = self.pools[key]
                    
                    # CRITICAL FIX: Reset IMAP state before returning to pool
                    if connection_type == "imap" and conn.imap_client:
                        try:
                            # Close any selected mailbox to reset state
                            await conn.imap_client.close()
                            logger.debug(f"Reset IMAP state when releasing connection for {user.email}")
                        except Exception as e:
                            # CLOSE might fail if no mailbox was selected, which is fine
                            logger.debug(f"CLOSE on release result (expected if no mailbox): {e}")
                    
                    conn.in_use = False
                    conn.last_used = asyncio.get_event_loop().time()
                    logger.debug(f"Released {connection_type} connection for {user.email} with clean state")
    
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
    
    async def _cleanup_connection(self, key: ConnectionKey):
        """Clean up a specific connection"""
        if key in self.pools:
            conn = self.pools[key]
            try:
                if conn.imap_client:
                    await conn.imap_client.logout()
            except Exception:
                pass
            try:
                if conn.smtp_client:
                    await conn.smtp_client.quit()
            except Exception:
                pass
            del self.pools[key]
    
    async def cleanup_idle_connections(self):
        """Clean up idle connections that exceed max_idle_time"""
        with tracer.start_as_current_span("cleanup_idle_connections"):
            current_time = asyncio.get_event_loop().time()
            keys_to_remove = []
            
            async with self.lock:
                for key, conn in self.pools.items():
                    if (not conn.in_use and 
                        current_time - conn.last_used > self.max_idle_time):
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    await self._cleanup_connection(key)
                    logger.info(f"Cleaned up idle connection for {key.email}")
    
    async def close_all_connections(self):
        """Close all connections in the pool"""
        with tracer.start_as_current_span("close_all_connections"):
            async with self.lock:
                keys = list(self.pools.keys())
                for key in keys:
                    await self._cleanup_connection(key)
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
            max_idle_time=getattr(settings, 'MAX_IDLE_TIME', 300)
        )
    return _connection_pool

@asynccontextmanager
async def get_imap_client(user):
    """Context manager for IMAP connections"""
    pool = get_connection_pool()
    client = await pool.get_imap_connection(user)
    try:
        yield client
    finally:
        await pool.release_connection(user, "imap")

@asynccontextmanager
async def get_smtp_client(user):
    """Context manager for SMTP connections"""
    pool = get_connection_pool()
    client = await pool.get_smtp_connection(user)
    try:
        yield client
    finally:
        await pool.release_connection(user, "smtp")
