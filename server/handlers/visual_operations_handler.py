"""
Visual Operations Handler
Tool: Configure Power BI visual properties in PBIP files

Operations:
- list: Find and list visuals matching criteria with their current configuration
- update_position: Update position and/or size of matching visuals
- replace_measure: Replace a measure in visuals while keeping the display name
"""
from typing import Dict, Any, List, Optional
import logging
import json
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


def _get_parent_group_offset(visual_data: Dict, visuals_path: Path) -> Dict[str, float]:
    """
    Calculate the cumulative offset from all parent groups.

    Power BI stores visual positions relative to their parent group.
    This function walks up the parent chain and sums all offsets to get
    the total offset that needs to be added to get absolute position,
    or subtracted to convert absolute to relative.

    Returns: {'x': total_x_offset, 'y': total_y_offset}
    """
    total_x = 0.0
    total_y = 0.0

    parent_name = visual_data.get('parentGroupName')
    visited = set()  # Prevent infinite loops

    while parent_name and parent_name not in visited:
        visited.add(parent_name)

        # Find the parent group's visual.json
        parent_path = visuals_path / parent_name / "visual.json"
        if not parent_path.exists():
            break

        parent_data = _load_json_file(parent_path)
        if not parent_data:
            break

        # Add parent's position to total offset
        parent_position = parent_data.get('position', {})
        total_x += parent_position.get('x', 0)
        total_y += parent_position.get('y', 0)

        # Move to next parent
        parent_name = parent_data.get('parentGroupName')

    return {'x': total_x, 'y': total_y}


def _get_visual_title(visual_data: Dict) -> Optional[str]:
    """Extract the display title from visual.json"""
    visual = visual_data.get('visual', {})
    vc_objects = visual.get('visualContainerObjects', {})

    # Try to get title from visualContainerObjects
    title_config = vc_objects.get('title', [])
    if title_config and len(title_config) > 0:
        title_props = title_config[0].get('properties', {})
        title_text = title_props.get('text', {})
        if 'expr' in title_text:
            literal = title_text['expr'].get('Literal', {})
            value = literal.get('Value', '')
            # Remove surrounding quotes
            if value.startswith("'") and value.endswith("'"):
                return value[1:-1]
            return value

    return None


def _extract_visual_info(visual_data: Dict, file_path: Path, visuals_path: Path) -> Dict:
    """Extract visual information from visual.json

    Positions are returned as ABSOLUTE positions (as shown in Power BI UI),
    calculated by adding parent group offsets to the relative position stored in JSON.
    """
    visual = visual_data.get('visual', {})
    position = visual_data.get('position', {})

    # Get visual type
    visual_type = visual.get('visualType', 'unknown')

    # Get display title
    display_title = _get_visual_title(visual_data)

    # Get relative position and size (as stored in JSON)
    relative_x = position.get('x', 0)
    relative_y = position.get('y', 0)
    z = position.get('z', 0)
    height = position.get('height', 0)
    width = position.get('width', 0)
    tab_order = position.get('tabOrder', 0)

    # Calculate parent group offset
    parent_offset = _get_parent_group_offset(visual_data, visuals_path)

    # Calculate absolute position (as shown in Power BI UI)
    absolute_x = relative_x + parent_offset['x']
    absolute_y = relative_y + parent_offset['y']

    # Check visibility
    is_hidden = visual_data.get('isHidden', False)
    parent_group = visual_data.get('parentGroupName')

    return {
        'file_path': str(file_path),
        'visual_name': visual_data.get('name', ''),
        'display_title': display_title,
        'visual_type': visual_type,
        'position': {
            'x': absolute_x,  # Absolute position (as shown in Power BI)
            'y': absolute_y,  # Absolute position (as shown in Power BI)
            'z': z,
            'height': height,
            'width': width,
            'tab_order': tab_order
        },
        '_relative_position': {  # Internal: relative position as stored in JSON
            'x': relative_x,
            'y': relative_y
        },
        '_parent_offset': parent_offset,  # Internal: for position calculations
        'is_hidden': is_hidden,
        'parent_group': parent_group
    }


def _get_page_display_name(page_folder: Path) -> str:
    """Get the display name for a page from its page.json file"""
    page_json_path = page_folder / "page.json"
    if page_json_path.exists():
        page_data = _load_json_file(page_json_path)
        if page_data:
            return page_data.get('displayName', page_folder.name)
    return page_folder.name


