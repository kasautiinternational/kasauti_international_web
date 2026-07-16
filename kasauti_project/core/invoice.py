# =====================================================
# NEW: GST Invoice PDF generator (reportlab)
# Admin me har order ke saath "Download Invoice" button
# isi file se PDF banata hai. Company details neeche
# COMPANY dict me hain — GSTIN wagera yahin edit karo.
# =====================================================
import io
import os
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# ─────────────────────────────────────────
# YAHAN APNI COMPANY DETAILS EDIT KARO
# ─────────────────────────────────────────
COMPANY = {
    'name': 'KASAUTI INTERNATIONAL LLP',
    'tagline': 'DTF Printing Supplies',
    'address_lines': [
        'Sector 63, Noida, Uttar Pradesh - 201301',
    ],
    'gstin': '09ABFFK6002L1Z8',        # <-- APNA REAL GSTIN YAHAN DAALO
    'email': 'kasautiinternational@gmail.com',
    'phone': '+91 8796560299',                        # <-- chaaho to phone daalo
    'website': 'kasautiinternational.com',
}
GST_RATE_LABEL = 'GST @ 18%'

# Theme colors (site jaisi cream + gold + dark)
DARK = colors.HexColor('#0f172a')
GOLD = colors.HexColor('#c9973f')
CREAM = colors.HexColor('#faf6ef')
GREY = colors.HexColor('#64748b')
LINE = colors.HexColor('#e2e8f0')


def _register_rupee_font():
    """DejaVuSans me rupee symbol hota hai — mil jaye to use karo,
    warna 'Rs.' fallback (Helvetica me rupee glyph nahi hota)."""
    candidates = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/dejavu/DejaVuSans.ttf',
    ]
    bold_candidates = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf',
    ]
    for reg, bold in zip(candidates, bold_candidates):
        if os.path.exists(reg) and os.path.exists(bold):
            try:
                pdfmetrics.registerFont(TTFont('Rupee', reg))
                pdfmetrics.registerFont(TTFont('Rupee-Bold', bold))
                return True
            except Exception:
                return False
    return False


_HAS_RUPEE = _register_rupee_font()
FONT = 'Rupee' if _HAS_RUPEE else 'Helvetica'
FONT_BOLD = 'Rupee-Bold' if _HAS_RUPEE else 'Helvetica-Bold'
RUPEE = '\u20b9' if _HAS_RUPEE else 'Rs.'


def money(value):
    """1234567.5 -> '12,34,567.50' (Indian comma style)."""
    value = Decimal(value or 0).quantize(Decimal('0.01'))
    sign = '-' if value < 0 else ''
    value = abs(value)
    whole, frac = divmod(value, 1)
    s = str(int(whole))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ','.join(parts) + ',' + tail
    return f"{sign}{s}.{int(frac * 100):02d}"


_ONES = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight',
         'Nine', 'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen',
         'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
_TENS = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy',
         'Eighty', 'Ninety']


