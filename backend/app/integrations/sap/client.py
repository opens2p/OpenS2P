"""
SAP client \u2014 handles low-level communication with SAP.
In production: SAP RFC / BAPI / OData calls.
For development: returns mock data.
"""
from __future__ import annotations
from app.integrations.sap.connector import SAPMockConnector
from app.integrations.base.connector import ConnectionConfig


def create_sap_connector(config: ConnectionConfig) -> SAPMockConnector:
    """Factory function to create a SAP connector instance."""
    return SAPMockConnector(config)
