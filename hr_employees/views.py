
from datetime import timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from hr_employees.utils import clean_employee_row, extract_matricule
from .models import Employee
from .serializers import BulletinEnvoiLogSerializer, EmployeeSerializer
import pandas as pd
from io import BytesIO
# views.py (dans EmployeeViewSet)

import fitz  # PyMuPDF
from django.core.mail import EmailMessage
from .models import BulletinEnvoiLog, Employee
import io
from pdf2image import convert_from_bytes
import pytesseract
import re
from django.utils import timezone







class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

    @action(detail=False, methods=['post'], url_path='import')
    def import_employees(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response({"error": "Aucun fichier fourni."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            
            df = pd.read_excel(file)
            print(df['MATRICULE'])
            #df.columns = df.iloc[0]
            
            #df = df.dropna(subset=['MATRICULE'])  # Supprimer les lignes vides

            for _, row in df.iterrows():
                raw_sexe = str(row.get("SEXE")).strip().upper()
                sexe_value = "H" if "H" in raw_sexe else "F" if "F" in raw_sexe else None

               
              

                employee_data = {
                    "matricule": str(row.get("MATRICULE")).strip(),
                    "nom": str(row.get("NOM")).strip(),
                    "prenom": str(row.get("PRENOM")).strip(),
                    "fonction": str(row.get("FONCTION")).strip(),
                    "sexe": sexe_value,
                    "date_embauche": row.get("DATE EMBAUCHE"),
                    "business_line": row.get("BUSINESS LINE"),
                    "projet": row.get("PROJET"),
                    "service": row.get("SERVICE"),
                    "manager": row.get("LINE MANAGER"),
                    "localisation": row.get("LOCALISATION"),
                    "email": row.get("ADRESSE MAIL"),
                    "telephone": str(row.get("TELEPHONE")),
                }

                print(employee_data)
                employee_data = clean_employee_row(row)
                serializer = EmployeeSerializer(data=employee_data)
                
                if serializer.is_valid():
                    serializer.save()
                else:
                    print(f"Erreur ligne {row.get('MATRICULE')}: {serializer.errors}")


            return Response({"message": "Import terminé avec succès."}, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    

    
        

    @action(detail=False, methods=["post"], url_path="send-bulletins")
    def send_bulletins(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "Aucun fichier fourni."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Convertit le PDF en images, une image par page
            images = convert_from_bytes(file.read(), dpi=300)
            results = []

            for i, image in enumerate(images):
                # OCR sur l'image de la page
                text = pytesseract.image_to_string(image, lang="fra")
                print(f"--- PAGE {i+1} ---")
                print(text)  # Pour debug

                # Extraction du matricule avec RegExp
                matricule = None
                matricule = extract_matricule(text)
                """if m:
                    matricule = m.group(1)"""
                print(f"[DEBUG] Matricule extrait : {matricule}")

                if not matricule:
                    BulletinEnvoiLog.objects.create(matricule="???", statut="échec", message="Matricule non trouvé (OCR)")
                    continue

                employee = Employee.objects.filter(matricule=matricule).first()
                if not employee or not employee.email:
                    BulletinEnvoiLog.objects.create(matricule=matricule, statut="échec", message="Email introuvable")
                    continue

                # Génère le PDF de la page (optionnel, tu peux adapter)
                # Ici tu peux refaire un fitz.open(stream=...) sur le PDF original si tu veux garder la page individuelle,
                # sinon tu peux réenregistrer l'image en PDF
                # Ex: image.save(f"page_{i+1}.pdf", "PDF")

                # Pour l'exemple, on envoie juste le PDF complet :
                file.seek(0)
                pdf_bytes = file.read()

                email = EmailMessage(
                    subject="Votre bulletin de salaire",
                    body="Bonjour, veuillez trouver votre bulletin en pièce jointe.",
                    from_email="mombaye@camusat.com",
                    to=[employee.email]
                )
                email.attach(f"bulletin_{matricule}.pdf", pdf_bytes, "application/pdf")

                try:
                    email.send()
                    BulletinEnvoiLog.objects.create(matricule=matricule, email=employee.email, statut="succès")
                except Exception as e:
                
                    BulletinEnvoiLog.objects.create(matricule=matricule, email=employee.email, statut="échec", message=str(e))

            return Response({"message": "Traitement terminé (OCR)."})

        except Exception as e:
            print(e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=["get"], url_path="bulletins-envoyes-recents")
    def bulletins_envoyes_recents(self, request):
        trois_mois = timezone.now() - timedelta(days=90)
        queryset = BulletinEnvoiLog.objects.filter(date_envoi__gte=trois_mois).order_by('-date_envoi')
        serializer = BulletinEnvoiLogSerializer(queryset, many=True)
        return Response(serializer.data)
