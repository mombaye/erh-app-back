from django.db import models

# Create your models here.
from django.db import models

class Employee(models.Model):
    SEXE_CHOICES = [
        ('H', 'Homme'),
        ('F', 'Femme'),
    ]

    matricule = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    fonction = models.CharField(max_length=100)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, null=True)
    date_embauche = models.CharField(max_length=100, blank=True, null=True)
    business_line = models.CharField(max_length=100, blank=True, null=True)
    projet = models.CharField(max_length=100, blank=True, null=True)
    service = models.CharField(max_length=100, blank=True, null=True)
    manager = models.CharField(max_length=100, blank=True, null=True)
    localisation = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    telephone = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f"{self.nom} {self.prenom}"
    

class BulletinEnvoiLog(models.Model):
    employees_id = models.BigIntegerField(null=True, blank=True)
    matricule = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True)
    statut = models.CharField(max_length=50)  # "succès", "échec", etc.
    message = models.TextField(blank=True)  # Détails en cas d’erreur
    date_envoi = models.DateTimeField(auto_now_add=True)
