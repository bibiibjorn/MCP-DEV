"""
Slicer Operations Handler
Tool 13: Configure Power BI slicer settings in PBIP files

Operations:
- list: Find and list slicers matching criteria with their current configuration
- configure_single_select: Change slicer to single-select with "All" selected
"""
from typing import Dict, Any, List, Optional
import logging
import json
import os
import re
from pathlib import Path
from server.registry import ToolDefinition
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


def _normalize_path(path: str) -> str:
    """Normalize path to handle Unix-style paths on Windows"""
    normalized_path = path

    # Convert WSL/Unix paths to Windows paths on Windows systems
    if re.match(r'^/mnt/([a-z])/', path, re.IGNORECASE):
        drive_letter = re.match(r'^/mnt/([a-z])/', path, re.IGNORECASE).group(1)
        rest_of_path = path[7:].replace('/', '\\')
        normalized_path = f"{drive_letter.upper()}:\\{rest_of_path}"
    elif path.startswith('/'):
        normalized_path = path.replace('/', '\\')

    return normalized_path


def _find_definition_folder(pbip_path: str) -> Optional[Path]:
    """Find the definition folder for a PBIP project"""
    path = Path(_normalize_path(pbip_path))

    if not path.exists():
        return None

    # If it's a .pbip file, look for .Report folder
    if path.is_file() and path.suffix == '.pbip':
        # Look for {name}.Report folder
        report_folder = path.parent / f"{path.stem}.Report"
        if report_folder.exists():
            definition = report_folder / "definition"
            if definition.exists():
                return definition

    # If it's a .Report folder
    if path.is_dir() and path.name.endswith('.Report'):
        definition = path / "definition"
        if definition.exists():
            return definition

    # If it's already a definition folder
    if path.is_dir() and path.name == "definition":
        return path

    # If it's a directory, search for .Report folders
    if path.is_dir():
        for item in path.iterdir():
            if item.is_dir() and item.name.endswith('.Report'):
                definition = item / "definition"
                if definition.exists():
                    return definition
        # Also check if definition exists directly
        definition = path / "definition"
        if definition.exists():
            return definition

    return None


def _load_json_file(file_path: Path) -> Optional[Dict]:
    """Load JSON file safely"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load JSON from {file_path}: {e}")
        return None


def _save_json_file(file_path: Path, data: Dict) -> bool:
    """Save JSON file with proper formatting"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save JSON to {file_path}: {e}")
        return False


