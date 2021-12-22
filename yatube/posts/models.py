from django.db import models
from django.contrib.auth import get_user_model

from pytils.translit import slugify


User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        'Группа',
        max_length=200,
        help_text='Укажите название группы'
    )
    slug = models.SlugField(
        'Адрес для страницы группы',
        max_length=60,
        unique=True,
        blank=True,
        help_text=('Оставьте поле пустым или укажите адрес для '
                   'страницы группы. Используйте только латиницу, '
                   'цифры, дефисы и знаки подчёркивания')
    )
    description = models.TextField(
        'Текст',
        help_text='Краткое описание группы'
    )

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:60]
        super().save(*args, **kwargs)


class Post(models.Model):
    text = models.TextField(
        'Текст',
        help_text='Текст поста',
    )
    pub_date = models.DateTimeField(
        'Дата поста',
        auto_now_add=True,
        db_index=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
        help_text='Загрузите изображение',
    )

    class Meta:
        verbose_name = 'Статя'
        verbose_name_plural = 'Статьи'
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
    )
    text = models.TextField(
        'Текст комментария',
        help_text='Введите текст комментария',
    )
    created = models.DateTimeField(
        'Дата комментария',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-created']

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-user']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_follow'
            )
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
