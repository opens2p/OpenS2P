"""
Integration-specific exceptions.
"""
from __future__ import annotations


class ConnectorError(Exception):
    """Base exception for connector errors."""
    pass


class AuthenticationError(ConnectorError):
    """Failed to authenticate with external system."""
    pass


class ConnectionError(ConnectorError):
    """Failed to connect to external system."""
    pass


class ExtractionError(ConnectorError):
    """Failed to extract data from external system."""
    pass


class TransformationError(ConnectorError):
    """Failed to transform data format."""
    pass


class LoadError(ConnectorError):
    """Failed to load data into target system."""
    pass


class MappingNotFoundError(ConnectorError):
    """No field mapping found for the given object type."""
    pass
