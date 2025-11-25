"""
Power BI MCP Server - Professional Tools Guide Generator
Creates a beautiful, modern PDF documentation with professional styling
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, Flowable, KeepTogether, ListFlowable, ListItem,
    HRFlowable
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle, Polygon
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os

# =============================================================================
# COLOR PALETTE - Modern Professional Theme
# =============================================================================
class Colors:
    # Primary colors
    PRIMARY_DARK = colors.HexColor('#1a365d')      # Deep navy blue
    PRIMARY = colors.HexColor('#2b6cb0')           # Power BI blue
    PRIMARY_LIGHT = colors.HexColor('#4299e1')     # Light blue

    # Accent colors
    ACCENT_GOLD = colors.HexColor('#d69e2e')       # Gold accent
    ACCENT_GREEN = colors.HexColor('#38a169')      # Success green
    ACCENT_ORANGE = colors.HexColor('#dd6b20')     # Warning orange
    ACCENT_RED = colors.HexColor('#e53e3e')        # Error red
    ACCENT_PURPLE = colors.HexColor('#805ad5')     # Purple highlight

    # Neutrals
    DARK_GRAY = colors.HexColor('#2d3748')         # Dark text
    MEDIUM_GRAY = colors.HexColor('#4a5568')       # Medium text
    LIGHT_GRAY = colors.HexColor('#718096')        # Light text
    VERY_LIGHT_GRAY = colors.HexColor('#e2e8f0')   # Borders
    BACKGROUND = colors.HexColor('#f7fafc')        # Light background
    WHITE = colors.HexColor('#ffffff')

    # Category colors
    CAT_CONNECTION = colors.HexColor('#3182ce')    # Blue
    CAT_SCHEMA = colors.HexColor('#38a169')        # Green
    CAT_DAX = colors.HexColor('#d69e2e')           # Gold
    CAT_OPERATIONS = colors.HexColor('#dd6b20')    # Orange
    CAT_ANALYSIS = colors.HexColor('#805ad5')      # Purple
    CAT_DEPENDENCIES = colors.HexColor('#e53e3e') # Red
    CAT_EXPORT = colors.HexColor('#319795')        # Teal
    CAT_DOCS = colors.HexColor('#667eea')          # Indigo
    CAT_COMPARE = colors.HexColor('#ed64a6')       # Pink
    CAT_PBIP = colors.HexColor('#00b5d8')          # Cyan
    CAT_TMDL = colors.HexColor('#9f7aea')          # Light purple
    CAT_HELP = colors.HexColor('#48bb78')          # Light green
    CAT_HYBRID = colors.HexColor('#f6ad55')        # Light orange


# =============================================================================
# CUSTOM FLOWABLES
# =============================================================================

class GradientRect(Flowable):
    """A rectangle with gradient fill effect (simulated)"""
    def __init__(self, width, height, color1, color2, text="", text_color=colors.white):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.color1 = color1
        self.color2 = color2
        self.text = text
        self.text_color = text_color

    def draw(self):
        # Draw gradient simulation with multiple rectangles
        steps = 20
        for i in range(steps):
            # Interpolate color
            ratio = i / steps
            r = self.color1.red + (self.color2.red - self.color1.red) * ratio
            g = self.color1.green + (self.color2.green - self.color1.green) * ratio
            b = self.color1.blue + (self.color2.blue - self.color1.blue) * ratio

            self.canv.setFillColor(colors.Color(r, g, b))
            y = self.height * i / steps
            self.canv.rect(0, y, self.width, self.height/steps + 1, fill=1, stroke=0)

        # Draw text if provided
        if self.text:
            self.canv.setFillColor(self.text_color)
            self.canv.setFont("Helvetica-Bold", 24)
            text_width = self.canv.stringWidth(self.text, "Helvetica-Bold", 24)
            self.canv.drawString((self.width - text_width) / 2, self.height / 2 - 10, self.text)


class CategoryHeader(Flowable):
    """A styled category header with icon and background"""
    def __init__(self, number, title, color, width=None):
        Flowable.__init__(self)
        self.number = number
        self.title = title
        self.color = color
        self.width = width or 500
        self.height = 50

    def draw(self):
        # Background rectangle with rounded corners effect
        self.canv.setFillColor(self.color)
        self.canv.roundRect(0, 0, self.width, self.height, 8, fill=1, stroke=0)

        # Number circle
        self.canv.setFillColor(Colors.WHITE)
        self.canv.circle(30, self.height/2, 18, fill=1, stroke=0)

        # Number text
        self.canv.setFillColor(self.color)
        self.canv.setFont("Helvetica-Bold", 16)
        num_text = str(self.number).zfill(2)
        num_width = self.canv.stringWidth(num_text, "Helvetica-Bold", 16)
        self.canv.drawString(30 - num_width/2, self.height/2 - 6, num_text)

        # Title text
        self.canv.setFillColor(Colors.WHITE)
        self.canv.setFont("Helvetica-Bold", 20)
        self.canv.drawString(60, self.height/2 - 7, self.title)


class ToolCard(Flowable):
    """A card-style container for tool documentation"""
    def __init__(self, tool_name, tool_id, description, when_to_use, example,
                 parameters, returns, color, width=None):
        Flowable.__init__(self)
        self.tool_name = tool_name
        self.tool_id = tool_id
        self.description = description
        self.when_to_use = when_to_use
        self.example = example
        self.parameters = parameters
        self.returns = returns
        self.color = color
        self.width = width or 500
        self._calculate_height()

    def _calculate_height(self):
        # Estimate height based on content
        base_height = 180
        param_lines = len(self.parameters.split('\n')) if self.parameters else 0
        example_lines = len(self.example.split('\n')) if self.example else 0
        self.height = base_height + (param_lines * 12) + (example_lines * 10)

    def draw(self):
        # Main card background
        self.canv.setFillColor(Colors.WHITE)
        self.canv.setStrokeColor(Colors.VERY_LIGHT_GRAY)
        self.canv.setLineWidth(1)
        self.canv.roundRect(0, 0, self.width, self.height, 6, fill=1, stroke=1)

        # Left color bar
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, 5, self.height, fill=1, stroke=0)

        # Tool name header
        y = self.height - 25
        self.canv.setFillColor(Colors.DARK_GRAY)
        self.canv.setFont("Helvetica-Bold", 14)
        self.canv.drawString(15, y, self.tool_name)

        # Tool ID
        self.canv.setFillColor(Colors.LIGHT_GRAY)
        self.canv.setFont("Helvetica", 9)
        self.canv.drawString(15, y - 15, f"({self.tool_id})")

        y -= 35

        # Description
        self.canv.setFillColor(Colors.MEDIUM_GRAY)
        self.canv.setFont("Helvetica", 10)
        self._draw_wrapped_text(self.description, 15, y, self.width - 30, 10)


class IconBadge(Flowable):
    """A small badge/icon element"""
    def __init__(self, text, bg_color, text_color=colors.white, width=80, height=24):
        Flowable.__init__(self)
        self.text = text
        self.bg_color = bg_color
        self.text_color = text_color
        self.width = width
        self.height = height

    def draw(self):
        self.canv.setFillColor(self.bg_color)
        self.canv.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=0)

        self.canv.setFillColor(self.text_color)
        self.canv.setFont("Helvetica-Bold", 9)
        text_width = self.canv.stringWidth(self.text, "Helvetica-Bold", 9)
        self.canv.drawString((self.width - text_width) / 2, 7, self.text)


class HorizontalLine(Flowable):
    """A styled horizontal line"""
    def __init__(self, width, color=Colors.VERY_LIGHT_GRAY, thickness=1):
        Flowable.__init__(self)
        self.width = width
        self.color = color
        self.thickness = thickness
        self.height = thickness + 4

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, self.height/2, self.width, self.height/2)


# =============================================================================
# STYLES
# =============================================================================

def create_styles():
    """Create all paragraph styles"""
    styles = getSampleStyleSheet()

    # Title styles
    styles.add(ParagraphStyle(
        name='MainTitle',
        parent=styles['Heading1'],
        fontSize=36,
        textColor=Colors.PRIMARY_DARK,
        alignment=TA_CENTER,
        spaceAfter=20,
        fontName='Helvetica-Bold',
        leading=44
    ))

    styles.add(ParagraphStyle(
        name='Subtitle',
        parent=styles['Normal'],
        fontSize=16,
        textColor=Colors.PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=30,
        fontName='Helvetica'
    ))

    styles.add(ParagraphStyle(
        name='VersionInfo',
        parent=styles['Normal'],
        fontSize=12,
        textColor=Colors.LIGHT_GRAY,
        alignment=TA_CENTER,
        spaceBefore=10,
        spaceAfter=10
    ))

    # Section headers
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=Colors.PRIMARY_DARK,
        spaceBefore=30,
        spaceAfter=15,
        fontName='Helvetica-Bold',
        borderColor=Colors.PRIMARY,
        borderWidth=0,
        borderPadding=5
    ))

    styles.add(ParagraphStyle(
        name='CategoryTitle',
        parent=styles['Heading2'],
        fontSize=20,
        textColor=Colors.WHITE,
        spaceBefore=25,
        spaceAfter=15,
        fontName='Helvetica-Bold',
        backColor=Colors.PRIMARY
    ))

    # Tool styles
    styles.add(ParagraphStyle(
        name='ToolName',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=Colors.DARK_GRAY,
        spaceBefore=15,
        spaceAfter=5,
        fontName='Helvetica-Bold',
        leftIndent=0
    ))

    styles.add(ParagraphStyle(
        name='ToolID',
        parent=styles['Normal'],
        fontSize=9,
        textColor=Colors.LIGHT_GRAY,
        spaceAfter=8,
        fontName='Helvetica'
    ))

    styles.add(ParagraphStyle(
        name='ToolDescription',
        parent=styles['Normal'],
        fontSize=11,
        textColor=Colors.MEDIUM_GRAY,
        spaceAfter=10,
        fontName='Helvetica',
        leading=15
    ))

    # Content styles
    styles.add(ParagraphStyle(
        name='CustomBodyText',
        parent=styles['Normal'],
        fontSize=10,
        textColor=Colors.DARK_GRAY,
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        leading=14
    ))

    styles.add(ParagraphStyle(
        name='SubheadingBlue',
        parent=styles['Normal'],
        fontSize=11,
        textColor=Colors.PRIMARY,
        spaceBefore=10,
        spaceAfter=5,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='ExampleText',
        parent=styles['Normal'],
        fontSize=9,
        textColor=Colors.MEDIUM_GRAY,
        backColor=Colors.BACKGROUND,
        borderColor=Colors.VERY_LIGHT_GRAY,
        borderWidth=1,
        borderPadding=8,
        leftIndent=10,
        rightIndent=10,
        spaceBefore=5,
        spaceAfter=10,
        fontName='Courier',
        leading=12
    ))

    styles.add(ParagraphStyle(
        name='ParameterText',
        parent=styles['Normal'],
        fontSize=9,
        textColor=Colors.DARK_GRAY,
        leftIndent=15,
        spaceAfter=3,
        fontName='Helvetica',
        leading=12
    ))

    styles.add(ParagraphStyle(
        name='TipBox',
        parent=styles['Normal'],
        fontSize=10,
        textColor=Colors.DARK_GRAY,
        backColor=colors.HexColor('#fef3c7'),
        borderColor=Colors.ACCENT_GOLD,
        borderWidth=1,
        borderPadding=10,
        spaceBefore=10,
        spaceAfter=10,
        leading=14
    ))

    styles.add(ParagraphStyle(
        name='InfoBox',
        parent=styles['Normal'],
        fontSize=10,
        textColor=Colors.DARK_GRAY,
        backColor=colors.HexColor('#ebf8ff'),
        borderColor=Colors.PRIMARY_LIGHT,
        borderWidth=1,
        borderPadding=10,
        spaceBefore=10,
        spaceAfter=10,
        leading=14
    ))

    styles.add(ParagraphStyle(
        name='TOCEntry',
        parent=styles['Normal'],
        fontSize=11,
        textColor=Colors.DARK_GRAY,
        spaceBefore=5,
        spaceAfter=5,
        leftIndent=20,
        fontName='Helvetica'
    ))

    styles.add(ParagraphStyle(
        name='QuickRefHeader',
        parent=styles['Normal'],
        fontSize=12,
        textColor=Colors.PRIMARY_DARK,
        spaceBefore=15,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='QuickRefItem',
        parent=styles['Normal'],
        fontSize=9,
        textColor=Colors.DARK_GRAY,
        spaceAfter=3,
        leftIndent=10,
        fontName='Helvetica',
        leading=12
    ))

    styles.add(ParagraphStyle(
        name='FooterText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=Colors.LIGHT_GRAY,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        name='WorkflowStep',
        parent=styles['Normal'],
        fontSize=10,
        textColor=Colors.DARK_GRAY,
        leftIndent=25,
        spaceBefore=3,
        spaceAfter=3,
        leading=14
    ))

    styles.add(ParagraphStyle(
        name='WorkflowTitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=Colors.PRIMARY_DARK,
        spaceBefore=15,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    ))

    return styles


# =============================================================================
# PAGE TEMPLATES
# =============================================================================

def create_header_footer(canvas, doc):
    """Add header and footer to each page"""
    canvas.saveState()

    page_width = doc.pagesize[0]
    page_height = doc.pagesize[1]

    # Header line
    canvas.setStrokeColor(Colors.PRIMARY)
    canvas.setLineWidth(2)
    canvas.line(50, page_height - 40, page_width - 50, page_height - 40)

    # Header text
    canvas.setFillColor(Colors.PRIMARY_DARK)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(50, page_height - 35, "Power BI MCP Server")

    canvas.setFillColor(Colors.LIGHT_GRAY)
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(page_width - 50, page_height - 35, "Complete Tools Reference Guide")

    # Footer
    canvas.setStrokeColor(Colors.VERY_LIGHT_GRAY)
    canvas.setLineWidth(1)
    canvas.line(50, 35, page_width - 50, 35)

    # Page number
    canvas.setFillColor(Colors.LIGHT_GRAY)
    canvas.setFont("Helvetica", 9)
    canvas.drawCentredString(page_width / 2, 20, f"Page {doc.page}")

    # Version info
    canvas.setFont("Helvetica", 8)
    canvas.drawString(50, 20, "MCP-PowerBi-Finvision v6.4.1")
    canvas.drawRightString(page_width - 50, 20, f"Generated: {datetime.now().strftime('%B %d, %Y')}")

    canvas.restoreState()


def create_cover_page(canvas, doc):
    """Create the cover page"""
    canvas.saveState()

    page_width = doc.pagesize[0]
    page_height = doc.pagesize[1]

    # Background gradient effect
    steps = 40
    for i in range(steps):
        ratio = i / steps
        r = 0.102 + (0.169 - 0.102) * ratio
        g = 0.212 + (0.424 - 0.212) * ratio
        b = 0.365 + (0.690 - 0.365) * ratio

        canvas.setFillColor(colors.Color(r, g, b))
        y = page_height * i / steps
        canvas.rect(0, y, page_width, page_height/steps + 1, fill=1, stroke=0)

    # Large decorative element
    canvas.setFillColor(colors.Color(1, 1, 1, 0.1))
    canvas.circle(page_width + 100, page_height - 200, 400, fill=1, stroke=0)
    canvas.circle(-100, 200, 300, fill=1, stroke=0)

    # Title area
    canvas.setFillColor(Colors.WHITE)
    canvas.setFont("Helvetica-Bold", 48)
    canvas.drawCentredString(page_width/2, page_height - 250, "Power BI")
    canvas.drawCentredString(page_width/2, page_height - 310, "MCP Server")

    # Subtitle
    canvas.setFont("Helvetica", 24)
    canvas.drawCentredString(page_width/2, page_height - 380, "Complete Tools Reference Guide")

    # Decorative line
    canvas.setStrokeColor(Colors.ACCENT_GOLD)
    canvas.setLineWidth(3)
    canvas.line(page_width/2 - 100, page_height - 410, page_width/2 + 100, page_height - 410)

    # Version badge
    canvas.setFillColor(Colors.ACCENT_GOLD)
    canvas.roundRect(page_width/2 - 80, page_height - 480, 160, 40, 8, fill=1, stroke=0)
    canvas.setFillColor(Colors.PRIMARY_DARK)
    canvas.setFont("Helvetica-Bold", 16)
    canvas.drawCentredString(page_width/2, page_height - 467, "Version 6.4.1")

    # Tool count badge
    canvas.setFillColor(colors.Color(1, 1, 1, 0.2))
    canvas.roundRect(page_width/2 - 100, page_height - 550, 200, 50, 8, fill=1, stroke=0)
    canvas.setFillColor(Colors.WHITE)
    canvas.setFont("Helvetica-Bold", 20)
    canvas.drawCentredString(page_width/2, page_height - 532, "29 Powerful Tools")

    # Categories info
    canvas.setFont("Helvetica", 14)
    canvas.drawCentredString(page_width/2, page_height - 600, "12 Categories | AI-Powered Analysis")

    # Bottom info
    canvas.setFillColor(colors.Color(1, 1, 1, 0.7))
    canvas.setFont("Helvetica", 12)
    canvas.drawCentredString(page_width/2, 100, "Analyze, Modify, and Document Power BI Models")
    canvas.drawCentredString(page_width/2, 80, "Through an AI-Powered Interface")

    # Date
    canvas.setFont("Helvetica", 10)
    canvas.drawCentredString(page_width/2, 50, f"Generated on {datetime.now().strftime('%B %d, %Y')}")

    canvas.restoreState()


# =============================================================================
# TOOL DATA
# =============================================================================

CATEGORIES = [
    {
        "number": "01",
        "title": "Connection",
        "color": Colors.CAT_CONNECTION,
        "description": "Connect to Power BI Desktop instances",
        "tools": [
            {
                "name": "Detect Power BI Instances",
                "id": "detect_powerbi_desktop",
                "description": "Automatically finds all running Power BI Desktop instances on your computer. This is your starting point for any analysis session.",
                "when_to_use": "Use this when you want to see which Power BI files are currently open before connecting to one.",
                "example": "Before starting analysis, run this to see: 'Found 2 instances: Sales Report (modified 10 mins ago), Customer Analysis (modified 2 hours ago)'",
                "parameters": "None required - just run it!",
                "returns": "List of all open Power BI Desktop files with their names and when they were last modified."
            },
            {
                "name": "Connect to Power BI Instance",
                "id": "connect_to_powerbi",
                "description": "Connects to a specific Power BI Desktop file that's currently open on your computer. This establishes the connection needed for all other tools.",
                "when_to_use": "Always use this first before using any other tools. It's like opening the file to work with it.",
                "example": "After detecting instances, connect to the first one (index 0) for the Sales Report, or index 1 for Customer Analysis.",
                "parameters": "model_index (optional, default=0): Which Power BI file to connect to (0 for first, 1 for second, etc.)",
                "returns": "Success message confirming connection to the Power BI model."
            }
        ]
    },
    {
        "number": "02",
        "title": "Schema & Search",
        "color": Colors.CAT_SCHEMA,
        "description": "Search and explore model structure",
        "tools": [
            {
                "name": "Search Objects",
                "id": "search_objects",
                "description": "Searches across all tables, columns, and measures to find objects matching your search term.",
                "when_to_use": "Use when you're looking for something but don't know which table it's in.",
                "example": "Search for 'Revenue' -> Finds: 'Total Revenue' measure, 'Revenue' column in FactSales, 'RevenueGoal' column.",
                "parameters": "search_term (required): What to search for\ntypes (optional): Filter by 'tables', 'columns', 'measures'",
                "returns": "All matching tables, columns, and measures with their locations."
            },
            {
                "name": "Search in Measure Expressions",
                "id": "search_string",
                "description": "Searches inside DAX formulas to find measures that use specific functions or references.",
                "when_to_use": "Use to find all measures that use a specific calculation method or reference another measure.",
                "example": "Search for 'CALCULATE' -> Finds all measures using the CALCULATE function in their DAX code.",
                "parameters": "search_term (required): Text to search for\nsearch_in (optional): 'name', 'expression', or 'both'",
                "returns": "List of measures where the search term appears, with the relevant DAX code."
            },
            {
                "name": "Column Operations",
                "id": "column_operations",
                "description": "Unified interface for all column operations: list, get details, statistics, distribution, create, update, delete columns.",
                "when_to_use": "Use for any column-related task - viewing, analyzing, or modifying columns.",
                "example": "operation='list' table='Sales' -> Lists all columns. operation='statistics' table='Sales' column='Amount' -> Gets stats.",
                "parameters": "operation (required): 'list', 'get', 'statistics', 'distribution', 'create', 'update', 'delete'\ntable (required for most): Table name\ncolumn (required for single-column ops): Column name",
                "returns": "Depends on operation: column list, details, statistics, or operation result."
            },
            {
                "name": "Measure Operations",
                "id": "measure_operations",
                "description": "Unified interface for all measure operations: list, get details, create, update, delete, rename measures.",
                "when_to_use": "Use for any measure-related task - viewing DAX code, creating new measures, or modifying existing ones.",
                "example": "operation='list' -> Lists all measures. operation='get' table='Sales' measure='Total Revenue' -> Gets DAX code.",
                "parameters": "operation (required): 'list', 'get', 'create', 'update', 'delete', 'rename'\ntable (required for most): Table name\nmeasure (required for single-measure ops): Measure name\nexpression (required for create/update): DAX formula",
                "returns": "Depends on operation: measure list, DAX details, or operation result."
            },
            {
                "name": "Relationship Operations",
                "id": "relationship_operations",
                "description": "Unified interface for all relationship operations: list, get, find, create, update, delete relationships between tables.",
                "when_to_use": "Use to understand or modify how tables are connected in the data model.",
                "example": "operation='list' -> Shows all relationships. operation='find' table='Sales' -> Finds relationships involving Sales table.",
                "parameters": "operation (required): 'list', 'get', 'find', 'create', 'update', 'delete'\nfrom_table, from_column, to_table, to_column (for specific relationships)",
                "returns": "Relationship details with cardinality, cross-filter direction, and active status."
            }
        ]
    },
    {
        "number": "03",
        "title": "DAX Intelligence",
        "color": Colors.CAT_DAX,
        "description": "Analyze, debug, and execute DAX",
        "tools": [
            {
                "name": "Execute DAX Query",
                "id": "run_dax",
                "description": "Runs a DAX query against the model and returns the results, just like the DAX query window in Power BI.",
                "when_to_use": "Use to test calculations, preview data, or run analysis queries.",
                "example": "Run: EVALUATE SUMMARIZE(FactSales, DimDate[Year], \"Total\", SUM(FactSales[SalesAmount]))",
                "parameters": "query (required): DAX query (EVALUATE statement)\ntop_n (optional): Limit results",
                "returns": "Query results as a table with columns and rows."
            },
            {
                "name": "Comprehensive DAX Intelligence",
                "id": "dax_intelligence",
                "description": "THE MAIN DAX TOOL - Analyzes DAX measures with validation, debugging, optimization, and recommendations. Includes smart measure finder with fuzzy matching!",
                "when_to_use": "Use whenever you want to understand, debug, or optimize a DAX measure. This is your go-to DAX analysis tool.",
                "example": "Analyze 'Total Revenue' -> Gets: syntax validation, context transitions, performance metrics, optimization suggestions.",
                "parameters": "expression (required): Either DAX code OR just measure name (auto-fetches!)\nanalysis_mode (optional): 'all' (default), 'analyze', 'debug', or 'report'",
                "returns": "Complete DAX analysis with 11 anti-pattern checks, context flow, VertiPaq metrics, and rewritten DAX suggestions."
            },
            {
                "name": "Analyze Measure Dependencies",
                "id": "analyze_measure_dependencies",
                "description": "Shows the complete dependency tree for a measure - what it depends on and what depends on it.",
                "when_to_use": "Use to understand measure relationships before making changes, or to trace calculation logic.",
                "example": "Analyze 'Profit Margin' -> Shows: Depends on 'Total Profit' and 'Total Revenue', with full tree.",
                "parameters": "table (required): Table name\nmeasure (required): Measure name",
                "returns": "Dependency tree showing all referenced measures, columns, and tables in a hierarchical structure."
            },
            {
                "name": "Get Measure Impact Analysis",
                "id": "get_measure_impact",
                "description": "Shows what would be affected if you change or delete this measure (impact analysis).",
                "when_to_use": "Use before modifying or deleting a measure to see what else might break.",
                "example": "Check impact of 'Total Sales' -> Shows: Used by 15 other measures. High impact!",
                "parameters": "table (required): Table name\nmeasure (required): Measure name",
                "returns": "List of all measures, reports, and visuals that reference this measure."
            }
        ]
    },
    {
        "number": "04",
        "title": "Data Sources",
        "color": Colors.CAT_OPERATIONS,
        "description": "View data sources and Power Query expressions",
        "tools": [
            {
                "name": "Get Data Sources",
                "id": "get_data_sources",
                "description": "Lists all data sources connected to the model (SQL databases, Excel files, web sources, etc.).",
                "when_to_use": "Use to understand where the data is coming from.",
                "example": "Returns: 'SQL Server: MyServer\\DB, Excel: C:\\Data\\Budget.xlsx'",
                "parameters": "None required",
                "returns": "List of data sources with connection details."
            },
            {
                "name": "Get Power Query M Expressions",
                "id": "get_m_expressions",
                "description": "Shows the M (Power Query) code that loads and transforms data for each table.",
                "when_to_use": "Use to see how data is being loaded and transformed in Power Query.",
                "example": "Get M for 'FactSales' -> Shows: Source = Sql.Database(\"server\", \"db\"), TransformedData = ...",
                "parameters": "table (optional): Filter by specific table",
                "returns": "Power Query M code for data loading and transformation."
            }
        ]
    },
    {
        "number": "05",
        "title": "Model Analysis",
        "color": Colors.CAT_ANALYSIS,
        "description": "Quick and comprehensive model health checks",
        "tools": [
            {
                "name": "Fast Model Analysis (Simple)",
                "id": "simple_analysis",
                "description": "Quick analysis of the model - runs 8 Microsoft MCP operations to get a complete overview in seconds. Perfect for getting started!",
                "when_to_use": "Use this as your first analysis step to quickly understand the model structure and statistics.",
                "example": "Run simple analysis -> Gets: Database info, model stats (15 tables, 245 measures), all tables, measures, relationships.",
                "parameters": "mode (optional): 'all' (default), 'tables', 'stats', 'measures', 'columns', 'relationships', 'roles', 'database', 'calculation_groups'",
                "returns": "Comprehensive model overview with expert insights. Execution time: ~2-5 seconds."
            },
            {
                "name": "Comprehensive Model Analysis (Full)",
                "id": "full_analysis",
                "description": "Deep analysis with Best Practice Analyzer (120+ rules), performance analysis, and data integrity checks.",
                "when_to_use": "Use for thorough model health check - identifies issues, optimization opportunities, and best practice violations.",
                "example": "Run full analysis -> Finds: 15 best practice violations, 3 performance issues, 2 integrity issues.",
                "parameters": "scope (optional): 'all', 'measures', 'model', 'performance'\ndepth (optional): 'quick', 'balanced', 'thorough'\nmax_seconds (optional): Time limit",
                "returns": "Detailed analysis with categorized issues and recommendations. Execution time: 10-180 seconds."
            }
        ]
    },
    {
        "number": "06",
        "title": "Model Operations",
        "color": Colors.CAT_TMDL,
        "description": "Advanced model operations and automation",
        "tools": [
            {
                "name": "TMDL Operations",
                "id": "tmdl_operations",
                "description": "Unified TMDL operations: export, find & replace, bulk rename, generate scripts. TMDL is the source code format for Power BI models.",
                "when_to_use": "Use for version control, batch updates, or refactoring model objects.",
                "example": "operation='export' output_dir='C:\\TMDL' -> Exports model. operation='find_replace' pattern='OldName' replacement='NewName'",
                "parameters": "operation (required): 'export', 'find_replace', 'bulk_rename', 'generate_script'\noutput_dir, pattern, replacement, renames (depending on operation)\ndry_run (optional): Preview without applying",
                "returns": "Operation results: exported files, matches found, or changes made."
            },
            {
                "name": "Calculation Group Operations",
                "id": "calculation_group_operations",
                "description": "Manage calculation groups (advanced DAX feature for reusable patterns like time intelligence).",
                "when_to_use": "Use to create, list, or delete calculation groups.",
                "example": "operation='list' -> Shows all calculation groups with items. operation='create' name='Time Intel' items=[...]",
                "parameters": "operation (required): 'list', 'list_items', 'create', 'delete'\nname (for create/delete): Group name\nitems (for create): Array of calculation items",
                "returns": "Calculation group details or operation result."
            },
            {
                "name": "Role Operations",
                "id": "role_operations",
                "description": "View Row-Level Security (RLS) and Object-Level Security (OLS) roles.",
                "when_to_use": "Use to see what security roles exist and their filter expressions.",
                "example": "operation='list' -> Shows: 'Regional Manager' role with DAX filters on Country table",
                "parameters": "operation (required): 'list'\nrole (optional): Specific role name",
                "returns": "List of security roles with their table filters and permissions."
            },
            {
                "name": "Batch Operations",
                "id": "batch_operations",
                "description": "Execute multiple operations in a single call - 3-5x faster than individual operations. Supports transaction rollback.",
                "when_to_use": "Use when creating/updating many objects at once for better performance.",
                "example": "Create 10 measures in one call, or update multiple columns at once.",
                "parameters": "operations (required): Array of operation definitions\nuse_transaction (optional): Enable rollback on failure",
                "returns": "Results for each operation with success/failure status."
            },
            {
                "name": "Manage Transactions",
                "id": "manage_transactions",
                "description": "ACID transaction management for model changes - begin, commit, or rollback groups of changes.",
                "when_to_use": "Use for complex changes where you want all-or-nothing behavior.",
                "example": "Begin transaction -> Make changes -> Commit (or Rollback if something fails)",
                "parameters": "action (required): 'begin', 'commit', 'rollback', 'status'",
                "returns": "Transaction status and ID."
            }
        ]
    },
    {
        "number": "07",
        "title": "Export & Schema",
        "color": Colors.CAT_EXPORT,
        "description": "Export model schema and structure",
        "tools": [
            {
                "name": "Get Live Model Schema",
                "id": "get_live_model_schema",
                "description": "Exports a lightweight JSON schema of the model structure - optimized for AI analysis with low token usage.",
                "when_to_use": "Use to get a quick snapshot of the model structure for documentation or analysis.",
                "example": "Export schema -> Returns JSON with: 15 tables, columns, measures, relationships.",
                "parameters": "None required",
                "returns": "Compact JSON schema without DAX expressions, perfect for quick model understanding."
            }
        ]
    },
    {
        "number": "08",
        "title": "Documentation",
        "color": Colors.CAT_DOCS,
        "description": "Generate professional model documentation",
        "tools": [
            {
                "name": "Generate Model Documentation (Word)",
                "id": "generate_model_documentation_word",
                "description": "Creates a comprehensive Word document with complete model documentation: tables, columns, measures, relationships, data sources.",
                "when_to_use": "Use to create professional documentation for sharing with team, stakeholders, or for compliance.",
                "example": "Generate docs -> Creates 45-page Word document with all model details.",
                "parameters": "output_path (optional): Where to save\ninclude_sections (optional): Array of sections to include",
                "returns": "Word document (.docx) with formatted, professional model documentation."
            },
            {
                "name": "Update Model Documentation (Word)",
                "id": "update_model_documentation_word",
                "description": "Updates an existing documentation Word file with current model state (faster than regenerating).",
                "when_to_use": "Use when you already have documentation and just want to refresh it with latest changes.",
                "example": "Update existing docs -> Updates tables section, adds new measures, updates date.",
                "parameters": "document_path (required): Path to existing Word document\nsections_to_update (optional): Which sections",
                "returns": "Updated Word document with current model information."
            }
        ]
    },
    {
        "number": "09",
        "title": "Comparison",
        "color": Colors.CAT_COMPARE,
        "description": "Compare Power BI models side-by-side",
        "tools": [
            {
                "name": "Compare Two Models",
                "id": "compare_pbi_models",
                "description": "Compares two Power BI models side-by-side to find differences (useful for comparing versions or dev vs. prod).",
                "when_to_use": "Use to see what changed between versions or to compare development and production models.",
                "example": "Compare Model A (dev) vs. Model B (prod) -> Shows: 5 new measures, 2 tables added, 12 measures changed.",
                "parameters": "model1_index (required): First model index\nmodel2_index (required): Second model index",
                "returns": "Detailed comparison report with all differences categorized (added, removed, modified)."
            }
        ]
    },
    {
        "number": "10",
        "title": "PBIP Analysis",
        "color": Colors.CAT_PBIP,
        "description": "Offline analysis of Power BI Project files",
        "tools": [
            {
                "name": "Analyze PBIP Repository (Offline)",
                "id": "analyze_pbip_repository",
                "description": "Analyzes a PBIP project folder (the new Power BI project format) and generates an HTML analysis report - works offline without Power BI running.",
                "when_to_use": "Use to analyze PBIP projects stored in Git/version control without opening Power BI Desktop.",
                "example": "Analyze C:\\Projects\\SalesModel.pbip -> Generates interactive HTML report.",
                "parameters": "pbip_folder_path (required): Path to .pbip project folder\noutput_path (optional): Where to save HTML",
                "returns": "Interactive HTML report with model analysis, browsable in any web browser."
            }
        ]
    },
    {
        "number": "11",
        "title": "Hybrid Analysis",
        "color": Colors.CAT_HYBRID,
        "description": "AI-powered comprehensive model analysis",
        "tools": [
            {
                "name": "Export Hybrid Analysis Package",
                "id": "export_hybrid_analysis",
                "description": "Exports a complete package combining: TMDL files + metadata + sample data from active model. Perfect for AI analysis!",
                "when_to_use": "Use to create a complete offline analysis package that includes structure, metadata, and actual sample data.",
                "example": "Export Sales model -> Creates folder with: TMDL files, metadata JSON, sample data parquet files.",
                "parameters": "pbip_folder_path (required): Path to .SemanticModel folder\noutput_dir (optional): Where to save\nsample_rows (optional, default 1000)",
                "returns": "Complete package folder with TMDL, JSON metadata, and Parquet sample data files."
            },
            {
                "name": "Analyze Hybrid Model",
                "id": "analyze_hybrid_model",
                "description": "BI EXPERT ANALYSIS - Automatically reads exported package and provides comprehensive AI-powered analysis with recommendations. Supports fuzzy search!",
                "when_to_use": "Use for the most comprehensive AI-powered model analysis - it reads EVERYTHING internally. Just point it at the analysis folder!",
                "example": "Analyze exported package -> Provides: Model structure analysis, DAX recommendations, data quality insights, optimization opportunities.",
                "parameters": "analysis_path (required): Path to exported analysis folder\noperation (required): 'smart_analyze'\nintent (optional): Natural language question for fuzzy search",
                "returns": "Comprehensive BI Expert analysis with structure insights, DAX recommendations, data quality analysis, and action items."
            }
        ]
    },
    {
        "number": "12",
        "title": "Help & Monitoring",
        "color": Colors.CAT_HELP,
        "description": "Built-in documentation and usage statistics",
        "tools": [
            {
                "name": "Show User Guide",
                "id": "show_user_guide",
                "description": "Displays comprehensive user guide with examples, best practices, and tool usage instructions.",
                "when_to_use": "Use whenever you need help or want to learn about specific features.",
                "example": "Show user guide -> Returns: Full documentation with categories, descriptions, examples.",
                "parameters": "section (optional): Specific section to show",
                "returns": "User guide with usage instructions and examples."
            },
            {
                "name": "Get Token Usage Statistics",
                "id": "get_token_usage",
                "description": "Shows token usage statistics for your session - helps monitor API costs and usage patterns.",
                "when_to_use": "Use to track how many tokens your analysis has consumed.",
                "example": "Get stats -> Shows: Total tokens used, tokens per tool, session duration.",
                "parameters": "None required",
                "returns": "Token usage breakdown by tool and total session statistics."
            }
        ]
    }
]

WORKFLOWS = [
    {
        "title": "First-Time Model Analysis",
        "description": "Get started with any new Power BI model",
        "steps": [
            ("detect_powerbi_desktop", "Find your model"),
            ("connect_to_powerbi", "Connect to it"),
            ("simple_analysis", "Quick overview (2-5 seconds)"),
            ("full_analysis", "Deep health check (optional)"),
            ("generate_model_documentation_word", "Create documentation")
        ]
    },
    {
        "title": "Analyze and Optimize DAX Measure",
        "description": "Debug and improve measure performance",
        "steps": [
            ("measure_operations (list)", "Find your measure"),
            ("dax_intelligence", "Analyze it (auto-fetches by name!)"),
            ("Review suggestions", "Validation, performance, optimizations"),
            ("measure_operations (update)", "Apply optimizations"),
            ("analyze_measure_dependencies", "Check what depends on it")
        ]
    },
    {
        "title": "Complete AI-Powered Analysis",
        "description": "The most powerful analysis workflow",
        "steps": [
            ("export_hybrid_analysis", "Export complete package"),
            ("analyze_hybrid_model", "AI analyzes EVERYTHING"),
            ("Review insights", "Structure, DAX, data quality, optimization"),
            ("Use fuzzy search", "\"show me revenue measures\"")
        ]
    },
    {
        "title": "Compare Dev vs Production",
        "description": "Find differences between model versions",
        "steps": [
            ("detect_powerbi_desktop", "Find both models"),
            ("connect_to_powerbi", "Connect to first (index=0)"),
            ("compare_pbi_models", "Compare them"),
            ("Review differences", "Added, removed, modified objects")
        ]
    },
    {
        "title": "Refactor Model Safely",
        "description": "Rename objects with automatic reference updates",
        "steps": [
            ("tmdl_operations (export)", "Export current model as TMDL"),
            ("tmdl_operations (bulk_rename)", "Rename objects (updates all references!)"),
            ("Apply TMDL", "Apply TMDL back to model")
        ]
    }
]


# =============================================================================
# DOCUMENT BUILDER
# =============================================================================

def build_document():
    """Build the complete PDF document"""

    output_path = r"C:\Users\bjorn.braet\powerbi-mcp-servers\MCP-PowerBi-Finvision\MCP_PowerBI_Tools_Guide_Professional.pdf"

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=60,
        bottomMargin=50
    )

    styles = create_styles()
    story = []

    # ==========================================================================
    # COVER PAGE (handled separately)
    # ==========================================================================
    story.append(PageBreak())

    # ==========================================================================
    # WELCOME PAGE
    # ==========================================================================
    story.append(Spacer(1, 30))
    story.append(Paragraph("Welcome to the Power BI MCP Server Tools Guide!", styles['SectionHeader']))
    story.append(Spacer(1, 10))

    welcome_text = """
    This comprehensive guide explains all <b>29 tools</b> available in the MCP-PowerBi-Finvision server.
    These tools allow you to analyze, modify, and document Power BI models through an AI-powered interface.
    """
    story.append(Paragraph(welcome_text, styles['CustomBodyText']))
    story.append(Spacer(1, 15))

    # What is MCP box
    mcp_text = """
    <b>What is an MCP Server?</b><br/><br/>
    MCP (Model Context Protocol) is a way for AI assistants to access specialized tools.
    This server provides tools specifically designed for working with Power BI Desktop models,
    enabling seamless integration between AI capabilities and your data modeling workflow.
    """
    story.append(Paragraph(mcp_text, styles['InfoBox']))
    story.append(Spacer(1, 15))

    # How to read this guide
    story.append(Paragraph("How to Read This Guide", styles['SubheadingBlue']))
    guide_items = [
        "Each tool has a clear description of what it does",
        "\"When to Use\" explains the situations where you'd use this tool",
        "Examples show real-world usage scenarios",
        "Parameters list what information you need to provide",
        "Results explain what you get back"
    ]
    for item in guide_items:
        story.append(Paragraph(f"<bullet>&bull;</bullet> {item}", styles['CustomBodyText']))

    story.append(Spacer(1, 15))

    # Getting started tip
    tip_text = """
    <b>Getting Started:</b><br/>
    1. Always start by connecting to a Power BI instance (Category 01)<br/>
    2. Use the analysis tools (Category 05) to understand the model<br/>
    3. Then use specific tools based on what you need to do
    """
    story.append(Paragraph(tip_text, styles['TipBox']))

    story.append(PageBreak())

    # ==========================================================================
    # TABLE OF CONTENTS
    # ==========================================================================
    story.append(Paragraph("Table of Contents", styles['SectionHeader']))
    story.append(Spacer(1, 20))

    # Create TOC table
    toc_data = []
    for cat in CATEGORIES:
        color_box = f'<font color="#{cat["color"].hexval()[2:]}">\u25A0</font>'
        toc_data.append([
            Paragraph(f'{color_box} <b>{cat["number"]} - {cat["title"]}</b>', styles['TOCEntry']),
            Paragraph(cat["description"], styles['TOCEntry'])
        ])

    toc_table = Table(toc_data, colWidths=[200, 280])
    toc_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, Colors.VERY_LIGHT_GRAY),
    ]))
    story.append(toc_table)

    story.append(PageBreak())

    # ==========================================================================
    # QUICK REFERENCE GUIDE
    # ==========================================================================
    story.append(Paragraph("Quick Reference Guide", styles['SectionHeader']))
    story.append(Paragraph("Most Commonly Used Tools", styles['SubheadingBlue']))
    story.append(Spacer(1, 10))

    quick_ref_sections = [
        {
            "title": "Connection (Always First!)",
            "color": Colors.CAT_CONNECTION,
            "tools": [
                ("detect_powerbi_desktop", "Find open Power BI files"),
                ("connect_to_powerbi", "Connect to one")
            ]
        },
        {
            "title": "Quick Model Overview",
            "color": Colors.CAT_ANALYSIS,
            "tools": [
                ("simple_analysis", "Fast 2-5 second overview"),
                ("column_operations", "List columns"),
                ("measure_operations", "List measures")
            ]
        },
        {
            "title": "Deep Analysis",
            "color": Colors.CAT_DAX,
            "tools": [
                ("full_analysis", "Complete health check (120+ rules)"),
                ("dax_intelligence", "Analyze and optimize DAX")
            ]
        },
        {
            "title": "Making Changes",
            "color": Colors.CAT_OPERATIONS,
            "tools": [
                ("measure_operations", "Create/update measures"),
                ("batch_operations", "Batch changes"),
                ("tmdl_operations", "Rename objects safely")
            ]
        },
        {
            "title": "Documentation",
            "color": Colors.CAT_DOCS,
            "tools": [
                ("generate_model_documentation_word", "Professional Word doc"),
                ("get_live_model_schema", "Export model schema")
            ]
        },
        {
            "title": "AI Analysis (Most Powerful!)",
            "color": Colors.CAT_HYBRID,
            "tools": [
                ("export_hybrid_analysis", "Export complete package"),
                ("analyze_hybrid_model", "AI BI Expert analysis")
            ]
        }
    ]

    for section in quick_ref_sections:
        # Section header with colored bar
        header_data = [[
            Paragraph(f'<font color="#{section["color"].hexval()[2:]}">\u25A0\u25A0</font> <b>{section["title"]}</b>', styles['QuickRefHeader'])
        ]]
        header_table = Table(header_data, colWidths=[480])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(header_table)

        for tool_id, desc in section["tools"]:
            story.append(Paragraph(f"<bullet>&bull;</bullet> <font face='Courier' size='9'>{tool_id}</font> - {desc}", styles['QuickRefItem']))

        story.append(Spacer(1, 5))

    story.append(PageBreak())

    # ==========================================================================
    # TOOL CATEGORIES
    # ==========================================================================
    for cat in CATEGORIES:
        # Category header
        cat_header_data = [[
            Paragraph(f'<font color="white"><b>{cat["number"]} - {cat["title"]}</b></font>',
                     ParagraphStyle('CatHeader', fontSize=18, textColor=Colors.WHITE, fontName='Helvetica-Bold'))
        ]]
        cat_header_table = Table(cat_header_data, colWidths=[490])
        cat_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), cat["color"]),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('ROUNDEDCORNERS', [8, 8, 8, 8]),
        ]))
        story.append(cat_header_table)
        story.append(Spacer(1, 15))

        # Tools in this category
        for tool in cat["tools"]:
            # Tool card
            tool_elements = []

            # Tool name and ID
            tool_elements.append(Paragraph(f'<font color="#{cat["color"].hexval()[2:]}">\u25A0</font> <b>{tool["name"]}</b>', styles['ToolName']))
            tool_elements.append(Paragraph(f'({tool["id"]})', styles['ToolID']))

            # Description
            tool_elements.append(Paragraph(f'<b>What it does:</b> {tool["description"]}', styles['ToolDescription']))

            # When to use
            tool_elements.append(Paragraph('<b>When to use this tool:</b>', styles['SubheadingBlue']))
            tool_elements.append(Paragraph(tool["when_to_use"], styles['CustomBodyText']))

            # Example - add spacer to prevent overlap with example box
            tool_elements.append(Spacer(1, 8))
            tool_elements.append(Paragraph('<b>Example:</b>', styles['SubheadingBlue']))
            tool_elements.append(Spacer(1, 4))
            tool_elements.append(Paragraph(tool["example"], styles['ExampleText']))

            # Parameters
            tool_elements.append(Paragraph('<b>Parameters:</b>', styles['SubheadingBlue']))
            for param_line in tool["parameters"].split('\n'):
                tool_elements.append(Paragraph(f"<bullet>&bull;</bullet> {param_line}", styles['ParameterText']))

            # Returns
            tool_elements.append(Paragraph('<b>What you get back:</b>', styles['SubheadingBlue']))
            tool_elements.append(Paragraph(tool["returns"], styles['CustomBodyText']))

            # Wrap tool in a bordered table for card effect
            tool_table_data = [[tool_elements]]
            tool_table = Table([[Spacer(1, 1)]], colWidths=[5])

            # Create the tool card
            card_content = []
            for elem in tool_elements:
                card_content.append(elem)

            tool_card_data = [[card_content]]
            tool_card = Table(tool_card_data, colWidths=[475])
            tool_card.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), Colors.WHITE),
                ('BOX', (0, 0), (-1, -1), 1, Colors.VERY_LIGHT_GRAY),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                ('ROUNDEDCORNERS', [6, 6, 6, 6]),
            ]))

            # Keep tool card together
            story.append(KeepTogether(card_content + [Spacer(1, 15)]))

        story.append(PageBreak())

    # ==========================================================================
    # COMMON WORKFLOWS
    # ==========================================================================
    story.append(Paragraph("Common Workflows", styles['SectionHeader']))
    story.append(Paragraph("Step-by-step guides for common tasks", styles['SubheadingBlue']))
    story.append(Spacer(1, 15))

    for i, workflow in enumerate(WORKFLOWS, 1):
        # Workflow header
        wf_header = Paragraph(f'<b>Workflow {i}: {workflow["title"]}</b>', styles['WorkflowTitle'])
        wf_desc = Paragraph(workflow["description"], styles['CustomBodyText'])

        story.append(wf_header)
        story.append(wf_desc)

        # Steps
        for j, (tool, desc) in enumerate(workflow["steps"], 1):
            step_text = f"<b>{j}.</b> <font face='Courier' size='9'>{tool}</font> - {desc}"
            story.append(Paragraph(step_text, styles['WorkflowStep']))

        story.append(Spacer(1, 15))

    story.append(PageBreak())

    # ==========================================================================
    # TIPS FOR SUCCESS
    # ==========================================================================
    story.append(Paragraph("Tips for Success", styles['SectionHeader']))
    story.append(Spacer(1, 10))

    tips = [
        ("Always connect first", "Use detect_powerbi_desktop and connect_to_powerbi before any other tools"),
        ("Start simple", "Use simple_analysis before full_analysis - it's faster and often sufficient"),
        ("Smart measure finder", "The dax_intelligence tool has smart measure finder - just type the measure name!"),
        ("Preview first", "Use dry_run=true when testing changes (previews without applying)"),
        ("Document regularly", "Export documentation regularly for team sharing"),
        ("AI-powered insights", "Use hybrid analysis tools for the most comprehensive AI-powered insights")
    ]

    for title, desc in tips:
        tip_para = Paragraph(f'<font color="#{Colors.ACCENT_GREEN.hexval()[2:]}">\u2713</font> <b>{title}:</b> {desc}', styles['CustomBodyText'])
        story.append(tip_para)
        story.append(Spacer(1, 5))

    story.append(Spacer(1, 20))

    # Getting help box
    help_text = """
    <b>Getting Help:</b><br/><br/>
    - Use tool <font face='Courier'>show_user_guide</font> for built-in help<br/>
    - All tools include detailed error messages to guide you<br/>
    - Check the GitHub repository for updates and support
    """
    story.append(Paragraph(help_text, styles['InfoBox']))

    # ==========================================================================
    # BUILD PDF
    # ==========================================================================

    def first_page(canvas, doc):
        create_cover_page(canvas, doc)

    def later_pages(canvas, doc):
        create_header_footer(canvas, doc)

    doc.build(story, onFirstPage=first_page, onLaterPages=later_pages)

    print(f"\nPDF generated successfully!")
    print(f"Output: {output_path}")
    return output_path


if __name__ == "__main__":
    build_document()
