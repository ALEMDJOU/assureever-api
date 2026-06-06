import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from app.models.remboursement import Remboursement


def generer_facture_pdf(remboursement: Remboursement) -> bytes:
    """
    Génère une facture PDF pour un remboursement donné.
    Retourne les bytes du PDF prêt à être téléchargé.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # En-tête
    titre_style = ParagraphStyle(
        "Titre",
        parent=styles["Title"],
        fontSize=18,
        textColor=colors.HexColor("#1a3a5c"),
        spaceAfter=12,
        alignment=TA_CENTER,
    )
    elements.append(Paragraph("ORGANISME DE SÉCURITÉ SOCIALE", titre_style))
    elements.append(Paragraph("FACTURE DE REMBOURSEMENT", titre_style))
    elements.append(Spacer(1, 0.5 * cm))

    # Ligne de séparation
    elements.append(
        Table(
            [[""]],
            colWidths=[17 * cm],
            style=TableStyle([("LINEABOVE", (0, 0), (-1, 0), 2, colors.HexColor("#1a3a5c"))]),
        )
    )
    elements.append(Spacer(1, 0.5 * cm))

    # Référence et date
    info_style = ParagraphStyle("Info", parent=styles["Normal"], fontSize=10, spaceAfter=6)
    elements.append(Paragraph(f"<b>N° Remboursement :</b> {remboursement.id}", info_style))
    elements.append(
        Paragraph(
            f"<b>Date :</b> {remboursement.date_remboursement.strftime('%d/%m/%Y à %H:%M')}",
            info_style,
        )
    )
    elements.append(Spacer(1, 0.5 * cm))

    # Tableau des détails
    donnees = [
        ["Désignation", "Montant"],
        ["Montant de la consultation", f"{remboursement.montant_consultation:,.0f} FCFA"],
        ["Taux de remboursement", f"{remboursement.taux_remboursement:.0f} %"],
        ["Montant remboursé", f"{remboursement.montant_rembourse:,.0f} FCFA"],
        ["Mode de paiement", remboursement.mode_paiement.value.replace("_", " ")],
        ["Statut", remboursement.statut.value],
    ]

    table = Table(donnees, colWidths=[10 * cm, 7 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 10),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                # Mettre en valeur la ligne montant remboursé
                ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 3), (-1, 3), colors.HexColor("#1a3a5c")),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 1 * cm))

    # Pied de page
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER,
    )
    elements.append(
        Paragraph(
            f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} — "
            "Système de Gestion Sécurité Sociale",
            footer_style,
        )
    )

    doc.build(elements)
    return buffer.getvalue()
