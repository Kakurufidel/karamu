import calendar
import logging
import qrcode
import sys
from io import BytesIO
from datetime import datetime
from PIL import Image as PILImage

# Vérification de reportlab
try:
    from reportlab.lib.pagesizes import A5
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.utils import ImageReader
    REPORTLAB_AVAILABLE = True
except ImportError as e:
    REPORTLAB_AVAILABLE = False
    print(f"REPORTLAB NOT AVAILABLE: {e}")

logger = logging.getLogger(__name__)


# ============================================================
# FONCTIONS UTILITAIRES POUR LA DATE EN FRANÇAIS
# ============================================================

def _french_day_name(date):
    """Retourne le jour de la semaine en français."""
    days = {
        0: "lundi", 1: "mardi", 2: "mercredi", 3: "jeudi",
        4: "vendredi", 5: "samedi", 6: "dimanche"
    }
    return days[date.weekday()]


def _french_month_name(date):
    """Retourne le mois en français."""
    months = {
        1: "janvier", 2: "février", 3: "mars", 4: "avril",
        5: "mai", 6: "juin", 7: "juillet", 8: "août",
        9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"
    }
    return months[date.month]


# ============================================================
# SERVICE PDF
# ============================================================

class InvitationPDFService:
    """Service de génération d'invitation PDF avec QR code et calendrier."""

    def __init__(self, guest_response):
        self.guest_response = guest_response
        self.event = guest_response.event
        logger.info(f"PDF Service init - Event: {self.event.name}, Guest: {guest_response.get_full_name()}")

    def generate(self):
        """
        Génère le PDF d'invitation.
        
        Returns:
            bytes: Contenu du PDF ou None en cas d'erreur
        """
        logger.info("Début génération PDF")
        
        if not REPORTLAB_AVAILABLE:
            logger.error("reportlab is not installed. Cannot generate PDF.")
            return None

        # Vérifier que l'événement a une date
        if not self.event.date:
            logger.warning("L'événement n'a pas de date. Utilisation d'une date par défaut.")
            # On continue quand même

        buffer = BytesIO()

        try:
            logger.info("Création du document PDF...")
            
            # Format A5 (148 x 210 mm)
            width, height = 420, 595
            doc = SimpleDocTemplate(
                buffer,
                pagesize=(width, height),
                rightMargin=20,
                leftMargin=20,
                topMargin=20,
                bottomMargin=20
            )

            styles = getSampleStyleSheet()
            story = []

            # ============================================================
            # STYLES
            # ============================================================
            cher_style = ParagraphStyle(
                'CherStyle',
                parent=styles['Normal'],
                fontSize=22,
                textColor=colors.HexColor('#1a1a2e'),
                alignment=TA_CENTER,
                spaceAfter=4,
                fontName='Helvetica-Bold'
            )

            guest_style = ParagraphStyle(
                'GuestStyle',
                parent=styles['Normal'],
                fontSize=16,
                textColor=colors.HexColor('#6B21A5'),
                alignment=TA_CENTER,
                spaceAfter=12,
                fontName='Helvetica-Bold'
            )

            body_style = ParagraphStyle(
                'BodyStyle',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#333333'),
                alignment=TA_CENTER,
                spaceAfter=8,
                fontName='Helvetica',
                leading=18
            )

            date_style = ParagraphStyle(
                'DateStyle',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#444444'),
                alignment=TA_CENTER,
                spaceAfter=12,
                fontName='Helvetica-Bold'
            )

            cal_style = ParagraphStyle(
                'CalStyle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#333333'),
                alignment=TA_CENTER,
                fontName='Helvetica'
            )

            qr_text_style = ParagraphStyle(
                'QRTextStyle',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#666666'),
                alignment=TA_CENTER,
                spaceAfter=2,
                fontName='Helvetica'
            )

            short_code_style = ParagraphStyle(
                'ShortCodeStyle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#06B6D4'),
                alignment=TA_CENTER,
                spaceAfter=4,
                fontName='Helvetica-Bold'
            )

            footer_style = ParagraphStyle(
                'FooterStyle',
                parent=styles['Normal'],
                fontSize=7,
                textColor=colors.HexColor('#CCCCCC'),
                alignment=TA_CENTER,
                spaceBefore=12
            )

            # ============================================================
            # 1. "Cher(e)" + NOM DE L'INVITÉ
            # ============================================================
            logger.info("Ajout du nom de l'invité...")
            story.append(Paragraph("Cher(e)", cher_style))
            guest_name = self.guest_response.get_full_name()
            if guest_name:
                story.append(Paragraph(guest_name.upper(), guest_style))
            story.append(Spacer(1, 4))

            # ============================================================
            # 2. TEXTE D'INVITATION
            # ============================================================
            logger.info("Ajout du message d'invitation...")
            message = self.event.invitation_text
            if message:
                story.append(Paragraph(message, body_style))
                story.append(Spacer(1, 6))

            # ============================================================
            # 3. DATE (avec jour en français)
            # ============================================================
            if self.event.date:
                logger.info("Ajout de la date...")
                date_obj = self.event.date
                jour = _french_day_name(date_obj)
                mois = _french_month_name(date_obj)
                date_str = f"Le {jour} {date_obj.day} {mois} {date_obj.year}."
                story.append(Paragraph(date_str, date_style))
                story.append(Spacer(1, 8))

            # ============================================================
            # 4. CALENDRIER DU MOIS
            # ============================================================
            if self.event.date:
                logger.info("Ajout du calendrier...")
                year = self.event.date.year
                month = self.event.date.month
                month_cal = calendar.monthcalendar(year, month)
                day_names = ["DIM", "LUN", "MAR", "MER", "JEU", "VEN", "SAM"]

                data = []
                data.append([Paragraph(d, cal_style) for d in day_names])
                for week in month_cal:
                    row = []
                    for day in week:
                        if day == 0:
                            row.append(Paragraph("", cal_style))
                        else:
                            row.append(Paragraph(str(day), cal_style))
                    data.append(row)

                col_widths = [width / 7.0 for _ in range(7)]
                cal_table = Table(data, colWidths=col_widths, hAlign='CENTER')
                cal_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ]))
                story.append(cal_table)
                story.append(Spacer(1, 10))

            # ============================================================
            # 5. QR CODE + CODE COURT
            # ============================================================
            invitation_link = self.guest_response.get_invitation_link()
            if invitation_link:
                logger.info("Génération du QR code...")
                try:
                    qr = qrcode.QRCode(version=1, box_size=6, border=2)
                    qr.add_data(invitation_link)
                    qr.make(fit=True)
                    qr_img = qr.make_image(fill_color="black", back_color="white")

                    qr_buffer = BytesIO()
                    qr_img.save(qr_buffer, format='PNG')
                    qr_buffer.seek(0)

                    qr_reader = ImageReader(qr_buffer)
                    
                    # QR code centré
                    qr_table = Table([[Image(qr_reader, width=55*mm, height=55*mm)]])
                    qr_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ]))
                    story.append(qr_table)
                    story.append(Spacer(1, 4))

                    # Texte sous le QR code
                    story.append(Paragraph("Scannez pour confirmer votre présence", qr_text_style))
                    story.append(Spacer(1, 2))

                    # Code court de l'invité
                    if self.guest_response.short_code:
                        story.append(Paragraph(f"Code: {self.guest_response.short_code}", short_code_style))
                except Exception as e:
                    logger.error(f"Erreur génération QR code: {e}")
                    # On continue sans QR code

            # ============================================================
            # 6. PIED DE PAGE
            # ============================================================
            logger.info("Ajout du pied de page...")
            story.append(Spacer(1, 6))
            year = self.event.date.strftime('%Y') if self.event.date else ''
            story.append(Paragraph(f"{self.event.name} - KaramuManage © {year}", footer_style))

            # ============================================================
            # GÉNÉRATION
            # ============================================================
            logger.info("Construction du PDF...")
            doc.build(story)
            buffer.seek(0)
            logger.info("PDF généré avec succès !")
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Erreur génération PDF: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None