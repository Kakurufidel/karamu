import json
from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils.translation import gettext as _
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse
from datetime import datetime

from apps.events.models import Event
from apps.guests.models import GuestResponse
from .models import DrinkPackaging, EventForecast
from .forms import EstimationSettingsForm
from .services import EstimationService


def user_can_manage_expenses(user, event):
    return (event.main_organizer == user or
            event.collaborators.filter(user=user, status='accepted').exists())


# ============================================================
# PRÉVISIONS (l'essentiel)
# ============================================================

class ForecastView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Vue principale des prévisions - tout est ici !"""
    template_name = 'expenses/forecast.html'

    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        return user_can_manage_expenses(self.request.user, self.event)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.event
        context['event'] = event
        context['total_invited'] = event.invited_guests.count()
        
        # Récupérer les prévisions sauvegardées
        forecast = getattr(event, 'forecast', None)
        if forecast:
            context['forecast_data'] = forecast.drink_forecast
            context['saved_forecast'] = {
                'total_guests': forecast.total_guests_expected,
                'attendance_rate': forecast.attendance_rate,
                'services': forecast.number_of_services,
                'currency': forecast.currency,
            }
        else:
            context['forecast_data'] = None
            context['saved_forecast'] = None
        
        return context


class SaveForecastView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Sauvegarde les prévisions"""
    
    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        return user_can_manage_expenses(self.request.user, self.event)

    def post(self, request, event_id):
        try:
            data = json.loads(request.body)
            
            # Sauvegarder ou créer les prévisions
            forecast, created = EventForecast.objects.update_or_create(
                event=self.event,
                defaults={
                    'total_guests_expected': data.get('total_guests', 0),
                    'attendance_rate': data.get('attendance_rate', 75),
                    'number_of_services': data.get('services', 1),
                    'currency': data.get('currency', 'CDF'),
                    'drink_forecast': data.get('drinks', []),
                }
            )
            
            # Mettre à jour ou créer les conditionnements automatiquement
            for drink_data in data.get('drinks', []):
                drink_name = drink_data.get('name')
                pieces = drink_data.get('pieces_per_case', 12)
                price = drink_data.get('price_per_case', 0)
                
                if drink_name:
                    DrinkPackaging.objects.update_or_create(
                        event=self.event,
                        drink_name=drink_name,
                        defaults={
                            'pieces_per_case': pieces,
                            'price_per_case': Decimal(str(price)),
                            'is_active': True,
                        }
                    )
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class RemoveDrinkView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Supprime une boisson des options de l'événement et des prévisions"""
    
    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        return user_can_manage_expenses(self.request.user, self.event)

    def post(self, request, event_id):
        try:
            data = json.loads(request.body)
            drink_name = data.get('drink_name')
            
            if not drink_name:
                return JsonResponse({'success': False, 'error': 'Nom de boisson manquant'})
            
            # 1. Supprimer des options de l'événement
            drink_options = self.event.drink_options or []
            if drink_name in drink_options:
                drink_options.remove(drink_name)
                self.event.drink_options = drink_options
                self.event.save()
            
            # 2. Supprimer des prévisions
            forecast = getattr(self.event, 'forecast', None)
            if forecast:
                new_forecast = [d for d in forecast.drink_forecast if d.get('name') != drink_name]
                forecast.drink_forecast = new_forecast
                forecast.save()
            
            # 3. Supprimer le conditionnement
            DrinkPackaging.objects.filter(
                event=self.event,
                drink_name=drink_name
            ).delete()
            
            return JsonResponse({'success': True})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class ExportForecastPDFView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Exporte les prévisions en PDF"""
    
    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        return user_can_manage_expenses(self.request.user, self.event)

    def get(self, request, event_id):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from io import BytesIO
        from datetime import datetime
        
        event = self.event
        forecast = getattr(event, 'forecast', None)
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], 
                                      fontSize=20, textColor=colors.HexColor('#2C3E50'),
                                      alignment=1, spaceAfter=20)
        story.append(Paragraph(f"Prévisions - {event.name}", title_style))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        if forecast:
            story.append(Paragraph(f"Total invités: {forecast.total_guests_expected}", styles['Normal']))
            story.append(Paragraph(f"Taux de présence: {forecast.attendance_rate}%", styles['Normal']))
            story.append(Paragraph(f"Tournées: {forecast.number_of_services}", styles['Normal']))
            story.append(Paragraph(f"Devise: {forecast.currency}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Calculer les données
            total_guests = forecast.total_guests_expected
            attending = int(total_guests * (forecast.attendance_rate / 100))
            total_with_services = attending * forecast.number_of_services
            
            data = [['Boisson', '%', 'Personnes', 'Pièces/casier', 'Casiers', 'Coût']]
            total_cost = 0
            
            for item in forecast.drink_forecast:
                percentage = item.get('percentage', 0)
                people = int((percentage / 100) * total_with_services)
                pieces = item.get('pieces_per_case', 12)
                price = item.get('price_per_case', 0)
                cases = (people + pieces - 1) // pieces if people > 0 else 0
                cost = cases * price
                total_cost += cost
                
                data.append([
                    item.get('name', ''),
                    f"{percentage}%",
                    str(people),
                    str(pieces),
                    str(cases),
                    f"{cost:.2f}"
                ])
            
            data.append(['', '', '', '', 'TOTAL', f"{total_cost:.2f}"])
            
            table = Table(data, colWidths=[100, 40, 50, 50, 40, 60])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B5CF6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ALIGN', (5, 1), (5, -1), 'RIGHT'),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"Coût total estimé: {total_cost:.2f} {forecast.currency}", 
                                   styles['Heading2']))
        else:
            story.append(Paragraph("Aucune prévision enregistrée.", styles['Normal']))
        
        story.append(Spacer(1, 30))
        story.append(Paragraph("Généré par KaramuManage", styles['Italic']))
        
        doc.build(story)
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="previsions_{event.slug}.pdf"'
        return response


# ============================================================
# ESTIMATION (basée sur les réponses réelles)
# ============================================================

class EstimationDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'expenses/estimation.html'

    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        return user_can_manage_expenses(self.request.user, self.event)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.event

        currency = self.request.session.get(f'estimation_currency_{event.id}', 'CDF')
        margin = self.request.session.get(f'estimation_margin_{event.id}', 0)
        include_pending = self.request.session.get(f'estimation_pending_{event.id}', True)
        pending_rate = self.request.session.get(f'estimation_pending_rate_{event.id}', 75)
        number_of_services = self.request.session.get(f'estimation_services_{event.id}', 1)

        service = EstimationService(
            event,
            margin_percentage=margin,
            include_pending=include_pending,
            pending_rate=pending_rate,
            number_of_services=number_of_services
        )

        estimation = service.calculate_needs()
        chart_data = service.get_chart_data()
        stats = service.get_stats()

        form = EstimationSettingsForm(initial={
            'currency': currency,
            'margin_percentage': margin,
            'include_pending': include_pending,
            'pending_rate': pending_rate,
            'number_of_services': number_of_services,
        })

        context.update({
            'event': event,
            'estimation': estimation,
            'chart_data': json.dumps(chart_data),
            'stats': stats,
            'form': form,
            'has_packagings': DrinkPackaging.objects.filter(event=event, is_active=True).exists(),
            'has_responses': GuestResponse.objects.filter(event=event, will_attend=True).exists(),
        })
        return context


class SaveEstimationSettingsView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        return user_can_manage_expenses(self.request.user, self.event)

    def post(self, request, event_id):
        form = EstimationSettingsForm(request.POST)
        if form.is_valid():
            request.session[f'estimation_currency_{event_id}'] = form.cleaned_data.get('currency', 'CDF')
            request.session[f'estimation_margin_{event_id}'] = form.cleaned_data.get('margin_percentage', 0)
            request.session[f'estimation_pending_{event_id}'] = form.cleaned_data.get('include_pending', True)
            request.session[f'estimation_pending_rate_{event_id}'] = form.cleaned_data.get('pending_rate', 75)
            request.session[f'estimation_services_{event_id}'] = form.cleaned_data.get('number_of_services', 1)
            messages.success(request, _('Paramètres mis à jour.'))
        return redirect('expenses:estimation', event_id=event_id)


class ExportDevisPDFView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        return user_can_manage_expenses(self.request.user, self.event)

    def get(self, request, event_id):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.utils import ImageReader
            from io import BytesIO
            import os
        except ImportError:
            messages.error(request, _('ReportLab non installé.'))
            return redirect('expenses:estimation', event_id=event_id)

        event = self.event
        currency = request.session.get(f'estimation_currency_{event.id}', 'CDF')
        margin = request.session.get(f'estimation_margin_{event.id}', 0)
        include_pending = request.session.get(f'estimation_pending_{event.id}', True)
        pending_rate = request.session.get(f'estimation_pending_rate_{event.id}', 75)
        number_of_services = request.session.get(f'estimation_services_{event.id}', 1)

        service = EstimationService(
            event,
            margin_percentage=margin,
            include_pending=include_pending,
            pending_rate=pending_rate,
            number_of_services=number_of_services
        )
        estimation = service.calculate_needs()

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=72)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                     fontSize=24, textColor=colors.HexColor('#2C3E50'),
                                     alignment=1, spaceAfter=30)

        story = []

        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
        if os.path.exists(logo_path):
            try:
                logo = ImageReader(logo_path)
                story.append(Image(logo, width=60*mm, height=20*mm))
                story.append(Spacer(1, 10))
            except:
                pass

        story.append(Paragraph("Devis - Estimation des boissons", title_style))
        story.append(Paragraph(f"Événement: {event.name}", styles['Normal']))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        
        organizer = event.main_organizer
        story.append(Paragraph(f"Organisateur: {organizer.first_name} {organizer.last_name}", styles['Normal']))
        story.append(Spacer(1, 20))

        story.append(Paragraph(f"Marge: {margin}% | Taux présence: {pending_rate}% | Tournées: {number_of_services}", styles['Normal']))
        story.append(Spacer(1, 20))

        data = [['Boisson', 'Personnes', 'Pièces/casier', 'Casiers', 'Prix/casier', 'Total']]
        for item in estimation['details']:
            if item.get('is_other', False):
                data.append([f"{item['drink_name']} *", str(item['needed_pieces']), '?', '?', '?', '?'])
            else:
                data.append([
                    item['drink_name'],
                    str(item['needed_pieces']),
                    str(item['pieces_per_case']),
                    str(item['cases_needed']),
                    f"{item['price_per_case']:.2f}",
                    f"{item['cost']:.2f}"
                ])

        data.append(['', '', '', '', 'Total', f"{estimation['total_cost']:.2f} {currency}"])

        table = Table(data, colWidths=[80, 50, 50, 40, 50, 60])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B5CF6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ALIGN', (5, 1), (5, -1), 'RIGHT'),
        ]))

        story.append(table)
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Coût total: {estimation['total_cost']:.2f} {currency}", styles['Title']))
        story.append(Spacer(1, 30))
        story.append(Paragraph("Généré par KaramuManage", styles['Italic']))

        doc.build(story)
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="devis_{event.slug}_{datetime.now().strftime("%Y%m%d")}.pdf"'
        return response


class ExportDevisSummaryView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        return user_can_manage_expenses(self.request.user, self.event)

    def get(self, request, event_id):
        currency = request.session.get(f'estimation_currency_{event_id}', 'CDF')
        margin = request.session.get(f'estimation_margin_{event_id}', 0)
        include_pending = request.session.get(f'estimation_pending_{event_id}', True)
        pending_rate = request.session.get(f'estimation_pending_rate_{event_id}', 75)
        number_of_services = request.session.get(f'estimation_services_{event_id}', 1)

        service = EstimationService(
            self.event,
            margin_percentage=margin,
            include_pending=include_pending,
            pending_rate=pending_rate,
            number_of_services=number_of_services
        )
        estimation = service.calculate_needs()

        response = HttpResponse(content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="devis_{self.event.slug}.txt"'

        lines = [
            "=" * 50,
            f"DEVIS - {self.event.name.upper()}",
            "=" * 50,
            f"Devise: {currency}",
            f"Marge: {margin}%",
            f"Tournées: {number_of_services}",
            "-" * 50,
        ]

        for item in estimation['details']:
            if item.get('is_other', False):
                lines.append(f"{item['drink_name']}: {item['needed_pieces']} personnes (NON CONFIGURÉ)")
            else:
                lines.append(
                    f"{item['drink_name']}: {item['needed_pieces']} personnes "
                    f"=> {item['cases_needed']} casiers ({item['cost']:.2f} {currency})"
                )

        lines.extend([
            "-" * 50,
            f"Total: {estimation['total_cost']:.2f} {currency}",
            "=" * 50,
            "Généré par KaramuManage",
        ])

        response.write('\n'.join(lines))
        return response