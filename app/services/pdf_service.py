import io
import os
import re
import unicodedata
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
from app.models.prescription import Prescription

_LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.jpg")
_LOGO = ImageReader(_LOGO_PATH) if os.path.exists(_LOGO_PATH) else None

# ─── Palette de Couleurs Modernes ─────────────────────────────────────────────

NAVY     = colors.HexColor("#0f2942")  # Couleur principale sombre (En-têtes, labels)
TEAL     = colors.HexColor("#0d9488")  # Couleur secondaire d'accentuation (Bordures, détails)
AMBER    = colors.HexColor("#d97706")  # Statut : En attente
GREEN    = colors.HexColor("#16a34a")  # Statut : Validé / Payé
RED      = colors.HexColor("#dc2626")  # Statut : Annulé
SLATE    = colors.HexColor("#475569")  # Texte principal
SLATE_LT = colors.HexColor("#cbd5e1")  # Texte secondaire clair
LIGHT_BG = colors.HexColor("#f8fafc")  # Fond de carte / section
BORDER   = colors.HexColor("#e2e8f0")  # Bordures grises très douces

PAGE_W, PAGE_H = A4
HEADER_H = 3.0 * cm
FOOTER_H = 1.4 * cm

_STYLES = getSampleStyleSheet()

_TYPE_MEDECIN_LABEL = {
    "GENERALISTE": "Médecin généraliste",
    "SPECIALISTE": "Médecin spécialiste",
}

_MODE_PAIEMENT_LABEL = {
    "VIREMENT_BANCAIRE": "Virement bancaire",
    "ESPECES": "Espèces",
    "MOBILE_MONEY": "Mobile Money",
}


def nom_fichier_pdf(prefixe: str, prenom: str | None, nom: str | None) -> str:
    """Nom de fichier de téléchargement propre (ex: Feuille_Maladie_Paul_Nguemo.pdf)."""
    parties = [prefixe] + [p for p in (prenom, nom) if p]
    brut = "_".join(parties)
    sans_accents = unicodedata.normalize("NFKD", brut).encode("ascii", "ignore").decode("ascii")
    propre = re.sub(r"[^A-Za-z0-9]+", "_", sans_accents).strip("_")
    return f"{propre}.pdf"


def _numero_court(uuid_value, prefix: str) -> str:
    """Référence courte et lisible pour l'affichage (ex: FM-3DD92F2D)."""
    return f"{prefix}-{str(uuid_value).split('-')[0].upper()}"


# ─── Composants Visuels Redessinés ────────────────────────────────────────────

def _signature_block(label_gauche: str, label_droite: str) -> Table:
    """Cadre de signatures officiel et esthétique."""
    style_title = ParagraphStyle("SignTitle", fontName="Helvetica-Bold", fontSize=9, textColor=NAVY)
    style_body = ParagraphStyle("SignBody", fontName="Helvetica-Oblique", fontSize=8, textColor=SLATE, alignment=TA_CENTER)
    
    box_gauche = [
        Paragraph(label_gauche, style_title),
        Spacer(1, 1.4 * cm),
        Paragraph("Signature et cachet", style_body)
    ]
    box_droite = [
        Paragraph(label_droite, style_title),
        Spacer(1, 1.4 * cm),
        Paragraph("Signature et cachet", style_body)
    ]
    
    table = Table(
        [[box_gauche, box_droite]],
        colWidths=[8.25 * cm, 8.25 * cm],
    )
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, 0), LIGHT_BG),
        ("BACKGROUND", (1, 0), (1, 0), LIGHT_BG),
        ("BOX", (0, 0), (0, 0), 0.75, BORDER),
        ("BOX", (1, 0), (1, 0), 0.75, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return table


def _badge(text: str, bg_color) -> Drawing:
    """Badge de statut élégant avec coins arrondis."""
    width, height = 4.0 * cm, 0.6 * cm
    d = Drawing(width, height)
    d.add(Rect(0, 0, width, height, rx=height / 2, ry=height / 2, fillColor=bg_color, strokeColor=None))
    d.add(String(width / 2, height / 2 - 3.0, text.upper(), fillColor=colors.white,
                  fontName="Helvetica-Bold", fontSize=8, textAnchor="middle"))
    return d


def _meta_strip(numero: str, date_label: str, date_value: str, badge: Drawing) -> Table:
    """Bandeau d'informations clés (Référence, Date, Statut)."""
    meta_style = ParagraphStyle("Meta", fontName="Helvetica", fontSize=9, textColor=SLATE, leading=13)
    cell_numero = Paragraph(f'<font color="#0f2942"><b>RÉFÉRENCE</b></font><br/>{numero}', meta_style)
    cell_date   = Paragraph(f'<font color="#0f2942"><b>{date_label.upper()}</b></font><br/>{date_value}', meta_style)

    table = Table([[cell_numero, cell_date, badge]], colWidths=[6.5 * cm, 5.5 * cm, 5.0 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (2, 0), (2, 0), 16),
        ("BOX", (0, 0), (-1, -1), 1.0, BORDER),
    ]))
    return table


