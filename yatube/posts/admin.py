from django.contrib import admin

from .models import Group, Post, Comment, Follow


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Класс для настройки отображения модели Post в интерфейсе админки."""
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Класс для настройки отображения модели Group в интерфейсе админки."""
    list_display = ('title', 'slug', 'description')
    search_fields = ('description',)
    empty_value_display = '-пусто-'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Класс для настройки отображения модели
     Comment в интерфейсе админки."""
    list_display = (
        'post',
        'text',
        'created',
        'author',
    )
    search_fields = ('comment',)
    empty_value_display = '-пусто-'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Класс для настройки отображения модели
     Follow в интерфейсе админки."""
    list_display = (
        'user',
        'author',
    )
    search_fields = ('follow',)
    empty_value_display = '-пусто-'
