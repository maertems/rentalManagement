"""
PDF generator — produces rental documents as bytes using fpdf2.
Three document types: Quittance de Loyer, Avis d'Échéance, Quittance de Garantie.
"""
from __future__ import annotations

from pathlib import Path

from fpdf import FPDF
from num2words import num2words

from app.services.pdf_context import ReceiptContext

SIGNATURE_PATH = Path("/app/files/signature.png")
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_ITALIC = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Colours
BLUE = (23, 133, 196)       # #1785C4
DARK_BG = (60, 60, 60)
LIGHT_GREY = (240, 240, 240)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _amount_to_words_fr(amount: float) -> str:
    """Convert amount to French words; omit centimes when they are zero."""
    euros = int(amount)
    centimes = round((amount - euros) * 100)
    result = num2words(euros, lang="fr") + (" euro" if euros <= 1 else " euros")
    if centimes > 0:
        result += " et " + num2words(centimes, lang="fr") + (
            " centime" if centimes <= 1 else " centimes"
        )
    return result


def _fmt_price(amount: float) -> str:
    return f"{amount:,.2f} €".replace(",", " ")


class _RentalPDF(FPDF):
    """Base PDF with shared header/footer helpers."""

    _show_footer: bool = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_font("DejaVu", "", FONT_REGULAR)
        self.add_font("DejaVu", "B", FONT_BOLD)
        self.add_font("DejaVu", "I", FONT_ITALIC)

    def footer(self):
        if self._show_footer:
            self.set_y(-12)
            self.set_font("DejaVu", "I", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 5, f"Page {self.page_no()}/{{nb}}", align="C")
            self.set_text_color(0, 0, 0)

    def set_blue(self) -> None:
        self.set_text_color(*BLUE)

    def set_black(self) -> None:
        self.set_text_color(*BLACK)

    def set_white(self) -> None:
        self.set_text_color(*WHITE)

    def _quittance_header(self, ctx: ReceiptContext) -> None:
        """Header commun quittance loyer / garantie.
        Gauche : propriétaire. Droite haut : ADRESSE DU BIEN. Droite bas : locataire."""
        RIGHT_X = 110
        RIGHT_W = 85  # jusqu'à x=195

        # Propriétaire — gauche
        self.set_xy(15, 15)
        self.set_font("DejaVu", "B", 10)
        self.cell(0, 5, ctx.owner_name, ln=True)
        self.set_font("DejaVu", "", 9)
        for line in [ctx.owner_address,
                     f"{ctx.owner_zip} {ctx.owner_city}",
                     ctx.owner_phone,
                     ctx.owner_email]:
            if line and line.strip():
                self.set_x(15)
                self.cell(0, 5, line, ln=True)
        owner_bottom = self.get_y()

        # "ADRESSE DU BIEN" — droite haut, bleu, right-aligned
        self.set_xy(RIGHT_X, 15)
        self.set_font("DejaVu", "B", 10)
        self.set_blue()
        self.cell(RIGHT_W, 5, "ADRESSE DU BIEN", align="R", ln=True)
        self.set_black()
        self.set_font("DejaVu", "", 9)
        for line in [ctx.unit_address, f"{ctx.unit_zip} {ctx.unit_city}"]:
            if line and line.strip():
                self.set_x(RIGHT_X)
                self.cell(RIGHT_W, 5, line, align="R", ln=True)

        # Locataire — droite, décalé vers le bas
        civility = f"{ctx.tenant_civility} " if ctx.tenant_civility else ""
        tenant_lines = [l for l in [
            f"{civility}{ctx.tenant_fullname}",
            ctx.tenant_billing_address,
            f"{ctx.tenant_billing_zip} {ctx.tenant_billing_city}",
        ] if l.strip()]
        tenant_y = 38
        self.set_font("DejaVu", "", 9)
        for line in tenant_lines:
            self.set_xy(RIGHT_X, tenant_y)
            self.cell(RIGHT_W, 5, line, ln=False)
            tenant_y += 5

        self.set_y(max(owner_bottom, tenant_y) + 12)

    def _owner_header(self, ctx: ReceiptContext) -> None:
        """Left column: owner info. Right column: property address."""
        self.set_font("DejaVu", "B", 11)
        self.set_black()
        self.cell(0, 6, ctx.owner_name, ln=True)
        self.set_font("DejaVu", "", 9)
        self.cell(0, 5, ctx.owner_address, ln=True)
        self.cell(0, 5, f"{ctx.owner_zip} {ctx.owner_city}", ln=True)
        if ctx.owner_phone:
            self.cell(0, 5, f"Tél : {ctx.owner_phone}", ln=True)

    def _property_address_box(self, ctx: ReceiptContext) -> None:
        """Right-aligned box with property address."""
        x_save = self.get_x()
        y_save = self.get_y()
        self.set_xy(120, 15)
        self.set_font("DejaVu", "", 9)
        self.set_fill_color(*LIGHT_GREY)
        self.multi_cell(
            75, 5,
            f"Bien loué :\n{ctx.unit_address}\n{ctx.unit_zip} {ctx.unit_city}",
            border=1, fill=True,
        )
        self.set_xy(x_save, max(y_save, self.get_y()))

    def _title(self, text: str) -> None:
        self.ln(6)
        self.set_font("DejaVu", "B", 16)
        self.set_blue()
        self.cell(0, 10, text, ln=True, align="C")
        self.set_black()
        self.ln(2)

    def _details_table(self, ctx: ReceiptContext) -> None:
        """Render the detail lines + total row."""
        col_desc = 140
        col_price = 45

        # Header row
        self.set_fill_color(*LIGHT_GREY)
        self.set_font("DejaVu", "B", 9)
        self.cell(col_desc, 7, "Description", border=1, fill=True)
        self.cell(col_price, 7, "Montant", border=1, fill=True, align="R", ln=True)

        # Detail rows
        self.set_font("DejaVu", "", 9)
        for line in ctx.details:
            self.cell(col_desc, 6, line.description, border=1)
            self.cell(col_price, 6, _fmt_price(line.price), border=1, align="R", ln=True)

        # Total row
        self.set_fill_color(*DARK_BG)
        self.set_font("DejaVu", "B", 10)
        self.set_white()
        self.cell(col_desc, 8, "Total", border=1, fill=True)
        self.cell(col_price, 8, _fmt_price(ctx.amount_total), border=1, fill=True, align="R", ln=True)
        self.set_black()

    def _signature_block(self, ctx: ReceiptContext) -> None:
        """'Fait à … le …' + signature image."""
        self.ln(8)
        self.set_font("DejaVu", "", 10)
        city = ctx.owner_city or ctx.unit_city
        self.cell(0, 6, f"Fait à {city} le {ctx.txt_date_today}", ln=True)
        if SIGNATURE_PATH.exists():
            self.image(str(SIGNATURE_PATH))
        self.ln(2)

    def _legal_footer_quittance(self) -> None:
        self.set_font("DejaVu", "I", 7)
        self.set_text_color(120, 120, 120)
        self.multi_cell(
            0, 4,
            "Le paiement de la présente quittance n'emporte pas présomption du paiement "
            "des termes antérieurs. Quittance nulle si le chèque est impayé.",
        )
        self.set_black()


