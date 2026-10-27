from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('hospitals/', include('hospitals.urls')),
    path('departments/', include('departments.urls')),
    path('employees/', include('employees.urls')),
    path('doctors/', include('doctors.urls')),
    path('patients/', include('patients.urls')),
    path('appointments/', include('appointments.urls')),
    path('billing/', include('billing.urls')),
    path('insurance/', include('insurance.urls')),
    path('opd/', include('opd.urls')),
    path('ipd/', include('ipd.urls')),
    path('pharmacy/', include('pharmacy.urls')),
    path('laboratory/', include('laboratory.urls')),
    path('radiology/', include('radiology.urls')),
    path('inventory/', include('inventory.urls')),
    path('hr/', include('hr.urls')),
    path('nursing/', include('nursing.urls')),
    path('ambulance/', include('ambulance.urls')),
    path('audit-logs/', include('auditlogs.urls')),
    path('notifications/', include('notifications.urls')),
    path('reports/', include('reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
