from flask import Flask, request, jsonify
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from openpyxl import Workbook
import base64
import os

app = Flask(__name__)

@app.route('/api/generar', methods=['POST'])
def generar():
    try:
        data = request.json
        cliente = data.get('cliente', 'Cliente')
        cuit_cliente = data.get('cuitCliente', '')
        fecha = data.get('fecha', '')
        condiciones = data.get('condiciones', '')
        items = data.get('items', [])

        empresa = {
            "nombre": "Reconstructora Unión S.A",
            "cuit": "30716717565",
            "direccion": "Buenos Aires, Olavarría, Av Pellegrini 5900",
            "email": "olavarria@reconstructoraunion.com"
        }

        # Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "Presupuesto"
        ws.append([empresa["nombre"], "", "", "", cliente])
        ws.append([f"Cuit: {empresa['cuit']}", "", "", "", f"CUIT: {cuit_cliente}"])
        ws.append([empresa["direccion"]])
        ws.append([empresa["email"]])
        ws.append([])
        ws.append(["Fecha de emisión:", fecha])
        ws.append([])
        ws.append(["Cantidad", "Descripción", "Precio Unitario", "Precio Total"])

        total = 0
        for item in items:
            cantidad = int(item["cantidad"])
            descripcion = item["descripcion"]
            precio = float(item["precio"])
            precio_total = cantidad * precio
            total += precio_total
            ws.append([cantidad, descripcion, f"${precio:,.2f}", f"${precio_total:,.2f}"])

        ws.append([])
        ws.append(["", "", "TOTAL", f"${total:,.2f}"])
        ws.append([])
        ws.append(["Condiciones de pago:", condiciones])

        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_base64 = base64.b64encode(excel_buffer.getvalue()).decode()

        # PDF
        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=A4)
        width, height = A4

        # Marca de agua
        watermark_path = os.path.join("public", "logo_union.png")
        if os.path.exists(watermark_path):
            img = ImageReader(watermark_path)
            c.saveState()
            c.translate(width / 4, height / 4)
            c.rotate(30)
            c.setFillAlpha(0.1)
            c.drawImage(img, 0, 0, width=width / 2, height=width / 2)
            c.restoreState()

        # Logo
        logo_path = os.path.join("public", "logo.png")
        if os.path.exists(logo_path):
            c.drawImage(logo_path, 250, height - 100, width=100)

        # Datos empresa
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, height - 50, empresa["nombre"])
        c.setFont("Helvetica", 10)
        c.drawString(40, height - 65, f"Cuit: {empresa['cuit']}")
        c.drawString(40, height - 80, empresa["direccion"])
        c.drawString(40, height - 95, empresa["email"])

        # Cliente
        c.setFont("Helvetica", 12)
        c.drawString(400, height - 50, cliente)
        c.drawString(400, height - 65, f"CUIT: {cuit_cliente}")
        c.drawString(400, height - 80, f"Fecha: {fecha}")

        # Título
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, height - 130, "Presupuesto por Ud. requerido")

        # Tabla
        y = height - 160
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Cant.")
        c.drawString(120, y, "Descripción")
        c.drawString(320, y, "Precio U.")
        c.drawString(420, y, "Precio Total")
        y -= 20

        c.setFont("Helvetica", 10)
        for item in items:
            cantidad = item["cantidad"]
            descripcion = item["descripcion"]
            precio = float(item["precio"])
            precio_total = cantidad * precio
            c.drawString(40, y, str(cantidad))
            c.drawString(120, y, descripcion[:30])
            c.drawString(320, y, f"${precio:,.2f}")
            c.drawString(420, y, f"${precio_total:,.2f}")
            y -= 15

        # Total
        c.setFillColorRGB(1, 1, 0)
        c.rect(320, y - 10, 200, 20, fill=True)
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(325, y - 5, f"TOTAL: ${total:,.2f}")
        y -= 30

        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Condiciones de pago:")
        c.setFont("Helvetica", 10)
        c.drawString(200, y, condiciones)

        c.showPage()
        c.save()

        pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode()

        return jsonify({"excel": excel_base64, "pdf": pdf_base64})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
