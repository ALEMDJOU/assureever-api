import io
import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib.utils import ImageReader

from app.models.remboursement import Remboursement
from app.models.feuille_maladie import FeuilleMaladie

_LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.jpg")
_LOGO = ImageReader(_LOGO_PATH) if os.path.exists(_LOGO_PATH) else None

# ─── Palette ──────────────────────────────────────────────────────────────────

NAVY     = colors.HexColor("#0f2942")
TEAL     = colors.HexColor("#0d9488")
AMBER    = colors.HexColor("#d97706")
GREEN    = colors.HexColor("#16a34a")
RED      = colors.HexColor("#dc2626")
SLATE    = colors.HexColor("#475569")
SLATE_LT = colors.HexColor("#cbd5e1")
LIGHT_BG = colors.HexColor("#f1f5f9")
BORDER   = colors.HexColor("#e2e8f0")

PAGE_W, PAGE_H = A4
HEADER_H = 3.0 * cm
FOOTER_H = 1.4 * cm

_STYLES = getSampleStyleSheet()


# ─── Letterhead (bandeau + pied de page, dessiné sur chaque page) ─────────────

def _letterhead(titre_document: str):
    def draw(canvas, _doc):
        canvas.saveState()

        # Bandeau supérieur
        canvas.setFillColor(NAVY)
        canvas.rect(0, PAGE_H - HEADER_H, PAGE_W, HEADER_H, fill=1, stroke=0)
        canvas.setFillColor(TEAL)
        canvas.rect(0, PAGE_H - HEADER_H - 0.1 * cm, PAGE_W, 0.1 * cm, fill=1, stroke=0)

        # Logo applicatif (rond, avec liseré blanc) ou repli sur un badge texte
        logo_cx, logo_cy, logo_r = 2.3 * cm, PAGE_H - HEADER_H / 2, 0.85 * cm
        if _LOGO is not None:
            canvas.saveState()
            path = canvas.beginPath()
            path.circle(logo_cx, logo_cy, logo_r)
            canvas.clipPath(path, stroke=0, fill=0)
            canvas.drawImage(
                _LOGO,
                logo_cx - logo_r, logo_cy - logo_r,
                width=logo_r * 2, height=logo_r * 2,
                mask="auto", preserveAspectRatio=True, anchor="c",
            )
            canvas.restoreState()
            canvas.setStrokeColor(colors.white)
            canvas.setLineWidth(1.2)
            canvas.circle(logo_cx, logo_cy, logo_r, fill=0, stroke=1)
        else:
            canvas.setFillColor(TEAL)
            canvas.circle(logo_cx, logo_cy, logo_r, fill=1, stroke=0)
            canvas.setFillColor(colors.white)
            canvas.setFont("Helvetica-Bold", 13)
            canvas.drawCentredString(logo_cx, logo_cy - 5, "AE")

        # Nom de l'application + institution
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 15)
        canvas.drawString(3.9 * cm, PAGE_H - HEADER_H / 2 + 6, "AssureEver")
        canvas.setFont("Helvetica", 8.5)
        canvas.setFillColor(SLATE_LT)
        canvas.drawString(3.9 * cm, PAGE_H - HEADER_H / 2 - 7,
                           "Organisme de Sécurité Sociale — Votre santé, notre engagement")

        # Titre du document
        canvas.setFont("Helvetica-Bold", 12)
        canvas.setFillColor(colors.white)
        canvas.drawRightString(PAGE_W - 2 * cm, PAGE_H - HEADER_H / 2 + 1, titre_document.upper())

        # Pied de page
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.6)
        canvas.line(2 * cm, FOOTER_H, PAGE_W - 2 * cm, FOOTER_H)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(SLATE)
        canvas.drawString(2 * cm, FOOTER_H - 12,
                           f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
        canvas.drawRightString(PAGE_W - 2 * cm, FOOTER_H - 12, f"Page {canvas.getPageNumber()}")
        canvas.setFont("Helvetica-Oblique", 7.5)
        canvas.drawCentredString(PAGE_W / 2, FOOTER_H - 12, "Système de Gestion — Sécurité Sociale")

        canvas.restoreState()
    return draw


def _nouveau_document(titre_document: str) -> SimpleDocTemplate:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=HEADER_H + 0.9 * cm,
        bottomMargin=FOOTER_H + 0.6 * cm,
    )
    doc._buffer = buffer
    doc._letterhead = _letterhead(titre_document)
    return doc


