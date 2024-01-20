from django.utils.translation import pgettext

from pretix.base.invoice import BaseReportlabInvoiceRenderer
from pretix.base.invoice import Modern1Renderer

from reportlab.graphics import barcode
from reportlab.graphics.barcode import code128
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfgen.canvas import Canvas

from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, KeepTogether, NextPageTemplate,
    PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

import pprint



class MyInvoiceRenderer(Modern1Renderer):
    identifier = 'barcode-dpsg'
    verbose_name = pgettext('invoice', 'Barcode Invoice Renderer (DPSG Würzburg)')
    #logo_left = 0

    def _on_first_page(self, canvas: Canvas, doc):
        Modern1Renderer._on_first_page(self, canvas, doc)
        canvas.saveState()
        self._draw_barcode(canvas)
        canvas.restoreState()

    def _draw_barcode(self, canvas: Canvas):
        barcode1=code128.Code128(self.invoice.number,barWidth=0.5*mm,barHeight=20*mm)
        #canvas.translate(100*mm, 100*mm)
        #barcode.canv = canvas
        #barcode.draw()
        #del barcode.canv
        #barcode2 = barcode.createBarcodeDrawing("Code128", value=self.invoice.number, humanReadable=True,barWidth=0.5*mm,barHeight=20*mm)
        barcode2 = barcode.createBarcodeDrawing("Code128", value="3802023AR12345", humanReadable=True, barWidth=0.3*mm, barHeight=18.5*mm, quiet=False)
        posX = self.pagesize[0] - barcode1.width - self.right_margin
        posX2 = self.pagesize[0] - barcode2.width - self.right_margin
        posY = self.pagesize[1] - 90*mm  # Labels (invoice number, invoice date) etc. are at 100*mm from top
        pprint.pprint(barcode2)
        barcode1.drawOn(canvas,posX,posX)
        barcode2.drawOn(canvas,posX2,posY)
        canvas.circle(posX,posX, 5*mm, stroke=1, fill=1)
        canvas.circle(self.pagesize[0],posY, 2*mm, stroke=1, fill=1)
        canvas.circle(self.pagesize[0]-self.right_margin,posY, 2*mm, stroke=1, fill=1)
        canvas.circle(self.pagesize[0]-self.right_margin-barcode2.width,posY, 2*mm, stroke=1, fill=1)
        print("Hallo Welt 2")
        debug_text = ("barcode1: " + str(barcode1.width) + " x " + str(barcode1.height) + ", <br />barcode2: " + str(barcode2.width) + " x " \
                + str(barcode2.height) + "<br />mm: " + str(mm) + "<br />" + "barcode2 (mm): " + str(barcode2.width / mm) + " x " + str(barcode2.height / mm))
        #debug_text = "Hallo Welt als Paragraph"
        print(debug_text)
        p = Paragraph(debug_text, style=self.stylesheet['Sender'])
        p.wrapOn(canvas, 75*mm, 100*mm)
        p.drawOn(canvas, 25*mm, 55*mm)
        p = Paragraph("Code version 13", style=self.stylesheet['Sender'])
        p.wrapOn(canvas, 100*mm, 100*mm)
        p.drawOn(canvas, 25*mm, 15*mm)
        p = Paragraph("This paragraph is at (posX,posX)", style=self.stylesheet['Sender'])
        p.wrapOn(canvas, 100*mm, 100*mm)
        p.drawOn(canvas, posX, posX)

