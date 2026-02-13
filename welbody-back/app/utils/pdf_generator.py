from io import BytesIO
from typing import Optional

from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def generate_patient_id_card_pdf(
    patient_id: str,
    full_name: str,
    gender: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    priority: Optional[str] = None,
) -> bytes:
    buffer = BytesIO()
    card = canvas.Canvas(buffer, pagesize=(3.5 * inch, 2.2 * inch))

    card.setFont("Helvetica-Bold", 10)
    card.drawString(10, 145, "WELBODY - PATIENT ID CARD")
    card.setFont("Helvetica", 9)
    card.drawString(10, 125, f"Patient ID: {patient_id}")
    card.drawString(10, 109, f"Name: {full_name}")
    card.drawString(10, 93, f"Gender: {gender or 'N/A'}")
    card.drawString(10, 77, f"DOB: {date_of_birth or 'N/A'}")
    card.drawString(10, 61, f"Triage Priority: {priority or 'N/A'}")

    card.showPage()
    card.save()
    buffer.seek(0)
    return buffer.getvalue()


def generate_medication_list_pdf(patient_id: str, patient_name: Optional[str], medications: list[dict]) -> bytes:
    buffer = BytesIO()
    doc = canvas.Canvas(buffer, pagesize=(8.5 * inch, 11 * inch))

    y = 760
    doc.setFont("Helvetica-Bold", 14)
    doc.drawString(50, y, "WELBODY - MEDICATION LIST")
    y -= 25
    doc.setFont("Helvetica", 10)
    doc.drawString(50, y, f"Patient ID: {patient_id}")
    y -= 15
    doc.drawString(50, y, f"Patient Name: {patient_name or 'N/A'}")
    y -= 25

    if not medications:
        doc.drawString(50, y, "No medications prescribed.")
    else:
        for index, med in enumerate(medications, start=1):
            if y < 90:
                doc.showPage()
                y = 760
            doc.setFont("Helvetica-Bold", 10)
            doc.drawString(50, y, f"{index}. {med.get('medication_name', 'Unknown Medication')}")
            y -= 14
            doc.setFont("Helvetica", 9)
            doc.drawString(65, y, f"Dose: {med.get('dose') or 'N/A'}")
            y -= 12
            doc.drawString(65, y, f"Frequency: {med.get('frequency') or 'N/A'}")
            y -= 12
            doc.drawString(65, y, f"Duration: {med.get('duration') or 'N/A'}")
            y -= 12
            doc.drawString(65, y, f"Instructions: {med.get('instructions') or 'N/A'}")
            y -= 18

    doc.showPage()
    doc.save()
    buffer.seek(0)
    return buffer.getvalue()