def _extract_slicer_info(visual_data: Dict, file_path: Path) -> Optional[Dict]:
    """Extract slicer information from visual.json"""
    visual = visual_data.get('visual', {})

    # Check if it's a slicer
    visual_type = visual.get('visualType', '')
    if visual_type != 'slicer':
        return None

    # Extract field information
    query_state = visual.get('query', {}).get('queryState', {})
    values_projections = query_state.get('Values', {}).get('projections', [])

    if not values_projections:
        return None

    field_info = values_projections[0].get('field', {})
    column_info = field_info.get('Column', {})

    if not column_info:
        return None

    entity = column_info.get('Expression', {}).get('SourceRef', {}).get('Entity', '')
    property_name = column_info.get('Property', '')

    # Get display name from various sources
    display_name = None

    # Try visualContainerObjects.title first
    vc_objects = visual.get('visualContainerObjects', {})
    title_config = vc_objects.get('title', [])
    if title_config and len(title_config) > 0:
        title_props = title_config[0].get('properties', {})
        title_text = title_props.get('text', {})
        if 'expr' in title_text:
            literal = title_text['expr'].get('Literal', {})
            display_name = literal.get('Value', '').strip("'")

    # Try projection displayName
    if not display_name:
        display_name = values_projections[0].get('displayName', '')

    # Try nativeQueryRef
    if not display_name:
        display_name = values_projections[0].get('nativeQueryRef', '')

    # Fallback to property name
    if not display_name:
        display_name = property_name

    # Get current selection mode
    objects = visual.get('objects', {})
    selection = objects.get('selection', [{}])
    selection_props = selection[0].get('properties', {}) if selection else {}

    data_config = objects.get('data', [{}])
    data_props = data_config[0].get('properties', {}) if data_config else {}

    # Check single select settings
    single_select = False
    strict_single_select = False
    select_all_checkbox = False
    is_inverted_selection = False

    if 'singleSelect' in selection_props:
        single_select = selection_props['singleSelect'].get('expr', {}).get('Literal', {}).get('Value', 'false') == 'true'

    if 'strictSingleSelect' in selection_props:
        strict_single_select = selection_props['strictSingleSelect'].get('expr', {}).get('Literal', {}).get('Value', 'false') == 'true'

    if 'selectAllCheckboxEnabled' in selection_props:
        select_all_checkbox = selection_props['selectAllCheckboxEnabled'].get('expr', {}).get('Literal', {}).get('Value', 'false') == 'true'

    if 'isInvertedSelectionMode' in data_props:
        is_inverted_selection = data_props['isInvertedSelectionMode'].get('expr', {}).get('Literal', {}).get('Value', 'false') == 'true'

    # Get current filter/selections
    general_config = objects.get('general', [{}])
    general_props = general_config[0].get('properties', {}) if general_config else {}

    current_filter = general_props.get('filter', {}).get('filter', {})
    selected_values = []

    if current_filter:
        where_clause = current_filter.get('Where', [])
        for condition in where_clause:
            in_clause = condition.get('Condition', {}).get('In', {})
            values = in_clause.get('Values', [])
            for value_list in values:
                for value_item in value_list:
                    literal = value_item.get('Literal', {})
                    val = literal.get('Value', '')
                    # Clean up the value
                    if val.startswith("'") and val.endswith("'"):
                        val = val[1:-1]
                    selected_values.append(val)

    # Determine selection mode string
    if is_inverted_selection and (single_select or strict_single_select):
        selection_mode = "single_select_all"  # Single select with "All" selected
    elif single_select or strict_single_select:
        selection_mode = "single_select"
    else:
        selection_mode = "multi_select"

    # Build relative path for readability
    try:
        rel_path = str(file_path.relative_to(file_path.parent.parent.parent.parent.parent))
    except ValueError:
        rel_path = str(file_path)

    return {
        'file_path': str(file_path),
        'relative_path': rel_path,
        'visual_name': visual_data.get('name', ''),
        'display_name': display_name,
        'entity': entity,
        'property': property_name,
        'field_reference': f"{entity}[{property_name}]",
        'selection_mode': selection_mode,
        'single_select': single_select,
        'strict_single_select': strict_single_select,
        'select_all_checkbox': select_all_checkbox,
        'is_inverted_selection': is_inverted_selection,
        'selected_values': selected_values,
        'has_filter': bool(current_filter)
    }


def _get_page_display_name(page_folder: Path) -> str:
    """Get the display name for a page from its page.json file"""
    page_json_path = page_folder / "page.json"
    if page_json_path.exists():
        page_data = _load_json_file(page_json_path)
        if page_data:
            return page_data.get('displayName', page_folder.name)
    return page_folder.name