def _find_visuals(
    definition_path: Path,
    display_title: Optional[str] = None,
    visual_type: Optional[str] = None,
    visual_name: Optional[str] = None,
    page_name: Optional[str] = None,
    include_hidden: bool = True
) -> List[Dict]:
    """Find all visuals matching the criteria"""
    matching_visuals = []

    # Search in pages folder
    pages_path = definition_path / "pages"
    if not pages_path.exists():
        return matching_visuals

    # Iterate through all pages
    for page_folder in pages_path.iterdir():
        if not page_folder.is_dir():
            continue

        # Get page display name
        page_id = page_folder.name
        page_display_name = _get_page_display_name(page_folder)

        # Filter by page name if specified
        if page_name:
            if page_name.lower() not in page_display_name.lower():
                continue

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

            visual_info = _extract_visual_info(visual_data, visual_json_path, visuals_path)

            # Skip hidden visuals unless requested
            if not include_hidden and visual_info['is_hidden']:
                continue

            # Add page information
            visual_info['page_id'] = page_id
            visual_info['page_name'] = page_display_name

            # Apply filters
            matches = True

            if display_title:
                # Case-insensitive partial match on display title
                if not visual_info['display_title'] or display_title.lower() not in visual_info['display_title'].lower():
                    matches = False

            if visual_type:
                # Case-insensitive match on visual type
                if visual_type.lower() != visual_info['visual_type'].lower():
                    matches = False

            if visual_name:
                # Case-insensitive match on visual name (ID)
                if visual_name.lower() != visual_info['visual_name'].lower():
                    matches = False

            if matches:
                matching_visuals.append(visual_info)

    return matching_visuals


def _update_visual_position(
    visual_data: Dict,
    x: Optional[float] = None,
    y: Optional[float] = None,
    width: Optional[float] = None,
    height: Optional[float] = None,
    z: Optional[int] = None,
    parent_offset: Optional[Dict[str, float]] = None
) -> Dict:
    """Update visual position and/or size

    Args:
        visual_data: The visual.json data
        x: Absolute x position (as shown in Power BI UI)
        y: Absolute y position (as shown in Power BI UI)
        width: Width (not affected by parent offset)
        height: Height (not affected by parent offset)
        z: Z-index (not affected by parent offset)
        parent_offset: Dict with 'x' and 'y' parent group offsets to subtract

    The x and y values are expected to be absolute positions (as displayed in Power BI).
    They will be converted to relative positions by subtracting the parent offset.
    """
    position = visual_data.setdefault('position', {})
    offset = parent_offset or {'x': 0, 'y': 0}

    if x is not None:
        # Convert absolute position to relative by subtracting parent offset
        position['x'] = x - offset['x']
    if y is not None:
        # Convert absolute position to relative by subtracting parent offset
        position['y'] = y - offset['y']
    if width is not None:
        position['width'] = width
    if height is not None:
        position['height'] = height
    if z is not None:
        position['z'] = z

    return visual_data