# ---------------------------------------------------------------------------
# Document generators
# ---------------------------------------------------------------------------

LEGAL_QUITTANCE = (
    "Le paiement de la présente n'emporte pas présomption de paiement des termes antérieurs. "
    "Cette quittance ou ce reçu annule tous les reçus qui auraient pu être donnés pour acompte "
    "versé sur le présent terme. En cas de congé précédemment donné, cette quittance ou ce reçu "
    "représenterait l'indemnité d'occupation et ne saurait être considéré comme un titre "
    "d'occupation. Sous réserve d'encaissement."
)


def generate_quittance_loyer(ctx: ReceiptContext) -> bytes:
    # Calcul hauteur de la clause légale pour réserver l'espace en bas
    # ~4 lignes × 4mm + marge = 25mm réservés
    LEGAL_RESERVE = 25
    FOOTER_RESERVE = 20  # pour le footer Page 1/1

    pdf = _RentalPDF(orientation="P", unit="mm", format="A4")
    pdf._show_footer = True
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=FOOTER_RESERVE + LEGAL_RESERVE)

    PAGE_W = 210
    MARGIN = 15

    # Table : 160mm centrée → x_start = (210-160)/2 = 25mm
    TABLE_W = 160
    TABLE_X = (PAGE_W - TABLE_W) / 2
    COL_DESC = 110
    COL_PRICE = TABLE_W - COL_DESC  # 50mm

    # ------------------------------------------------------------------ Header
    pdf._quittance_header(ctx)

    # ------------------------------------------------------------------ Titre
    pdf.set_font("DejaVu", "B", 16)
    pdf.set_blue()
    pdf.cell(0, 10, "QUITTANCE DE LOYER", align="C", ln=True)
    pdf.set_black()
    pdf.ln(8)

    # ------------------------------------------------------------------ Paragraphe légal
    civility = f"{ctx.tenant_civility} " if ctx.tenant_civility else ""
    amount_words = _amount_to_words_fr(ctx.amount_total)
    amount_str = f"{ctx.amount_total:.2f}€"
    pdf.set_font("DejaVu", "", 10)
    pdf.multi_cell(
        0, 6,
        f"{ctx.owner_name}, propriétaire du bien désigné ci-dessus, déclare avoir reçu "
        f"de {civility}{ctx.tenant_fullname} la somme de {amount_str} ({amount_words}) "
        f"au titre du paiement du loyer et des charges pour la période de location "
        f"du {ctx.txt_date_from} au {ctx.txt_date_to} et lui en donne quittance.",
    )
    pdf.ln(8)

    # ------------------------------------------------------------------ Tableau
    pdf.set_font("DejaVu", "B", 11)
    pdf.set_blue()
    pdf.set_x(TABLE_X)
    pdf.cell(TABLE_W, 7, "Détails du règlement", ln=True)
    pdf.set_black()
    pdf.ln(3)

    ROW_H = 10
    pdf.set_font("DejaVu", "", 10)
    pdf.set_draw_color(180, 180, 180)
    pdf.set_line_width(0.2)

    # Ligne supérieure (grise)
    y = pdf.get_y()
    pdf.line(TABLE_X, y, TABLE_X + TABLE_W, y)

    for line in ctx.details:
        pdf.set_x(TABLE_X + 3)
        pdf.cell(COL_DESC - 3, ROW_H, line.description, ln=False)
        pdf.cell(COL_PRICE - 3, ROW_H, _fmt_price(line.price), align="R", ln=False)
        pdf.ln(ROW_H)
        # Séparateur entre chaque ligne (gris)
        y = pdf.get_y()
        pdf.line(TABLE_X, y, TABLE_X + TABLE_W, y)

    # Ligne épaisse noire avant le total
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.5)
    y = pdf.get_y()
    pdf.line(TABLE_X, y, TABLE_X + TABLE_W, y)

    # Ligne total — gras
    pdf.set_font("DejaVu", "B", 10)
    pdf.set_x(TABLE_X + 3)
    pdf.cell(COL_DESC - 3, ROW_H, "Total à payer", ln=False)
    pdf.cell(COL_PRICE - 3, ROW_H, _fmt_price(ctx.amount_total), align="R", ln=False)
    pdf.ln(ROW_H)

    pdf.set_line_width(0.2)
    pdf.ln(10)

    # ------------------------------------------------------------------ Signature
    city = ctx.owner_city or ctx.unit_city
    pdf.set_font("DejaVu", "", 10)
    pdf.set_x(TABLE_X)
    pdf.cell(0, 6, f"Fait à {city} le {ctx.txt_date_today}", ln=True)
    pdf.ln(2)
    pdf.set_x(TABLE_X + 10)
    pdf.cell(0, 6, ctx.owner_name, ln=True)
    if SIGNATURE_PATH.exists():
        pdf.image(str(SIGNATURE_PATH), x=TABLE_X + 20)

    # ------------------------------------------------------------------ Clause légale ancrée en bas
    # Désactiver auto_page_break pour écrire dans la zone réservée
    pdf.set_auto_page_break(False)
    pdf.set_y(297 - FOOTER_RESERVE - LEGAL_RESERVE)
    pdf.set_font("DejaVu", "", 7)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 4, LEGAL_QUITTANCE)
    pdf.set_black()

    return bytes(pdf.output())