def _find_slicers(definition_path: Path, display_name: Optional[str], entity: Optional[str], property_name: Optional[str]) -> List[Dict]:
    """Find all slicers matching the criteria"""
    matching_slicers = []

    # Search in pages folder
    pages_path = definition_path / "pages"
    if not pages_path.exists():
        return matching_slicers

    # Build page name cache for efficiency
    page_name_cache: Dict[str, str] = {}

    # Iterate through all pages
    for page_folder in pages_path.iterdir():
        if not page_folder.is_dir():
            continue

        # Get page display name (cached)
        page_id = page_folder.name
        if page_id not in page_name_cache:
            page_name_cache[page_id] = _get_page_display_name(page_folder)
        page_display_name = page_name_cache[page_id]

        visuals_path = page_folder / "visuals"
        if not visuals_path.exists():
            continue

        # Iterate through all visuals
        for visual_folder in visuals_path.iterdir():
            if not visual_folder.is_dir():
                continue

            visual_json_path = visual_folder / "visual.json"
            if not visual_json_path.exists():
                continue

            visual_data = _load_json_file(visual_json_path)
            if not visual_data:
                continue

            slicer_info = _extract_slicer_info(visual_data, visual_json_path)
            if not slicer_info:
                continue

            # Add page information
            slicer_info['page_id'] = page_id
            slicer_info['page_name'] = page_display_name

            # Apply filters
            matches = True

            if display_name:
                # Case-insensitive partial match on display name
                if display_name.lower() not in slicer_info['display_name'].lower():
                    matches = False

            if entity:
                # Case-insensitive match on entity
                if entity.lower() != slicer_info['entity'].lower():
                    matches = False

            if property_name:
                # Case-insensitive match on property
                if property_name.lower() != slicer_info['property'].lower():
                    matches = False

            if matches:
                matching_slicers.append(slicer_info)

    return matching_slicers


def _configure_single_select_all(visual_data: Dict) -> Dict:
    """
    Configure a slicer for single-select with "All" selected.

    Changes made:
    1. Set selection.singleSelect = true
    2. Set selection.strictSingleSelect = true
    3. Set selection.selectAllCheckboxEnabled = true
    4. Set data.isInvertedSelectionMode = true
    5. Remove any filter from general properties
    """
    visual = visual_data.get('visual', {})
    objects = visual.setdefault('objects', {})

    # Configure selection properties
    selection = objects.setdefault('selection', [{'properties': {}}])
    if not selection:
        selection = [{'properties': {}}]
        objects['selection'] = selection

    selection_props = selection[0].setdefault('properties', {})

    # Set single select options
    selection_props['strictSingleSelect'] = {
        'expr': {
            'Literal': {
                'Value': 'true'
            }
        }
    }
    selection_props['selectAllCheckboxEnabled'] = {
        'expr': {
            'Literal': {
                'Value': 'true'
            }
        }
    }
    selection_props['singleSelect'] = {
        'expr': {
            'Literal': {
                'Value': 'true'
            }
        }
    }

    # Configure data properties for inverted selection mode
    data = objects.setdefault('data', [{'properties': {}}])
    if not data:
        data = [{'properties': {}}]
        objects['data'] = data

    data_props = data[0].setdefault('properties', {})

    # Set inverted selection mode (means "All" is selected)
    data_props['isInvertedSelectionMode'] = {
        'expr': {
            'Literal': {
                'Value': 'true'
            }
        }
    }

    # Remove any existing filter from general properties
    general = objects.get('general', [])
    if general and len(general) > 0:
        general_props = general[0].get('properties', {})
        if 'filter' in general_props:
            del general_props['filter']

    return visual_data


