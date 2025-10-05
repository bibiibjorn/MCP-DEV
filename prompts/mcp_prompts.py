"""
MCP Prompts for the PBIXRay MCP Server

This module contains all the MCP prompts that provide guided interactions
for users working with Power BI Desktop models.
"""

def register_prompts(mcp):
    """Register all MCP prompts with the FastMCP instance."""

    # Basic detection and connection prompts
    @mcp.prompt
    def detect_powerbi_instances() -> str:
        """Detect running Power BI Desktop instances"""
        return "Can you detect my Power BI Desktop instances?"

    @mcp.prompt
    def connect_to_model() -> str:
        """Connect to a Power BI Desktop instance"""
        return "Can you connect to my Power BI Desktop model? Show me the available instances first."

    # Model exploration prompts
    @mcp.prompt
    def explore_model_structure() -> str:
        """Get a comprehensive overview of the model structure"""
        return "Can you give me a complete overview of my Power BI model? Show me all tables, measures, columns, and relationships."

    @mcp.prompt
    def list_all_measures() -> str:
        """List all DAX measures in the model"""
        return "Can you list all DAX measures in this model with their tables and display folders?"

    @mcp.prompt
    def analyze_table_structure() -> str:
        """Analyze the structure of a specific table"""
        return "Can you describe the structure of a specific table including columns, measures, and relationships?"

    # DAX analysis prompts
    @mcp.prompt
    def search_dax_expressions() -> str:
        """Search for text in DAX measures"""
        return "Can you search for specific text or patterns in DAX measure expressions?"

    @mcp.prompt
    def analyze_measure_complexity() -> str:
        """Analyze DAX measure complexity"""
        return "Can you analyze the complexity of DAX measures in this model? Show me measures that might be complex or need optimization."

    @mcp.prompt
    def list_calculated_columns() -> str:
        """List calculated columns in the model"""
        return "Can you show me all calculated columns in this model? I want to identify potential performance issues."

    # Performance analysis prompts
    @mcp.prompt
    def analyze_query_performance() -> str:
        """Analyze DAX query performance with SE/FE breakdown"""
        return "Can you analyze the performance of a DAX query? Show me Storage Engine vs Formula Engine breakdown with multiple runs."

    @mcp.prompt
    def get_vertipaq_statistics() -> str:
        """Get VertiPaq storage statistics"""
        return "Can you show me VertiPaq storage statistics? I want to understand memory usage and compression."

    @mcp.prompt
    def performance_optimization_analysis() -> str:
        """Comprehensive performance optimization analysis"""
        return "Can you perform a comprehensive performance analysis? Include query performance, storage statistics, and identify optimization opportunities."

    # Best Practice Analyzer prompts
    @mcp.prompt
    def run_bpa_analysis() -> str:
        """Run Best Practice Analyzer on the current model"""
        return "Can you run a Best Practice Analyzer scan on this Power BI model? Show me all violations and issues."

    @mcp.prompt
    def show_critical_bpa_issues() -> str:
        """Show only critical BPA issues"""
        return "Can you show me only the critical errors from the Best Practice Analyzer? I want to focus on the most important issues."

    @mcp.prompt
    def bpa_performance_issues() -> str:
        """Get performance-related BPA issues"""
        return "Can you run BPA and show me only performance-related issues and recommendations?"

    @mcp.prompt
    def bpa_dax_issues() -> str:
        """Get DAX-related BPA issues"""
        return "Can you analyze my DAX expressions using Best Practice Analyzer? Show me syntax issues and optimization opportunities."

    # Data exploration prompts
    @mcp.prompt
    def preview_table_data() -> str:
        """Preview data from a table"""
        return "Can you show me a preview of the data from a specific table?"

    @mcp.prompt
    def analyze_column_statistics() -> str:
        """Get statistics for a column"""
        return "Can you analyze a specific column and show me statistics like min, max, distinct count, and nulls?"

    @mcp.prompt
    def explore_column_values() -> str:
        """Sample unique values from a column"""
        return "Can you show me sample values from a specific column?"

    # Relationship analysis prompts
    @mcp.prompt
    def analyze_relationships() -> str:
        """Analyze model relationships"""
        return "Can you show me all relationships in this model? Include active status, cardinality, and cross-filter direction."

    @mcp.prompt
    def find_relationship_issues() -> str:
        """Identify potential relationship issues"""
        return "Can you analyze relationships and identify potential issues like inactive relationships or incorrect cardinality?"

    # Data source prompts
    @mcp.prompt
    def show_data_sources() -> str:
        """Show data sources and connections"""
        return "Can you show me all data sources and connections in this model?"

    @mcp.prompt
    def show_power_query_expressions() -> str:
        """Show Power Query M expressions"""
        return "Can you show me the Power Query (M) expressions in this model?"

    # Search and discovery prompts
    @mcp.prompt
    def search_model_objects() -> str:
        """Search for objects in the model"""
        return "Can you search for specific objects (tables, columns, measures) in the model by name or pattern?"

    @mcp.prompt
    def find_unused_objects() -> str:
        """Find potentially unused objects"""
        return "Can you help me find potentially unused objects like hidden tables, columns, or measures that might be cleaned up?"

    # Documentation and export prompts
    @mcp.prompt
    def export_model_schema() -> str:
        """Export complete model schema"""
        return "Can you export the complete model schema including all tables, columns, measures, and relationships in a structured format?"

    @mcp.prompt
    def document_model_structure() -> str:
        """Generate model documentation"""
        return "Can you help me document this Power BI model? Create a comprehensive description of its structure and components."

    # DAX injection and modification prompts
    @mcp.prompt
    def create_new_measure() -> str:
        """Create a new DAX measure"""
        return "Can you help me create a new DAX measure? I'll provide the table, measure name, and expression."

    @mcp.prompt
    def update_existing_measure() -> str:
        """Update an existing DAX measure"""
        return "Can you update an existing DAX measure with a new expression?"

    # Troubleshooting prompts
    @mcp.prompt
    def troubleshoot_performance() -> str:
        """Troubleshoot performance issues"""
        return "This model is running slowly. Can you help me troubleshoot performance issues? Check for common problems and suggest optimizations."

    @mcp.prompt
    def debug_dax_errors() -> str:
        """Help debug DAX errors"""
        return "I'm getting errors in my DAX expressions. Can you help me debug and fix them?"

    @mcp.prompt
    def validate_model_design() -> str:
        """Validate overall model design"""
        return "Can you validate my model design? Check for best practices violations, performance issues, and design problems."

    # Comparison and analysis prompts
    @mcp.prompt
    def compare_model_versions() -> str:
        """Compare different versions of the model"""
        return "Can you help me understand what's changed in my model? Compare current structure with previous analysis."

    @mcp.prompt
    def analyze_model_complexity() -> str:
        """Analyze overall model complexity"""
        return "Can you analyze the overall complexity of this model? Show me metrics like table count, measure count, relationship count, and complexity indicators."

    # Advanced prompts
    @mcp.prompt
    def optimization_roadmap() -> str:
        """Create an optimization roadmap"""
        return "Can you create an optimization roadmap for this model? Prioritize issues by impact and provide step-by-step recommendations."

    @mcp.prompt
    def pre_deployment_check() -> str:
        """Pre-deployment validation"""
        return "I'm about to deploy this model. Can you perform a pre-deployment check? Run BPA, check performance, and validate the structure."

    @mcp.prompt
    def model_health_check() -> str:
        """Comprehensive model health check"""
        return "Can you perform a complete health check on this Power BI model? Include BPA analysis, performance metrics, and design validation."
