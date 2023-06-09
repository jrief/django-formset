from django.db import models


class Company(models.Model):
    name = models.CharField(
        verbose_name="Company name",
        max_length=50,
    )

    created_by = models.CharField(
        editable=False,
        max_length=40,
        db_index=True,
    )

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        unique_together = ['name', 'created_by']

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(
        verbose_name="Department name",
        max_length=50,
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='departments',
    )

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        unique_together = ['name', 'company']

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(
        verbose_name="Team name",
        max_length=50,
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='teams',
    )

    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Teams"
        unique_together = ['name', 'department']

    def __str__(self):
        return self.name