def generate_avis_echeance(ctx: ReceiptContext) -> bytes:
    pdf = _RentalPDF(orientation="P", unit="mm", format="A4")
    pdf._show_footer = True
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=20)

    PAGE_W = 210
    MARGIN = 15
    BOX_W = PAGE_W - 2 * MARGIN   # 180 mm
    COL_DESC = 130
    COL_PRICE = BOX_W - COL_DESC  # 50 mm

    # ------------------------------------------------------------------ Header
    # Propriétaire — bloc gauche
    pdf.set_xy(MARGIN, 15)
    pdf.set_font("DejaVu", "B", 10)
    pdf.cell(0, 5, ctx.owner_name, ln=True)
    pdf.set_font("DejaVu", "", 9)
    for line in [ctx.owner_address,
                 f"{ctx.owner_zip} {ctx.owner_city}",
                 ctx.owner_phone,
                 ctx.owner_email]:
        if line and line.strip():
            pdf.set_x(MARGIN)
            pdf.cell(0, 5, line, ln=True)

    # Locataire — bloc droit, légèrement décalé vers le bas
    civility = f"{ctx.tenant_civility} " if ctx.tenant_civility else ""
    tenant_lines = [l for l in [
        f"{civility}{ctx.tenant_fullname}",
        ctx.tenant_billing_address,
        f"{ctx.tenant_billing_zip} {ctx.tenant_billing_city}",
    ] if l.strip()]
    tenant_y = 38
    pdf.set_font("DejaVu", "", 9)
    for line in tenant_lines:
        pdf.set_xy(110, tenant_y)
        pdf.cell(85, 5, line, ln=False)
        tenant_y += 5

    pdf.set_y(max(pdf.get_y(), tenant_y) + 12)

    # ------------------------------------------------------------------ Titre
    pdf.set_font("DejaVu", "B", 16)
    pdf.set_blue()
    pdf.cell(0, 10, "AVIS D'ECHEANCE", align="C", ln=True)
    pdf.set_black()
    pdf.ln(5)

    # ------------------------------------------------------------------ Box
    # On écrit le contenu, puis on dessine le cadre par-dessus (fond transparent)
    box_start_y = pdf.get_y()
    pdf.set_y(box_start_y + 7)  # padding haut

    # "Période" (gras) + "du … au …" (normal) — centré
    lbl = "Période "
    rest = f"du {ctx.txt_date_from} au {ctx.txt_date_to}"
    pdf.set_font("DejaVu", "B", 10)
    w_lbl = pdf.get_string_width(lbl)
    pdf.set_font("DejaVu", "", 10)
    w_rest = pdf.get_string_width(rest)
    start_x = (PAGE_W - w_lbl - w_rest) / 2
    pdf.set_xy(start_x, pdf.get_y())
    pdf.set_font("DejaVu", "B", 10)
    pdf.cell(w_lbl, 6, lbl, ln=False)
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(w_rest, 6, rest, ln=True)

    pdf.ln(6)

    # "Adresse de la location" — bleu gras centré
    pdf.set_font("DejaVu", "B", 10)
    pdf.set_blue()
    pdf.cell(0, 6, "Adresse de la location", align="C", ln=True)
    pdf.set_black()
    pdf.ln(4)

    # Adresse centrée
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 5, ctx.unit_address, align="C", ln=True)
    pdf.cell(0, 5, f"{ctx.unit_zip} {ctx.unit_city}", align="C", ln=True)

    box_end_y = pdf.get_y() + 7  # padding bas
    pdf.rect(MARGIN, box_start_y, BOX_W, box_end_y - box_start_y)
    pdf.set_y(box_end_y + 5)

    # ------------------------------------------------------------------ Tableau
    ROW_H = 10
    pdf.set_font("DejaVu", "", 10)
    for line in ctx.details:
        pdf.cell(COL_DESC, ROW_H, f"  {line.description}", border=1)
        pdf.cell(COL_PRICE, ROW_H, f"{_fmt_price(line.price)}  ", border=1, align="R", ln=True)

    # Ligne Total (gras)
    pdf.set_font("DejaVu", "B", 10)
    pdf.cell(COL_DESC, ROW_H, "  Total à payer", border=1)
    pdf.cell(COL_PRICE, ROW_H, f"{_fmt_price(ctx.amount_total)}  ", border=1, align="R", ln=True)

    pdf.ln(7)

    # ------------------------------------------------------------------ Pied
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 6, f"Paiement exigible le : {ctx.txt_date_payment}", ln=True)
    if ctx.owner_iban:
        pdf.cell(0, 6, f"Coordonnées bancaires : {ctx.owner_iban}", ln=True)
    pdf.ln(5)
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 5, "Cet avis est une demande de paiement.", ln=True)
    pdf.cell(0, 5, "Il ne peut en aucun cas servir de quittance de loyer.", ln=True)
    pdf.set_black()

    return bytes(pdf.output())


