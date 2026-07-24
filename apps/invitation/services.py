import logging
import qrcode
import requests
from io import BytesIO
from django.conf import settings
from django.core.files.storage import default_storage
from reportlab.lib.pagesizes import A4, A5, letter
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage

logger = logging.getLogger(__name__)


class InvitationPDFService:
    """
    Service de génération d'invitation PDF avec QR code et photo dynamique.
    
    Utilise les modèles Event et GuestResponse pour créer des invitations
    personnalisées au format A4, A5 ou letter.
    """

    def __init__(self, guest_response):
        """
        Initialise le service avec une réponse d'invité.
        
        Args:
            guest_response: Instance du modèle GuestResponse
        """
        self.guest_response = guest_response
        self.event = guest_response.event
        logger.info(f"PDF Service init - Event: {self.event.name}, Guest: {guest_response.get_full_name()}")

    def _load_image(self, image_field):
        """
        Charge une image depuis un champ ImageField de Django ou une URL.
        
        Args:
            image_field: Champ ImageField de Django (event.event_photo)
        
        Returns:
            PIL.Image ou None
        """
        if not image_field:
            return None
            
        try:
            # Si c'est un champ ImageField de Django
            if hasattr(image_field, 'url'):
                # Vérifier si c'est une URL distante ou un fichier local
                if image_field.url.startswith(('http://', 'https://')):
                    response = requests.get(image_field.url, timeout=10)
                    response.raise_for_status()
                    img = PILImage.open(BytesIO(response.content))
                else:
                    # Fichier local via le storage Django
                    file_path = default_storage.path(image_field.name)
                    img = PILImage.open(file_path)
                return img
            # Si c'est déjà un chemin ou URL
            elif isinstance(image_field, str):
                if image_field.startswith(('http://', 'https://')):
                    response = requests.get(image_field, timeout=10)
                    response.raise_for_status()
                    img = PILImage.open(BytesIO(response.content))
                else:
                    img = PILImage.open(image_field)
                return img
        except Exception as e:
            logger.error(f"Erreur chargement image: {e}")
            return None

    def _format_date_french(self, date_obj):
        """
        Formate une date en français.
        
        Args:
            date_obj: Objet date
        
        Returns:
            str: Date formatée en français
        """
        if not date_obj:
            return ""
        
        date_str = date_obj.strftime("%A %d %B %Y")
        date_fr = date_str.replace("Monday", "Lundi").replace("Tuesday", "Mardi") \
                         .replace("Wednesday", "Mercredi").replace("Thursday", "Jeudi") \
                         .replace("Friday", "Vendredi").replace("Saturday", "Samedi") \
                         .replace("Sunday", "Dimanche") \
                         .replace("January", "Janvier").replace("February", "Février") \
                         .replace("March", "Mars").replace("April", "Avril") \
                         .replace("May", "Mai").replace("June", "Juin") \
                         .replace("July", "Juillet").replace("August", "Août") \
                         .replace("September", "Septembre").replace("October", "Octobre") \
                         .replace("November", "Novembre").replace("December", "Décembre")
        return date_fr

    def generate(self, page_format='A4', qr_size=60):
        """
        Génère le PDF d'invitation.
        
        Args:
            page_format (str): 'A4', 'A5', ou 'letter' (défaut: 'A4')
            qr_size (int): Taille du QR code en mm (défaut: 60)
        
        Returns:
            bytes: Contenu du PDF ou None en cas d'erreur
        """
        logger.info("Début génération PDF")

        # Choix du format de page
        formats = {
            'A4': A4,
            'A5': A5,
            'letter': letter
        }
        pagesize = formats.get(page_format, A4)
        width, height = pagesize

        buffer = BytesIO()

        try:
            # Document avec marges confortables
            doc = SimpleDocTemplate(
                buffer,
                pagesize=pagesize,
                rightMargin=25,
                leftMargin=25,
                topMargin=25,
                bottomMargin=25
            )

            styles = getSampleStyleSheet()
            story = []

            # Couleur principale de l'événement
            primary_color = self.event.event_color or '#8B5CF6'
            
            # ============================================================
            # STYLES MODERNES ET ÉLÉGANTS
            # ============================================================
            
            # Titre "Cher(e)" - grand et élégant
            cher_style = ParagraphStyle(
                'CherStyle',
                parent=styles['Normal'],
                fontSize=28,
                textColor=colors.HexColor('#1a1a2e'),
                alignment=TA_CENTER,
                spaceAfter=6,
                fontName='Helvetica-Bold'
            )

            # Nom de l'invité - en vedette avec la couleur de l'événement
            guest_style = ParagraphStyle(
                'GuestStyle',
                parent=styles['Normal'],
                fontSize=22,
                textColor=colors.HexColor(primary_color),
                alignment=TA_CENTER,
                spaceAfter=16,
                fontName='Helvetica-Bold'
            )

            # Type d'événement (Mariage, Anniversaire, etc.)
            event_type_style = ParagraphStyle(
                'EventTypeStyle',
                parent=styles['Normal'],
                fontSize=14,
                textColor=colors.HexColor('#666666'),
                alignment=TA_CENTER,
                spaceAfter=8,
                fontName='Helvetica'
            )

            # Message d'invitation - bien stylisé
            message_style = ParagraphStyle(
                'MessageStyle',
                parent=styles['Normal'],
                fontSize=14,
                textColor=colors.HexColor('#2d2d2d'),
                alignment=TA_CENTER,
                spaceAfter=20,
                fontName='Helvetica',
                leading=22,
                borderPadding=10,
                backColor=colors.HexColor('#f8f4ff')
            )

            # Date - élégante avec la couleur de l'événement
            date_style = ParagraphStyle(
                'DateStyle',
                parent=styles['Normal'],
                fontSize=16,
                textColor=colors.HexColor(primary_color),
                alignment=TA_CENTER,
                spaceAfter=8,
                fontName='Helvetica-Bold'
            )
            
            # Heure
            time_style = ParagraphStyle(
                'TimeStyle',
                parent=styles['Normal'],
                fontSize=14,
                textColor=colors.HexColor('#444444'),
                alignment=TA_CENTER,
                spaceAfter=6,
                fontName='Helvetica'
            )
            
            # Lieu
            location_style = ParagraphStyle(
                'LocationStyle',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#555555'),
                alignment=TA_CENTER,
                spaceAfter=20,
                fontName='Helvetica'
            )

            # Code vestimentaire
            dress_style = ParagraphStyle(
                'DressStyle',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.HexColor('#666666'),
                alignment=TA_CENTER,
                spaceAfter=12,
                fontName='Helvetica'
            )

            # QR code texte
            qr_text_style = ParagraphStyle(
                'QRTextStyle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#666666'),
                alignment=TA_CENTER,
                spaceAfter=4,
                fontName='Helvetica'
            )

            # Code court - distinctif avec la couleur de l'événement
            short_code_style = ParagraphStyle(
                'ShortCodeStyle',
                parent=styles['Normal'],
                fontSize=14,
                textColor=colors.HexColor(primary_color),
                alignment=TA_CENTER,
                spaceAfter=8,
                fontName='Helvetica-Bold'
            )

            # Pied de page
            footer_style = ParagraphStyle(
                'FooterStyle',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#999999'),
                alignment=TA_CENTER,
                spaceBefore=20,
                fontName='Helvetica'
            )

            # ============================================================
            # 1. PHOTO DE L'ÉVÉNEMENT (event.event_photo)
            # ============================================================
            if self.event.event_photo:
                logger.info("Ajout de la photo de l'événement...")
                try:
                    img = self._load_image(self.event.event_photo)
                    if img:
                        # Redimensionnement proportionnel
                        max_width = width - 80
                        max_height = height * 0.35
                        
                        img_width, img_height = img.size
                        ratio = min(max_width/img_width, max_height/img_height)
                        new_width = img_width * ratio
                        new_height = img_height * ratio
                        
                        img = img.resize((int(new_width), int(new_height)), PILImage.Resampling.LANCZOS)
                        
                        # Sauvegarde temporaire
                        img_buffer = BytesIO()
                        img.save(img_buffer, format='PNG')
                        img_buffer.seek(0)
                        
                        # Intégration dans le PDF
                        img_reader = ImageReader(img_buffer)
                        img_table = Table([[Image(img_reader, width=new_width, height=new_height)]])
                        img_table.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ]))
                        story.append(img_table)
                        story.append(Spacer(1, 16))
                except Exception as e:
                    logger.error(f"Erreur chargement photo: {e}")

            # ============================================================
            # 2. "Cher(e)" + NOM DE L'INVITÉ
            # ============================================================
            logger.info("Ajout du nom de l'invité...")
            story.append(Paragraph("Cher(e)", cher_style))
            
            # Nom complet de l'invité
            guest_name = self.guest_response.get_full_name()
            if guest_name:
                story.append(Paragraph(guest_name.upper(), guest_style))
            story.append(Spacer(1, 4))

            # ============================================================
            # 3. TYPE D'ÉVÉNEMENT + NOMS SPÉCIFIQUES
            # ============================================================
            # Display names (ex: "Cahaya Dewi & Daniel Galleg" pour mariage)
            if self.event.display_names:
                story.append(Paragraph(self.event.display_names, event_type_style))
                story.append(Spacer(1, 4))
            
            # Type d'événement (ex: "Mariage", "Anniversaire")
            if self.event.display_title:
                story.append(Paragraph(self.event.display_title, event_type_style))
                story.append(Spacer(1, 6))

            # ============================================================
            # 4. TEXTE D'INVITATION (event.invitation_message)
            # ============================================================
            logger.info("Ajout du message d'invitation...")
            if self.event.invitation_text:
                msg_paragraph = Paragraph(self.event.invitation_text, message_style)
                story.append(msg_paragraph)
                story.append(Spacer(1, 10))

            # ============================================================
            # 5. DATE, HEURE ET LIEU
            # ============================================================
            if self.event.date:
                logger.info("Ajout de la date...")
                date_fr = self._format_date_french(self.event.date)
                story.append(Paragraph(f"📅 {date_fr}", date_style))
                story.append(Spacer(1, 4))
            
            if self.event.time:
                logger.info("Ajout de l'heure...")
                time_str = self.event.time.strftime("%H:%M")
                story.append(Paragraph(f"🕐 {time_str}", time_style))
                story.append(Spacer(1, 4))
            
            if self.event.location:
                logger.info("Ajout du lieu...")
                location_text = f"📍 {self.event.location}"
                if self.event.google_maps_link:
                    location_text = f'<link href="{self.event.google_maps_link}">{location_text}</link>'
                story.append(Paragraph(location_text, location_style))
                story.append(Spacer(1, 12))

            # ============================================================
            # 6. CODE VESTIMENTAIRE (optionnel)
            # ============================================================
            if self.event.dress_code:
                story.append(Paragraph(f"👔 {self.event.dress_code}", dress_style))

            # ============================================================
            # 7. QR CODE + CODE COURT (à la fin)
            # ============================================================
            invitation_link = self.guest_response.get_invitation_link()
            if invitation_link:
                logger.info("Génération du QR code...")
                try:
                    qr = qrcode.QRCode(version=1, box_size=8, border=3)
                    qr.add_data(invitation_link)
                    qr.make(fit=True)
                    qr_img = qr.make_image(fill_color="black", back_color="white")

                    qr_buffer = BytesIO()
                    qr_img.save(qr_buffer, format='PNG')
                    qr_buffer.seek(0)

                    qr_reader = ImageReader(qr_buffer)
                    
                    # QR code centré
                    qr_table = Table([[Image(qr_reader, width=qr_size*mm, height=qr_size*mm)]])
                    qr_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ]))
                    story.append(qr_table)
                    story.append(Spacer(1, 6))

                    # Texte sous le QR code
                    story.append(Paragraph("Scannez pour confirmer votre présence ✨", qr_text_style))
                    story.append(Spacer(1, 4))

                    # Code court de l'invité
                    if self.guest_response.short_code:
                        story.append(Paragraph(f"Code invité : {self.guest_response.short_code}", short_code_style))
                except Exception as e:
                    logger.error(f"Erreur génération QR code: {e}")

            # ============================================================
            # 8. PIED DE PAGE
            # ============================================================
            logger.info("Ajout du pied de page...")
            story.append(Spacer(1, 10))
            year = self.event.date.strftime('%Y') if self.event.date else ''
            footer_text = f"{self.event.name}"
            if year:
                footer_text += f" · {year}"
            footer_text += " · KaramuManage"
            story.append(Paragraph(footer_text, footer_style))

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