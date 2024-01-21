from django.utils.translation import pgettext
from django.utils.formats import date_format

from pretix.base.invoice import BaseReportlabInvoiceRenderer
from pretix.base.invoice import Modern1Renderer

from reportlab.graphics import barcode
from reportlab.graphics.barcode import code128
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle, StyleSheet1
from reportlab.pdfgen import canvas
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

from reportlab.lib import colors, pagesizes
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, StyleSheet1
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, KeepTogether, NextPageTemplate,
    PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

import pprint

class MyInvoiceRenderer(Modern1Renderer):
    identifier = 'barcode-dpsg'
    verbose_name = pgettext('invoice', 'Barcode Invoice Renderer (DPSG Würzburg)')

    def _on_first_page(self, canvas: Canvas, doc):
        Modern1Renderer._on_first_page(self, canvas, doc)
        canvas.saveState()
        self._draw_barcode(canvas)
        canvas.restoreState()

    def _draw_barcode(self, canvas: Canvas):
        inv_barcode = barcode.createBarcodeDrawing("Code128", value="38020" + self.invoice.number, humanReadable=True, barWidth=0.31*mm, barHeight=18.5*mm, quiet=False)
        posX = self.pagesize[0] - inv_barcode.width - self.right_margin
        posY = self.pagesize[1] - 95*mm  # Labels for metadata (invoice number, invoice date) etc. are at 100*mm from top
        inv_barcode.drawOn(canvas,posX,posY)
        canvas.circle(self.pagesize[0],posY, 2*mm, stroke=1, fill=1)
        canvas.circle(self.pagesize[0]-self.right_margin,posY, 2*mm, stroke=1, fill=1)
        canvas.circle(self.pagesize[0]-self.right_margin-inv_barcode.width,posY, 2*mm, stroke=1, fill=1)
        debug_text = ("inv_barcode: " + str(inv_barcode.width) + " x " \
                + str(inv_barcode.height) + "<br />mm: " + str(mm) + "<br />" + "inv_barcode: " + str(inv_barcode.width / mm) + "mm x " + str(inv_barcode.height / mm) + "mm")
        p = Paragraph(debug_text, style=self.stylesheet['Sender'])
        p.wrapOn(canvas, 75*mm, 100*mm)
        p.drawOn(canvas, 25*mm, 55*mm)
        p = Paragraph("Code version 20", style=self.stylesheet['Sender'])
        p.wrapOn(canvas, 100*mm, 100*mm)
        p.drawOn(canvas, 25*mm, 40*mm)
        meta_data = self.event.meta_data
        p = Paragraph("event: " + pprint.pformat(meta_data), style=self.stylesheet['Sender'])
        p.wrapOn(canvas, 100*mm, 100*mm)
        p.drawOn(canvas, 25*mm, 35*mm)
        ktr = meta_data['KTR']
        p = Paragraph("event: " + pprint.pformat(ktr), style=self.stylesheet['Sender'])
        p.wrapOn(canvas, 100*mm, 100*mm)
        p.drawOn(canvas, 25*mm, 30*mm)

    # This method is mostly copied from Modern1Renderer, only adds an additional field for metadata
    def _draw_metadata(self, canvas):
        # Draws the "invoice number -- date" line. This has gotten a little more complicated since we
        # encountered some events with very long invoice numbers. In this case, we automatically reduce
        # the font size until it fits.
        begin_top = 100 * mm

        def _draw(label, value, value_size, x, width, bold=False, sublabel=None):
            if canvas.stringWidth(value, self.font_regular, value_size) > width and value_size > 6:
                return False
            textobject = canvas.beginText(x, self.pagesize[1] - begin_top)
            textobject.setFont(self.font_regular, 8)
            textobject.textLine(self._normalize(label))
            textobject.moveCursor(0, 5)
            textobject.setFont(self.font_bold if bold else self.font_regular, value_size)
            textobject.textLine(self._normalize(value))

            if sublabel:
                textobject.moveCursor(0, 1)
                textobject.setFont(self.font_regular, 8)
                textobject.textLine(self._normalize(sublabel))

            return textobject

        value_size = 10
        while value_size >= 5:
            if self.event.settings.invoice_renderer_highlight_order_code:
                kwargs = dict(bold=True, sublabel=pgettext('invoice', '(Please quote at all times.)'))
            else:
                kwargs = {}
            objects = [
                _draw(pgettext('invoice', 'Order code'), self.invoice.order.full_code, value_size, self.left_margin, 45 * mm, **kwargs)
            ]

            p = Paragraph(
                self._normalize(date_format(self.invoice.date, "DATE_FORMAT")),
                style=ParagraphStyle(name=f'Normal{value_size}', fontName=self.font_regular, fontSize=value_size, leading=value_size * 1.2)
            )
            w = stringWidth(p.text, p.frags[0].fontName, p.frags[0].fontSize)
            p.wrapOn(canvas, w, 15 * mm)
            date_x = self.pagesize[0] - w - self.right_margin

            if self.invoice.is_cancellation:
                objects += [
                    _draw(pgettext('invoice', 'Cancellation number'), self.invoice.number,
                          value_size, self.left_margin + 35 * mm, 35 * mm),
                    _draw(pgettext('invoice', 'Original invoice'), self.invoice.refers.number,
                          value_size, self.left_margin + 70 * mm, date_x - self.left_margin - 70 * mm - 5 * mm),
                ]
            else:
                objects += [
                    _draw(pgettext('invoice', 'Invoice number'), self.invoice.number,
                          value_size, self.left_margin + 60 * mm, date_x - self.left_margin - 60 * mm - 5 * mm),
                ]

            # Here ist the addition
            if self.event.meta_data:
                ktr = self.event.meta_data['KTR']
                if ktr is not None and len(ktr) > 0:
                    objects += [
                        _draw('KTR', ktr,
                              value_size, self.left_margin + 105 * mm, date_x - self.left_margin - 105 * mm - 5 * mm),
                    ]
            if self.event.meta_data:
                kn = self.event.meta_data['KN']
                if kn is not None and len(kn) > 0:
                    objects += [
                        _draw('KN', kn,
                              value_size, self.left_margin + 120 * mm, date_x - self.left_margin - 120 * mm - 5 * mm),
                    ]

            if all(objects):
                for o in objects:
                    canvas.drawText(o)
                break
            value_size -= 1

        p.drawOn(canvas, date_x, self.pagesize[1] - begin_top - 10 - 6)

        textobject = canvas.beginText(date_x, self.pagesize[1] - begin_top)
        textobject.setFont(self.font_regular, 8)
        if self.invoice.is_cancellation:
            textobject.textLine(self._normalize(pgettext('invoice', 'Cancellation date')))
        else:
            textobject.textLine(self._normalize(pgettext('invoice', 'Invoice date')))
        canvas.drawText(textobject)
