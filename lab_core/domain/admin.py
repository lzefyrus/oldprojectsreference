# encoding: utf-8

from django.contrib import admin
from django.contrib.gis import admin as geo_admin
from reversion.admin import VersionAdmin

from domain.models import *

admin.site.register(Exam)
admin.site.register(Patient)
admin.site.register(InsuranceCompany)
admin.site.register(LaboratoryBrand)
admin.site.register(ExamResult)
admin.site.register(ExamResultDetail)

admin.site.register(ExamExpiration)
admin.site.register(HealthInsurance)
admin.site.register(HealthInsurancePlan)
admin.site.register(Holiday)
admin.site.register(PrescriptionPiece)


class LaboratoryPropertyBaseAdmin(admin.ModelAdmin):
    raw_id_fields = ('laboratory',)
    related_lookup_fields = {
        'laboratory': ['laboratory'],
    }


@admin.register(LaboratoryCollectionTime)
class LaboratoryCollectionTimeAdmin(LaboratoryPropertyBaseAdmin):
    pass


@admin.register(LaboratoryOpeningHours)
class LaboratoryOpeningHoursAdmin(LaboratoryPropertyBaseAdmin):
    pass


@admin.register(LaboratoryFacilities)
class LaboratoryCollectionTimeAdmin(LaboratoryPropertyBaseAdmin):
    pass


@admin.register(PreparationStep)
class PreparationStepAdmin(admin.ModelAdmin):
    raw_id_fields = ('laboratory', 'exam')
    related_lookup_fields = {
        'laboratory': ['laboratory'],
        'exam': ['exam'],
    }


class LabAdmin(geo_admin.GeoModelAdmin):
    readonly_fields = ('lat', 'lng')

    raw_id_fields = ('exams', 'brand')
    related_lookup_fields = {
        'exams': ['exams'],
        'brand': ['brand'],
    }

    fieldsets = (
        ('Data', {'fields': ('external_id', 'brand', 'exams', 'description', 'is_active', 'cnpj', 'street',
                             'street_number', 'zip_code', 'city', 'district', 'state', 'state_abbreviation', 'country',)}),
        ('Geo Data', {
            'classes': ('collapse',),
            'fields': ('point', 'lat', 'lng')
        })
    )

admin.site.register(Laboratory, LabAdmin)


class PrescriptionPieceInline(admin.StackedInline):
    model = PrescriptionPiece
    extra = 0


@admin.register(MedicalPrescription)
class MedicalPrescriptionAdmin(VersionAdmin):
    change_list_filter_template = "admin/filter_listing.html"
    inlines = [PrescriptionPieceInline]
    raw_id_fields = ('patient','insurance_company','modified_by','health_insurance_plan')
    related_lookup_fields = {
        # 'patient': ['patient'],
        # 'insurance_company': ['insurance_company'],
        'modified_by': ['modified_by'],
        'health_insurance_plan': ['health_insurance_plan'],
    }
    list_filter = ('status', )
    search_fields = ('id','patient__full_name','patient__user__email')


@admin.register(ScheduledExam)
class ScheduledExamAdmin(VersionAdmin):
    change_list_filter_template = "admin/filter_listing.html"
    raw_id_fields = ('prescription_piece','exam','modified_by', 'prescription', 'laboratory')
    related_lookup_fields = {
        'prescription_piece': ['prescription_piece'],
        'modified_by': ['modified_by'],
        'exam': ['exam'],
        'prescription': ['prescription'],
        'laboratory': ['laboratory'],
    }
    list_filter = ('status', )
    search_fields = ('id','prescription__patient__user__email', 'prescription__patient__full_name', 'prescription__id')


@admin.register(RejectionReason)
class RejectionReasonAdmin(admin.ModelAdmin):
    list_display = ('status', 'feedback', 'instruction', 'sort_order')


@admin.register(ScheduledExamPhoneCall)
class ScheduledExamPhoneCallAdmin(admin.ModelAdmin):
    raw_id_fields = ('scheduled_exam', )