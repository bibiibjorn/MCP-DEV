"""
TMDL Measure Migrator - Extract and copy measures between TMDL files

Enables migration of measures between Power BI models with:
- Display folder filtering
- Duplicate handling
- TMDL format validation and fixing
- Dry-run mode for previewing changes
"""

import logging
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


@dataclass
class MeasureInfo:
    """Information about a measure"""
    name: str
    display_folder: str
    content: str
    line_number: int


@dataclass
class MigrationResult:
    """Result of a measure migration operation"""
    success: bool
    measures_found: int
    measures_migrated: int
    duplicates_skipped: int
    backup_path: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    measures: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "success": self.success,
            "measures_found": self.measures_found,
            "measures_migrated": self.measures_migrated,
            "duplicates_skipped": self.duplicates_skipped,
            "backup_path": self.backup_path,
            "errors": self.errors,
            "warnings": self.warnings,
            "measures": self.measures[:50]  # Limit to first 50 for output
        }


class TmdlMeasureMigrator:
    """
    TMDL Measure Migrator for copying measures between models.

    Features:
    - Extract measures by display folder pattern
    - Copy to target with duplicate handling
    - Fix TMDL formatting issues (empty lines after /// comments)
    - Dry-run mode for safe previewing
    - Automatic backups before modifications
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize measure migrator with configuration.

        Args:
            config: Optional configuration dict
        """
        self.config = config or {}
        self.backup_enabled = self.config.get("backup_before_edit", True)
        self.backup_dir = Path(self.config.get("backup_directory", "./backups/tmdl"))

    def extract_measures(
        self,
        source_path: str,
        display_folder_filter: Optional[str] = None
    ) -> List[MeasureInfo]:
        """
        Extract measures from a TMDL file.

        Args:
            source_path: Path to source TMDL file (m Measure.tmdl or similar)
            display_folder_filter: Optional display folder prefix to filter by

        Returns:
            List of MeasureInfo objects
        """
        measures = []
        path = Path(source_path)

        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        content = path.read_text(encoding='utf-8')
        lines = content.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i]

            # Handle /// comment before measure
            comment_line = None
            if line.strip().startswith('///'):
                comment_line = line
                i += 1
                # Skip empty lines after comment
                while i < len(lines) and not lines[i].strip():
                    i += 1
                if i >= len(lines):
                    break
                line = lines[i]

            # Check if this line starts a measure
            if line.strip().startswith('measure '):
                measure_start = i
                measure_lines = []
                if comment_line:
                    measure_lines.append(comment_line)
                measure_lines.append(line)
                i += 1

                # Collect all lines of this measure
                while i < len(lines):
                    current = lines[i]
                    # End of measure detection
                    if (current.strip().startswith('measure ') or
                        current.strip().startswith('partition ') or
                        current.strip().startswith('///')):
                        break
                    measure_lines.append(current)
                    i += 1

                # Extract measure info
                measure_text = '\n'.join(measure_lines)

                # Get measure name
                name_match = re.search(r"measure\s+'([^']+)'|measure\s+(\S+)\s*=", measure_lines[1 if comment_line else 0])
                if name_match:
                    name = name_match.group(1) or name_match.group(2)
                else:
                    name = "Unknown"

                # Get display folder
                folder_match = re.search(r'displayFolder:\s*(.+)', measure_text)
                display_folder = folder_match.group(1).strip() if folder_match else ""

                # Filter by display folder if specified
                if display_folder_filter:
                    if not display_folder.startswith(display_folder_filter):
                        continue

                # Clean trailing empty lines
                while measure_lines and not measure_lines[-1].strip():
                    measure_lines.pop()

                measures.append(MeasureInfo(
                    name=name,
                    display_folder=display_folder,
                    content='\n'.join(measure_lines),
                    line_number=measure_start
                ))
            else:
                i += 1

        logger.info(f"Extracted {len(measures)} measures from {source_path}")
        return measures

    def migrate_measures(
        self,
        source_path: str,
        target_path: str,
        display_folder_filter: Optional[str] = None,
        replace_target: bool = False,
        skip_duplicates: bool = True,
        dry_run: bool = True
    ) -> MigrationResult:
        """
        Migrate measures from source to target TMDL file.

        Args:
            source_path: Path to source TMDL file
            target_path: Path to target TMDL file
            display_folder_filter: Optional display folder prefix to filter by
            replace_target: If True, replace target content entirely; if False, append
            skip_duplicates: Skip measures that already exist in target
            dry_run: Preview changes without applying

        Returns:
            MigrationResult with details
        """
        result = MigrationResult(
            success=False,
            measures_found=0,
            measures_migrated=0,
            duplicates_skipped=0
        )

        try:
            # Extract measures from source
            source_measures = self.extract_measures(source_path, display_folder_filter)
            result.measures_found = len(source_measures)

            if not source_measures:
                result.warnings.append(f"No measures found matching filter: {display_folder_filter}")
                result.success = True
                return result

            # Get existing measures in target (for duplicate detection)
            target_file = Path(target_path)
            existing_names = set()
            target_header = ""
            target_partition = ""

            if target_file.exists():
                target_content = target_file.read_text(encoding='utf-8')

                # Extract existing measure names
                for match in re.finditer(r"measure\s+'([^']+)'|measure\s+(\S+)\s*=", target_content):
                    name = match.group(1) or match.group(2)
                    existing_names.add(name)

                # Extract header (table definition)
                header_match = re.match(r"(table\s+'[^']+'\s*\n\tlineageTag:[^\n]+\n)", target_content)
                if header_match:
                    target_header = header_match.group(1)
                else:
                    # Fallback: use first 2 lines
                    lines = target_content.split('\n')
                    if len(lines) >= 2:
                        target_header = '\n'.join(lines[:3]) + '\n'

                # Extract partition section
                partition_match = re.search(r"(\tpartition\s+'[^']+'.+)$", target_content, re.DOTALL)
                if partition_match:
                    target_partition = partition_match.group(1)

            else:
                # Create default header if target doesn't exist
                target_header = """table 'm Measure'
\tlineageTag: 00000000-0000-0000-0000-000000000000

"""

            # Filter duplicates and prepare measures to migrate
            measures_to_migrate = []
            for measure in source_measures:
                if skip_duplicates and measure.name in existing_names:
                    result.duplicates_skipped += 1
                    result.warnings.append(f"Skipped duplicate: {measure.name}")
                else:
                    measures_to_migrate.append(measure)
                    result.measures.append({
                        "name": measure.name,
                        "display_folder": measure.display_folder
                    })

            result.measures_migrated = len(measures_to_migrate)

            if dry_run:
                result.success = True
                result.warnings.append("DRY RUN - No changes applied")
                return result

            # Create backup if enabled
            if self.backup_enabled and target_file.exists():
                backup_path = self._create_backup(target_path)
                result.backup_path = str(backup_path)

            # Build new content
            if replace_target:
                new_content = target_header + '\n'
            else:
                if target_file.exists():
                    # Remove partition section to append measures before it
                    new_content = re.sub(r'\tpartition\s+.+$', '', target_content, flags=re.DOTALL).rstrip() + '\n\n'
                else:
                    new_content = target_header

            for measure in measures_to_migrate:
                new_content += measure.content + '\n\n'

            # Add partition section
            if target_partition:
                new_content += target_partition
            else:
                new_content += self._default_partition()

            # Fix TMDL formatting (no empty lines after /// comments)
            new_content = self._fix_tmdl_format(new_content)

            # Write to target
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(new_content, encoding='utf-8')

            result.success = True
            logger.info(f"Migrated {result.measures_migrated} measures to {target_path}")

        except Exception as e:
            logger.error(f"Error during measure migration: {e}", exc_info=True)
            result.errors.append(str(e))

        return result

    def create_measure_table(
        self,
        target_path: str,
        source_path: str,
        display_folder_filter: Optional[str] = None,
        lineage_tag: Optional[str] = None,
        dry_run: bool = True
    ) -> MigrationResult:
        """
        Create a new m Measure table with only filtered measures.

        Args:
            target_path: Path to target TMDL file
            source_path: Path to source TMDL file
            display_folder_filter: Optional display folder prefix to filter by
            lineage_tag: Optional lineageTag for the table
            dry_run: Preview changes without applying

        Returns:
            MigrationResult with details
        """
        result = MigrationResult(
            success=False,
            measures_found=0,
            measures_migrated=0,
            duplicates_skipped=0
        )

        try:
            # Extract measures from source
            source_measures = self.extract_measures(source_path, display_folder_filter)
            result.measures_found = len(source_measures)

            if not source_measures:
                result.warnings.append(f"No measures found matching filter: {display_folder_filter}")
                result.success = True
                return result

            # Remove duplicates by name
            seen_names = set()
            unique_measures = []
            for measure in source_measures:
                if measure.name not in seen_names:
                    seen_names.add(measure.name)
                    unique_measures.append(measure)
                    result.measures.append({
                        "name": measure.name,
                        "display_folder": measure.display_folder
                    })
                else:
                    result.duplicates_skipped += 1

            result.measures_migrated = len(unique_measures)

            if dry_run:
                result.success = True
                result.warnings.append("DRY RUN - No changes applied")
                return result

            # Create backup if target exists
            target_file = Path(target_path)
            if self.backup_enabled and target_file.exists():
                backup_path = self._create_backup(target_path)
                result.backup_path = str(backup_path)

            # Build new content
            tag = lineage_tag or "0285e392-0bf7-4d8c-a926-1d7db16824f0"
            new_content = f"""table 'm Measure'
\tlineageTag: {tag}

"""

            for measure in unique_measures:
                new_content += measure.content + '\n\n'

            new_content += self._default_partition()

            # Fix TMDL formatting (no empty lines after /// comments)
            new_content = self._fix_tmdl_format(new_content)

            # Write to target
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(new_content, encoding='utf-8')

            result.success = True
            logger.info(f"Created measure table with {result.measures_migrated} measures at {target_path}")

        except Exception as e:
            logger.error(f"Error creating measure table: {e}", exc_info=True)
            result.errors.append(str(e))

        return result

    def _create_backup(self, file_path: str) -> Path:
        """Create a backup of the file before modification."""
        source = Path(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source.stem}_{timestamp}{source.suffix}"
        backup_path = self.backup_dir / backup_name

        self.backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, backup_path)

        logger.info(f"Created backup: {backup_path}")
        return backup_path

    def _default_partition(self) -> str:
        """Return default partition definition for m Measure table."""
        return """\tpartition 'm Measure' = m
\t\tmode: import
\t\tsource =
\t\t\t\tlet
\t\t\t\t    Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("i44FAA==", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [Column1 = _t]),
\t\t\t\t    #"Changed Type" = Table.TransformColumnTypes(Source,{{"Column1", type text}}),
\t\t\t\t    #"Removed Columns" = Table.RemoveColumns(#"Changed Type",{"Column1"})
\t\t\t\tin
\t\t\t\t    #"Removed Columns"

\tannotation PBI_ResultType = Table
"""

    def _fix_tmdl_format(self, content: str) -> str:
        """
        Fix TMDL formatting issues.

        TMDL requires no empty lines after /// comments before measure definitions.
        This method removes such empty lines to prevent parsing errors.

        Args:
            content: TMDL content to fix

        Returns:
            Fixed TMDL content
        """
        # Remove empty lines between /// comments and measure definitions
        content = re.sub(r'(\t///[^\n]*)\n\n(\tmeasure)', r'\1\n\2', content)

        # Also handle multiple empty lines
        content = re.sub(r'(\t///[^\n]*)\n\n+(\tmeasure)', r'\1\n\2', content)

        return content
