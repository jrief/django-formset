class SessionModelFormViewMixin:
    """
    Mixin class to be added to views inheriting from `django.views.generic.UpdateView`. This workaround is used for
    demonstration purpose, where we do not have a unique identifier to retrieve the desired object. Instead, we use
    the session_key to assign the latest model instance to the user with that session.
    Remember to add a CharField named ``created_by`` with a minimum length of 40 to the model used for this form.
    """
    def get_queryset(self):
        if not self.request.session.session_key:
            self.request.session.cycle_key()
        queryset = super().get_queryset()
        return queryset.filter(created_by=self.request.session.session_key)

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return queryset.last()

    def form_valid(self, form):
        response = super().form_valid(form)
        if form.instance.created_by != self.request.session.session_key:
            form.instance.created_by = self.request.session.session_key
            form.instance.save(update_fields=['created_by'])
        return response


class SessionFormCollectionViewMixin:
    """
    Mixin class to be added to views inheriting from `formset.views.EditCollectionView`. This workaround is used for
    demonstration purpose, where we do not have a unique identifier to retrieve the desired object. Instead, we use
    the session_key to assign the latest model instance to the user with that session.
    Remember to add a CharField named ``created_by`` with a minimum length of 40 to the model implementing the main
    object.
    """
    def get_queryset(self):
        if not self.request.session.session_key:
            self.request.session.cycle_key()
        queryset = super().get_queryset()
        return queryset.filter(created_by=self.request.session.session_key)

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        if object := queryset.last():
            return object
        return self.model(created_by=self.request.session.session_key)

    def form_collection_valid(self, form_collection):
        if not self.object:
            self.object = self.model.objects.create(created_by=self.request.session.session_key)
        return super().form_collection_valid(form_collection)