def generate_quittance_garantie(ctx: ReceiptContext) -> bytes:
    pdf = _RentalPDF(orientation="P", unit="mm", format="A4")
    pdf._show_footer = True
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=20)

    # ------------------------------------------------------------------ Header
    pdf._quittance_header(ctx)

    # ------------------------------------------------------------------ Titre
    pdf.set_font("DejaVu", "B", 16)
    pdf.set_blue()
    pdf.cell(0, 10, "RECU DU DEPOT DE GARANTIE", align="C", ln=True)
    pdf.set_black()
    pdf.ln(10)

    # ------------------------------------------------------------------ Paragraphe légal
    civility = f"{ctx.tenant_civility} " if ctx.tenant_civility else ""
    amount_str = f"{ctx.amount_total:.2f}€"
    pdf.set_font("DejaVu", "", 10)
    pdf.multi_cell(
        0, 6,
        f"Reçu le {ctx.txt_date_from}, de {civility}{ctx.tenant_fullname} "
        f"la somme de {amount_str} au titre du dépôt de garantie du bien désigné ci-dessus.",
    )
    pdf.ln(8)

    # ------------------------------------------------------------------ Clause restitution
    pdf.multi_cell(
        0, 6,
        "Le dépôt de garantie sera restitué dans les deux mois suivant la remise des clés "
        "lors du départ du locataire déduction faite des éventuelles retenues prévues au "
        "contrat de bail.",
    )
    pdf.ln(15)

    # ------------------------------------------------------------------ Signature (centre-droite)
    city = ctx.owner_city or ctx.unit_city
    pdf.set_font("DejaVu", "", 10)
    pdf.set_x(110)
    pdf.cell(85, 6, f"Fait à {city} le {ctx.txt_date_today}", ln=True)
    pdf.set_x(110)
    pdf.cell(85, 6, ctx.owner_name, ln=True)
    if SIGNATURE_PATH.exists():
        pdf.image(str(SIGNATURE_PATH), x=120)

    return bytes(pdf.output())


def generate_receipt_pdf(ctx: ReceiptContext, doc_type_override: str | None = None) -> bytes:
    """Auto-detect document type unless overridden."""
    if doc_type_override == "garantie" or (doc_type_override is None and ctx.is_garantie):
        return generate_quittance_garantie(ctx)
    if doc_type_override == "quittance" or (doc_type_override is None and ctx.paid):
        return generate_quittance_loyer(ctx)
    return generate_avis_echeance(ctx)