def _two(n):
    if n < 20:
        return _ONES[n]
    return (_TENS[n // 10] + (' ' + _ONES[n % 10] if n % 10 else '')).strip()


def _three(n):
    if n >= 100:
        rest = _two(n % 100)
        return (_ONES[n // 100] + ' Hundred' + (' ' + rest if rest else '')).strip()
    return _two(n)


def amount_in_words(value):
    """12345.50 -> 'Twelve Thousand ... Rupees and Fifty Paise Only'
    (Indian system: crore / lakh / thousand)."""
    value = Decimal(value or 0).quantize(Decimal('0.01'))
    rupees = int(value)
    paise = int((value - rupees) * 100)

    if rupees == 0:
        words = 'Zero'
    else:
        parts = []
        crore, rem = divmod(rupees, 10000000)
        lakh, rem = divmod(rem, 100000)
        thousand, rem = divmod(rem, 1000)
        if crore:
            parts.append(_two(crore) + ' Crore')
        if lakh:
            parts.append(_two(lakh) + ' Lakh')
        if thousand:
            parts.append(_two(thousand) + ' Thousand')
        if rem:
            parts.append(_three(rem))
        words = ' '.join(parts)

    result = words + ' Rupees'
    if paise:
        result += ' and ' + _two(paise) + ' Paise'
    return result + ' Only'


def build_invoice_pdf(order):
    """Order se GST invoice PDF banata hai. Returns: bytes."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    M = 18 * mm  # margin

    items = list(order.items.all())
    subtotal = (order.total_amount or 0) - (order.gst_amount or 0)
    invoice_no = f"KI/{order.created_at.strftime('%Y')}/{order.id:05d}"

    # ── Header band ──
    c.setFillColor(DARK)
    c.rect(0, H - 38 * mm, W, 38 * mm, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.setFont(FONT_BOLD, 17)
    c.drawString(M, H - 16 * mm, COMPANY['name'])
    c.setFillColor(colors.HexColor('#94a3b8'))
    c.setFont(FONT, 9)
    c.drawString(M, H - 22 * mm, COMPANY['tagline'])
    y = H - 27 * mm
    for line in COMPANY['address_lines']:
        c.drawString(M, y, line)
        y -= 4.2 * mm
    contact = COMPANY['email']
    if COMPANY['phone']:
        contact += '  |  ' + COMPANY['phone']
    c.drawString(M, y, contact)

    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 22)
    c.drawRightString(W - M, H - 17 * mm, 'TAX INVOICE')
    c.setFont(FONT, 9)
    c.setFillColor(colors.HexColor('#94a3b8'))
    c.drawRightString(W - M, H - 24 * mm, f"GSTIN: {COMPANY['gstin']}")

    # ── Invoice meta + Bill To ──
    top = H - 48 * mm
    c.setFillColor(CREAM)
    c.roundRect(M, top - 30 * mm, W - 2 * M, 30 * mm, 3 * mm, fill=1, stroke=0)

    c.setFillColor(GREY)
    c.setFont(FONT_BOLD, 8)
    c.drawString(M + 6 * mm, top - 7 * mm, 'BILL TO')
    c.setFillColor(DARK)
    c.setFont(FONT_BOLD, 11)
    c.drawString(M + 6 * mm, top - 12.5 * mm, order.name or '')
    c.setFont(FONT, 9)
    yy = top - 17.5 * mm
    # Address ko max ~55 chars ki lines me todo
    addr = (order.address or '').replace('\r', ' ').replace('\n', ', ')
    words = addr.split()
    line = ''
    lines = []
    for w_ in words:
        if len(line) + len(w_) + 1 <= 55:
            line = (line + ' ' + w_).strip()
        else:
            lines.append(line)
            line = w_
    if line:
        lines.append(line)
    for ln in lines[:2]:
        c.drawString(M + 6 * mm, yy, ln)
        yy -= 4.2 * mm
    c.drawString(M + 6 * mm, yy, f"Phone: {order.phone} \n  Email: {order.email}")

    c.setFillColor(GREY)
    c.setFont(FONT_BOLD, 8)
    c.drawString(W / 2 + 14 * mm, top - 7 * mm, 'INVOICE NO.')
    c.drawString(W / 2 + 14 * mm, top - 16 * mm, 'INVOICE DATE')
    c.drawString(W / 2 + 14 * mm, top - 25 * mm, 'ORDER NO.')
    c.setFillColor(DARK)
    c.setFont(FONT_BOLD, 10)
    c.drawRightString(W - M - 6 * mm, top - 7 * mm, invoice_no)
    c.setFont(FONT, 10)
    c.drawRightString(W - M - 6 * mm, top - 16 * mm,
                      order.created_at.strftime('%d %b %Y'))
    c.drawRightString(W - M - 6 * mm, top - 25 * mm, f"#{order.id}")

    # ── Items table ──
    ty = top - 40 * mm
    col_sno = M
    col_desc = M + 12 * mm
    col_qty = W - M - 70 * mm
    col_rate = W - M - 40 * mm
    col_amt = W - M

    c.setFillColor(DARK)
    c.rect(M, ty - 2 * mm, W - 2 * M, 8 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 9)
    c.drawString(col_sno + 2 * mm, ty, '#')
    c.drawString(col_desc, ty, 'DESCRIPTION')
    c.drawRightString(col_qty, ty, 'QTY')
    c.drawRightString(col_rate, ty, 'RATE')
    c.drawRightString(col_amt - 2 * mm, ty, 'AMOUNT')

    ty -= 9 * mm
    c.setFont(FONT, 9.5)
    for i, it in enumerate(items, start=1):
        desc = it.product_title or ''
        if it.size:
            desc += f"  [{it.size} in]"
        line_total = (it.unit_price or 0) * (it.quantity or 0)

        c.setFillColor(DARK)
        c.drawString(col_sno + 2 * mm, ty, str(i))
        c.drawString(col_desc, ty, desc[:52])
        c.drawRightString(col_qty, ty, str(it.quantity))
        c.drawRightString(col_rate, ty, f"{RUPEE}{money(it.unit_price)}")
        c.drawRightString(col_amt - 2 * mm, ty, f"{RUPEE}{money(line_total)}")

        c.setStrokeColor(LINE)
        c.setLineWidth(0.5)
        c.line(M, ty - 2.5 * mm, W - M, ty - 2.5 * mm)
        ty -= 7.5 * mm

    # ── Totals block ──
    ty -= 3 * mm
    label_x = W - M - 60 * mm
    c.setFont(FONT, 9.5)
    c.setFillColor(GREY)
    c.drawString(label_x, ty, 'Taxable Value')
    c.setFillColor(DARK)
    c.drawRightString(col_amt - 2 * mm, ty, f"{RUPEE}{money(subtotal)}")
    ty -= 6.5 * mm
    c.setFillColor(GREY)
    c.drawString(label_x, ty, GST_RATE_LABEL)
    c.setFillColor(DARK)
    c.drawRightString(col_amt - 2 * mm, ty, f"{RUPEE}{money(order.gst_amount)}")
    ty -= 3.5 * mm
    c.setStrokeColor(DARK)
    c.setLineWidth(1)
    c.line(label_x, ty, W - M, ty)
    ty -= 7 * mm
    c.setFont(FONT_BOLD, 12)
    c.drawString(label_x, ty, 'GRAND TOTAL')
    c.setFillColor(GOLD)
    c.drawRightString(col_amt - 2 * mm, ty, f"{RUPEE}{money(order.total_amount)}")

    # ── Amount in words ──
    ty -= 12 * mm
    c.setFillColor(GREY)
    c.setFont(FONT_BOLD, 8)
    c.drawString(M, ty, 'AMOUNT IN WORDS')
    c.setFillColor(DARK)
    c.setFont(FONT, 9.5)
    c.drawString(M, ty - 5 * mm, amount_in_words(order.total_amount))

    # ── Footer ──
    c.setFillColor(CREAM)
    c.rect(0, 0, W, 26 * mm, fill=1, stroke=0)
    c.setFillColor(GREY)
    c.setFont(FONT, 8)
    c.drawString(M, 18 * mm,
                 'This is a computer-generated invoice and does not require a signature.')
    c.drawString(M, 13 * mm,
                 f"Questions? Write to {COMPANY['email']}")
    c.setFillColor(DARK)
    c.setFont(FONT_BOLD, 9)
    c.drawRightString(W - M, 15 * mm, f"For {COMPANY['name']}")

    c.showPage()
    c.save()
    return buf.getvalue()