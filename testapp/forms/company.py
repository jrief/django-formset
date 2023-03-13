from django.forms import fields, widgets
from django.forms.models import ModelForm, construct_instance, model_to_dict

from formset.collection import FormCollection

from testapp.models import Company, Member, Team


class CompanyForm(ModelForm):
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
    ''' 2nd level - This level DOES NOT work - there are no initial member-forms
    '''
    min_siblings = 0
    member = MemberForm()
    add_label = "Add Member"

    def model_to_dict(self, team):
        fields = self.declared_holders['member']._meta.fields
        return [{'member': model_to_dict(member, fields=fields)}
                for member in team.members.all()]

    def construct_instance(self, team, cleaned_data):
        for data in cleaned_data:
            try:
                member = team.members.get(id=data['member']['id'])
            except (KeyError, Member.DoesNotExist):
                member = Member(team=team)
            form_class = self.declared_holders['member'].__class__
            form = form_class(data=data['member'], instance=member)
            if form.is_valid():
                if form.marked_for_removal:
                    member.delete()
                else:
                    construct_instance(form, member)
                    form.save()


class TeamCollection(FormCollection):
    """ 1st level - This level works - saved objects are rendered
    """
    min_siblings = 0
    team = TeamForm()
    members = MemberCollection()
    add_label = "Add Team"

    def model_to_dict(self, company):
        fields = self.declared_holders['team']._meta.fields
        return  [{'team': model_to_dict(team, fields=fields)}
            for team in company.teams.all()]

    def construct_instance(self, company, cleaned_data):
        for data in cleaned_data:
            try:
                team = company.teams.get(id=data['team']['id'])
            except (KeyError, Team.DoesNotExist):
                team = Team(company=company)
            form_class = self.declared_holders['team'].__class__
            form = form_class(data=data['team'], instance=team)
            if form.is_valid():
                if form.marked_for_removal:
                    team.delete()
                else:
                    construct_instance(form, team)
                    form.save()


class CompanyCollection(FormCollection):
    """ 0 level - Main edited object
    """
    form = CompanyForm()
    teams = TeamCollection()

    def construct_instance(self, company, cleaned_data):
        super().construct_instance(company, cleaned_data)
        return
        for data in cleaned_data:
            try:
                team = company.teams.get(id=data['team']['id'])
            except (KeyError, Team.DoesNotExist):
                team = Team(company=company)
            form_class = self.declared_holders['team'].__class__
            form = form_class(data=data['team'], instance=team)
            if form.is_valid():
                if form.marked_for_removal:
                    team.delete()
                else:
                    construct_instance(form, team)
                    form.save()
