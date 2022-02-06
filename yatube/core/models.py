from django.db import models


class CreatedModel(models.Model):
    pub_date = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        abstract = True
        ordering = ('-pub_date',)