def _section_title(text: str) -> Table:
    """Titre de section moderne avec barre verticale d'accentuation en Teal."""
    style = ParagraphStyle(
        "SectionText", fontName="Helvetica-Bold", fontSize=10,
        textColor=NAVY, spaceBefore=0, spaceAfter=0,
    )
    p = Paragraph(text.upper(), style)
    t = Table([[ "", p ]], colWidths=[0.25 * cm, 16.75 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), TEAL),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (1, 0), (1, 0), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _card(rows: list) -> Table:
    """Tableau de données auto-adaptatif (Card) avec encadré et lignes séparatrices."""
    lbl_style = ParagraphStyle("CardLbl", fontName="Helvetica-Bold", fontSize=9, textColor=NAVY, leading=12)
    val_style = ParagraphStyle("CardVal", fontName="Helvetica", fontSize=9, textColor=SLATE, leading=12)
    
    formatted_rows = []
    for r in rows:
        lbl = Paragraph(r[0], lbl_style) if isinstance(r[0], str) else r[0]
        val = Paragraph(r[1], val_style) if isinstance(r[1], str) else r[1]
        formatted_rows.append([lbl, val])

    table = Table(formatted_rows, colWidths=[5.5 * cm, 11.5 * cm])
    style = [
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("BOX", (0, 0), (-1, -1), 0.75, BORDER),
    ]
    for i in range(len(rows) - 1):
        style.append(("LINEBELOW", (0, i), (-1, i), 0.5, BORDER))
    table.setStyle(TableStyle(style))
    return table


def _highlight_card(rows: list) -> Table:
    """Carte financière (Montants) avec surbrillance verte pour le net remboursé/total."""
    lbl_style = ParagraphStyle("HiLbl", fontName="Helvetica", fontSize=9.5, textColor=SLATE, leading=13)
    val_style = ParagraphStyle("HiVal", fontName="Helvetica", fontSize=9.5, textColor=SLATE, leading=13, alignment=TA_RIGHT)
    
    lbl_bold_style = ParagraphStyle("HiLblB", fontName="Helvetica-Bold", fontSize=11, textColor=colors.HexColor("#065f46"), leading=14)
    val_bold_style = ParagraphStyle("HiValB", fontName="Helvetica-Bold", fontSize=11, textColor=colors.HexColor("#065f46"), leading=14, alignment=TA_RIGHT)
    
    formatted_rows = []
    for idx, r in enumerate(rows):
        is_last = (idx == len(rows) - 1)
        if is_last:
            lbl = Paragraph(r[0], lbl_bold_style)
            val = Paragraph(r[1], val_bold_style)
        else:
            lbl = Paragraph(r[0], lbl_style)
            val = Paragraph(r[1], val_style)
        formatted_rows.append([lbl, val])

    table = Table(formatted_rows, colWidths=[11.5 * cm, 5.5 * cm])
    style = [
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -2), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -2), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("BOX", (0, 0), (-1, -1), 0.75, BORDER),
        # Dernière ligne mise en avant en vert clair
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ecfdf5")),
        ("TOPPADDING", (0, -1), (-1, -1), 10),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
        ("LINEABOVE", (0, -1), (-1, -1), 1.2, TEAL),
    ]
    for i in range(len(rows) - 2):
        style.append(("LINEBELOW", (0, i), (-1, i), 0.5, BORDER))
    table.setStyle(TableStyle(style))
    return table


