# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('status/', include('signals.apps.health.urls')),

    # The Signals application is routed behind the HAproxy with `/signals/` as path.
    path('signals/', include('signals.apps.api.urls')),
    path('signals/admin/', admin.site.urls),

    # SOAP stand-in endpoints
    path('signals/sigmax/', include('signals.apps.sigmax.urls')),

    # Questionnaire
    path('signals/v1/public/', include('signals.apps.questionnaire.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static

    media_root = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns + media_root
