from django.forms import fields, widgets
from django.forms.models import ModelForm

from formset.collection import FormCollection

from testapp.models import Company, Member, Team


class MemberForm(ModelForm):
    id = fields.IntegerField(
        required=False,
        widget=widgets.HiddenInput,
    )

    class Meta:
        model = Member
        fields = ['id', 'name']


class MemberCollection(FormCollection):
    min_siblings = 0
    member = MemberForm()
    legend = "Members"
    add_label = "Add Member"
    related_field = 'team'

    def retrieve_instance(self, data):
        if data := data.get('member'):
            try:
                return self.instance.members.get(id=data.get('id') or 0)
            except (AttributeError, Member.DoesNotExist, ValueError):
                return Member(name=data.get('name'), team=self.instance)


class TeamForm(ModelForm):
    id = fields.IntegerField(
        required=False,
        widget=widgets.HiddenInput,
    )

    class Meta:
        model = Team
        fields = ['id', 'name']


class TeamCollection(FormCollection):
    min_siblings = 0
    team = TeamForm()
    members = MemberCollection()
    legend = "Teams"
    add_label = "Add Team"
    related_field = 'company'

    def retrieve_instance(self, data):
        if data := data.get('team'):
            try:
                return self.instance.teams.get(id=data.get('id') or 0)
            except (AttributeError, Team.DoesNotExist, ValueError):
                return Team(name=data.get('name'), company=self.instance)


class CompanyForm(ModelForm):
    class Meta:
        model = Company
        fields = '__all__'


class CompanyCollection(FormCollection):
    company = CompanyForm()
    teams = TeamCollection()


class CompanyPlusForm(CompanyForm):
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
    company = CompanyPlusForm()
    teams = TeamCollection()
    min_siblings = 1
    legend = "Company"
    add_label = "Add Company"

    def retrieve_instance(self, data):
        if data := data.get('company'):
            try:
                return Company.objects.get(id=data.get('id') or 0)
            except Company.DoesNotExist:
                return Company(name=data.get('name'))
