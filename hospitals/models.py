from django.db import models

from core.kenya import COUNTY_CHOICES, KEPH_LEVEL_CHOICES


class Branch(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    county = models.CharField(max_length=30, choices=COUNTY_CHOICES, blank=True)
    mfl_code = models.CharField(
        'MFL code', max_length=10, blank=True,
        help_text='Kenya Master Health Facility List (KMHFL) code',
    )
    keph_level = models.PositiveSmallIntegerField('KEPH level', choices=KEPH_LEVEL_CHOICES, null=True, blank=True)
    sha_accredited = models.BooleanField('SHA accredited', default=False)
    is_main_branch = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'
        ordering = ['name']

    def __str__(self):
        return self.name
