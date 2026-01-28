"""
MCP-PowerBI-Finvision User Guide PDF Generator
Generates a professional PDF documentation with icons, visual examples and flow diagrams.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas
import os

# Colors - Power BI inspired
PRIMARY_BLUE = colors.HexColor('#0078D4')
SECONDARY_BLUE = colors.HexColor('#106EBE')
DARK_BLUE = colors.HexColor('#004578')
ACCENT_YELLOW = colors.HexColor('#FFB900')
ACCENT_ORANGE = colors.HexColor('#FF8C00')
TEXT_DARK = colors.HexColor('#323130')
TEXT_LIGHT = colors.HexColor('#605E5C')
BG_LIGHT = colors.HexColor('#F3F2F1')
BG_LIGHTER = colors.HexColor('#FAF9F8')
SUCCESS_GREEN = colors.HexColor('#107C10')
WARNING_RED = colors.HexColor('#D13438')
BORDER_COLOR = colors.HexColor('#E1DFDD')
PURPLE = colors.HexColor('#8764B8')

# Icons using standard PDF-safe characters
# These characters render correctly in Helvetica/standard fonts
ICONS = {
    'connection': chr(0x25BA),   # ►
    'model': chr(0x25A0),        # ■
    'batch': chr(0x25CF),        # ●
    'search': chr(0x25B6),       # ▶
    'brain': chr(0x2605),        # ★
    'analysis': chr(0x25B2),     # ▲
    'folder': chr(0x25A0),       # ■
    'docs': chr(0x25CF),         # ●
    'debug': chr(0x25C6),        # ◆
    'help': chr(0x25CB),         # ○
    'tip': chr(0x2605),          # ★
    'success': chr(0x2713),      # ✓
    'warning': chr(0x25B2),      # ▲
    'arrow': chr(0x25BA),        # ►
    'check': chr(0x2022),        # •
    'star': chr(0x2605),         # ★
    'rocket': chr(0x25BA),       # ►
    'gear': chr(0x25CF),         # ●
    'lightning': chr(0x25C6),    # ◆
    'target': chr(0x25CF),       # ●
    'clock': chr(0x25CB),        # ○
    'chart': chr(0x25B2),        # ▲
    'key': chr(0x25BA),          # ►
    'lock': chr(0x25A0),         # ■
    'sync': chr(0x25CF),         # ●
    'magic': chr(0x2605),        # ★
    'future': chr(0x25BA),       # ►
}


def create_styles():
    """Create custom paragraph styles."""
    styles = getSampleStyleSheet()

    # Cover title
    styles.add(ParagraphStyle(
        name='CoverTitle',
        parent=styles['Heading1'],
        fontSize=36,
        textColor=PRIMARY_BLUE,
        alignment=TA_CENTER,
        spaceAfter=8,
        fontName='Helvetica-Bold',
        leading=42
    ))

    # Cover subtitle
    styles.add(ParagraphStyle(
        name='CoverSubtitle',
        parent=styles['Normal'],
        fontSize=16,
        textColor=TEXT_LIGHT,
        alignment=TA_CENTER,
        spaceAfter=30,
        fontName='Helvetica'
    ))

    # Section heading with icon space
    styles.add(ParagraphStyle(
        name='SectionHeading',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=PRIMARY_BLUE,
        spaceBefore=25,
        spaceAfter=12,
        fontName='Helvetica-Bold',
        leading=28
    ))

    # Subsection heading
    styles.add(ParagraphStyle(
        name='SubsectionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=DARK_BLUE,
        spaceBefore=18,
        spaceAfter=8,
        fontName='Helvetica-Bold',
        leading=18
    ))

    # Tool name heading
    styles.add(ParagraphStyle(
        name='ToolHeading',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=PRIMARY_BLUE,
        spaceBefore=12,
        spaceAfter=6,
        fontName='Helvetica-Bold',
        leading=14
    ))

    # Body text
    styles.add(ParagraphStyle(
        name='Body',
        parent=styles['Normal'],
        fontSize=10,
        textColor=TEXT_DARK,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        leading=14
    ))

    # Info box text
    styles.add(ParagraphStyle(
        name='InfoBox',
        parent=styles['Normal'],
        fontSize=10,
        textColor=TEXT_DARK,
        alignment=TA_LEFT,
        spaceAfter=4,
        leading=14
    ))

    # Code style
    styles.add(ParagraphStyle(
        name='CodeBlock',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Courier',
        textColor=TEXT_DARK,
        backColor=BG_LIGHT,
        leftIndent=8,
        rightIndent=8,
        spaceBefore=4,
        spaceAfter=4,
        leading=12
    ))

    # TOC style
    styles.add(ParagraphStyle(
        name='TOCEntry',
        parent=styles['Normal'],
        fontSize=12,
        textColor=TEXT_DARK,
        spaceBefore=10,
        leftIndent=15,
        leading=16
    ))

    # Bullet style
    styles.add(ParagraphStyle(
        name='BulletItem',
        parent=styles['Normal'],
        fontSize=10,
        textColor=TEXT_DARK,
        leftIndent=15,
        spaceBefore=2,
        spaceAfter=2,
        leading=13
    ))

    # Example style
    styles.add(ParagraphStyle(
        name='Example',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Oblique',
        textColor=SECONDARY_BLUE,
        leftIndent=15,
        spaceAfter=3,
        leading=12
    ))

    # Small text
    styles.add(ParagraphStyle(
        name='Small',
        parent=styles['Normal'],
        fontSize=8,
        textColor=TEXT_LIGHT,
        leading=10
    ))

    # Category header
    styles.add(ParagraphStyle(
        name='CategoryHeader',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.white,
        spaceBefore=15,
        spaceAfter=8,
        fontName='Helvetica-Bold',
        leading=16
    ))

    return styles


def create_icon_header(icon, text, styles, color=PRIMARY_BLUE):
    """Create a section header - icon parameter kept for compatibility but not used."""
    return Paragraph(
        f'<font color="{color.hexval()}">{text}</font>',
        styles['SectionHeading']
    )


def create_category_banner(icon, title, description, color=PRIMARY_BLUE):
    """Create a colored category banner. Icon parameter kept for compatibility but not shown."""
    data = [[
        Paragraph(f'<b><font color="white">{title}</font></b><br/>'
                  f'<font color="white" size="9">{description}</font>',
                  ParagraphStyle('BannerText', fontSize=11, textColor=colors.white, leading=14))
    ]]

    table = Table(data, colWidths=[6.3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))
    return table


def create_info_box(content, box_type='info', styles=None):
    """Create a styled info box."""
    if box_type == 'tip':
        bg_color = colors.HexColor('#FFF8E1')
        border_color = ACCENT_YELLOW
        title = "TIP"
    elif box_type == 'success':
        bg_color = colors.HexColor('#E8F5E9')
        border_color = SUCCESS_GREEN
        title = "NOTE"
    elif box_type == 'warning':
        bg_color = colors.HexColor('#FFF3E0')
        border_color = ACCENT_ORANGE
        title = "IMPORTANT"
    elif box_type == 'example':
        bg_color = colors.HexColor('#E3F2FD')
        border_color = SECONDARY_BLUE
        title = "EXAMPLE"
    else:  # info
        bg_color = colors.HexColor('#E3F2FD')
        border_color = PRIMARY_BLUE
        title = "INFO"

    # Build content with styled header
    inner_content = f'<b><font color="{border_color.hexval()}">{title}</font></b><br/><br/>{content}'

    data = [[Paragraph(inner_content, styles['InfoBox'] if styles else
                       ParagraphStyle('InfoBox', fontSize=10, leading=14))]]

    table = Table(data, colWidths=[6.3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_color),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LINEBEFORE', (0, 0), (0, -1), 4, border_color),
    ]))
    return table


def create_flow_diagram(steps, title=None):
    """Create a visual flow diagram with styled boxes."""
    elements = []

    if title:
        elements.append(Paragraph(
            f'<b><font color="{DARK_BLUE.hexval()}">{title}</font></b>',
            ParagraphStyle('FlowTitle', fontSize=10, spaceBefore=8, spaceAfter=6)
        ))

    # Build flow cells with arrows
    ARROW_CHAR = chr(0x2192)  # → rightward arrow
    flow_cells = []
    for i, step in enumerate(steps):
        flow_cells.append(('step', step))
        if i < len(steps) - 1:
            flow_cells.append(('arrow', f'<font color="{PRIMARY_BLUE.hexval()}" size="14">{ARROW_CHAR}</font>'))

    # Calculate widths
    step_width = 1.2*inch
    arrow_width = 0.35*inch

    col_widths = []
    for cell_type, _ in flow_cells:
        if cell_type == 'arrow':
            col_widths.append(arrow_width)
        else:
            col_widths.append(step_width)

    # Create paragraphs for cells
    styled_cells = []
    for cell_type, cell_content in flow_cells:
        if cell_type == 'arrow':
            styled_cells.append(Paragraph(cell_content, ParagraphStyle('Arrow', alignment=TA_CENTER, fontSize=14)))
        else:
            styled_cells.append(Paragraph(
                f'<font size="8"><b>{cell_content}</b></font>',
                ParagraphStyle('StepBox', alignment=TA_CENTER, fontSize=8, leading=10)
            ))

    flow_table = Table([styled_cells], colWidths=col_widths)

    # Style the table
    style_commands = [
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]

    # Add box styling to step cells (not arrows)
    for i, (cell_type, _) in enumerate(flow_cells):
        if cell_type != 'arrow':
            style_commands.extend([
                ('BOX', (i, 0), (i, 0), 1.5, PRIMARY_BLUE),
                ('BACKGROUND', (i, 0), (i, 0), BG_LIGHTER),
                ('LEFTPADDING', (i, 0), (i, 0), 4),
                ('RIGHTPADDING', (i, 0), (i, 0), 4),
            ])

    flow_table.setStyle(TableStyle(style_commands))
    elements.append(flow_table)
    elements.append(Spacer(1, 8))

    return elements


def create_conversation_example(user_says, claude_does, result=None, styles=None):
    """Create a styled conversation example."""
    content_parts = [
        f'<font color="{SECONDARY_BLUE.hexval()}"><b>You:</b></font> "{user_says}"',
        f'<br/><br/><font color="{SUCCESS_GREEN.hexval()}"><b>Claude:</b></font> {claude_does}'
    ]
    if result:
        content_parts.append(f'<br/><br/><font color="{TEXT_LIGHT.hexval()}"><b>Result:</b></font> {result}')

    content = "".join(content_parts)

    data = [[Paragraph(content, styles['InfoBox'])]]
    table = Table(data, colWidths=[6.3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHTER),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
    ]))
    return table


def create_tool_card(tool_name, description, operations=None, examples=None,
                     conversation_examples=None, flow_steps=None, styles=None):
    """Create a styled tool card."""
    elements = []

    # Tool name with icon
    elements.append(Paragraph(
        f'<font color="{PRIMARY_BLUE.hexval()}"><b>{tool_name}</b></font>',
        styles['ToolHeading']
    ))

    # Description
    elements.append(Paragraph(description, styles['Body']))

    # Visual flow diagram if provided
    if flow_steps:
        elements.extend(create_flow_diagram(flow_steps))

    # Operations in a nice table
    if operations:
        elements.append(Spacer(1, 4))
        op_data = []
        for op_name, op_desc in operations:
            op_data.append([
                Paragraph(f'<font name="Courier" color="{PRIMARY_BLUE.hexval()}" size="9">{op_name}</font>',
                         ParagraphStyle('OpName', fontSize=9)),
                Paragraph(f'<font size="9">{op_desc}</font>',
                         ParagraphStyle('OpDesc', fontSize=9))
            ])

        if op_data:
            op_table = Table(op_data, colWidths=[1.5*inch, 4.8*inch])
            op_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('BACKGROUND', (0, 0), (0, -1), BG_LIGHTER),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_COLOR),
            ]))
            elements.append(op_table)

    # Conversation examples
    if conversation_examples:
        elements.append(Spacer(1, 6))
        for ex in conversation_examples[:2]:
            elements.append(create_conversation_example(
                ex.get('user', ''),
                ex.get('claude', ''),
                ex.get('result', None),
                styles
            ))
            elements.append(Spacer(1, 4))

    # Simple examples
    elif examples:
        elements.append(Spacer(1, 4))
        for example in examples[:3]:
            elements.append(Paragraph(
                f'<font color="{SECONDARY_BLUE.hexval()}" size="9">"{example}"</font>',
                styles['Example']
            ))

    elements.append(Spacer(1, 10))
    return elements


def create_feature_grid(features, styles):
    """Create a 2-column feature grid. Features can be (icon, title, desc) or (title, desc)."""
    rows = []
    for i in range(0, len(features), 2):
        row = []
        for j in range(2):
            if i + j < len(features):
                feat = features[i + j]
                if len(feat) == 3:
                    _, title, desc = feat  # Ignore icon
                else:
                    title, desc = feat
                cell_content = Paragraph(
                    f'<b><font color="{DARK_BLUE.hexval()}">{title}</font></b><br/>'
                    f'<font size="9" color="{TEXT_LIGHT.hexval()}">{desc}</font>',
                    ParagraphStyle('FeatureCell', fontSize=10, alignment=TA_CENTER, leading=14)
                )
                row.append(cell_content)
            else:
                row.append('')
        rows.append(row)

    table = Table(rows, colWidths=[3.15*inch, 3.15*inch])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('BOX', (0, 0), (0, -1), 1, BORDER_COLOR),
        ('BOX', (1, 0), (1, -1), 1, BORDER_COLOR),
        ('LINEBELOW', (0, 0), (-1, -2), 1, BORDER_COLOR),
    ]))
    return table


def build_pdf():
    """Build the complete PDF document."""
    output_path = os.path.join(os.path.dirname(__file__), 'MCP-PowerBI-Finvision-User-Guide.pdf')

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=0.6*inch,
        leftMargin=0.6*inch,
        topMargin=0.6*inch,
        bottomMargin=0.6*inch
    )

    styles = create_styles()
    elements = []

    # ========== COVER PAGE ==========
    elements.append(Spacer(1, 1.2*inch))

    # Decorative line
    elements.append(HRFlowable(width="40%", thickness=3, color=PRIMARY_BLUE, spaceBefore=0, spaceAfter=20))

    elements.append(Paragraph("MCP-PowerBI-Finvision", styles['CoverTitle']))
    elements.append(Paragraph("AI-Powered Power BI Analysis Server", styles['CoverSubtitle']))

    # Version badge
    version_data = [[Paragraph(
        f'<font color="{TEXT_DARK.hexval()}"><b>Version 7.7+</b>  |  User Guide</font>',
        ParagraphStyle('Version', fontSize=11, alignment=TA_CENTER)
    )]]
    version_table = Table(version_data, colWidths=[3*inch])
    version_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(version_table)

    elements.append(Spacer(1, 0.6*inch))

    # Tagline
    elements.append(Paragraph(
        f'<i><font color="{TEXT_LIGHT.hexval()}">"Unlock the full potential of your Power BI models with AI assistance"</font></i>',
        ParagraphStyle('Tagline', fontSize=12, alignment=TA_CENTER)
    ))

    elements.append(Spacer(1, 0.6*inch))

    # Key features preview - clean colored boxes without icons
    feature_items = [
        ("50+ Tools", PRIMARY_BLUE),
        ("DAX Intelligence", SECONDARY_BLUE),
        ("Best Practices", SUCCESS_GREEN),
        ("Auto Docs", PURPLE),
    ]

    preview_cells = []
    for label, color in feature_items:
        cell_para = Paragraph(
            f'<font size="10" color="white"><b>{label}</b></font>',
            ParagraphStyle('FeatureBox', alignment=TA_CENTER)
        )
        preview_cells.append(cell_para)

    preview_table = Table([preview_cells], colWidths=[1.4*inch]*4)
    preview_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('BACKGROUND', (0, 0), (0, 0), PRIMARY_BLUE),
        ('BACKGROUND', (1, 0), (1, 0), SECONDARY_BLUE),
        ('BACKGROUND', (2, 0), (2, 0), SUCCESS_GREEN),
        ('BACKGROUND', (3, 0), (3, 0), PURPLE),
    ]))
    elements.append(preview_table)

    elements.append(Spacer(1, 0.8*inch))

    # What's inside summary
    inside_content = Paragraph(
        f'<font color="{TEXT_DARK.hexval()}" size="10">'
        f'<b>What\'s Inside:</b> Learn how to leverage AI to analyze Power BI models, '
        f'write DAX measures, debug visuals, optimize performance, and generate documentation - '
        f'all through natural language conversations.</font>',
        ParagraphStyle('Inside', alignment=TA_CENTER, leading=14)
    )
    inside_table = Table([[inside_content]], colWidths=[5.5*inch])
    inside_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHTER),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
    ]))
    elements.append(inside_table)

    elements.append(PageBreak())

    # ========== TABLE OF CONTENTS ==========
    elements.append(Paragraph(
        f'<font color="{PRIMARY_BLUE.hexval()}"><b>Table of Contents</b></font>',
        styles['SectionHeading']
    ))
    elements.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_BLUE, spaceBefore=5, spaceAfter=15))

    toc_items = [
        ("1", "Why Claude?", "AI capabilities, connectors & strengths"),
        ("2", "What is MCP?", "Understanding the Model Context Protocol"),
        ("3", "What is MCP-PowerBI-Finvision?", "Your AI-powered Power BI companion"),
        ("4", "Getting Started", "Installation and first connection"),
        ("5", "Tools Overview", "50+ tools across 10 categories"),
        ("6", "Complete Tool Reference", "Detailed tool documentation"),
        ("7", "Common Workflows", "Step-by-step guides"),
        ("8", "Tips & Best Practices", "Get the most out of MCP"),
        ("9", "Beyond Power BI", "VS Code, Fabric, PySpark & more"),
        ("10", "The Future: Fabric MCP", "What's coming next"),
    ]

    toc_data = []
    for num, title, desc in toc_items:
        toc_data.append([
            Paragraph(f'<b><font color="{PRIMARY_BLUE.hexval()}">{num}</font></b>',
                     ParagraphStyle('TocNum', fontSize=12, alignment=TA_CENTER)),
            Paragraph(f'<b>{title}</b><br/><font size="8" color="{TEXT_LIGHT.hexval()}">{desc}</font>',
                     ParagraphStyle('TocTitle', fontSize=11, leading=14))
        ])

    toc_table = Table(toc_data, colWidths=[0.4*inch, 5.5*inch])
    toc_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_COLOR),
    ]))
    elements.append(toc_table)

    elements.append(PageBreak())

    # ========== SECTION 1: WHY CLAUDE? ==========
    elements.append(create_icon_header(ICONS['star'], "1. Why Claude?", styles))
    elements.append(HRFlowable(width="100%", thickness=2, color=BORDER_COLOR, spaceBefore=5, spaceAfter=15))

    elements.append(create_info_box(
        "<b>Claude</b> is Anthropic's most capable AI assistant, built on cutting-edge research in AI safety "
        "and helpfulness. It combines deep technical knowledge with nuanced understanding, making it an ideal "
        "partner for complex analytical and development tasks across any domain.",
        'info', styles
    ))
    elements.append(Spacer(1, 15))

    # Key Strengths
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">Claude\'s Key Strengths</font></b>',
        styles['SubsectionHeading']
    ))

    strengths = [
        ("Advanced Reasoning", "Breaks down complex problems into logical steps, handles multi-step analysis, and provides clear explanations of its thinking"),
        ("Extended Context", "Processes up to 200K tokens - entire codebases, long documents, or complex datasets in a single conversation"),
        ("Code Excellence", "Writes production-quality code in 20+ languages including Python, TypeScript, SQL, DAX, and more with best practices built-in"),
        ("Learning Partner", "Explains concepts at any level, teaches patterns, and helps you grow your skills while solving real problems"),
    ]
    elements.append(create_feature_grid(strengths, styles))

    elements.append(Spacer(1, 15))

    # General Capabilities section
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">What Claude Can Do</font></b>',
        styles['SubsectionHeading']
    ))

    capabilities = [
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Software Development</b> - Write, debug, refactor, and review code across any language or framework',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Data Analysis</b> - Analyze datasets, write queries, create visualizations, and extract insights',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Technical Writing</b> - Generate documentation, API specs, architecture diagrams, and technical guides',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Problem Solving</b> - Debug issues, optimize performance, design systems, and plan implementations',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Research & Learning</b> - Explain complex topics, summarize papers, and answer technical questions',
    ]
    for cap in capabilities:
        elements.append(Paragraph(cap, styles['BulletItem']))

    elements.append(Spacer(1, 15))

    # Available Interfaces
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">Ways to Use Claude</font></b>',
        styles['SubsectionHeading']
    ))

    cell_style = ParagraphStyle('Cell', fontSize=9, leading=11)
    interfaces_data = [
        [Paragraph('<b>Interface</b>', ParagraphStyle('H', fontSize=9, textColor=colors.white)),
         Paragraph('<b>Best For</b>', ParagraphStyle('H', fontSize=9, textColor=colors.white)),
         Paragraph('<b>Key Features</b>', ParagraphStyle('H', fontSize=9, textColor=colors.white))],
        [Paragraph('Claude.ai', cell_style), Paragraph('General tasks, conversations', cell_style), Paragraph('Web interface, file uploads, artifacts, projects', cell_style)],
        [Paragraph('Claude Desktop', cell_style), Paragraph('Power users, MCP integrations', cell_style), Paragraph('Native app, MCP server support, local tools', cell_style)],
        [Paragraph('Claude Code (CLI)', cell_style), Paragraph('Developers, automation', cell_style), Paragraph('Terminal-based, git integration, agentic coding', cell_style)],
        [Paragraph('API', cell_style), Paragraph('Applications, workflows', cell_style), Paragraph('Programmatic access, batch processing, custom apps', cell_style)],
        [Paragraph('IDE Extensions', cell_style), Paragraph('In-editor assistance', cell_style), Paragraph('VS Code, JetBrains - code completion & chat', cell_style)],
    ]

    interfaces_table = Table(interfaces_data, colWidths=[1.4*inch, 1.7*inch, 2.8*inch])
    interfaces_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHTER]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(interfaces_table)

    elements.append(Spacer(1, 15))

    # Extensibility with MCP
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">Extensibility with MCP</font></b>',
        styles['SubsectionHeading']
    ))

    elements.append(Paragraph(
        "Claude's capabilities can be extended through the <b>Model Context Protocol (MCP)</b> - an open standard "
        "that allows Claude to connect to external tools and data sources. This guide focuses on one such extension: "
        "<b>MCP-PowerBI-Finvision</b>, which gives Claude deep access to Power BI Desktop.",
        styles['Body']
    ))

    elements.append(Spacer(1, 10))

    elements.append(create_info_box(
        "With MCP, Claude goes from being a helpful assistant to an <b>active collaborator</b> that can read your files, "
        "query your databases, interact with your tools, and execute operations on your behalf - all while maintaining "
        "the safety and helpfulness that Claude is known for.",
        'tip', styles
    ))

    elements.append(PageBreak())

    # ========== SECTION 2: WHAT IS MCP ==========
    elements.append(create_icon_header(ICONS['target'], "2. What is MCP?", styles))
    elements.append(HRFlowable(width="100%", thickness=2, color=BORDER_COLOR, spaceBefore=5, spaceAfter=15))

    elements.append(create_info_box(
        "<b>Model Context Protocol (MCP)</b> is like a universal translator between AI assistants "
        "(like Claude) and software tools. It allows AI to understand and interact with "
        "specialized applications in a standardized way.",
        'info', styles
    ))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">Think of it Like This...</font></b>',
        styles['SubsectionHeading']
    ))
    elements.append(Paragraph(
        "Imagine you have a brilliant assistant who speaks English, but your Power BI files "
        "speak a completely different \"language.\" MCP acts as an interpreter:",
        styles['Body']
    ))

    # Visual flow
    elements.extend(create_flow_diagram(
        ["You\n(English)", "Claude\n(AI)", "MCP Server\n(Translator)", "Power BI\n(Technical)"],
        "The Communication Flow:"
    ))

    benefits = [
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Translates requests</b> from natural language into technical commands',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Executes operations</b> on your behalf (create measures, analyze performance)',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Returns results</b> in a way you can understand',
    ]
    for benefit in benefits:
        elements.append(Paragraph(benefit, styles['BulletItem']))

    elements.append(Spacer(1, 15))
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">A Real Example</font></b>',
        styles['SubsectionHeading']
    ))

    elements.append(create_conversation_example(
        "Show me all measures in my Sales table",
        "Understands your intent, calls 02_Measure_Operations with table='Sales'",
        "A nicely formatted list of all 15 measures with descriptions and DAX expressions",
        styles
    ))

    elements.append(Spacer(1, 15))
    elements.append(create_info_box(
        "You don't need to know DAX, M queries, or technical Power BI commands. "
        "Just describe what you want in plain English!",
        'tip', styles
    ))

    elements.append(PageBreak())

    # ========== SECTION 3: WHAT IS FINVISION ==========
    elements.append(create_icon_header(ICONS['star'], "3. What is MCP-PowerBI-Finvision?", styles))
    elements.append(HRFlowable(width="100%", thickness=2, color=BORDER_COLOR, spaceBefore=5, spaceAfter=15))

    elements.append(create_info_box(
        "<b>MCP-PowerBI-Finvision</b> is a specialized MCP server designed specifically for "
        "Power BI Desktop. It provides <b>50+ tools</b> across <b>10 categories</b> that enable "
        "AI assistants to analyze, modify, and optimize your Power BI models.",
        'info', styles
    ))
    elements.append(Spacer(1, 15))

    # Feature grid
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">Key Capabilities</font></b>',
        styles['SubsectionHeading']
    ))

    features = [
        ("Model Analysis", "Examine tables, columns, measures"),
        ("DAX Intelligence", "Analyze, debug, optimize DAX"),
        ("Best Practices", "120+ rules to identify issues"),
        ("Performance", "Find slow queries & optimize"),
        ("CRUD Operations", "Create, update, delete objects"),
        ("Visual Debugging", "Analyze visuals & filter contexts"),
        ("Documentation", "Auto-generate Word documents"),
        ("Offline Analysis", "Analyze PBIP without Power BI"),
    ]
    elements.append(create_feature_grid(features, styles))

    elements.append(Spacer(1, 15))
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">Example: Creating a Measure</font></b>',
        styles['SubsectionHeading']
    ))

    elements.extend(create_flow_diagram(
        ["Describe\nmeasure", "Claude\nwrites DAX", "MCP creates\nin Power BI", "See it in\nyour model"],
    ))

    elements.append(create_conversation_example(
        "Create a measure for year-over-year sales growth",
        "Writes the DAX and creates the measure for you",
        "YoY Growth = DIVIDE([Current Sales] - [Prior Year Sales], [Prior Year Sales])",
        styles
    ))

    elements.append(PageBreak())

    # ========== SECTION 4: GETTING STARTED ==========
    elements.append(create_icon_header(ICONS['rocket'], "4. Getting Started", styles))
    elements.append(HRFlowable(width="100%", thickness=2, color=BORDER_COLOR, spaceBefore=5, spaceAfter=15))

    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">Prerequisites</font></b>',
        styles['SubsectionHeading']
    ))

    prereqs = [
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Windows 10/11</b> (64-bit)',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Power BI Desktop</b> installed',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Claude Desktop</b> or MCP-compatible AI client',
    ]
    for prereq in prereqs:
        elements.append(Paragraph(prereq, styles['BulletItem']))

    elements.append(Spacer(1, 15))
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">Installation</font></b>',
        styles['SubsectionHeading']
    ))

    elements.extend(create_flow_diagram(
        ["Download\nrelease", "Extract\nfiles", "Run\nsetup.bat", "Restart\nClaude"],
        "Quick Install:"
    ))

    elements.append(Paragraph(
        "The <b>setup.bat</b> script automatically configures Claude Desktop to use the MCP server. "
        "It detects your Python installation, creates the virtual environment, installs dependencies, "
        "and updates your Claude configuration file.",
        styles['Body']
    ))

    elements.append(Spacer(1, 15))
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">Your First Connection</font></b>',
        styles['SubsectionHeading']
    ))

    elements.append(create_info_box(
        f'<b>Step 1:</b> Open Power BI Desktop with your .pbix file<br/>'
        f'<b>Step 2:</b> Open Claude Desktop<br/>'
        f'<b>Step 3:</b> Type: "Connect to my Power BI model"<br/>'
        f'<b>Step 4:</b> Claude automatically detects and connects!<br/>'
        f'<b>Step 5:</b> Start exploring: "Give me an overview"',
        'success', styles
    ))

    elements.append(PageBreak())

    # ========== SECTION 5: TOOLS OVERVIEW ==========
    elements.append(create_icon_header(ICONS['model'], "5. Tools Overview", styles))
    elements.append(HRFlowable(width="100%", thickness=2, color=BORDER_COLOR, spaceBefore=5, spaceAfter=15))

    elements.append(Paragraph(
        "The server provides <b>50+ tools</b> organized into <b>10 categories</b>. "
        "You don't need to memorize them - just describe what you want!",
        styles['Body']
    ))
    elements.append(Spacer(1, 12))

    # Tools overview table
    overview_data = [
        [Paragraph('<b>Category</b>', ParagraphStyle('Header', fontSize=9, textColor=colors.white)),
         Paragraph('<b>Purpose</b>', ParagraphStyle('Header', fontSize=9, textColor=colors.white)),
         Paragraph('<b>#</b>', ParagraphStyle('Header', fontSize=9, textColor=colors.white, alignment=TA_CENTER))],
        ['01 Connection', 'Detect and connect to Power BI Desktop', '2'],
        ['02 Model Ops', 'CRUD for tables, columns, measures, relationships', '8'],
        ['03 Batch/Trans', 'Execute multiple operations atomically', '2'],
        ['04 Query/Search', 'Run DAX queries and search objects', '6'],
        ['05 DAX Intelligence', 'Analyze, debug, and optimize DAX', '5'],
        ['06 Analysis', 'Model analysis and best practices', '3'],
        ['07 PBIP Analysis', 'Offline project file analysis', '10'],
        ['08 Documentation', 'Generate model documentation', '2'],
        ['09 Debug', 'Visual debugging and advanced analysis', '11'],
        ['10 Help', 'User guides and references', '1'],
    ]

    overview_table = Table(overview_data, colWidths=[1.6*inch, 3.8*inch, 0.5*inch])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHTER]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(overview_table)

    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">Natural Language to Tools</font></b>',
        styles['SubsectionHeading']
    ))

    mapping_data = [
        [Paragraph('<b>You Say...</b>', ParagraphStyle('H', fontSize=9, textColor=colors.white)),
         Paragraph('<b>Tool Used</b>', ParagraphStyle('H', fontSize=9, textColor=colors.white))],
        ['"List all measures"', '02_Measure_Operations (list)'],
        ['"Show DAX for Total Sales"', '02_Measure_Operations (get)'],
        ['"Create a YTD measure"', '02_Measure_Operations (create)'],
        ['"Find measures using CALCULATE"', '04_Search_String'],
        ['"Analyze this measure"', '05_DAX_Intelligence'],
        ['"Check for best practice issues"', '06_Full_Analysis'],
        ['"Generate documentation"', '08_Generate_Documentation_Word'],
    ]

    mapping_table = Table(mapping_data, colWidths=[2.8*inch, 3.1*inch])
    mapping_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (1, 1), (1, -1), 'Courier'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHTER]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(mapping_table)

    elements.append(PageBreak())

    # ========== SECTION 6: TOOL REFERENCE ==========
    elements.append(create_icon_header(ICONS['gear'], "6. Complete Tool Reference", styles))
    elements.append(HRFlowable(width="100%", thickness=2, color=BORDER_COLOR, spaceBefore=5, spaceAfter=15))

    # 01 Connection
    elements.append(create_category_banner(ICONS['connection'], "01 Connection Tools",
                                           "Detect and connect to Power BI Desktop instances", PRIMARY_BLUE))
    elements.append(Spacer(1, 8))

    elements.extend(create_flow_diagram(
        ["Power BI\nrunning", "Detect\ninstances", "Connect", "Ready!"],
        "Connection Flow:"
    ))

    elements.extend(create_tool_card(
        "01_Detect_PBI_Instances",
        "Scans your system for running Power BI Desktop instances. Returns file names and ports.",
        conversation_examples=[{
            "user": "What Power BI files do I have open?",
            "claude": "Scans for running instances",
            "result": "Found 2: Sales_Model.pbix (port 52000), Finance_Model.pbix (port 52100)"
        }],
        styles=styles
    ))

    elements.extend(create_tool_card(
        "01_Connect_To_Instance",
        "Establishes connection to a Power BI instance. Auto-detects if only one is running.",
        conversation_examples=[{
            "user": "Connect to my Power BI model",
            "claude": "Auto-detects and connects",
            "result": "Connected to Sales_Model.pbix - 15 tables, 42 measures"
        }],
        styles=styles
    ))

    # 02 Model Operations
    elements.append(create_category_banner(ICONS['model'], "02 Model Operations",
                                           "Complete CRUD for all model objects", SECONDARY_BLUE))
    elements.append(Spacer(1, 8))

    elements.extend(create_tool_card(
        "02_Table_Operations",
        "Manage tables: list, describe, preview data, create, rename, delete.",
        operations=[
            ("list", "Get all tables"),
            ("describe", "Table details with columns/measures"),
            ("preview", "Sample data rows"),
            ("create/rename/delete", "Modify tables"),
        ],
        conversation_examples=[{
            "user": "Show me what's in the Sales table",
            "claude": "Gets structure and sample data",
            "result": "Sales: 8 columns, 5 measures, 2 relationships. Shows first 10 rows."
        }],
        styles=styles
    ))

    elements.extend(create_tool_card(
        "02_Measure_Operations",
        "Create, read, update, delete measures. The most frequently used tool!",
        operations=[
            ("list", "List measure names (fast)"),
            ("get", "Get measure WITH DAX expression"),
            ("create", "Create new measure"),
            ("update/delete/rename", "Modify measures"),
        ],
        conversation_examples=[
            {"user": "Show DAX for Profit Margin", "claude": "Retrieves measure",
             "result": "DIVIDE([Revenue] - [Cost], [Revenue])"},
            {"user": "Create average order value measure", "claude": "Creates measure",
             "result": "Created: Avg Order Value = DIVIDE([Total Sales], [Order Count])"}
        ],
        styles=styles
    ))

    elements.extend(create_tool_card(
        "02_Column_Operations",
        "Work with columns: statistics, distributions, create calculated columns.",
        operations=[
            ("list/get", "View columns and details"),
            ("statistics", "Min, max, distinct count, blanks"),
            ("distribution", "Value frequency analysis"),
            ("create", "Create calculated column"),
        ],
        styles=styles
    ))

    elements.extend(create_tool_card(
        "02_Relationship_Operations",
        "Manage relationships between tables.",
        operations=[
            ("list", "All relationships"),
            ("find", "Relationships for a table"),
            ("create/delete", "Modify relationships"),
        ],
        styles=styles
    ))

    elements.extend(create_tool_card(
        "02_Calculation_Group_Operations",
        "Manage calculation groups for time intelligence.",
        examples=["List calculation groups", "Create Time Intelligence group"],
        styles=styles
    ))

    elements.extend(create_tool_card(
        "02_Role_Operations",
        "View Row-Level Security (RLS) and Object-Level Security (OLS) roles.",
        styles=styles
    ))

    elements.extend(create_tool_card(
        "02_TMDL_Operations",
        "TMDL automation: export, find/replace, bulk rename with reference updates.",
        styles=styles
    ))

    elements.append(PageBreak())

    # 03 Batch
    elements.append(create_category_banner(ICONS['batch'], "03 Batch & Transactions",
                                           "Execute multiple operations efficiently", PURPLE))
    elements.append(Spacer(1, 8))

    elements.extend(create_flow_diagram(
        ["Define\noperations", "Execute\nbatch", "Succeed or\nrollback", "3-5x\nfaster!"],
        "Batch Flow:"
    ))

    elements.extend(create_tool_card(
        "03_Batch_Operations",
        "Execute multiple operations in one batch. 3-5x faster than individual calls!",
        conversation_examples=[{
            "user": "Create 5 measures: Total Sales, Avg Sales, YTD, MTD, Count",
            "claude": "Uses batch operation",
            "result": "Created 5 measures in 1.2s (vs 6+ seconds individually)"
        }],
        styles=styles
    ))

    elements.extend(create_tool_card(
        "03_Manage_Transactions",
        "Transaction control: begin, commit, rollback for complex operations.",
        styles=styles
    ))

    # 04 Query & Search
    elements.append(create_category_banner(ICONS['search'], "04 Query & Search",
                                           "Execute DAX queries and search objects", SUCCESS_GREEN))
    elements.append(Spacer(1, 8))

    elements.extend(create_tool_card(
        "04_Run_DAX",
        "Execute DAX queries with automatic safety limits.",
        operations=[
            ("query", "The DAX query (EVALUATE statement)"),
            ("top_n", "Max rows (default: 100)"),
            ("mode", "'auto', 'analyze', 'profile', 'simple'"),
        ],
        conversation_examples=[{
            "user": "Show me sales by category",
            "claude": "Runs SUMMARIZECOLUMNS query",
            "result": "Electronics: $1.2M, Clothing: $800K, Home: $600K..."
        }],
        styles=styles
    ))

    elements.extend(create_tool_card(
        "04_Search_Objects",
        "Search across tables, columns, and measures by name.",
        conversation_examples=[{
            "user": "Find everything related to 'revenue'",
            "claude": "Searches all objects",
            "result": "Found: Revenue table, Total Revenue measure, Revenue_Category column"
        }],
        styles=styles
    ))

    elements.extend(create_tool_card(
        "04_Search_String",
        "Search inside measure DAX expressions for patterns.",
        conversation_examples=[{
            "user": "Which measures use CALCULATE?",
            "claude": "Searches DAX expressions",
            "result": "15 measures found: YTD Sales, MTD Sales, Filtered Revenue..."
        }],
        styles=styles
    ))

    elements.extend(create_tool_card(
        "04_Get_Data_Sources / 04_Get_M_Expressions / 04_Validate_DAX",
        "List data sources, view M expressions, validate DAX syntax before execution.",
        styles=styles
    ))

    elements.append(PageBreak())

    # 05 DAX Intelligence
    elements.append(create_category_banner(ICONS['brain'], "05 DAX Intelligence",
                                           "Your AI-powered DAX expert!", ACCENT_ORANGE))
    elements.append(Spacer(1, 8))

    elements.extend(create_flow_diagram(
        ["Input DAX", "Analyze\ncontext", "Detect\nanti-patterns", "Suggest\noptimizations"],
        "DAX Analysis Flow:"
    ))

    elements.extend(create_tool_card(
        "05_DAX_Intelligence",
        "The most powerful DAX tool. Analyzes context transitions, detects anti-patterns, "
        "provides step-by-step debugging with optimization suggestions.",
        operations=[
            ("expression", "DAX or measure name (fuzzy match!)"),
            ("analyze", "Context transition analysis"),
            ("debug", "Step-by-step debugging"),
            ("report", "Comprehensive 8-section report"),
        ],
        conversation_examples=[
            {"user": "What's wrong with my Profit Margin measure?", "claude": "Runs analysis",
             "result": "Found: unnecessary CALCULATE, missing blank handling. Fix provided."},
            {"user": "Debug CALCULATE(SUM(Sales[Amount]), FILTER(ALL(Date)...))",
             "claude": "Steps through filter context",
             "result": "Step 1: ALL removes filters... Step 2: FILTER applies Year=2024..."}
        ],
        styles=styles
    ))

    elements.extend(create_tool_card(
        "05_Analyze_Dependencies / 05_Get_Measure_Impact",
        "Visualize measure dependencies. See what depends on a measure before changing it.",
        conversation_examples=[{
            "user": "What depends on Total Sales?",
            "claude": "Analyzes dependents",
            "result": "8 measures: YTD Sales, MTD Sales, Sales Growth, Profit Margin..."
        }],
        styles=styles
    ))

    elements.extend(create_tool_card(
        "05_Export_DAX_Measures / 05_Column_Usage_Mapping",
        "Export all measures to CSV. Analyze which measures use which columns.",
        styles=styles
    ))

    # 06 Analysis
    elements.append(create_category_banner(ICONS['analysis'], "06 Analysis",
                                           "Model analysis and best practices", WARNING_RED))
    elements.append(Spacer(1, 8))

    elements.extend(create_tool_card(
        "06_Simple_Analysis",
        "Fast model overview in 2-5 seconds.",
        conversation_examples=[{
            "user": "Give me an overview",
            "claude": "Runs simple analysis",
            "result": "15 tables, 42 measures, 18 relationships. Largest: Sales (2.1M rows)"
        }],
        styles=styles
    ))

    elements.extend(create_tool_card(
        "06_Full_Analysis",
        "Comprehensive analysis with 120+ best practice rules.",
        conversation_examples=[{
            "user": "Check my model for issues",
            "claude": "Runs 120+ rules",
            "result": "3 warnings: (1) Missing description, (2) Bidirectional relationship..."
        }],
        styles=styles
    ))

    elements.extend(create_tool_card(
        "06_Compare_PBI_Models",
        "Compare two models to see differences.",
        styles=styles
    ))

    elements.append(PageBreak())

    # 07 PBIP Analysis
    elements.append(create_category_banner(ICONS['folder'], "07 PBIP Analysis",
                                           "Offline analysis without Power BI running!", DARK_BLUE))
    elements.append(Spacer(1, 8))

    elements.append(create_info_box(
        "<b>What is PBIP?</b> Power BI Project format stores your model as text files. "
        "These tools analyze PBIP files <b>without needing Power BI Desktop running!</b>",
        'tip', styles
    ))
    elements.append(Spacer(1, 8))

    elements.append(create_info_box(
        "<b>Requirement:</b> PBIP tools require a <b>PBIP Path folder</b> to be specified. "
        "This is the folder containing your .pbip file and the associated Report/SemanticModel subfolders.",
        'important', styles
    ))
    elements.append(Spacer(1, 8))

    elements.extend(create_tool_card(
        "07_Analyze_PBIP_Repository / 07_Report_Info / 07_PBIP_Dependency_Analysis",
        "Generate HTML reports, get page/visual info, explore dependencies interactively.",
        styles=styles
    ))

    elements.extend(create_tool_card(
        "07_Slicer_Operations",
        "Manage slicer configurations and visual interactions.",
        operations=[
            ("list", "Find slicers with values"),
            ("configure_single_select", "Change to single-select"),
            ("list_interactions", "Cross-filtering settings"),
            ("set_interaction", "Configure interactions"),
        ],
        styles=styles
    ))

    elements.extend(create_tool_card(
        "07_Visual_Operations",
        "Comprehensive visual editing for PBIP reports.",
        operations=[
            ("list", "Find visuals by title/type/page"),
            ("update_position", "Move and resize visuals"),
            ("replace_measure", "Bulk replace measures"),
            ("sync_visual", "Sync across pages"),
            ("update_visual_config", "Update fonts, colors, axis"),
        ],
        conversation_examples=[
            {"user": "Resize all cards to 200x100", "claude": "Updates all cards",
             "result": "Updated 12 card visuals across 5 pages"},
            {"user": "Replace 'Old Measure' with 'New Measure'", "claude": "Bulk replaces",
             "result": "Replaced in 8 visuals on 4 pages"}
        ],
        styles=styles
    ))

    elements.extend(create_tool_card(
        "07_Analyze_Aggregation / 07_Analyze_Bookmarks / 07_Analyze_Theme_Compliance",
        "Analyze aggregation tables, bookmarks, and theme compliance.",
        styles=styles
    ))

    # 08 Documentation
    elements.append(create_category_banner(ICONS['docs'], "08 Documentation",
                                           "Auto-generate comprehensive model documentation", SECONDARY_BLUE))
    elements.append(Spacer(1, 8))

    elements.extend(create_tool_card(
        "08_Generate_Documentation_Word",
        "Create comprehensive Word document with full model documentation including tables, "
        "measures, relationships, and data lineage.",
        conversation_examples=[{
            "user": "Generate documentation for my model",
            "claude": "Analyzes entire model, generates structured Word document",
            "result": "Generated 45-page document with TOC, table descriptions, all 42 measures with DAX, "
                     "relationship diagram, and data source inventory"
        }],
        styles=styles
    ))

    elements.extend(create_tool_card(
        "08_Generate_Markdown_Docs",
        "Generate markdown documentation suitable for wikis, GitHub, or Confluence.",
        conversation_examples=[{
            "user": "Create markdown docs for our wiki",
            "claude": "Generates markdown files with proper formatting",
            "result": "Created: README.md, TABLES.md, MEASURES.md, RELATIONSHIPS.md - ready for Git!"
        }],
        styles=styles
    ))

    elements.append(PageBreak())

    # 09 Debug - EXPANDED SECTION
    elements.append(create_category_banner(ICONS['debug'], "09 Debug Tools",
                                           "Powerful debugging and analysis tools", WARNING_RED))
    elements.append(Spacer(1, 8))

    elements.append(create_info_box(
        "The Debug tools are your secret weapon for troubleshooting complex Power BI issues. "
        "From visual filter contexts to measure performance comparisons, these tools help you "
        "understand <b>exactly</b> what's happening under the hood.",
        'info', styles
    ))
    elements.append(Spacer(1, 8))

    elements.append(create_info_box(
        "<b>Requirements:</b> Debug tools require: (1) An <b>open Power BI Desktop file (.pbix)</b> for live model connection, "
        "and (2) A <b>link to the PBIP report folder</b> to access visual and page definitions.",
        'important', styles
    ))
    elements.append(Spacer(1, 12))

    # 09_Debug_Visual - Detailed
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">09_Debug_Visual - Visual Debugging</font></b>',
        styles['SubsectionHeading']
    ))

    elements.append(Paragraph(
        "Ever wondered why a visual shows unexpected values? Debug_Visual reveals everything: "
        "the filter context, applied slicers, cross-filters, and the actual DAX query being executed.",
        styles['Body']
    ))

    elements.extend(create_flow_diagram(
        ["Select\nvisual", "Capture\ncontext", "Show\nfilters", "Reveal\nDAX query"],
        "Visual Debugging Flow:"
    ))

    elements.extend(create_tool_card(
        "Debug_Visual Operations",
        "Comprehensive visual debugging with multiple analysis modes.",
        operations=[
            ("get_filter_context", "See ALL filters affecting a visual (page, report, slicer, cross-filter)"),
            ("get_visual_query", "Capture the exact DAX query Power BI generates for the visual"),
            ("analyze_performance", "Measure query execution time and identify bottlenecks"),
            ("explain_calculation", "Step-by-step explanation of how a value is calculated"),
        ],
        styles=styles
    ))

    elements.append(create_conversation_example(
        "Why does my Sales chart show $0 for Electronics?",
        "Debugs the visual, reveals a hidden page-level filter excluding Electronics category",
        "Found the issue! Page filter 'Category NOT IN (Electronics)' is active. "
        "This filter was set on the page and is hiding Electronics from all visuals.",
        styles
    ))
    elements.append(Spacer(1, 8))

    elements.append(create_conversation_example(
        "Debug the filter context on my YTD Sales card",
        "Captures complete filter context including all slicer states",
        "Active filters: Year=2024, Region=North America, Product Category=ALL (no filter). "
        "Cross-filter from Customer table: Customer Segment=Enterprise. "
        "Page filter: Is Active=TRUE",
        styles
    ))
    elements.append(Spacer(1, 12))

    # 09_Compare_Measures - Detailed
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">09_Compare_Measures - Side-by-Side Analysis</font></b>',
        styles['SubsectionHeading']
    ))

    elements.append(Paragraph(
        "The ultimate tool for validating optimizations. Compare two measure versions with "
        "identical filter contexts to verify they produce the same results - and see performance gains.",
        styles['Body']
    ))

    elements.extend(create_flow_diagram(
        ["Original\nmeasure", "Optimized\nmeasure", "Same\ncontext", "Compare\nresults"],
        "Measure Comparison Flow:"
    ))

    compare_examples = [
        [Paragraph('<b>Scenario</b>', ParagraphStyle('H', fontSize=9, textColor=colors.white)),
         Paragraph('<b>What You Learn</b>', ParagraphStyle('H', fontSize=9, textColor=colors.white))],
        ['Before/after optimization', 'Verify same result, see speed improvement (e.g., 145ms vs 45ms)'],
        ['Two different approaches', 'Which formula is faster for your data size?'],
        ['Legacy vs new measure', 'Safe to replace? Results match exactly?'],
        ['CALCULATE vs SUMX', 'Context transition impact on your specific model'],
    ]

    compare_table = Table(compare_examples, colWidths=[2.2*inch, 3.7*inch])
    compare_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_ORANGE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHTER]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(compare_table)
    elements.append(Spacer(1, 8))

    elements.append(create_conversation_example(
        "Compare my original Profit Margin with the optimized version",
        "Runs both measures with identical filter context, measures execution time",
        "Results MATCH: Both return 0.423 (42.3%)\n"
        "Performance: Original=145ms, Optimized=45ms - 3.2x faster!\n"
        "Safe to deploy the optimized version.",
        styles
    ))
    elements.append(Spacer(1, 12))

    # 09_Validate - Detailed
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">09_Validate - Automated Testing</font></b>',
        styles['SubsectionHeading']
    ))

    elements.append(Paragraph(
        "Run automated validation tests on your model. Catch issues before they reach production: "
        "circular dependencies, invalid references, broken relationships, and more.",
        styles['Body']
    ))

    elements.extend(create_tool_card(
        "Validation Categories",
        "Comprehensive model validation across multiple dimensions.",
        operations=[
            ("syntax", "Validate all DAX expressions compile correctly"),
            ("references", "Check for broken column/table references"),
            ("relationships", "Detect circular paths, ambiguous relationships"),
            ("security", "Verify RLS/OLS rules are properly configured"),
            ("performance", "Identify potential performance issues"),
        ],
        styles=styles
    ))

    elements.append(create_conversation_example(
        "Validate my model before deployment",
        "Runs comprehensive validation suite",
        "Validation complete: 2 warnings, 1 error\n"
        "- ERROR: Measure 'Old Revenue' references deleted column 'Sales[OldPrice]'\n"
        "- WARNING: Bidirectional relationship Date<->Sales may cause ambiguity\n"
        "- WARNING: 3 measures have no description",
        styles
    ))
    elements.append(Spacer(1, 12))

    # 09_Profile - Detailed
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">09_Profile - Performance Profiling</font></b>',
        styles['SubsectionHeading']
    ))

    elements.append(Paragraph(
        "Deep performance analysis at the query level. See exactly where time is spent: "
        "Storage Engine (SE) vs Formula Engine (FE), cache hits, and query plans.",
        styles['Body']
    ))

    elements.extend(create_flow_diagram(
        ["Run\nquery", "Capture\nmetrics", "Analyze\nSE vs FE", "Find\nbottleneck"],
        "Performance Profiling Flow:"
    ))

    profile_metrics = [
        [Paragraph('<b>Metric</b>', ParagraphStyle('H', fontSize=9, textColor=colors.white)),
         Paragraph('<b>What It Tells You</b>', ParagraphStyle('H', fontSize=9, textColor=colors.white))],
        ['Total Duration', 'End-to-end query execution time'],
        ['SE (Storage Engine)', 'Time scanning/aggregating data from VertiPaq'],
        ['FE (Formula Engine)', 'Time calculating DAX logic (often the bottleneck!)'],
        ['SE Queries', 'Number of data requests (fewer is better)'],
        ['Cache Hit', 'Was result served from cache? (warm vs cold)'],
    ]

    profile_table = Table(profile_metrics, colWidths=[1.8*inch, 4.1*inch])
    profile_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SUCCESS_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHTER]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(profile_table)
    elements.append(Spacer(1, 8))

    elements.append(create_conversation_example(
        "Profile my slowest measure",
        "Executes with profiling enabled, breaks down timing",
        "Measure: Complex YTD Calculation\n"
        "Total: 2,340ms | SE: 180ms (8%) | FE: 2,160ms (92%)\n"
        "Bottleneck: Formula Engine - the DAX is doing heavy row-by-row iteration.\n"
        "Recommendation: Replace SUMX with CALCULATE + FILTER for better SE utilization.",
        styles
    ))
    elements.append(Spacer(1, 12))

    # 09_Advanced_Analysis - Detailed
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">09_Advanced_Analysis - Deep Dive</font></b>',
        styles['SubsectionHeading']
    ))

    elements.append(Paragraph(
        "Advanced analytical tools for complex debugging scenarios. Trace calculation chains, "
        "analyze memory usage, and understand VertiPaq compression.",
        styles['Body']
    ))

    elements.extend(create_tool_card(
        "Advanced Analysis Operations",
        "Deep technical analysis for expert users.",
        operations=[
            ("memory_analysis", "Table/column memory footprint and compression ratios"),
            ("calculation_chain", "Trace the full dependency chain of a measure"),
            ("cardinality_analysis", "Find high-cardinality columns impacting performance"),
            ("relationship_paths", "Visualize all paths between two tables"),
            ("unused_objects", "Find tables, columns, measures never used in reports"),
        ],
        styles=styles
    ))

    elements.append(create_conversation_example(
        "Why is my model so large? Analyze memory usage",
        "Scans all tables and columns, calculates compression ratios",
        "Total model size: 2.4GB\n"
        "Top consumers:\n"
        "1. FactTransactions[Description] - 890MB (37%) - High cardinality text!\n"
        "2. FactTransactions[TransactionID] - 450MB (19%) - GUID column\n"
        "3. DimProduct[ProductDetails] - 280MB (12%)\n"
        "Recommendation: Remove Description column or move to separate table.",
        styles
    ))
    elements.append(Spacer(1, 8))

    elements.append(create_conversation_example(
        "Show me all unused columns in my model",
        "Analyzes report visuals and measure references",
        "Found 23 unused columns across 8 tables:\n"
        "- DimCustomer: [OldAddress], [Fax], [MiddleName]\n"
        "- FactSales: [LegacyID], [ImportDate], [BatchNumber]\n"
        "- DimProduct: [DiscontinuedDate], [OldSKU]...\n"
        "Removing these could reduce model size by ~180MB.",
        styles
    ))
    elements.append(Spacer(1, 12))

    # 10 Help
    elements.append(create_category_banner(ICONS['help'], "10 Help & Reference",
                                           "Built-in guidance and documentation", TEXT_LIGHT))
    elements.append(Spacer(1, 8))

    elements.extend(create_tool_card(
        "10_Show_User_Guide",
        "Access built-in documentation, tool reference, and examples directly from Claude.",
        conversation_examples=[{
            "user": "How do I use the DAX Intelligence tool?",
            "claude": "Shows detailed usage guide with examples",
            "result": "DAX Intelligence accepts measure names or DAX expressions. "
                     "Use 'analyze' mode for context analysis, 'debug' for step-by-step..."
        }],
        styles=styles
    ))

    elements.append(PageBreak())

    # ========== SECTION 7: WORKFLOWS ==========
    elements.append(create_icon_header(ICONS['chart'], "7. Common Workflows", styles))
    elements.append(HRFlowable(width="100%", thickness=2, color=BORDER_COLOR, spaceBefore=5, spaceAfter=15))

    # Workflow 1
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">Workflow 1: Model Exploration</font></b>',
        styles['SubsectionHeading']
    ))
    elements.extend(create_flow_diagram(["Connect", "Overview", "List tables", "Describe", "Measures"]))
    elements.append(create_info_box(
        '<b>1.</b> "Connect to my Power BI model"<br/>'
        '<b>2.</b> "Give me an overview"<br/>'
        '<b>3.</b> "List all tables"<br/>'
        '<b>4.</b> "Describe the Sales table"<br/>'
        '<b>5.</b> "Show me all measures"',
        'example', styles
    ))
    elements.append(Spacer(1, 12))

    # Workflow 2
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">Workflow 2: Creating Measures</font></b>',
        styles['SubsectionHeading']
    ))
    elements.extend(create_flow_diagram(["Review\nexisting", "Create", "Analyze", "Test", "Done!"]))
    elements.append(create_info_box(
        '<b>1.</b> "Show existing sales measures"<br/>'
        '<b>2.</b> "Create a measure for YoY growth"<br/>'
        '<b>3.</b> "Analyze this measure for issues"<br/>'
        '<b>4.</b> "Test it: show growth by category"<br/>'
        '<b>5.</b> Refine if needed',
        'example', styles
    ))
    elements.append(Spacer(1, 12))

    # Workflow 3
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">Workflow 3: Performance</font></b>',
        styles['SubsectionHeading']
    ))
    elements.extend(create_flow_diagram(["Full\nanalysis", "Review", "Analyze\nslow", "Compare", "Update"]))
    elements.append(create_info_box(
        '<b>1.</b> "Run full performance analysis"<br/>'
        '<b>2.</b> "Show high cardinality columns"<br/>'
        '<b>3.</b> "Analyze the slowest measure"<br/>'
        '<b>4.</b> "Compare original vs optimized"<br/>'
        '<b>5.</b> "Update the measure"',
        'example', styles
    ))

    elements.append(PageBreak())

    # ========== SECTION 8: TIPS ==========
    elements.append(create_icon_header(ICONS['tip'], "8. Tips & Best Practices", styles))
    elements.append(HRFlowable(width="100%", thickness=2, color=BORDER_COLOR, spaceBefore=5, spaceAfter=15))

    elements.append(create_info_box(
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Start simple</b> - "Connect" then "Give me an overview"<br/>'
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Use natural language</b> - Claude picks the right tool<br/>'
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Be specific</b> - "Show DAX for Total Sales" not "show code"<br/>'
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Iterate</b> - Ask follow-up questions<br/>'
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Analyze before changing</b> - Check impact first',
        'success', styles
    ))
    elements.append(Spacer(1, 12))

    elements.append(create_info_box(
        f'<font color="{WARNING_RED.hexval()}">&#8226;</font> <b>Don\'t close Power BI</b> while using MCP<br/>'
        f'<font color="{WARNING_RED.hexval()}">&#8226;</font> <b>Don\'t skip testing</b> - Verify changes work<br/>'
        f'<font color="{WARNING_RED.hexval()}">&#8226;</font> <b>Don\'t ignore warnings</b> - Best practice results matter<br/>'
        f'<font color="{WARNING_RED.hexval()}">&#8226;</font> <b>Always connect first</b> before other operations',
        'warning', styles
    ))
    elements.append(Spacer(1, 15))

    # Quick reference
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">Quick Reference</font></b>',
        styles['SubsectionHeading']
    ))

    phrases_data = [
        [Paragraph('<b>You Say...</b>', ParagraphStyle('H', fontSize=9, textColor=colors.white)),
         Paragraph('<b>What Happens</b>', ParagraphStyle('H', fontSize=9, textColor=colors.white))],
        ['"What\'s in my model?"', 'Quick overview of tables, measures, relationships'],
        ['"Show DAX for [name]"', 'Retrieves full measure expression'],
        ['"Create a measure for..."', 'Claude writes DAX and creates it'],
        ['"What\'s wrong with this?"', 'DAX analysis with suggestions'],
        ['"Make my model faster"', 'Performance analysis with recommendations'],
        ['"Document my model"', 'Generates Word documentation'],
        ['"What depends on [X]?"', 'Impact analysis before changes'],
    ]

    phrases_table = Table(phrases_data, colWidths=[2.5*inch, 3.4*inch])
    phrases_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHTER]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(phrases_table)

    elements.append(PageBreak())

    # ========== SECTION 9: BEYOND POWER BI ==========
    elements.append(create_icon_header(ICONS['magic'], "9. Beyond Power BI: Claude as Your Dev Partner", styles))
    elements.append(HRFlowable(width="100%", thickness=2, color=BORDER_COLOR, spaceBefore=5, spaceAfter=15))

    elements.append(create_info_box(
        "Claude isn't just for Power BI analysis! When working with Power BI projects in a development "
        "environment, Claude can assist with <b>Visual Studio workflows</b>, <b>deployment conflicts</b>, "
        "<b>Microsoft Fabric notebooks</b>, and <b>PySpark</b> development.",
        'info', styles
    ))
    elements.append(Spacer(1, 15))

    # Visual Studio Section
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">Visual Studio & Source Control</font></b>',
        styles['SubsectionHeading']
    ))

    elements.append(Paragraph(
        "When working with PBIP (Power BI Project) files in Visual Studio or VS Code, Claude can help with:",
        styles['Body']
    ))

    vs_items = [
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Understanding TMDL files</b> - Claude can explain table definitions, measures, and relationships',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Code reviews</b> - Review changes before committing to version control',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Debugging issues</b> - Identify problems in model definition files',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Refactoring</b> - Suggest improvements to measure organization and naming',
    ]
    for item in vs_items:
        elements.append(Paragraph(item, styles['BulletItem']))

    elements.append(Spacer(1, 10))
    elements.append(create_conversation_example(
        "I'm looking at model.tmdl in Visual Studio - explain what this partition definition does",
        "Reads the TMDL structure and explains the partition type, source query, and refresh behavior",
        "This is an M-partition querying your SQL database with incremental refresh enabled...",
        styles
    ))
    elements.append(Spacer(1, 15))

    # Merge Conflicts Section
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">Resolving Merge Conflicts in Deployments</font></b>',
        styles['SubsectionHeading']
    ))

    elements.extend(create_flow_diagram(
        ["Conflict\ndetected", "Claude\nanalyzes", "Explains\ndifferences", "Suggests\nresolution"],
        "Merge Conflict Resolution Flow:"
    ))

    elements.append(Paragraph(
        "When multiple developers work on the same Power BI project, merge conflicts can occur. "
        "Claude helps you understand and resolve these conflicts:",
        styles['Body']
    ))

    merge_items = [
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Identify conflicting changes</b> - Understand what each version modified',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Semantic analysis</b> - Know if changes affect the same measures/relationships',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Resolution strategies</b> - Get guidance on which changes to keep',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Impact assessment</b> - Understand downstream effects of each choice',
    ]
    for item in merge_items:
        elements.append(Paragraph(item, styles['BulletItem']))

    elements.append(Spacer(1, 10))
    elements.append(create_conversation_example(
        "I have a merge conflict in Sales.tmdl between dev and main branch - help me resolve it",
        "Analyzes both versions, identifies the conflicting measure definitions, explains the differences",
        "Branch 'dev' added a new filter to [Total Sales], while 'main' updated the format string. "
        "These changes are compatible - you can keep both modifications.",
        styles
    ))

    elements.append(Spacer(1, 10))
    elements.append(create_info_box(
        "<b>Pro Tip:</b> Before deploying, ask Claude to compare your development model with production "
        "using 06_Compare_PBI_Models to preview all differences and potential conflicts.",
        'tip', styles
    ))
    elements.append(Spacer(1, 15))

    # Fabric Notebooks Section
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">Microsoft Fabric Notebooks</font></b>',
        styles['SubsectionHeading']
    ))

    elements.append(Paragraph(
        "Microsoft Fabric notebooks allow you to work with data using Python, PySpark, and SQL. "
        "Claude can assist with writing and debugging notebook code:",
        styles['Body']
    ))

    fabric_items = [
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Data transformation</b> - Write efficient Spark transformations',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Lakehouse integration</b> - Query Delta tables and manage data pipelines',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Semantic model refresh</b> - Script automated refreshes via the Fabric REST API',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Cross-workspace operations</b> - Work with data across multiple workspaces',
    ]
    for item in fabric_items:
        elements.append(Paragraph(item, styles['BulletItem']))

    elements.append(Spacer(1, 10))
    elements.append(create_conversation_example(
        "Write a Fabric notebook cell that reads from my Lakehouse and aggregates sales by region",
        "Writes PySpark code using spark.read.format('delta') with proper aggregations",
        "df = spark.read.format('delta').load('Tables/Sales')\\n"
        "result = df.groupBy('Region').agg(sum('Amount').alias('TotalSales'))",
        styles
    ))
    elements.append(Spacer(1, 15))

    # PySpark Section
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">PySpark Development</font></b>',
        styles['SubsectionHeading']
    ))

    elements.extend(create_flow_diagram(
        ["Describe\ntask", "Claude writes\nPySpark", "Debug &\noptimize", "Deploy to\nFabric"],
        "PySpark Development Flow:"
    ))

    elements.append(Paragraph(
        "PySpark is essential for big data processing in Fabric. Claude helps with:",
        styles['Body']
    ))

    pyspark_items = [
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Writing efficient transformations</b> - Avoid common performance pitfalls',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Schema management</b> - Define and evolve Delta table schemas',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Window functions</b> - Complex analytical queries made simple',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>UDF optimization</b> - When to use and when to avoid user-defined functions',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Debugging errors</b> - Understand cryptic Spark error messages',
    ]
    for item in pyspark_items:
        elements.append(Paragraph(item, styles['BulletItem']))

    elements.append(Spacer(1, 10))

    # PySpark examples table
    pyspark_examples = [
        [Paragraph('<b>You Ask...</b>', ParagraphStyle('H', fontSize=9, textColor=colors.white)),
         Paragraph('<b>Claude Helps With...</b>', ParagraphStyle('H', fontSize=9, textColor=colors.white))],
        ['"Calculate running total by date"', 'Window function with orderBy and rowsBetween'],
        ['"Deduplicate records keeping latest"', 'Row numbering with partition and filter'],
        ['"Join two large DataFrames efficiently"', 'Broadcast hints, bucketing strategies'],
        ['"Read from SQL Server incrementally"', 'JDBC connection with partition predicates'],
        ['"Write to Delta with merge/upsert"', 'DeltaTable.forPath with merge conditions'],
    ]

    pyspark_table = Table(pyspark_examples, colWidths=[2.6*inch, 3.3*inch])
    pyspark_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PURPLE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHTER]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(pyspark_table)

    elements.append(Spacer(1, 15))
    elements.append(create_info_box(
        f'<b>The Power Combo:</b> Use the MCP-PowerBI-Finvision server to analyze '
        'your semantic model, then ask Claude to write PySpark code in Fabric notebooks that '
        'prepares data specifically for that model. Full end-to-end assistance!',
        'success', styles
    ))

    elements.append(PageBreak())

    # ========== SECTION 10: THE FUTURE - FABRIC MCP ==========
    elements.append(create_icon_header(ICONS['future'], "10. The Future: Fabric MCP Server", styles))
    elements.append(HRFlowable(width="100%", thickness=2, color=BORDER_COLOR, spaceBefore=5, spaceAfter=15))

    elements.append(create_info_box(
        "Imagine the power of MCP-PowerBI-Finvision... but for the <b>entire Microsoft Fabric ecosystem</b>. "
        "A dedicated <b>Fabric MCP Server</b> could revolutionize how you interact with your data platform!",
        'info', styles
    ))
    elements.append(Spacer(1, 15))

    # Vision
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">The Vision</font></b>',
        styles['SubsectionHeading']
    ))

    elements.append(Paragraph(
        "A Fabric MCP Server would enable Claude to directly interact with all Fabric workloads - "
        "from Lakehouses to Data Pipelines, from Notebooks to Real-Time Analytics. "
        "Natural language becomes your interface to the entire data platform.",
        styles['Body']
    ))

    elements.append(Spacer(1, 10))
    elements.extend(create_flow_diagram(
        ["You\nask", "Claude\nunderstands", "Fabric MCP\nexecutes", "Results\ndelivered"],
        "End-to-End Fabric Automation:"
    ))
    elements.append(Spacer(1, 15))

    # Potential Capabilities
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">Potential Capabilities</font></b>',
        styles['SubsectionHeading']
    ))

    # Lakehouse Operations
    elements.append(Paragraph(
        f'<b><font color="{PRIMARY_BLUE.hexval()}">Lakehouse Operations</font></b>',
        styles['Body']
    ))
    lakehouse_items = [
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Table management</b> - Create, alter, optimize Delta tables via natural language',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Data exploration</b> - "Show me the schema of the Sales table"',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Quality checks</b> - "Are there any null values in the CustomerID column?"',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Time travel</b> - "Show me the data as it was yesterday at 3pm"',
    ]
    for item in lakehouse_items:
        elements.append(Paragraph(item, styles['BulletItem']))

    elements.append(Spacer(1, 8))

    # Data Pipeline Operations
    elements.append(Paragraph(
        f'<b><font color="{PRIMARY_BLUE.hexval()}">Data Pipeline Orchestration</font></b>',
        styles['Body']
    ))
    pipeline_items = [
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Pipeline monitoring</b> - "What pipelines failed in the last 24 hours?"',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Trigger management</b> - "Pause all pipelines in the Finance workspace"',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Lineage tracking</b> - "Where does this table get its data from?"',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Cost analysis</b> - "Which pipelines consume the most capacity?"',
    ]
    for item in pipeline_items:
        elements.append(Paragraph(item, styles['BulletItem']))

    elements.append(Spacer(1, 8))

    # Notebook Operations
    elements.append(Paragraph(
        f'<b><font color="{PRIMARY_BLUE.hexval()}">Notebook Automation</font></b>',
        styles['Body']
    ))
    notebook_items = [
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Code generation</b> - "Write a notebook that deduplicates the Orders table"',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Execution</b> - "Run the daily-refresh notebook and tell me when it finishes"',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Debugging</b> - "Why did this notebook fail? Show me the error"',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Scheduling</b> - "Schedule this notebook to run every Monday at 6am"',
    ]
    for item in notebook_items:
        elements.append(Paragraph(item, styles['BulletItem']))

    elements.append(Spacer(1, 8))

    # Warehouse & SQL
    elements.append(Paragraph(
        f'<b><font color="{PRIMARY_BLUE.hexval()}">Warehouse & SQL Analytics</font></b>',
        styles['Body']
    ))
    warehouse_items = [
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Query execution</b> - "Show me top 10 customers by revenue this quarter"',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Schema exploration</b> - "What views depend on the DimCustomer table?"',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Performance tuning</b> - "Which queries are running slow today?"',
        f'<font color="{SUCCESS_GREEN.hexval()}">&#8226;</font> <b>Security audit</b> - "Who has access to the PII schema?"',
    ]
    for item in warehouse_items:
        elements.append(Paragraph(item, styles['BulletItem']))

    elements.append(Spacer(1, 15))

    # Example Conversations
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">What Conversations Could Look Like</font></b>',
        styles['SubsectionHeading']
    ))

    elements.append(create_conversation_example(
        "Create a new Lakehouse table from the CSV files in the landing zone",
        "Scans landing zone, infers schema, creates optimized Delta table with proper partitioning",
        "Created 'Sales_Raw' table with 2.3M rows, partitioned by Year/Month, Z-ordered by CustomerID",
        styles
    ))
    elements.append(Spacer(1, 8))

    elements.append(create_conversation_example(
        "Why is the Finance pipeline taking so long today?",
        "Analyzes run history, checks data volumes, identifies bottleneck activity",
        "The 'Transform_Transactions' activity is processing 3x more rows than usual due to month-end. "
        "Consider adding incremental refresh.",
        styles
    ))
    elements.append(Spacer(1, 8))

    elements.append(create_conversation_example(
        "Set up a complete ETL from our Azure SQL database to a Gold layer table",
        "Creates connection, designs pipeline with bronze/silver/gold architecture, implements SCD Type 2",
        "Created pipeline 'SQL_to_Gold_Customers' with: source connection, bronze landing, silver cleansing, "
        "gold dimension table with history tracking. Ready for scheduling.",
        styles
    ))
    elements.append(Spacer(1, 15))

    # The Combined Power
    elements.append(Paragraph(
        f'<b><font color="{DARK_BLUE.hexval()}">The Combined Power: Finvision + Fabric</font></b>',
        styles['SubsectionHeading']
    ))

    combined_vision = [
        [Paragraph('<b>Current: Finvision</b>', ParagraphStyle('H', fontSize=9, textColor=colors.white)),
         Paragraph('<b>Future: + Fabric MCP</b>', ParagraphStyle('H', fontSize=9, textColor=colors.white))],
        ['Analyze semantic model', 'Analyze + trace data back to source'],
        ['Optimize DAX measures', 'Optimize DAX + underlying Lakehouse queries'],
        ['Document Power BI model', 'Document entire data lineage end-to-end'],
        ['Debug visual filter context', 'Debug from visual through pipeline to source'],
        ['Create measures in Power BI', 'Create full stack: source query + transform + measure'],
    ]

    combined_table = Table(combined_vision, colWidths=[2.9*inch, 3.0*inch])
    combined_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PURPLE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHTER]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(combined_table)

    elements.append(Spacer(1, 15))
    elements.append(create_info_box(
        f'<b>Stay Tuned!</b> The Fabric MCP Server will be released as a standalone companion project. '
        'It will transform how teams interact with their entire Microsoft Fabric environment - '
        'making AI assistance available across the full data lifecycle, from ingestion to insights.',
        'tip', styles
    ))

    # Footer
    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_BLUE, spaceBefore=15, spaceAfter=10))

    footer_content = Paragraph(
        f'<font size="11"><b>MCP-PowerBI-Finvision</b></font>  |  '
        f'<font size="9" color="{TEXT_LIGHT.hexval()}">AI-Powered Power BI Analysis</font><br/>'
        f'<font size="8" color="{TEXT_LIGHT.hexval()}">For more info, visit the project repository or ask Claude!</font>',
        ParagraphStyle('Footer', alignment=TA_CENTER, leading=14)
    )
    elements.append(footer_content)

    # Build PDF
    doc.build(elements)
    print(f"PDF generated successfully: {output_path}")
    return output_path


if __name__ == "__main__":
    build_pdf()
