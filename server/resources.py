"""
MCP Resources Management
Exposes exported model files as MCP resources for direct access by AI/MCP clients
"""
import json
import gzip
import logging
from typing import Dict, List, Optional, Callable
from pathlib import Path
from mcp.types import Resource

logger = logging.getLogger(__name__)


class ResourceManager:
    """Manages MCP resources for exported model files"""

    def __init__(self):
        """Initialize resource manager"""
        self._export_cache: Dict[str, Dict] = {}  # uri -> metadata
        self._latest_export: Optional[str] = None
        self._dynamic_resources: Dict[str, Dict] = {}  # uri -> {provider, metadata}

    def register_export(self, file_path: str, metadata: Dict) -> str:
        """
        Register an exported file as an MCP resource

        Args:
            file_path: Path to the exported file
            metadata: Export metadata (format, size, statistics, etc.)

        Returns:
            Resource URI
        """
        try:
            # Create URI for this resource
            file_name = Path(file_path).name
            uri = f"powerbi://export/{file_name}"

            # Store in cache
            self._export_cache[uri] = {
                'file_path': file_path,
                'metadata': metadata,
                'uri': uri
            }

            # Track latest export
            self._latest_export = uri

            logger.info(f"Registered MCP resource: {uri}")
            return uri

        except Exception as e:
            logger.error(f"Error registering export: {e}")
            raise

    def get_latest_export_uri(self) -> Optional[str]:
        """Get URI of the most recent export"""
        return self._latest_export

    def register_dynamic_resource(self, uri: str, name: str, description: str,
                                  provider: Callable[[], str], mime_type: str = "text/markdown"):
        """
        Register a dynamic resource that generates content on-demand

        Args:
            uri: Resource URI
            name: Resource name
            description: Resource description
            provider: Callable that returns the resource content
            mime_type: MIME type of the content
        """
        self._dynamic_resources[uri] = {
            'name': name,
            'description': description,
            'provider': provider,
            'mime_type': mime_type
        }
        logger.info(f"Registered dynamic MCP resource: {uri}")

    def list_resources(self) -> List[Resource]:
        """List all available resources"""
        resources = []

        # Add dynamic resources first (like token usage)
        for uri, data in self._dynamic_resources.items():
            resources.append(Resource(
                uri=uri,
                name=data['name'],
                description=data['description'],
                mimeType=data['mime_type']
            ))

        # Add latest export as a special resource
        if self._latest_export:
            resources.append(Resource(
                uri="powerbi://export/latest",
                name="Latest Model Export",
                description="Most recently exported Power BI model data (JSON format)",
                mimeType="application/json"
            ))

        # Add all cached exports
        for uri, data in self._export_cache.items():
            metadata = data['metadata']
            resources.append(Resource(
                uri=uri,
                name=Path(data['file_path']).name,
                description=f"Power BI model export ({metadata.get('format', 'json')}, {metadata.get('file_size_mb', 0)} MB)",
                mimeType=self._get_mime_type(data['file_path'])
            ))

        return resources

    def read_resource(self, uri: str) -> str:
        """
        Read resource content by URI

        Args:
            uri: Resource URI

        Returns:
            Resource content as string
        """
        try:
            # Check if it's a dynamic resource
            if uri in self._dynamic_resources:
                logger.info(f"Reading dynamic resource: {uri}")
                provider = self._dynamic_resources[uri]['provider']
                return provider()

            # Handle latest export alias
            if uri == "powerbi://export/latest":
                if not self._latest_export:
                    raise ValueError("No exports available")
                uri = self._latest_export

            # Get resource data
            if uri not in self._export_cache:
                raise ValueError(f"Resource not found: {uri}")

            resource_data = self._export_cache[uri]
            file_path = resource_data['file_path']

            # Log the file path being accessed
            logger.info(f"Reading resource from: {file_path}")

            # Verify file exists
            if not Path(file_path).exists():
                logger.error(f"File not found: {file_path}")
                raise FileNotFoundError(f"Export file not found: {file_path}")

            # Read file content based on format
            if file_path.endswith('.json.gz'):
                logger.info(f"Reading compressed JSON from {file_path}")
                with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                    content = f.read()
                    logger.info(f"Read {len(content)} characters from compressed JSON")
                    return content
            elif file_path.endswith('.json'):
                logger.info(f"Reading uncompressed JSON from {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logger.info(f"Read {len(content)} characters from JSON")
                    return content
            elif file_path.endswith('.md'):
                logger.info(f"Reading markdown from {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                raise ValueError(f"Unsupported file format: {file_path}")

        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}", exc_info=True)
            raise

    def get_resource_info(self, uri: str) -> Optional[Dict]:
        """Get metadata about a resource"""
        if uri == "powerbi://export/latest" and self._latest_export:
            uri = self._latest_export
        return self._export_cache.get(uri)

    def clear_cache(self):
        """Clear all cached resources"""
        self._export_cache.clear()
        self._latest_export = None
        logger.info("Resource cache cleared")

    def _get_mime_type(self, file_path: str) -> str:
        """Determine MIME type from file extension"""
        if file_path.endswith('.json') or file_path.endswith('.json.gz'):
            return "application/json"
        elif file_path.endswith('.md'):
            return "text/markdown"
        else:
            return "application/octet-stream"


# Global resource manager instance
_resource_manager = ResourceManager()


def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance"""
    return _resource_manager