def _finaliser(doc: SimpleDocTemplate, elements: list) -> bytes:
    doc.build(elements, onFirstPage=doc._letterhead, onLaterPages=doc._letterhead)
    return doc._buffer.getvalue()


# ─── Composants visuels réutilisables ──────────────────────────────────────────

def _badge(text: str, bg_color) -> Drawing:
    width, height = 5.0 * cm, 0.7 * cm
    d = Drawing(width, height)
    d.add(Rect(0, 0, width, height, rx=height / 2, ry=height / 2, fillColor=bg_color, strokeColor=None))
    d.add(String(width / 2, height / 2 - 3.2, text, fillColor=colors.white,
                  fontName="Helvetica-Bold", fontSize=9, textAnchor="middle"))
    return d


def _meta_strip(numero: str, date_label: str, date_value: str, badge: Drawing) -> Table:
    meta_style = ParagraphStyle("Meta", fontName="Helvetica", fontSize=9, textColor=SLATE, leading=13)
    cell_numero = Paragraph(f'<font color="#0f2942"><b>N°</b></font><br/>{numero}', meta_style)
    cell_date   = Paragraph(f'<font color="#0f2942"><b>{date_label}</b></font><br/>{date_value}', meta_style)

    table = Table([[cell_numero, cell_date, badge]], colWidths=[6 * cm, 6 * cm, 5 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (2, 0), (2, 0), 14),
        ("BOX", (0, 0), (-1, -1), 0.75, BORDER),
    ]))
    return table


def _section_title(text: str) -> Paragraph:
    style = ParagraphStyle(
        "Section", fontName="Helvetica-Bold", fontSize=11.5,
        textColor=NAVY, spaceBefore=4, spaceAfter=8,
    )
    return Paragraph(f'<font color="#0d9488">●</font>&nbsp;&nbsp;{text}', style)


def _card(rows: list) -> Table:
    table = Table(rows, colWidths=[6 * cm, 11 * cm])
    style = [
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
        ("TEXTCOLOR", (1, 0), (1, -1), SLATE),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("BOX", (0, 0), (-1, -1), 0.75, BORDER),
    ]
    for i in range(len(rows) - 1):
        style.append(("LINEBELOW", (0, i), (-1, i), 0.5, BORDER))
    table.setStyle(TableStyle(style))
    return table


def _highlight_card(rows: list) -> Table:
    """Carte mise en avant (montant final) avec fond et texte teal/navy accentués."""
    table = Table(rows, colWidths=[10 * cm, 7 * cm])
    style = [
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), SLATE),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("BOX", (0, 0), (-1, -1), 0.75, BORDER),
        # Dernière ligne (montant net) mise en avant
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ecfdf5")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, -1), (-1, -1), 12),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor("#065f46")),
        ("TOPPADDING", (0, -1), (-1, -1), 12),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
        ("LINEABOVE", (0, -1), (-1, -1), 1, TEAL),
    ]
    for i in range(len(rows) - 2):
        style.append(("LINEBELOW", (0, i), (-1, i), 0.5, BORDER))
    table.setStyle(TableStyle(style))
    return table


# ─── Facture de remboursement ──────────────────────────────────────────────────

_REMBOURSEMENT_BADGE = {
    "EN_ATTENTE": ("En attente", AMBER),
    "PAYE":       ("Payé", GREEN),
    "ANNULE":     ("Annulé", RED),
}


