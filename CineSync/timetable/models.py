from datetime import timedelta

from django.core.validators import MinValueValidator
from django.db.models import (
    CASCADE,
    CharField,
    DateTimeField,
    FloatField,
    ForeignKey,
    IntegerField,
    Manager,
    Model,
)
from django.utils import timezone

from films.models import Film


class FilmSessionsManager(Manager):
    def nearest_timetable(self):
        current_datetime = timezone.now()
        end_datetime = current_datetime + timedelta(days=5)
        queryset = super().get_queryset()
        queryset = queryset.select_related('film', 'auditorium')
        queryset = queryset.prefetch_related('film__genres', 'film__countries')
        queryset = queryset.filter(
            start_datetime__gte=current_datetime,
            start_datetime__lte=end_datetime,
        )
        return queryset.order_by(FilmSession.start_datetime.field.name)

    def all_timetable(self):
        current_datetime = timezone.now()
        queryset = super().get_queryset()
        queryset = queryset.select_related('film', 'auditorium')
        queryset = queryset.prefetch_related('film__genres', 'film__countries')
        queryset = queryset.filter(start_datetime__gte=current_datetime)
        queryset = queryset.prefetch_related(FilmSession.film.field.name)
        return queryset.order_by(FilmSession.start_datetime.field.name)


class Auditorium(Model):
    number = CharField(
        max_length=20,
        verbose_name='Номер кинозала',
    )

    def __str__(self):
        return self.number

    class Meta:
        db_table = 'timetable_auditoriums'
        verbose_name = 'зал'
        verbose_name_plural = 'Залы'


class Row(Model):
    row_number = IntegerField(
        verbose_name='Номер ряда',
        validators=[
            MinValueValidator(1),
        ],
    )

    column_count = IntegerField(
        verbose_name='Количество кресел в ряду',
        validators=[
            MinValueValidator(1),
        ],
    )

    auditorium = ForeignKey(
        Auditorium,
        on_delete=CASCADE,
        verbose_name='Зал',
        related_name='rows',
        related_query_name='rows',
    )

    class Meta:
        db_table = 'timetable_rows'
        verbose_name = 'место'
        verbose_name_plural = 'Места'


class FilmSession(Model):
    objects = FilmSessionsManager()

    start_datetime = DateTimeField(
        verbose_name='Дата и время начала сеанса',
    )

    end_datetime = DateTimeField(
        verbose_name='Дата и время окончания сеанса',
        blank=True,
        null=True,
    )

    price = FloatField(
        verbose_name='Цена билета',
        validators=[
            MinValueValidator(1),
        ],
    )

    film = ForeignKey(
        Film,
        on_delete=CASCADE,
        verbose_name='Фильм',
        related_name='sessions',
        related_query_name='sessions',
    )
    auditorium = ForeignKey(
        Auditorium,
        on_delete=CASCADE,
        verbose_name='Зал',
        related_name='sessions',
        related_query_name='sessions',
    )

    def __str__(self):
        return (
            f'{self.film.name} - {str(self.start_datetime)}'
            f' - {self.auditorium}'
        )

    def save(self, *args, **kwargs):
        if self.start_datetime and self.film.duration:
            self.end_datetime = self.start_datetime + timedelta(
                minutes=self.film.duration,
            )

        super().save(*args, **kwargs)

    class Meta:
        db_table = 'timetable_film_sessions'
        verbose_name = 'сеанс'
        verbose_name_plural = 'Сеансы'
