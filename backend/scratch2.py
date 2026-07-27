from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
try:
    qr = QrCodeWidget("https://orma.ai/verify/1234")
    d = Drawing(30, 30)
    d.add(qr)
    print("QrCodeWidget rendered successfully")
except Exception as e:
    import traceback
    traceback.print_exc()
