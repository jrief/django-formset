class SessionModelFormViewMixin:
    """
    Mixin class to be used for model detail views. Instead of a passing a unique identifier,
    use the session_key to assign each model to the user with that session.
    """
    def get_queryset(self):
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
