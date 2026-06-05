from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


class ExportService:
    def markdown_to_pdf(self, markdown_text: str, title: str) -> bytes:
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter, title=title, leftMargin=48, rightMargin=48, topMargin=48)
        styles = getSampleStyleSheet()
        story = [Paragraph(title, styles["Title"]), Spacer(1, 14)]
        for raw_line in markdown_text.splitlines():
            line = raw_line.strip()
            if not line:
                story.append(Spacer(1, 8))
                continue
            if line.startswith("# "):
                story.append(Paragraph(line[2:], styles["Heading1"]))
            elif line.startswith("## "):
                story.append(Paragraph(line[3:], styles["Heading2"]))
            elif line.startswith("### "):
                story.append(Paragraph(line[4:], styles["Heading3"]))
            elif line.startswith("- "):
                story.append(Paragraph(f"&bull; {line[2:]}", styles["BodyText"]))
            else:
                story.append(Paragraph(line, styles["BodyText"]))
        doc.build(story)
        return output.getvalue()
