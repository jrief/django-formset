from django.forms import fields, widgets
from django.forms.models import ModelForm, construct_instance, model_to_dict

from formset.collection import FormCollection

from testapp.models import Company, Member, Team


class CompanyForm(ModelForm):
    id = fields.IntegerField(
        required=False,
        widget=widgets.HiddenInput,
    )

    class Meta:
        model = Company
        fields = '__all__'


class TeamForm(ModelForm):
    id = fields.IntegerField(
        required=False,
        widget=widgets.HiddenInput,
    )

    class Meta:
        model = Team
        fields = ['id', 'name']


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
    add_label = "Add Member"

    def model_to_dict(self, team):
        fields = self.declared_holders['member']._meta.fields
        return [{'member': model_to_dict(member, fields=fields)}
                for member in team.members.all()]

    def construct_instance(self, team):
        for holder in self.valid_holders:
            member_form = holder['member']
            instance = member_form.instance
            id = member_form.cleaned_data.get('id') or 0
            try:
                instance = Member.objects.get(id=id)
            except Member.DoesNotExist:
                instance.id = None
                instance.team = team
            else:
                if member_form.marked_for_removal:
                    instance.delete()
                    continue
                else:
                    member_form.instance = instance
            construct_instance(member_form, instance)
            member_form.save()


class TeamCollection(FormCollection):
    min_siblings = 0
    team = TeamForm()
    members = MemberCollection()
    legend = "Team"
    add_label = "Add Team"

    def model_to_dict(self, company):
        fields = self.declared_holders['team']._meta.fields
        data = []
        for team in company.teams.all():
            data.append({
                'team': model_to_dict(team, fields=fields),
                'members': self.declared_holders['members'].model_to_dict(team),
            })
        return data

    def construct_instance(self, company):
        for holder in self.valid_holders:
            team_form = holder['team']
            instance = team_form.instance
            id = team_form.cleaned_data['id'] or 0
            try:
                instance = Team.objects.get(id=id)
            except Team.DoesNotExist:
                instance.id = None
                instance.company = company
            else:
                if team_form.marked_for_removal:
                    instance.delete()
                    continue
                else:
                    team_form.instance = instance
            construct_instance(team_form, instance)
            team_form.save()
            holder['members'].construct_instance(instance)


class CompanyCollection(FormCollection):
    company = CompanyForm()
    teams = TeamCollection()


class CompaniesCollection(FormCollection):
    company = CompanyForm()
    teams = TeamCollection()
    min_siblings = 1
    legend = "Company"
    add_label = "Add Company"

    def construct_instances(self):
        for holder in self.valid_holders:
            company_form = holder['company']
            instance = company_form.instance
            id = company_form.cleaned_data['id'] or 0
            try:
                instance = Company.objects.get(id=id)
            except Company.DoesNotExist:
                instance.id = None
            else:
                if company_form.marked_for_removal:
                    instance.delete()
                    continue
                else:
                    company_form.instance = instance
            construct_instance(company_form, instance)
            company_form.save()
            holder['teams'].construct_instance(instance)