# ─── Papier En-tête (Letterhead) ──────────────────────────────────────────────

def _letterhead(titre_document: str, reference: str = ""):
    def draw(canvas, _doc):
        canvas.saveState()

        # Ligne d'accentuation en haut de la page
        canvas.setFillColor(NAVY)
        canvas.rect(0, PAGE_H - 0.2 * cm, PAGE_W, 0.2 * cm, fill=1, stroke=0)
        canvas.setFillColor(TEAL)
        canvas.rect(0, PAGE_H - 0.3 * cm, PAGE_W, 0.1 * cm, fill=1, stroke=0)

        # Dessin du logo (ou badge textuel par défaut)
        logo_cx, logo_cy, logo_r = 2.5 * cm, PAGE_H - 1.8 * cm, 0.7 * cm
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
            canvas.setStrokeColor(BORDER)
            canvas.setLineWidth(1)
            canvas.circle(logo_cx, logo_cy, logo_r, fill=0, stroke=1)
        else:
            canvas.setFillColor(TEAL)
            canvas.circle(logo_cx, logo_cy, logo_r, fill=1, stroke=0)
            canvas.setFillColor(colors.white)
            canvas.setFont("Helvetica-Bold", 12)
            canvas.drawCentredString(logo_cx, logo_cy - 4, "AE")

        # Informations de l'organisation (Gauche)
        canvas.setFillColor(NAVY)
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawString(3.6 * cm, PAGE_H - 1.6 * cm, "AssureEver")
        canvas.setFont("Helvetica-Bold", 7.5)
        canvas.setFillColor(TEAL)
        canvas.drawString(3.6 * cm, PAGE_H - 2.0 * cm, "SÉCURITÉ SOCIALE")
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(SLATE)
        canvas.drawString(3.6 * cm, PAGE_H - 2.3 * cm, "Votre santé, notre engagement")

        # Infos du document (Droite)
        canvas.setFont("Helvetica-Bold", 12)
        canvas.setFillColor(NAVY)
        canvas.drawRightString(PAGE_W - 2 * cm, PAGE_H - 1.6 * cm, titre_document.upper())
        
        if reference:
            canvas.setFont("Helvetica-Bold", 8.5)
            canvas.setFillColor(SLATE)
            canvas.drawRightString(PAGE_W - 2 * cm, PAGE_H - 2.0 * cm, f"Réf : {reference}")
        
        # Ligne de séparation horizontale sous le bandeau
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.8)
        canvas.line(2 * cm, PAGE_H - 2.8 * cm, PAGE_W - 2 * cm, PAGE_H - 2.8 * cm)

        # Pied de page (Footer)
        canvas.line(2 * cm, FOOTER_H, PAGE_W - 2 * cm, FOOTER_H)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(SLATE)
        canvas.drawString(2 * cm, FOOTER_H - 12,
                           f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
        canvas.drawRightString(PAGE_W - 2 * cm, FOOTER_H - 12, f"Page {canvas.getPageNumber()}")
        canvas.setFont("Helvetica-Oblique", 7.5)
        canvas.drawCentredString(PAGE_W / 2, FOOTER_H - 12, "Système de Gestion de Sécurité Sociale — AssureEver")

        canvas.restoreState()
    return draw


def _nouveau_document(titre_document: str, reference: str = "") -> SimpleDocTemplate:
    """Initialise un document PDF A4 prêt pour la construction."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=HEADER_H + 0.5 * cm,
        bottomMargin=FOOTER_H + 0.6 * cm,
    )
    doc._buffer = buffer
    doc._letterhead = _letterhead(titre_document, reference)
    return doc


def _finaliser(doc: SimpleDocTemplate, elements: list) -> bytes:
    """Compile le document ReportLab et renvoie les octets du fichier PDF."""
    doc.build(elements, onFirstPage=doc._letterhead, onLaterPages=doc._letterhead)
    return doc._buffer.getvalue()


# ─── Facture de remboursement ─────────────────────────────────────────────────

_REMBOURSEMENT_BADGE = {
    "EN_ATTENTE": ("En attente", AMBER),
    "PAYE":       ("Payé", GREEN),
    "ANNULE":     ("Annulé", RED),
}


def generer_facture_pdf(remboursement: Remboursement) -> bytes:
    """Génère le PDF de la facture d'un remboursement."""
    ref_facture = _numero_court(remboursement.id, "RB")
    doc = _nouveau_document("Facture de remboursement", reference=ref_facture)
    elements: list = []

    # Bandeau du statut de paiement
    label, color = _REMBOURSEMENT_BADGE.get(remboursement.statut.value, ("—", SLATE))
    elements.append(_meta_strip(
        numero=ref_facture,
        date_label="Date",
        date_value=remboursement.date_remboursement.strftime("%d/%m/%Y à %H:%M"),
        badge=_badge(label, color),
    ))
    elements.append(Spacer(1, 0.6 * cm))

    # section 1 : Assuré
    elements.append(_section_title("Bénéficiaire (Assuré)"))
    elements.append(Spacer(1, 0.2 * cm))
    assure = remboursement.assure
    if assure:
        elements.append(_card([
            ["N° Assuré", assure.numero_assure],
            ["Nom complet", f"{assure.prenom} {assure.nom}"],
            ["Date de naissance", assure.date_naissance.strftime("%d/%m/%Y")],
        ]))
    else:
        elements.append(_card([["Information", "Aucun assuré lié à ce remboursement."]]))
    elements.append(Spacer(1, 0.6 * cm))

    # section 2 : Source (Feuille de maladie)
    feuille = remboursement.feuille_maladie
    if feuille:
        consultation = feuille.consultation
        medecin = consultation.medecin if consultation else None
        
        elements.append(_section_title("Détails médicaux associés"))
        elements.append(Spacer(1, 0.2 * cm))
        
        lignes_med = [
            ["N° Feuille de maladie", _numero_court(feuille.id, "FM")]
        ]
        if medecin:
            type_label = _TYPE_MEDECIN_LABEL.get(medecin.type_medecin.value, medecin.type_medecin.value.title())
            lignes_med.append(["Médecin consulté", f"Dr. {medecin.prenom} {medecin.nom} ({type_label})"])
        if consultation:
            lignes_med.append(["Date de consultation", consultation.date_consultation.strftime("%d/%m/%Y")])
            
        elements.append(_card(lignes_med))
        elements.append(Spacer(1, 0.6 * cm))

    # Section 3 : Détails du paiement
    mode_label = _MODE_PAIEMENT_LABEL.get(remboursement.mode_paiement.value, remboursement.mode_paiement.value.title())
    details = [
        ["Mode de paiement", mode_label],
        ["Taux de remboursement", f"{remboursement.taux_remboursement:.0f} %"],
    ]
    if remboursement.reference_virement:
        details.append(["Référence de transaction / virement", remboursement.reference_virement])

    elements.append(_section_title("Modalités de paiement"))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(_card(details))
    elements.append(Spacer(1, 0.6 * cm))

    # Section 4 : Finances
    elements.append(_section_title("Récapitulatif financier"))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(_highlight_card([
        ["Montant total des frais de consultation", f"{remboursement.montant_consultation:,.0f} FCFA"],
        ["Montant net pris en charge (remboursé)", f"{remboursement.montant_rembourse:,.0f} FCFA"],
    ]))
    
    # Signatures
    elements.append(Spacer(1, 1.0 * cm))
    elements.append(_signature_block("Pour l'organisme (Assureur)", "Visa du bénéficiaire"))

    return _finaliser(doc, elements)


# ─── Feuille de maladie ───────────────────────────────────────────────────────

_FEUILLE_BADGE = {
    "EN_ATTENTE": ("En attente", AMBER),
    "COMPLETE":   ("Complétée", TEAL),
    "REMBOURSEE": ("Remboursée", GREEN),
}


def generer_feuille_pdf(feuille: FeuilleMaladie) -> bytes:
    """Génère le PDF d'une feuille de maladie avec ses prescriptions éventuelles."""
    ref_feuille = _numero_court(feuille.id, "FM")
    doc = _nouveau_document("Feuille de maladie", reference=ref_feuille)
    elements: list = []

    assure = feuille.assure
    consultation = feuille.consultation
    medecin = consultation.medecin if consultation else None

    # Métadonnées et statut
    label, color = _FEUILLE_BADGE.get(feuille.statut.value, ("—", SLATE))
    elements.append(_meta_strip(
        numero=ref_feuille,
        date_label="Enregistrée le",
        date_value=feuille.created_at.strftime("%d/%m/%Y à %H:%M"),
        badge=_badge(label, color),
    ))
    elements.append(Spacer(1, 0.6 * cm))

    # Section 1 : Assuré
    elements.append(_section_title("Informations de l'Assuré"))
    elements.append(Spacer(1, 0.2 * cm))
    if assure:
        elements.append(_card([
            ["N° Assuré", assure.numero_assure],
            ["Nom complet", f"{assure.prenom} {assure.nom}"],
            ["Date de naissance", assure.date_naissance.strftime("%d/%m/%Y")],
        ]))
    elements.append(Spacer(1, 0.6 * cm))

    # Section 2 : Consultation médicale
    elements.append(_section_title("Détails de la consultation"))
    elements.append(Spacer(1, 0.2 * cm))
    lignes_consultation = []
    if medecin:
        type_label = _TYPE_MEDECIN_LABEL.get(medecin.type_medecin.value, medecin.type_medecin.value.title())
        lignes_consultation.append(
            ["Médecin traitant", f"Dr. {medecin.prenom} {medecin.nom} ({type_label})"]
        )
    if consultation:
        lignes_consultation.append(["Date de consultation", consultation.date_consultation.strftime("%d/%m/%Y")])
        lignes_consultation.append(["Motif de consultation", consultation.motif])
        if consultation.diagnostic:
            lignes_consultation.append(["Diagnostic médical", consultation.diagnostic])
        if consultation.actes_realises:
            lignes_consultation.append(["Actes ou examens réalisés", consultation.actes_realises])
    
    if lignes_consultation:
        elements.append(_card(lignes_consultation))
    elements.append(Spacer(1, 0.6 * cm))

    # Section 3 : Prescriptions / Ordonnance (si existantes)
    prescriptions = consultation.prescriptions if consultation else []
    if prescriptions:
        elements.append(_section_title("Prescriptions & Ordonnances médicales"))
        elements.append(Spacer(1, 0.2 * cm))
        prescription_rows = []
        for idx, p in enumerate(prescriptions):
            num = idx + 1
            if p.type_prescription.value == "MEDICAMENT" and p.prescription_medicament:
                pm = p.prescription_medicament
                desc = f"<b>{pm.nom_medicament}</b> ({pm.dosage})<br/>Posologie : {pm.posologie}<br/>Durée de traitement : {pm.duree_traitement_jours} jours"
                prescription_rows.append([f"Médicament n°{num}", desc])
            elif p.type_prescription.value == "CONSULTATION_SPECIALISTE" and p.prescription_consultation:
                pc = p.prescription_consultation
                spec_info = ""
                if pc.specialiste:
                    spec_info = f"<br/>Spécialiste recommandé : Dr. {pc.specialiste.prenom} {pc.specialiste.nom} ({pc.specialiste.specialite})"
                desc = f"<b>Recommandation de consultation spécialisée</b><br/>Motif : {pc.motif}{spec_info}"
                prescription_rows.append([f"Spécialiste n°{num}", desc])
        
        if prescription_rows:
            elements.append(_card(prescription_rows))
            elements.append(Spacer(1, 0.6 * cm))

    # Section 4 : Montant de la prestation
    elements.append(_section_title("Montant de la consultation"))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(_highlight_card([
        ["Frais de consultation médicale", f"{feuille.montant_consultation:,.0f} FCFA"],
    ]))

    # Section 5 : Observations (si existantes)
    if feuille.observations:
        elements.append(Spacer(1, 0.6 * cm))
        elements.append(_section_title("Observations de l'assureur"))
        elements.append(Spacer(1, 0.2 * cm))
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

    # Cadre de signatures
    elements.append(Spacer(1, 1.0 * cm))
    elements.append(_signature_block("Visa du médecin traitant", "Visa et cachet de l'organisme"))

    return _finaliser(doc, elements)
