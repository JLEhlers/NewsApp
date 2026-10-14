from django.contrib import admin

from .models import Article, CustomUser, Newsletter, Publisher

admin.site.register(CustomUser)
admin.site.register(Publisher)
admin.site.register(Article)
admin.site.register(Newsletter)
