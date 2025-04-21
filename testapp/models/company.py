from django.db import models


class Company(models.Model):
    name = models.CharField(
        verbose_name="Company name",
        max_length=50,
        help_text="The name of the company",
    )
    created_by = models.CharField(
        editable=False,
        max_length=40,
        db_index=True,
    )

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        constraints = [models.UniqueConstraint(fields=['name', 'created_by'], name='unique_company')]

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(
        verbose_name="Department name",
        max_length=50,
        help_text="The name of the department",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='departments',
    )

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        constraints = [models.UniqueConstraint(fields=['name', 'company'], name='unique_department')]

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(
        verbose_name="Team name",
        max_length=50,
        help_text="The name of the team",
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='teams',
    )

    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Teams"
        constraints = [models.UniqueConstraint(fields=['name', 'department'], name='unique_team')]

    def __str__(self):
        return self.name