def handle_slicer_operations(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle slicer configuration operations"""
    operation = args.get('operation', 'list')
    pbip_path = args.get('pbip_path')

    if not pbip_path:
        return {
            'success': False,
            'error': 'pbip_path parameter is required - path to PBIP project, .Report folder, or definition folder'
        }

    # Find definition folder
    definition_path = _find_definition_folder(pbip_path)
    if not definition_path:
        return {
            'success': False,
            'error': f'Could not find definition folder in: {pbip_path}. Ensure path points to a valid PBIP project.'
        }

    # Get filter parameters
    display_name = args.get('display_name')
    entity = args.get('entity')
    property_name = args.get('property')

    if operation == 'list':
        # Find and list slicers with their current configuration
        slicers = _find_slicers(definition_path, display_name, entity, property_name)

        if not slicers:
            return {
                'success': True,
                'message': 'No slicers found matching the criteria',
                'slicers': [],
                'count': 0
            }

        return {
            'success': True,
            'message': f'Found {len(slicers)} slicer(s) matching criteria',
            'slicers': slicers,
            'count': len(slicers)
        }

    elif operation == 'configure_single_select':
        # Find matching slicers
        slicers = _find_slicers(definition_path, display_name, entity, property_name)

        if not slicers:
            return {
                'success': False,
                'error': 'No slicers found matching the criteria. Use operation "list" to see available slicers.'
            }

        # Check for dry_run mode
        dry_run = args.get('dry_run', False)

        changes = []
        errors = []

        for slicer in slicers:
            file_path = Path(slicer['file_path'])

            # Capture before state
            before_state = {
                'selection_mode': slicer['selection_mode'],
                'single_select': slicer['single_select'],
                'strict_single_select': slicer['strict_single_select'],
                'select_all_checkbox': slicer['select_all_checkbox'],
                'is_inverted_selection': slicer['is_inverted_selection'],
                'selected_values': slicer['selected_values'],
                'has_filter': slicer['has_filter']
            }

            if dry_run:
                # Just report what would change
                changes.append({
                    'file_path': str(file_path),
                    'relative_path': slicer['relative_path'],
                    'page_name': slicer.get('page_name', ''),
                    'page_id': slicer.get('page_id', ''),
                    'display_name': slicer['display_name'],
                    'field_reference': slicer['field_reference'],
                    'before': before_state,
                    'after': {
                        'selection_mode': 'single_select_all',
                        'single_select': True,
                        'strict_single_select': True,
                        'select_all_checkbox': True,
                        'is_inverted_selection': True,
                        'selected_values': [],
                        'has_filter': False
                    },
                    'status': 'would_change' if before_state['selection_mode'] != 'single_select_all' else 'already_configured'
                })
            else:
                # Load, modify, and save
                visual_data = _load_json_file(file_path)
                if not visual_data:
                    errors.append({
                        'file_path': str(file_path),
                        'error': 'Failed to load visual.json'
                    })
                    continue

                # Apply configuration
                modified_data = _configure_single_select_all(visual_data)

                # Save changes
                if _save_json_file(file_path, modified_data):
                    changes.append({
                        'file_path': str(file_path),
                        'relative_path': slicer['relative_path'],
                        'page_name': slicer.get('page_name', ''),
                        'page_id': slicer.get('page_id', ''),
                        'display_name': slicer['display_name'],
                        'field_reference': slicer['field_reference'],
                        'before': before_state,
                        'after': {
                            'selection_mode': 'single_select_all',
                            'single_select': True,
                            'strict_single_select': True,
                            'select_all_checkbox': True,
                            'is_inverted_selection': True,
                            'selected_values': [],
                            'has_filter': False
                        },
                        'status': 'changed'
                    })
                else:
                    errors.append({
                        'file_path': str(file_path),
                        'error': 'Failed to save changes'
                    })

        result = {
            'success': len(errors) == 0,
            'operation': 'configure_single_select',
            'dry_run': dry_run,
            'message': f'{"Would modify" if dry_run else "Modified"} {len(changes)} slicer(s)',
            'changes': changes,
            'changes_count': len(changes)
        }

        if errors:
            result['errors'] = errors
            result['errors_count'] = len(errors)
            result['message'] += f' with {len(errors)} error(s)'

        return result

    else:
        return {
            'success': False,
            'error': f'Unknown operation: {operation}. Valid operations: list, configure_single_select'
        }


def register_slicer_operations_handler(registry):
    """Register slicer operations handler"""
    from server.tool_schemas import TOOL_SCHEMAS

    tool = ToolDefinition(
        name="slicer_operations",
        description="[PBIP] Configure Power BI slicer settings - list slicers with current values, change to single-select with All selected",
        handler=handle_slicer_operations,
        input_schema=TOOL_SCHEMAS.get('slicer_operations', {}),
        category="pbip",
        sort_order=120
    )
    registry.register(tool)

    logger.info("Registered slicer_operations handler")
