from django.db import models


class CountyUnnormalized(models.Model):
    state_code = models.CharField(
        verbose_name="State code",
        max_length=2,
    )

    state_name = models.CharField(
        verbose_name="State name",
        max_length=20,
        db_index=True,
    )

    county_name = models.CharField(
        verbose_name="County name",
        max_length=30,
    )

    class Meta:
        ordering = ['state_name', 'county_name']


    def __str__(self):
        return f"{self.county_name} ({self.state_code})"


class State(models.Model):
    code = models.CharField(
        verbose_name="Code",
        max_length=2,
    )

    name = models.CharField(
        verbose_name="Name",
        max_length=20,
        db_index=True,
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class County(models.Model):
    state = models.ForeignKey(
        State,
        on_delete=models.CASCADE,
    )

    name = models.CharField(
        verbose_name="Name",
        max_length=30,
    )

    class Meta:
        ordering = ['state', 'name']

    def __str__(self):
        return f"{self.name} ({self.state.code})"