def generer_facture_pdf(remboursement: Remboursement) -> bytes:
    """Génère le PDF de la facture d'un remboursement."""
    doc = _nouveau_document("Facture de remboursement")
    elements: list = []

    label, color = _REMBOURSEMENT_BADGE.get(remboursement.statut.value, ("—", SLATE))
    elements.append(_meta_strip(
        numero=str(remboursement.id),
        date_label="Date",
        date_value=remboursement.date_remboursement.strftime("%d/%m/%Y à %H:%M"),
        badge=_badge(label, color),
    ))
    elements.append(Spacer(1, 0.7 * cm))

    elements.append(_section_title("Détails du remboursement"))
    elements.append(_card([
        ["Mode de paiement", remboursement.mode_paiement.value.replace("_", " ").title()],
        ["Taux de remboursement", f"{remboursement.taux_remboursement:.0f} %"],
    ]))
    elements.append(Spacer(1, 0.6 * cm))

    elements.append(_section_title("Récapitulatif financier"))
    elements.append(_highlight_card([
        ["Montant de la consultation", f"{remboursement.montant_consultation:,.0f} FCFA"],
        ["Montant remboursé", f"{remboursement.montant_rembourse:,.0f} FCFA"],
    ]))

    return _finaliser(doc, elements)


# ─── Feuille de maladie ─────────────────────────────────────────────────────────

_FEUILLE_BADGE = {
    "EN_ATTENTE": ("En attente", AMBER),
    "COMPLETE":   ("Complétée", TEAL),
    "REMBOURSEE": ("Remboursée", GREEN),
}


def generer_feuille_pdf(feuille: FeuilleMaladie) -> bytes:
    """
    Génère le PDF d'une feuille de maladie.
    Suppose que `feuille.assure` et `feuille.consultation` (avec `consultation.medecin`)
    sont déjà chargés (eager loading via selectinload).
    """
    doc = _nouveau_document("Feuille de maladie")
    elements: list = []

    assure = feuille.assure
    consultation = feuille.consultation
    medecin = consultation.medecin if consultation else None

    label, color = _FEUILLE_BADGE.get(feuille.statut.value, ("—", SLATE))
    elements.append(_meta_strip(
        numero=str(feuille.id),
        date_label="Enregistrée le",
        date_value=feuille.created_at.strftime("%d/%m/%Y à %H:%M"),
        badge=_badge(label, color),
    ))
    elements.append(Spacer(1, 0.7 * cm))

    elements.append(_section_title("Assuré"))
    if assure:
        elements.append(_card([
            ["N° Assuré", assure.numero_assure],
            ["Nom complet", f"{assure.prenom} {assure.nom}"],
            ["Date de naissance", assure.date_naissance.strftime("%d/%m/%Y")],
        ]))
    elements.append(Spacer(1, 0.6 * cm))

    elements.append(_section_title("Consultation"))
    lignes_consultation = []
    if medecin:
        lignes_consultation.append(
            ["Médecin", f"Dr. {medecin.prenom} {medecin.nom} — {medecin.type_medecin.value.title()}"]
        )
    if consultation:
        lignes_consultation.append(["Date de consultation", consultation.date_consultation.strftime("%d/%m/%Y")])
        lignes_consultation.append(["Motif", consultation.motif])
        if consultation.diagnostic:
            lignes_consultation.append(["Diagnostic", consultation.diagnostic])
        if consultation.actes_realises:
            lignes_consultation.append(["Actes réalisés", consultation.actes_realises])
    elements.append(_card(lignes_consultation))
    elements.append(Spacer(1, 0.6 * cm))

    elements.append(_section_title("Montant"))
    elements.append(_highlight_card([
        ["Montant de la consultation", f"{feuille.montant_consultation:,.0f} FCFA"],
    ]))

    if feuille.observations:
        elements.append(Spacer(1, 0.6 * cm))
        elements.append(_section_title("Observations"))
        obs_style = ParagraphStyle("Obs", fontName="Helvetica", fontSize=9.5, textColor=SLATE, leading=14)
        obs_table = Table([[Paragraph(feuille.observations, obs_style)]], colWidths=[17 * cm])
        obs_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
            ("BOX", (0, 0), (-1, -1), 0.75, BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ]))
        elements.append(obs_table)

    return _finaliser(doc, elements)
