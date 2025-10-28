"""
TMDL Handler
Handles TMDL automation operations
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

def handle_validate_tmdl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Validate TMDL syntax with linting"""
    tmdl_path = args.get('tmdl_path')

    if not tmdl_path:
        return {
            'success': False,
            'error': 'tmdl_path parameter is required'
        }

    try:
        from core.tmdl import TmdlValidator
        validator = TmdlValidator()

        result = validator.validate_syntax(tmdl_path)

        return result.to_dict()

    except ImportError as ie:
        logger.error(f"Import error: {ie}", exc_info=True)
        return {
            'success': False,
            'error': 'TmdlValidator not available. This is an internal error.',
            'error_type': 'import_error'
        }
    except FileNotFoundError as fnf:
        return {
            'success': False,
            'error': f'TMDL path not found: {str(fnf)}'
        }
    except Exception as e:
        logger.error(f"Error validating TMDL: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Error validating TMDL: {str(e)}'
        }

def handle_tmdl_find_replace(args: Dict[str, Any]) -> Dict[str, Any]:
    """Find and replace in TMDL with regex support"""
    tmdl_path = args.get('tmdl_path')
    pattern = args.get('pattern')
    replacement = args.get('replacement')
    dry_run = args.get('dry_run', True)
    regex = args.get('regex', False)
    case_sensitive = args.get('case_sensitive', True)
    target = args.get('target', 'all')

    if not tmdl_path:
        return {
            'success': False,
            'error': 'tmdl_path parameter is required'
        }

    if not pattern or replacement is None:
        return {
            'success': False,
            'error': 'pattern and replacement parameters are required'
        }

    try:
        from core.tmdl import TmdlBulkEditor
        editor = TmdlBulkEditor()

        result = editor.replace_in_measures(
            tmdl_path=tmdl_path,
            find=pattern,
            replace=replacement,
            regex=regex,
            case_sensitive=case_sensitive,
            dry_run=dry_run,
            target=target
        )

        return result.to_dict()

    except ImportError as ie:
        logger.error(f"Import error: {ie}", exc_info=True)
        return {
            'success': False,
            'error': 'TmdlBulkEditor not available. This is an internal error.',
            'error_type': 'import_error'
        }
    except FileNotFoundError as fnf:
        return {
            'success': False,
            'error': f'TMDL path not found: {str(fnf)}'
        }
    except Exception as e:
        logger.error(f"Error in TMDL find/replace: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Error in TMDL find/replace: {str(e)}'
        }

def handle_tmdl_bulk_rename(args: Dict[str, Any]) -> Dict[str, Any]:
    """Bulk rename with reference updates"""
    tmdl_path = args.get('tmdl_path')
    renames = args.get('renames', [])
    dry_run = args.get('dry_run', True)
    update_references = args.get('update_references', True)

    if not tmdl_path:
        return {
            'success': False,
            'error': 'tmdl_path parameter is required'
        }

    if not renames:
        return {
            'success': False,
            'error': 'renames parameter required (array of rename operations with "object_type", "old_name" and "new_name")'
        }

    # Validate and normalize rename operations
    normalized_renames = []
    for i, rename in enumerate(renames):
        if not isinstance(rename, dict):
            return {
                'success': False,
                'error': f'Rename operation {i+1} must be a dictionary'
            }

        # Ensure required fields exist
        if 'old_name' not in rename or 'new_name' not in rename:
            return {
                'success': False,
                'error': f'Rename operation {i+1} must have "old_name" and "new_name" fields'
            }

        # Add object_type if missing (default to measure)
        normalized_rename = {
            'object_type': rename.get('object_type', 'measure'),
            'old_name': rename['old_name'],
            'new_name': rename['new_name']
        }

        # Add optional table_name for measures and columns
        if 'table_name' in rename:
            normalized_rename['table_name'] = rename['table_name']

        normalized_renames.append(normalized_rename)

    try:
        from core.tmdl import TmdlBulkEditor
        editor = TmdlBulkEditor()

        result = editor.bulk_rename(
            tmdl_path=tmdl_path,
            renames=normalized_renames,
            update_references=update_references,
            dry_run=dry_run
        )

        return result.to_dict()

    except ImportError as ie:
        logger.error(f"Import error: {ie}", exc_info=True)
        return {
            'success': False,
            'error': 'TmdlBulkEditor not available. This is an internal error.',
            'error_type': 'import_error'
        }
    except FileNotFoundError as fnf:
        return {
            'success': False,
            'error': f'TMDL path not found: {str(fnf)}'
        }
    except Exception as e:
        logger.error(f"Error in TMDL bulk rename: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Error in TMDL bulk rename: {str(e)}'
        }

def handle_tmdl_generate_script(args: Dict[str, Any]) -> Dict[str, Any]:
    """Generate TMDL script from definition"""
    definition = args.get('definition')
    object_type = args.get('object_type', 'table')  # table, measure, relationship, calc_group

    if not definition:
        return {
            'success': False,
            'error': 'definition parameter is required (object definition as dict)'
        }

    try:
        from core.tmdl import TmdlScriptGenerator
        generator = TmdlScriptGenerator()

        # Use the unified method that handles all object types
        script = generator.generate_from_definition(object_type, definition)

        return {
            'success': True,
            'script': script
        }

    except ImportError as ie:
        logger.error(f"Import error: {ie}", exc_info=True)
        return {
            'success': False,
            'error': 'TmdlScriptGenerator not available. This is an internal error.',
            'error_type': 'import_error'
        }
    except Exception as e:
        logger.error(f"Error generating TMDL script: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Error generating TMDL script: {str(e)}'
        }

def register_tmdl_handlers(registry):
    """Register all TMDL handlers"""
    from server.tool_schemas import TOOL_SCHEMAS

    tools = [
        ToolDefinition(
            name="validate_tmdl",
            description="Validate TMDL syntax with linting",
            handler=handle_validate_tmdl,
            input_schema=TOOL_SCHEMAS.get('validate_tmdl', {}),
            category="tmdl",
            sort_order=44
        ),
        ToolDefinition(
            name="tmdl_find_replace",
            description="Find and replace in TMDL with regex support",
            handler=handle_tmdl_find_replace,
            input_schema=TOOL_SCHEMAS.get('tmdl_find_replace', {}),
            category="tmdl",
            sort_order=45
        ),
        ToolDefinition(
            name="tmdl_bulk_rename",
            description="Bulk rename with reference updates",
            handler=handle_tmdl_bulk_rename,
            input_schema=TOOL_SCHEMAS.get('tmdl_bulk_rename', {}),
            category="tmdl",
            sort_order=46
        ),
        ToolDefinition(
            name="tmdl_generate_script",
            description="Generate TMDL script from definition",
            handler=handle_tmdl_generate_script,
            input_schema=TOOL_SCHEMAS.get('tmdl_generate_script', {}),
            category="tmdl",
            sort_order=47
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} TMDL handlers")
