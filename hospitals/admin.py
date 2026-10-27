from django.contrib import admin
from .models import Branch


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'county', 'mfl_code', 'keph_level', 'sha_accredited', 'phone', 'is_main_branch', 'is_active']
    list_filter = ['county', 'keph_level', 'sha_accredited', 'is_main_branch', 'is_active']
    search_fields = ['name', 'phone', 'mfl_code']