def _replace_measure_in_visual(
    visual_data: Dict,
    source_entity: str,
    source_property: str,
    target_entity: str,
    target_property: str,
    new_display_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Replace a measure reference in visual projections.

    Searches through all query state projections (Values, Rows, Columns, etc.)
    and replaces measures matching source_entity/source_property with target values.

    Returns: Dict with 'modified': bool, 'changes': list of change descriptions
    """
    changes = []
    modified = False

    visual = visual_data.get('visual', {})
    query = visual.get('query', {})
    query_state = query.get('queryState', {})

    # Search through all projection areas (Values, Rows, Columns, etc.)
    for area_name, area_data in query_state.items():
        projections = area_data.get('projections', []) if isinstance(area_data, dict) else []

        for i, projection in enumerate(projections):
            field = projection.get('field', {})
            measure = field.get('Measure', {})

            if not measure:
                continue

            expression = measure.get('Expression', {})
            source_ref = expression.get('SourceRef', {})
            current_entity = source_ref.get('Entity', '')
            current_property = measure.get('Property', '')

            # Check if this matches the source measure (case-insensitive comparison)
            if (current_entity.lower() == source_entity.lower() and
                current_property.lower() == source_property.lower()):

                # Store original values for reporting
                original_entity = current_entity
                original_property = current_property
                original_display_name = projection.get('displayName', projection.get('nativeQueryRef', ''))

                # Update the measure reference
                source_ref['Entity'] = target_entity
                measure['Property'] = target_property

                # Update queryRef and nativeQueryRef
                old_query_ref = projection.get('queryRef', '')
                projection['queryRef'] = f"{target_entity}.{target_property}"
                projection['nativeQueryRef'] = target_property

                # Handle display name
                if new_display_name:
                    projection['displayName'] = new_display_name
                elif 'displayName' not in projection:
                    # If there was no displayName, set it to preserve the header
                    projection['displayName'] = original_display_name or original_property
                # else: keep existing displayName (the original header)

                changes.append({
                    'area': area_name,
                    'index': i,
                    'from': {
                        'entity': original_entity,
                        'property': original_property,
                        'display_name': original_display_name
                    },
                    'to': {
                        'entity': target_entity,
                        'property': target_property,
                        'display_name': projection.get('displayName', target_property)
                    }
                })
                modified = True

    return {
        'modified': modified,
        'changes': changes
    }


def handle_visual_operations(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle visual editing operations"""
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
    display_title = args.get('display_title')
    visual_type = args.get('visual_type')
    visual_name = args.get('visual_name')
    page_name = args.get('page_name')
    include_hidden = args.get('include_hidden', True)

    if operation == 'list':
        # Find and list visuals with their current configuration
        visuals = _find_visuals(
            definition_path,
            display_title=display_title,
            visual_type=visual_type,
            visual_name=visual_name,
            page_name=page_name,
            include_hidden=include_hidden
        )

        if not visuals:
            return {
                'success': True,
                'message': 'No visuals found matching the criteria',
                'visuals': [],
                'count': 0
            }

        # Check for summary_only mode (default: True to reduce response size)
        summary_only = args.get('summary_only', True)

        if summary_only:
            # Return condensed visual info
            condensed_visuals = []
            for visual in visuals:
                condensed = {
                    'display_title': visual['display_title'],
                    'page_name': visual.get('page_name', ''),
                    'visual_type': visual['visual_type'],
                    'visual_name': visual['visual_name'],
                    'position': visual['position']
                }
                if visual.get('is_hidden'):
                    condensed['is_hidden'] = True
                condensed_visuals.append(condensed)

            return {
                'success': True,
                'message': f'Found {len(visuals)} visual(s) matching criteria',
                'visuals': condensed_visuals,
                'count': len(visuals),
                'summary_only': True,
                'hint': 'Use summary_only=false for full details including file paths',
                'note': 'Positions are absolute (as shown in Power BI UI), accounting for parent group offsets'
            }

        # Strip internal fields from full output
        clean_visuals = []
        for visual in visuals:
            clean_visual = {k: v for k, v in visual.items() if not k.startswith('_')}
            clean_visuals.append(clean_visual)

        return {
            'success': True,
            'message': f'Found {len(visuals)} visual(s) matching criteria',
            'visuals': clean_visuals,
            'count': len(visuals)
        }

    elif operation == 'update_position':
        # Get position/size parameters
        new_x = args.get('x')
        new_y = args.get('y')
        new_width = args.get('width')
        new_height = args.get('height')
        new_z = args.get('z')

        # Validate that at least one position/size parameter is provided
        if all(v is None for v in [new_x, new_y, new_width, new_height, new_z]):
            return {
                'success': False,
                'error': 'At least one position/size parameter is required: x, y, width, height, or z'
            }

        # Find matching visuals
        visuals = _find_visuals(
            definition_path,
            display_title=display_title,
            visual_type=visual_type,
            visual_name=visual_name,
            page_name=page_name,
            include_hidden=include_hidden
        )

        if not visuals:
            return {
                'success': False,
                'error': 'No visuals found matching the criteria. Use operation "list" to see available visuals.'
            }

        # Check for dry_run mode
        dry_run = args.get('dry_run', False)

        changes = []
        errors = []

        for visual in visuals:
            file_path = Path(visual['file_path'])

            # Capture before state
            before_position = visual['position'].copy()

            # Calculate after state
            after_position = before_position.copy()
            if new_x is not None:
                after_position['x'] = new_x
            if new_y is not None:
                after_position['y'] = new_y
            if new_width is not None:
                after_position['width'] = new_width
            if new_height is not None:
                after_position['height'] = new_height
            if new_z is not None:
                after_position['z'] = new_z

            # Check if anything would change
            position_changed = before_position != after_position

            if dry_run:
                # Just report what would change
                status = 'would_change' if position_changed else 'no_change'
                changes.append({
                    'display_title': visual['display_title'],
                    'page_name': visual.get('page_name', ''),
                    'visual_name': visual['visual_name'],
                    'before': {
                        'x': before_position.get('x'),
                        'y': before_position.get('y'),
                        'width': before_position.get('width'),
                        'height': before_position.get('height')
                    },
                    'after': {
                        'x': after_position.get('x'),
                        'y': after_position.get('y'),
                        'width': after_position.get('width'),
                        'height': after_position.get('height')
                    },
                    'status': status
                })
            else:
                if not position_changed:
                    changes.append({
                        'display_title': visual['display_title'],
                        'page_name': visual.get('page_name', ''),
                        'visual_name': visual['visual_name'],
                        'status': 'no_change'
                    })
                    continue

                # Load, modify, and save
                visual_data = _load_json_file(file_path)
                if not visual_data:
                    errors.append({
                        'file_path': str(file_path),
                        'error': 'Failed to load visual.json'
                    })
                    continue

                # Apply position changes
                # Pass parent offset so absolute positions are converted to relative
                parent_offset = visual.get('_parent_offset', {'x': 0, 'y': 0})
                modified_data = _update_visual_position(
                    visual_data,
                    x=new_x,
                    y=new_y,
                    width=new_width,
                    height=new_height,
                    z=new_z,
                    parent_offset=parent_offset
                )

                # Save changes
                if _save_json_file(file_path, modified_data):
                    changes.append({
                        'display_title': visual['display_title'],
                        'page_name': visual.get('page_name', ''),
                        'visual_name': visual['visual_name'],
                        'before': {
                            'x': before_position.get('x'),
                            'y': before_position.get('y'),
                            'width': before_position.get('width'),
                            'height': before_position.get('height')
                        },
                        'after': {
                            'x': after_position.get('x'),
                            'y': after_position.get('y'),
                            'width': after_position.get('width'),
                            'height': after_position.get('height')
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
            'operation': 'update_position',
            'dry_run': dry_run,
            'message': f'{"Would modify" if dry_run else "Modified"} {len([c for c in changes if c.get("status") in ["changed", "would_change"]])} visual(s)',
            'changes': changes,
            'changes_count': len(changes)
        }

        if errors:
            result['errors'] = errors
            result['errors_count'] = len(errors)
            result['message'] += f' with {len(errors)} error(s)'

        return result

    elif operation == 'replace_measure':
        # Get replace_measure parameters
        source_entity = args.get('source_entity')
        source_property = args.get('source_property')
        target_entity = args.get('target_entity')
        target_property = args.get('target_property')
        new_display_name = args.get('new_display_name')
        dry_run = args.get('dry_run', False)

        # Validate required parameters
        if not all([source_entity, source_property, target_entity, target_property]):
            return {
                'success': False,
                'error': 'replace_measure requires: source_entity, source_property, target_entity, target_property'
            }

        # Find matching visuals
        visuals = _find_visuals(
            definition_path,
            display_title=display_title,
            visual_type=visual_type,
            visual_name=visual_name,
            page_name=page_name,
            include_hidden=include_hidden
        )

        if not visuals:
            return {
                'success': True,
                'message': 'No visuals found matching the criteria',
                'changes': [],
                'count': 0
            }

        all_changes = []
        errors = []
        visuals_modified = 0

        for visual in visuals:
            file_path = Path(visual['file_path'])

            # Load visual data
            visual_data = _load_json_file(file_path)
            if not visual_data:
                errors.append({
                    'file_path': str(file_path),
                    'error': 'Failed to load visual.json'
                })
                continue

            # Try to replace measure
            result = _replace_measure_in_visual(
                visual_data,
                source_entity,
                source_property,
                target_entity,
                target_property,
                new_display_name
            )

            if result['modified']:
                change_record = {
                    'display_title': visual['display_title'],
                    'page_name': visual.get('page_name', ''),
                    'visual_name': visual['visual_name'],
                    'visual_type': visual['visual_type'],
                    'measure_changes': result['changes'],
                    'status': 'would_change' if dry_run else 'changed'
                }

                if not dry_run:
                    # Save the modified visual
                    if _save_json_file(file_path, visual_data):
                        change_record['status'] = 'changed'
                        visuals_modified += 1
                    else:
                        change_record['status'] = 'error'
                        errors.append({
                            'file_path': str(file_path),
                            'error': 'Failed to save changes'
                        })
                else:
                    visuals_modified += 1

                all_changes.append(change_record)

        result = {
            'success': len(errors) == 0,
            'operation': 'replace_measure',
            'dry_run': dry_run,
            'message': f'{"Would replace" if dry_run else "Replaced"} measure in {visuals_modified} visual(s)',
            'source': {
                'entity': source_entity,
                'property': source_property
            },
            'target': {
                'entity': target_entity,
                'property': target_property
            },
            'changes': all_changes,
            'changes_count': len(all_changes)
        }

        if new_display_name:
            result['new_display_name'] = new_display_name

        if errors:
            result['errors'] = errors
            result['errors_count'] = len(errors)
            result['message'] += f' with {len(errors)} error(s)'

        return result

    else:
        return {
            'success': False,
            'error': f'Unknown operation: {operation}. Valid operations: list, update_position, replace_measure'
        }


def register_visual_operations_handler(registry):
    """Register visual operations handler"""
    from server.tool_schemas import TOOL_SCHEMAS

    tool = ToolDefinition(
        name="08_Visual_Operations",
        description="[PBIP] Edit Power BI visual properties - list visuals, resize/reposition visuals, replace measures in visuals",
        handler=handle_visual_operations,
        input_schema=TOOL_SCHEMAS.get('visual_operations', {}),
        category="pbip",
        sort_order=74  # 08 = PBIP Analysis
    )
    registry.register(tool)

    logger.info("Registered visual_operations handler")
