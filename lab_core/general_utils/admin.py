# encode: utf-8

from django.contrib import admin

from .models import *


class LetsencryptModelAdmin(admin.ModelAdmin):
    list_display = ('id', )


admin.site.register(LetsencryptModel, LetsencryptModelAdmin)
admin.site.register(MobileSettings)