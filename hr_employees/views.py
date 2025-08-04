
from datetime import timedelta
import os
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

from django.core.mail import EmailMultiAlternatives


from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.conf import settings
from hr_employees.permissions import IsStaffOrGlobalAdmin
from rest_framework import permissions

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]  # 👈 toute l’API nécessite auth

    @action(detail=False, methods=['post'], url_path='import')
    def import_employees(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response({"error": "Aucun fichier fourni."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            
            df = pd.read_excel(file)
           
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
            file_bytes = file.read()
            # Convertit le PDF en images, une image par page
            images = convert_from_bytes(file_bytes, dpi=300)
            results = []
            pdf_document = fitz.open(stream=file_bytes, filetype="pdf")

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
                single_page_pdf = fitz.open()
                single_page_pdf.insert_pdf(pdf_document, from_page=i, to_page=i)
                pdf_bytes = single_page_pdf.tobytes()

                current_year = timezone.now().year
                current_month = timezone.now().month
                matricule = employee.matricule
                folder = os.path.join(
                    settings.BULLETIN_DIR,
                    str(current_year),
                    f"{current_month:02d}",
                    matricule
                )
                os.makedirs(folder, exist_ok=True)
                filepath = os.path.join(folder, f"bulletin_{current_year}_{current_month:02d}.pdf")
                with open(filepath, "wb") as f:
                    f.write(pdf_bytes)


                html_message = f"""
                <html>
                <body style="font-family: 'Segoe UI', Arial, sans-serif; background: #f7f9fa; margin:0; padding:0;">
                    <table width="100%" bgcolor="#f7f9fa" style="padding: 40px 0;">
                    <tr>
                        <td align="center">
                        <table width="450" bgcolor="#fff" style="border-radius:14px;box-shadow:0 2px 16px #00000010;overflow:hidden">
                            <tr>
                            <td align="center" style="padding:28px 28px 0 28px;">
                                <img src="https://camusat.com/wp-content/uploads/2023/01/logo-camusat.svg" alt="Camusat" style="height:48px;margin-bottom:12px;" />
                                <h2 style="color:#174189;letter-spacing:1px;margin-bottom:10px;">Votre bulletin de salaire</h2>
                                <p style="color:#223243;font-size:15px;line-height:1.7;margin:10px 0 24px 0;">
                                Bonjour <b>{employee.prenom} {employee.nom}</b>,<br>
                                Veuillez trouver ci-joint votre <b>bulletin de salaire</b> du mois de {timezone.now().strftime('%B %Y')}.<br>
                                <span style="color:#747c8a;">(Ce document est confidentiel.)</span>
                                </p>
                                
                                <div style="font-size:13px;color:#aaa;margin-bottom:6px;">
                                <b>Camusat Sénégal</b><br>
                                Service RH — {timezone.now().strftime('%B %Y')}
                                </div>
                                <div style="color:#aaa;font-size:12px;margin-top:14px;">
                                Ceci est un message automatique, merci de ne pas répondre directement à cet e-mail.
                                </div>
                            </td>
                            </tr>
                        </table>
                        </td>
                    </tr>
                    </table>
                </body>
                </html>
                """

                email = EmailMultiAlternatives(
                    subject="Votre bulletin de salaire",
                    body="Bonjour, veuillez trouver votre bulletin de salaire en pièce jointe.",
                    from_email="rh.senegal@camusat.com",
                    to=[employee.email]
                )
                email.attach(f"bulletin_{matricule}.pdf", pdf_bytes, "application/pdf")
                email.attach_alternative(html_message, "text/html")

                try:
                    email.send()
                    BulletinEnvoiLog.objects.create(matricule=matricule, email=employee.email, statut="succès")
                except Exception as e:
                    print(e)
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
    

    
   

    @action(
        detail=False,
        methods=["post"],
        url_path="create-accounts",
        permission_classes=[IsStaffOrGlobalAdmin],  # 👈 ici staff ou global admin suffisent
    )
    def create_accounts(self, request):
        """
        Crée des comptes utilisateurs pour une liste d'IDs employés
        et envoie les credentials par mail pro.
        """
        employee_ids = request.data.get("employee_ids", [])
        if not employee_ids:
            return Response({"error": "Aucun ID employé fourni."}, status=status.HTTP_400_BAD_REQUEST)
        
        User = get_user_model()
        created = []
        errors = []
        
        for emp_id in employee_ids:
            try:
                emp = Employee.objects.get(id=emp_id)
                print(emp)
                # Vérifie si déjà un compte existe avec ce mail
                if User.objects.filter(email=emp.email).exists():
                    errors.append(f"Compte déjà existant pour {emp.email}")
                    continue

                # Génère un username unique et mot de passe temporaire
                username = emp.email.split('@')[0]
                password = get_random_string(length=12)

                user = User.objects.create_user(
                    username=username,
                    email=emp.email,
                    password=password,
                    country=emp.country if hasattr(emp, "country") else None,
                
                    first_login=True,
                    is_staff=True,
                    is_global_admin=False,
                    employee=emp,  # 👈 on lie le user à l'employé
                )


                # Si CustomUser a country etc., adapte ici

                # Envoi du mail de credentials
                plateforme_url = getattr(settings, "PLATFORM_URL", "https://erh.camusats.com")
                subject = "Création de votre compte RH Camusat"
                html_message = f"""
                <html>
                <body style="font-family:Arial,sans-serif;">
                    <h2 style="color:#174189;">Bienvenue sur la plateforme RH Camusat</h2>
                    <p>Bonjour <b>{emp.prenom} {emp.nom}</b>,<br>
                    Un compte vient d'être créé pour vous.<br>
                    Accédez à la plateforme via <a href="{plateforme_url}">{plateforme_url}</a><br><br>
                    <b>Identifiant :</b> {emp.email}<br>
                    <b>Mot de passe provisoire :</b> {password}<br>
                    <span style="color:#888;">(Vous pourrez le modifier à la première connexion.)</span>
                    <br><br>
                    <i>Ce mail est automatique, ne pas répondre.</i>
                    </p>
                </body>
                </html>
                """

                email = EmailMultiAlternatives(
                    subject=subject,
                    body=f"Bonjour {emp.prenom}, votre compte a été créé. Identifiant: {emp.email} | Mot de passe provisoire: {password}",
                    from_email="rh.senegal@camusat.com",
                    to=[emp.email],
                )
                email.attach_alternative(html_message, "text/html")
                email.send()
                created.append(emp.email)

            except Employee.DoesNotExist:
                errors.append(f"Employé ID {emp_id} introuvable.")
            except Exception as e:
                print(e)
                errors.append(str(e))

        return Response({
            "comptes_crees": created,
            "erreurs": errors
        })


    @action(detail=False, methods=['post'], url_path="send-bulletins-to-user")
    def send_bulletins_to_user(self, request):
        """
        Un utilisateur demande à recevoir un ou plusieurs bulletins.
        Payload attendu: { "matricule": "123456", "mois": [ { "year": 2024, "month": 6 }, ... ], "email": "..." }
        """
        data = request.data
        matricule = data.get("matricule")
        email = data.get("email")  # facultatif, sinon user connecté
        mois = data.get("mois", [])  # [{ "year": 2024, "month": 7 }, ...]
        
        if not matricule or not mois:
            return Response({"error": "Matricule et mois requis"}, status=400)
        
        employee = Employee.objects.filter(matricule=matricule).first()
        to_email = email or (employee.email if employee else None)
        if not to_email:
            return Response({"error": "Email non trouvé"}, status=400)
        
        files_attached = []
        not_found = []
        errors = []

        for entry in mois:
            try:
                year, month = entry.get("year"), entry.get("month")
                path = os.path.join(
                    settings.BULLETIN_DIR,
                    str(year),
                    f"{int(month):02d}",
                    str(matricule),
                    f"bulletin_{year}_{int(month):02d}.pdf"
                )
                if os.path.exists(path):
                    files_attached.append(path)
                else:
                    not_found.append(f"{year}-{month:02d}")
            except Exception as e:
                errors.append(f"{year}-{month:02d} : {str(e)}")
        
        if not files_attached:
            return Response({"error": f"Aucun fichier trouvé pour les périodes demandées: {not_found}", "details": errors}, status=404)
        
        # Prépare et envoie le mail avec toutes les pièces jointes
        try:
            subject = "Vos bulletins de salaire demandés"
            body = f"Bonjour, veuillez trouver vos bulletins de salaire en pièces jointes pour les périodes demandées."
            email_message = EmailMultiAlternatives(subject, body, from_email="rh.senegal@camusat.com", to=[to_email])
            for filepath in files_attached:
                try:
                    with open(filepath, "rb") as f:
                        email_message.attach(os.path.basename(filepath), f.read(), "application/pdf")
                except Exception as e:
                    errors.append(f"Erreur lecture fichier {filepath}: {str(e)}")
            email_message.send()
        except Exception as e:
            return Response({"error": "Erreur lors de l'envoi du mail.", "details": str(e), "fichiers_trouves": files_attached, "not_found": not_found}, status=500)

        return Response({
            "message": f"{len(files_attached)} bulletin(s) envoyés à {to_email}.",
            "not_found": not_found,
            "errors": errors
        })


    

    @action(detail=True, methods=["get"], url_path="available-bulletins")
    def available_bulletins(self, request, pk=None):
        """
        Retourne la liste des bulletins disponibles (année, mois) pour un matricule donné.
        L'URL sera : /api/employees/{matricule}/available-bulletins/
        """
        matricule = pk
        base_dir = settings.BULLETIN_DIR  # ex: "/app/data/bulletins"
        result = []
        # Chemin: .../année/mois/matricule/bulletin_année_mois.pdf
        for year in os.listdir(base_dir):
            year_path = os.path.join(base_dir, year)
            if not os.path.isdir(year_path) or not year.isdigit():
                continue
            for month in os.listdir(year_path):
                month_path = os.path.join(year_path, month)
                if not os.path.isdir(month_path) or not re.match(r"\d{2}", month):
                    continue
                emp_path = os.path.join(month_path, matricule)
                if not os.path.isdir(emp_path):
                    continue
                # Vérifie si le PDF existe
                pdf_name = f"bulletin_{year}_{month}.pdf"
                pdf_path = os.path.join(emp_path, pdf_name)
                if os.path.isfile(pdf_path):
                    result.append({"year": int(year), "month": int(month)})
        # Trie du plus récent au plus ancien
        result.sort(reverse=True, key=lambda x: (x["year"], x["month"]))
        return Response(result)
