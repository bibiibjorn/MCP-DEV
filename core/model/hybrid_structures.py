"""
Hybrid Analysis Data Structures

Data classes for hybrid analysis JSON files (metadata, catalog, dependencies)
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime


@dataclass
class ModelMetadata:
    """Model-level metadata"""
    name: str
    compatibility_level: int
    default_mode: str
    culture: str
    analysis_timestamp: str
    tmdl_source: str = "pbip"
    tmdl_export_path: str = "../tmdl/"
    export_version: str = "4.1-pbip"


@dataclass
class StatisticsSummary:
    """Model statistics summary"""
    tables: Dict[str, int]
    columns: Dict[str, int]
    measures: Dict[str, Any]
    relationships: Dict[str, int]
    security: Dict[str, int]


@dataclass
class RowCountInfo:
    """Row count information for a table"""
    table: str
    row_count: int
    last_refresh: Optional[str] = None


@dataclass
class ExportPerformance:
    """Export performance metrics"""
    export_time_seconds: float
    json_library: str = "orjson"
    compression: str = "snappy"
    worker_count: int = 1
    tmdl_strategy: str = "symlink"


@dataclass
class Metadata:
    """Complete metadata.json structure"""
    model: ModelMetadata
    statistics: StatisticsSummary
    row_counts: Dict[str, Any]
    cardinality_summary: Dict[str, Any]
    export_performance: ExportPerformance

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class ColumnInfo:
    """Column metadata"""
    name: str
    data_type: str
    is_key: bool = False
    is_hidden: bool = False
    cardinality: Optional[int] = None
    cardinality_ratio: Optional[float] = None
    used_in_relationships: bool = False
    used_in_measures: bool = False
    used_in_visuals: bool = False
    used_in_rls: bool = False
    measure_references: int = 0
    is_unused: bool = False
    usage_confidence: float = 1.0
    estimated_memory_mb: Optional[float] = None
    optimization_priority: str = "low"


@dataclass
class TableInfo:
    """Table metadata"""
    name: str
    type: str  # "dimension" | "fact" | "calculation"
    tmdl_path: str
    column_count: int
    row_count: Optional[int] = None
    relationship_count: int = 0
    has_sample_data: bool = False
    sample_data_path: Optional[str] = None
    columns: List[ColumnInfo] = field(default_factory=list)
    unused_columns: List[str] = field(default_factory=list)
    optimization_potential_mb: float = 0.0


@dataclass
class MeasureInfo:
    """Measure metadata"""
    name: str
    table: str
    display_folder: Optional[str] = None
    tmdl_path: str = "tmdl/expressions.tmdl"
    line_number: Optional[int] = None


@dataclass
class RoleInfo:
    """Role metadata"""
    name: str
    tmdl_path: str
    table_count: int = 0


@dataclass
class Catalog:
    """Complete catalog.json structure"""
    tables: List[TableInfo]
    relationships_path: str = "tmdl/relationships.tmdl"
    roles: List[RoleInfo] = field(default_factory=list)
    optimization_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Measures:
    """Complete measures.json structure"""
    measures: List[MeasureInfo]
    total_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class DependencyInfo:
    """Dependency information for a measure/column/table"""
    columns: List[str] = field(default_factory=list)  # Format: "Table[Column]"
    measures: List[str] = field(default_factory=list)


@dataclass
class ReferencedBy:
    """Referenced by information"""
    measures: List[str] = field(default_factory=list)
    count: int = 0


@dataclass
class MeasureDependency:
    """Complete measure dependency information"""
    expression: str
    table: str
    dependencies: DependencyInfo
    referenced_by: ReferencedBy


@dataclass
class ColumnDependency:
    """Column usage information"""
    table: str
    data_type: str
    used_in_measures: List[str] = field(default_factory=list)
    used_in_relationships: bool = False
    used_in_rls: bool = False
    usage_count: int = 0


@dataclass
class TableDependency:
    """Table usage information"""
    type: str
    relationships: Dict[str, Any] = field(default_factory=dict)
    used_in_measures: int = 0
    used_in_rls: bool = False
    critical: bool = False


@dataclass
class Dependencies:
    """Complete dependencies.json structure"""
    measures: Dict[str, MeasureDependency]
    columns: Dict[str, ColumnDependency]
    tables: Dict[str, TableDependency]
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class FilePart:
    """Information about a file part in multi-part files"""
    part_number: int
    filename: str
    size_bytes: int
    content_range: str


@dataclass
class FileManifest:
    """Manifest for multi-part files"""
    file_type: str  # "catalog" | "dependencies"
    total_parts: int
    total_size_bytes: int
    split_strategy: str
    parts: List[FilePart]
    reassembly_instructions: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class RelationshipInfo:
    """Relationship metadata"""
    name: str
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    is_active: bool = True
    cross_filter_direction: str = "OneDirection"  # "OneDirection" | "BothDirections"
    cardinality: str = "ManyToOne"  # "OneToOne" | "OneToMany" | "ManyToOne" | "ManyToMany"
    security_filtering_behavior: str = "OneDirection"
    relies_on_referential_integrity: bool = False


@dataclass
class Relationships:
    """Complete relationships.json structure"""
    relationships: List[RelationshipInfo]
    total_count: int = 0
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class PBIPSourceInfo:
    """PBIP source information"""
    source_pbip_path: str
    source_pbip_absolute: str
    pbip_last_modified: str
    model_name: str
    export_timestamp: str
    export_version: str = "4.1-pbip"
    tmdl_strategy: str = "symlink"
    tmdl_file_count: int = 0
    tmdl_total_size_bytes: int = 0
    connection_used: bool = False
    sample_data_extracted: bool = False
    pbix_file: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
