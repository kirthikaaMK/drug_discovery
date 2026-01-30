from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
import os

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
        )
        self.normal_style = self.styles['Normal']

    def generate_report(self, query, results, summary, output_buffer=None):
        """
        Generate a comprehensive PDF report
        If output_buffer is provided, writes to buffer, else to file
        """
        if output_buffer:
            doc = SimpleDocTemplate(output_buffer, pagesize=letter)
        else:
            output_path = os.path.join(os.path.dirname(__file__), '..', 'reports', f'report_{query.replace(" ", "_")}.pdf')
            doc = SimpleDocTemplate(output_path, pagesize=letter)

        story = []

        # Title
        story.append(Paragraph(f"Drug Discovery Analysis Report: {query}", self.title_style))
        story.append(Spacer(1, 12))

        # Executive Summary
        story.append(Paragraph("Executive Summary", self.heading_style))
        story.append(Paragraph(summary.replace('\n', '<br/>'), self.normal_style))
        story.append(Spacer(1, 12))

        # Individual Agent Results
        for agent_name, result in results.items():
            story.append(Paragraph(f"{result['agent']} Analysis", self.heading_style))
            story.append(Paragraph(result['insights'], self.normal_style))

            if result['data']:
                # Create table from data
                if isinstance(result['data'], list) and result['data']:
                    headers = list(result['data'][0].keys())
                    table_data = [headers]
                    for row in result['data'][:10]:  # Limit to 10 rows
                        table_data.append([str(row.get(h, '')) for h in headers])

                    table = Table(table_data)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (0, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 12))

        # Build PDF
        doc.build(story)
        return output_buffer if output_buffer else output_path