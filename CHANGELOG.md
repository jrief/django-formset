## Changes

- 0.9 (next)
  * Fixed problems when resetting a formset containing multiple collections with siblings: All just
    added collections are removed on reset.
  * Distinguish while removing a collection: A just added collection is removed, while existing
    collections are marked for removal.
  * On cleaning post data while processing collections, one can choose whether to keep existig but
    removed colections for further processing, or ignore them.
  * Allow extra label to be added inside the "Add collection" button.

- 0.8.8
  * Use a simpler and semantically more correct HTML representation for the file uploader widget.

- 0.8.7
  * Fix: If an uploaded image has an EXIF orientation tag, that image that is transposed accordingly.
  * On file upload, fill the progressbar to only 90%. The remaining 10% of the progressbar are
    filled after successful image transformation.
  * Rename Event "submit" to "submitted", because otherwise FireFox triggers a page reload.

- 0.8.6
  * Fix: Files uploaded into collections with siblings, are not duplicated anymore.
  * Fix: Clear `cleaned_data` during form validation to prevent duplicate content.
  * Fix occasionally occuring MRO-TypeError when instantiating checkbox widget.
  * Remove tag "_marked_for_removal_" while submitting form. Use Array with holes instead.
  * In Collections with siblings, do not extend number of siblings, if maximum is reached.

- 0.8.5
  * Fix: Form collections with empty siblings, on submission now create an empty array.

- 0.8.4
  * Add optional argument for delay in milliseconds to button actions `okay` and `bummer`. 
  * Resetting a django-formset removes all just added sibling collections and unmarks all
    collections for removal.
  * Fields beeing hidden on the client using `show-if`/`hide-if` also are disabled to prevent
    validation – which wouldn't make sense anyway.
  * Add parameter `legend` to Form Collection so that a collection can have an optional title.

- 0.8.3
  * Fix: For ``field_css_classes``, fall back to form name rather than its prefix.

- 0.8.2
  * Fix: Set empty dropbox item on upload widget during form reset.
  * Fix: Collections with siblings on root level generated invalid form data.
  * Add special placeholder to render errors for collections with siblings.
  * Add additional actions to button: Spinner, Okay, Bummer and Reload.
  * In Button's proceed action, print a warning, if neither a success-, nor a
    fallback-URL is given to proceed.
  * In `FormCollectionView` handle response of posting formsets analogous to the way
    Django handles forms.

- 0.8.1
  * Adopt `DualSelector` for Tailwind.css.
  * Hide `calendar-picker-indicator` in touched input date fields.
  * Fix: Expecting path for base location as Path object.
  * Fix: Updating of existing object failed.
  * Add method `get_extra_data` to class `FormView`.
  * Increase max filename length to 250 characters.
  * Fix: Abort silently if input field is missing.
  * Replace `<div>`-based progress bar against proper HTML element `<progress>`.

- 0.8
  * Add widget `DualSelector` which accepts multiple values and is the form field counterpart
    to Django's `ManyToManyField`. This is an alternative widget to `SelectizeMultiple`.

- 0.7
  * Add widget `SelectizeMultiple` which accepts multiple values and is the form field counterpart
    to Django's `ManyToManyField`.
  * Bugfix in UploadWidget: Do not delete existing file on form update.

- 0.6
  * Content from `FileUploadWidget` can be transfered to a Django model and vice versa.

- 0.4
  * It is possible to control every aspect of the feedback, given to the user while he fills the
    input fields.
  * Templatetag `render_form` and `formsetify` accepts parameters `form_classes` and
    `collection_classes` for finer styling control.

- 0.3
  * Add `show-if`, `hide-if` and `disable-if` attribute parsing to fields and fieldsets.
  * Add class `Fieldset` to handle forms with legends and the possibility for hiding and disabling.
  * Form Collections may have siblings and can be extended.

- 0.2
  * Refactored to work for Django>4 only.
  * Added Form Collections.

- 0.1
  * Initial release.
