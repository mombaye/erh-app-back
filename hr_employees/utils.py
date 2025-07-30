from datetime import datetime
import pandas as pd
import re

def parse_date(value):
    """Convertit une valeur Excel en chaîne de date valide, ou retourne None."""
    if pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d')
    if isinstance(value, str):
        try:
            return datetime.strptime(value.strip(), '%d/%m/%Y').strftime('%Y-%m-%d')
        except ValueError:
            try:
                return datetime.strptime(value.strip(), '%Y-%m-%d').strftime('%Y-%m-%d')
            except ValueError:
                return None
    return None

def normalize_sexe(value):
    """Nettoie et convertit le champ sexe."""
    if not value or pd.isna(value):
        return None
    value = str(value).strip().upper()
    return 'H' if 'H' in value else 'F' if 'F' in value else None

def clean_string(value):
    """Trim et transforme en string ou None si vide."""
    if pd.isna(value):
        return None
    return str(value).strip()

def clean_employee_row(row):
    """Nettoie une ligne de dataframe Excel en dict compatible serializer."""
    return {
        "matricule": clean_string(row.get("MATRICULE")),
        "nom": clean_string(row.get("NOM")),
        "prenom": clean_string(row.get("PRENOM")),
        "fonction": clean_string(row.get("FONCTION")),
        "sexe": normalize_sexe(row.get("SEXE")),
        "date_embauche": parse_date(row.get("DATE EMBAUCHE")),
        "business_line": clean_string(row.get("BUSINESS LINE")),
        "projet": clean_string(row.get("PROJET")),
        "service": clean_string(row.get("SERVICE")),
        "manager": clean_string(row.get("LINE MANAGER")),
        "localisation": clean_string(row.get("LOCALISATION")),
        "email": clean_string(row.get("ADRESSE MAIL")),
        "telephone": clean_string(row.get("TELEPHONE")),
    }


def extract_matricule(text):
    # Motif 1 : Matricule : 12345
    m = re.search(r"matricule[^0-9A-Za-z]*([A-Za-z0-9]{3,})", text, re.IGNORECASE)
    if m:
        return m.group(1)
    # Motif 2 : juste un code à 5-8 chiffres/lettres isolé sur une ligne
    m = re.search(r"^[A-Za-z0-9]{3,}$", text, re.MULTILINE)
    if m:
        return m.group(0)
    return None


def extract_matricule(text):
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if "matricule" in line.lower():
            # Vérifie à droite sur la même ligne (colonne)
            match = re.search(r"Matricule[^\w\d]*([A-Za-z0-9]{2,})", line, re.IGNORECASE)
            if match:
                # Vérifie que ce n'est pas un mot du type "Niveau" ou "Coefficient"
                val = match.group(1)
                if not val.lower() in ["niveau", "coefficient"]:
                    return val.strip()
            # Sinon, essaye la ligne d'après (en-dessous)
            if idx + 1 < len(lines):
                next_val = lines[idx + 1].strip()
                # Cherche le premier nombre à 2 ou 3 chiffres ou une chaîne alphanumérique plausible
                mat_match = re.match(r"([A-Za-z0-9]{2,})", next_val)
                if mat_match and not mat_match.group(1).lower() in ["niveau", "coefficient"]:
                    return mat_match.group(1)
    # Si rien trouvé, prend le premier nombre à 2 ou 3 chiffres du texte complet
    m = re.search(r"\b\d{2,5}\b", text)
    if m:
        return m.group(0)
    return None
