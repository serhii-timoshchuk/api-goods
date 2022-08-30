from django.contrib import admin # noqa
from . import models


class GalleryInline(admin.TabularInline):
    fk_name = 'product'
    model = models.Gallery


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [GalleryInline, ]
    ordering = ['id']
    list_display = ['name', 'price', 'user']
    readonly_fields = ['createdon']


admin.site.register(models.Gallery)
admin.site.register(models.Author)
