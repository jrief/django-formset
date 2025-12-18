from django.forms import fields, widgets
from django.forms.models import ModelForm

from formset.collection import AddSiblingActivator, FormCollection

from testapp.models.company import Company, Department, Team


class TeamForm(ModelForm):
    id = fields.IntegerField(
        required=False,
        widget=widgets.HiddenInput,
    )

    class Meta:
        model = Team
        fields = ['id', 'name']


class TeamCollection(FormCollection):
    induce_add_sibling = '.add_team:add_sibling'
    min_siblings = 0
    max_siblings = 3
    extra_siblings = 1
    team = TeamForm()
    legend = "Teams"
    related_field = 'department'

    add_team = AddSiblingActivator("Add Team")

    def retrieve_instance(self, data):
        if data := data.get('team'):
            try:
                return self.instance.teams.get(id=data.get('id') or 0)
            except (AttributeError, Team.DoesNotExist, ValueError):
                return Team(name=data.get('name'), department=self.instance)


class DepartmentForm(ModelForm):
    id = fields.IntegerField(
        required=False,
        widget=widgets.HiddenInput,
    )

    class Meta:
        model = Department
        fields = ['id', 'name']


class DepartmentCollection(FormCollection):
    induce_add_sibling = '.add_department:add_sibling'
    min_siblings = 0
    extra_siblings = 1
    department = DepartmentForm()
    teams = TeamCollection()
    legend = "Departments"
    related_field = 'company'

    add_department = AddSiblingActivator("Add Department")

    def retrieve_instance(self, data):
        if data := data.get('department'):
            try:
                return self.instance.departments.get(id=data.get('id') or 0)
            except (AttributeError, Department.DoesNotExist, ValueError):
                return Department(name=data.get('name'), company=self.instance)


class CompanyForm(ModelForm):
    class Meta:
        model = Company
        fields = '__all__'


class CompanyCollection(FormCollection):
    company = CompanyForm()
    departments = DepartmentCollection()


class MultipleCompanyForm(CompanyForm):
    id = fields.IntegerField(
        required=False,
        widget=widgets.HiddenInput,
    )

    created_by = fields.CharField(
        required=False,
        widget=widgets.HiddenInput,
        help_text="Dummy field required to distinguish the namespace of companies for each user",
    )


class CompaniesCollection(FormCollection):
    company = MultipleCompanyForm()
    departments = DepartmentCollection()
    min_siblings = 1
    legend = "Company"
    add_label = "Add Company"

    def retrieve_instance(self, data):
        if data := data.get('company'):
            try:
                return Company.objects.get(id=data.get('id') or 0)
            except Company.DoesNotExist:
                return Company(name=data.get('name'))
