```python
"""
BPA (Best Practice Analyzer) Tools for Semantic Model MCP Server

This module contains all BPA-related MCP tools for analyzing semantic models
and TMSL definitions against best practice rules.
"""

import os
import json
import logging
import urllib.parse
import sys
import clr
from typing import Optional
from fastmcp import FastMCP
from core.bpa_service import BPAService
from Microsoft.AnalysisServices.Tabular import Server, Database, JsonSerializer, SerializeOptions  # type: ignore
from core.auth import get_access_token

# Configure logging to match pbixray_v4_optimized_bpa.py
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def register_bpa_tools(mcp: FastMCP):
    """Register all BPA-related MCP tools"""
    # Centralize BPAService instantiation
    server_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        bpa_service = BPAService(server_directory)
    except Exception as e:
        logger.error(f"Failed to initialize BPAService: {e}")
        bpa_service = None

    # Load .NET DLLs
    dotnet_dir = os.environ.get('DOTNET_DLL_PATH', os.path.join(server_directory, "dotnet"))
    try:
        clr.AddReference(os.path.join(dotnet_dir, "Microsoft.AnalysisServices.Tabular.dll"))
        clr.AddReference(os.path.join(dotnet_dir, "Microsoft.Identity.Client.dll"))
        clr.AddReference(os.path.join(dotnet_dir, "Microsoft.IdentityModel.Abstractions.dll"))
    except (OSError, ImportError) as e:
        logger.error(f"Failed to load .NET assemblies: {e}")
        bpa_service = None

    @mcp.tool
    def analyze_model_bpa(workspace_name: str, dataset_name: str) -> str:
        """Analyze a semantic model against Best Practice Analyzer (BPA) rules.

        Args:
            workspace_name: The Power BI workspace name
            dataset_name: The dataset/model name to analyze

        Returns:
            JSON string with BPA analysis results including violations and summary
        """
        if not workspace_name or not dataset_name:
            logger.error("Invalid workspace_name or dataset_name")
            return json.dumps({
                'success': False,
                'error': 'Workspace_name and dataset_name must be non-empty strings',
                'error_type': 'invalid_input'
            }, indent=2)

        if not bpa_service:
            logger.error("BPAService not initialized")
            return json.dumps({
                'success': False,
                'error': 'BPA service unavailable',
                'error_type': 'service_unavailable'
            }, indent=2)

        try:
            # Get access token
            access_token = get_access_token()
            if not access_token:
                logger.error("No valid access token")
                return json.dumps({
                    'success': False,
                    'error': 'No valid access token available',
                    'error_type': 'auth_error'
                }, indent=2)

            # Connect to Power BI and get TMSL definition
            workspace_name_encoded = urllib.parse.quote(workspace_name)
            connection_string = f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace_name_encoded};Password={access_token}"
            server = Server()
            try:
                server.Connect(connection_string)
            except Exception as e:
                logger.error(f"Failed to connect to Power BI: {e}")
                return json.dumps({
                    'success': False,
                    'error': f'Connection failed: {str(e)}',
                    'error_type': 'connection_error'
                }, indent=2)

            # Find the database/dataset
            database = None
            for db in server.Databases:
                if db.Name == dataset_name:
                    database = db
                    break

            if not database:
                server.Disconnect()
                logger.error(f"Dataset '{dataset_name}' not found in workspace '{workspace_name}'")
                return json.dumps({
                    'success': False,
                    'error': f"Dataset '{dataset_name}' not found in workspace '{workspace_name}'",
                    'error_type': 'dataset_not_found'
                }, indent=2)

            # Get TMSL definition
            options = SerializeOptions()
            options.IgnoreInferredObjects = True
            options.IgnoreInferredProperties = True
            options.IgnoreTimestamps = True
            options.SplitMultilineStrings = True

            try:
                tmsl_definition = JsonSerializer.SerializeDatabase(database, options)
            except Exception as e:
                server.Disconnect()
                logger.error(f"Failed to serialize TMSL: {e}")
                return json.dumps({
                    'success': False,
                    'error': f'TMSL serialization failed: {str(e)}',
                    'error_type': 'tmsl_serialization_error'
                }, indent=2)

            server.Disconnect()

            # Analyze TMSL
            try:
                result = bpa_service.analyze_model_from_tmsl(tmsl_definition)
                logger.info(f"BPA analysis completed for {workspace_name}/{dataset_name}")
                return json.dumps({
                    'success': True,
                    'workspace_name': workspace_name,
                    'dataset_name': dataset_name,
                    'violations': result.get('violations', []),
                    'summary': result.get('summary', {})
                }, indent=2)
            except Exception as e:
                logger.error(f"BPA analysis failed: {e}")
                return json.dumps({
                    'success': False,
                    'error': f'BPA analysis failed: {str(e)}',
                    'error_type': 'bpa_analysis_error'
                }, indent=2)

        except Exception as e:
            logger.error(f"Unexpected error in analyze_model_bpa: {e}")
            return json.dumps({
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'unexpected_error'
            }, indent=2)

    @mcp.tool
    def analyze_tmsl_bpa(tmsl_definition: str) -> str:
        """Analyze a TMSL definition directly against Best Practice Analyzer (BPA) rules.

        Args:
            tmsl_definition: TMSL JSON string (raw or escaped format)

        Returns:
            JSON string with BPA analysis results including violations and summary
        """
        if not tmsl_definition or not isinstance(tmsl_definition, str):
            logger.error("Invalid TMSL definition")
            return json.dumps({
                'success': False,
                'error': 'TMSL definition must be a non-empty string',
                'error_type': 'invalid_input'
            }, indent=2)

        if not bpa_service:
            logger.error("BPAService not initialized")
            return json.dumps({
                'success': False,
                'error': 'BPA service unavailable',
                'error_type': 'service_unavailable'
            }, indent=2)

        try:
            result = bpa_service.analyze_model_from_tmsl(tmsl_definition)
            logger.info("TMSL BPA analysis completed")
            return json.dumps({
                'success': True,
                'violations': result.get('violations', []),
                'summary': result.get('summary', {})
            }, indent=2)
        except ValueError as e:
            logger.error(f"Invalid TMSL JSON: {e}")
            return json.dumps({
                'success': False,
                'error': f'Invalid TMSL JSON: {str(e)}',
                'error_type': 'tmsl_parse_error'
            }, indent=2)
        except Exception as e:
            logger.error(f"TMSL BPA analysis failed: {e}")
            return json.dumps({
                'success': False,
                'error': f'TMSL BPA analysis failed: {str(e)}',
                'error_type': 'tmsl_bpa_analysis_error'
            }, indent=2)

    @mcp.tool
    def get_bpa_violations_by_severity(severity: str) -> str:
        """Get BPA violations filtered by severity level.

        Args:
            severity: Severity level to filter by (INFO, WARNING, ERROR)

        Returns:
            JSON string with filtered violations
        """
        valid_severities = ['INFO', 'WARNING', 'ERROR']
        if not severity or severity.upper() not in valid_severities:
            logger.error(f"Invalid severity: {severity}")
            return json.dumps({
                'success': False,
                'error': f'Severity must be one of {", ".join(valid_severities)}',
                'error_type': 'invalid_input'
            }, indent=2)

        if not bpa_service:
            logger.error("BPAService not initialized")
            return json.dumps({
                'success': False,
                'error': 'BPA service unavailable; run analyze_model_bpa or analyze_tmsl_bpa first',
                'error_type': 'service_unavailable'
            }, indent=2)

        try:
            violations = bpa_service.get_violations_by_severity(severity.upper())
            logger.info(f"Retrieved {len(violations)} violations for severity {severity}")
            return json.dumps({
                'success': True,
                'severity_filter': severity.upper(),
                'violation_count': len(violations),
                'violations': violations
            }, indent=2)
        except Exception as e:
            logger.error(f"Error filtering BPA violations by severity: {e}")
            return json.dumps({
                'success': False,
                'error': f'Error filtering BPA violations by severity: {str(e)}',
                'error_type': 'bpa_filter_error'
            }, indent=2)

    @mcp.tool
    def get_bpa_violations_by_category(category: str) -> str:
        """Get BPA violations filtered by category.

        Args:
            category: Category to filter by (Performance, DAX Expressions, Maintenance, Naming Conventions, Formatting)

        Returns:
            JSON string with filtered violations
        """
        if not category or not isinstance(category, str):
            logger.error("Invalid category")
            return json.dumps({
                'success': False,
                'error': 'Category must be a non-empty string',
                'error_type': 'invalid_input'
            }, indent=2)

        if not bpa_service:
            logger.error("BPAService not initialized")
            return json.dumps({
                'success': False,
                'error': 'BPA service unavailable; run analyze_model_bpa or analyze_tmsl_bpa first',
                'error_type': 'service_unavailable'
            }, indent=2)

        try:
            violations = bpa_service.get_violations_by_category(category)
            logger.info(f"Retrieved {len(violations)} violations for category {category}")
            return json.dumps({
                'success': True,
                'category_filter': category,
                'violation_count': len(violations),
                'violations': violations
            }, indent=2)
        except Exception as e:
            logger.error(f"Error filtering BPA violations by category: {e}")
            return json.dumps({
                'success': False,
                'error': f'Error filtering BPA violations by category: {str(e)}',
                'error_type': 'bpa_filter_error'
            }, indent=2)

    @mcp.tool
    def get_bpa_rules_summary() -> str:
        """Get summary information about loaded BPA rules.

        Returns:
            JSON string with rules summary including counts by category and severity
        """
        if not bpa_service:
            logger.error("BPAService not initialized")
            return json.dumps({
                'success': False,
                'error': 'BPA service unavailable',
                'error_type': 'service_unavailable'
            }, indent=2)

        try:
            summary = bpa_service.get_rules_summary()
            logger.info("Retrieved BPA rules summary")
            return json.dumps({
                'success': True,
                'rules_summary': summary
            }, indent=2)
        except Exception as e:
            logger.error(f"Error getting BPA rules summary: {e}")
            return json.dumps({
                'success': False,
                'error': f'Error getting BPA rules summary: {str(e)}',
                'error_type': 'bpa_rules_error'
            }, indent=2)

    @mcp.tool
    def get_bpa_categories() -> str:
        """Get list of available BPA rule categories.

        Returns:
            JSON string with list of available categories
        """
        if not bpa_service:
            logger.error("BPAService not initialized")
            return json.dumps({
                'success': False,
                'error': 'BPA service unavailable',
                'error_type': 'service_unavailable'
            }, indent=2)

        try:
            categories = bpa_service.get_available_categories()
            logger.info(f"Retrieved {len(categories)} BPA categories")
            return json.dumps({
                'success': True,
                'available_categories': categories
            }, indent=2)
        except Exception as e:
            logger.error(f"Error getting BPA categories: {e}")
            return json.dumps({
                'success': False,
                'error': f'Error getting BPA categories: {str(e)}',
                'error_type': 'bpa_categories_error'
            }, indent=2)

    @mcp.tool
    def generate_bpa_report(workspace_name: str, dataset_name: str, format_type: str = 'summary') -> str:
        """Generate a comprehensive Best Practice Analyzer report for a semantic model.

        Args:
            workspace_name: The Power BI workspace name
            dataset_name: The dataset/model name to analyze
            format_type: Report format ('summary', 'detailed', 'by_category')

        Returns:
            JSON string with comprehensive BPA report
        """
        valid_formats = ['summary', 'detailed', 'by_category']
        if not workspace_name or not dataset_name:
            logger.error("Invalid workspace_name or dataset_name")
            return json.dumps({
                'success': False,
                'error': 'Workspace_name and dataset_name must be non-empty strings',
                'error_type': 'invalid_input'
            }, indent=2)

        if format_type not in valid_formats:
            logger.error(f"Invalid format_type: {format_type}")
            return json.dumps({
                'success': False,
                'error': f'Format_type must be one of {", ".join(valid_formats)}',
                'error_type': 'invalid_input'
            }, indent=2)

        if not bpa_service:
            logger.error("BPAService not initialized")
            return json.dumps({
                'success': False,
                'error': 'BPA service unavailable',
                'error_type': 'service_unavailable'
            }, indent=2)

        try:
            # Get access token
            access_token = get_access_token()
            if not access_token:
                logger.error("No valid access token")
                return json.dumps({
                    'success': False,
                    'error': 'No valid access token available',
                    'error_type': 'auth_error'
                }, indent=2)

            # Connect to Power BI and get TMSL definition
            workspace_name_encoded = urllib.parse.quote(workspace_name)
            connection_string = f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace_name_encoded};Password={access_token}"
            server = Server()
            try:
                server.Connect(connection_string)
            except Exception as e:
                logger.error(f"Failed to connect to Power BI: {e}")
                return json.dumps({
                    'success': False,
                    'error': f'Connection failed: {str(e)}',
                    'error_type': 'connection_error'
                }, indent=2)

            # Find the database/dataset
            database = None
            for db in server.Databases:
                if db.Name == dataset_name:
                    database = db
                    break

            if not database:
                server.Disconnect()
                logger.error(f"Dataset '{dataset_name}' not found in workspace '{workspace_name}'")
                return json.dumps({
                    'success': False,
                    'error': f"Dataset '{dataset_name}' not found in workspace '{workspace_name}'",
                    'error_type': 'dataset_not_found'
                }, indent=2)

            # Get TMSL definition
            options = SerializeOptions()
            options.IgnoreInferredObjects = True
            options.IgnoreInferredProperties = True
            options.IgnoreTimestamps = True
            options.SplitMultilineStrings = True

            try:
                tmsl_definition = JsonSerializer.SerializeDatabase(database, options)
            except Exception as e:
                server.Disconnect()
                logger.error(f"Failed to serialize TMSL: {e}")
                return json.dumps({
                    'success': False,
                    'error': f'TMSL serialization failed: {str(e)}',
                    'error_type': 'tmsl_serialization_error'
                }, indent=2)

            server.Disconnect()

            # Generate BPA report
            try:
                report = bpa_service.generate_bpa_report(tmsl_definition, format_type)
                logger.info(f"Generated BPA report for {workspace_name}/{dataset_name} in {format_type} format")
                return json.dumps({
                    'success': True,
                    'workspace_name': workspace_name,
                    'dataset_name': dataset_name,
                    'format_type': format_type,
                    'report': report
                }, indent=2)
            except Exception as e:
                logger.error(f"Error generating BPA report: {e}")
                return json.dumps({
                    'success': False,
                    'error': f'Error generating BPA report: {str(e)}',
                    'error_type': 'bpa_report_error'
                }, indent=2)

        except Exception as e:
            logger.error(f"Unexpected error in generate_bpa_report: {e}")
            return json.dumps({
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'unexpected_error'
            }, indent=2)