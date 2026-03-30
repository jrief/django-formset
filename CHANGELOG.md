## Changes

- 2.2.4
  * Fix #266: Timing issue in widgets `DateField` and `DateTimeField`. Input focus switched before
    processing user input in Firefox and Safari browsers.
  * Better handling of methods `clean_content` in RichtextArea and its dialog forms.
  * Fix: Richtext rendering for text nodes with multiple marks now handled properly.
  * Fix: In forms Meta classes using `fields_map`, the initial value is ignored.

- 2.2.3
  * Widgets `DateRangePicker`, `DateRangeTextbox`, `DateRangeCalendar`, `DateTimeRangePicker`,
    `DateTimeRangeTextbox` and `DateTimeRangeCalendar` now mimick the disabled properly if the
    underlying input field is disabled.
  * Fix #251: In `FileUploadWidget`, accept MIME-type is now checked on the client side before
    upoading a file.
  * Fix: Use proper renderer for widget `TelInput` introduced in Django-6.0.
  * Fix #256: Set position for widget `PhoneNumberInput` if used with a default country.
  * Fix: Open international selector for widget `PhoneNumberInput` if used without a default
    country and user starts typing.
  * Fix: In `Selectize` widget, when using `filter_by`, an empty filter value is now properly
    ignored when loading options lazily.

- 2.2.2
  * Fix in `StepperCollection`: Do not check the validity of transient forms.
  * Fix in `PhoneNumberField`: If field is empty, it now validates unless required.

- 2.2.1
  * Decativate all decorators `@allowedAction`, as they only work locally but not on
    https://django-formset.fly.dev/
  * Fix in `PhoneNumberField`: If field is not required and remains empty, it validates.

- 2.2
  * Improve: Handle detached buttons separately when rendering form collections. This allows the use
    of detached buttons inside collections with siblings.
  * **Pending breaking change**: In classes inheriting from a `FormCollection` with siblings, the
    attribute `add_label` is deprecated in favor of `induce_add_sibling` and its corresponding
    activator field. This gives developers the freedom where to place and how to style the buttons
    used to add siblings. 
  * **Pending breaking change**: In classes inheriting from a `FormCollection` with siblings, method
    `retrieve_instance` is replaced against `get_or_create_instance`. The latter now also returns a
    Boolean value when an instance was created which is stored as `created` inside the valid holders
    of a collection. This allows developers to distinguish between existing instances and newly
    created ones, when preparing the response.
  * Each time a formset is submitted, an `extra_data` object is added to the request payload. This
    can be used to pass arbitrary data to the submission. If partial submissions are used, the new
    button action `setExtraData` can be used to add response data to this object.
  * Feat: Add attribute `reverse_accessor` on FormCollection. This allows developers to specify the
    reverse accessor name of a `ForeignKey` relation used in collections.
  * Fix: Detached buttons use the prefixed path for name attributes.
  * Fix: The backend implementation of the `RichtextArea` widget now validates the length of
    submitted text ignoring all HTML tags. This emulates the behaviour of its frontend counterpart.
  * If any of the forms to be submitted partially does not validate, then report that form and do
    not send any data to the server. This action can be bypassed by setting `force-submission`.
  * Add hook, so that dialogs and stepper-steps are forced to become visible when reporting the
    validity and their forms contain invalid fields.
  * Fix: Widgets observing an `UploadedFileInput` now handle attributes `df-require`, `df-disable`,
    `df-show` and `df-hide` as expected.
  * Feat: Button action `setFieldValue()` now can update a complete datastructure of field values
    inside `formset_data`. Until version 2.1 it only was possible to update scalar values. 
  * Fix: The `Selectize` widget now correctly pilfers the height of its original widget, even if
    style attribute is set `height: auto;`. 
  * The initial values specified in an `Activator` field now is rendered as `value="…"` inside its
    associated `Button` widget.
  * Fix #244: Multiple widgets of type `RichtextArea` can use the same dialog form inheriting from
    `RichtextDialogForm`. 
  * Add support for Django-6.0 and drop support for Django-5.0.
  * Adopt the styling of the file upload widget, it now responds to dragging events. 

- 2.1.4
  * Fix: In `StepperCollection` only immediate children are considered as `StepperSteps`. This
    caused problems when nesting collections.
  * Fix race condition during initialization of `RichtextArea` widget: This web component might
    already have been initialized, before `FieldGroup` was constructed.
  * Improve readablility: Use emdash in Date(Time)Range widget to separate from – until datetimes.
  * Fix rare problem when dragging a sortable collection.
  * Improve UX: Set background-color for smoother dragging of a `FormCollection`.
  * Fix: Accept Date(Time)Range objects delivered by Postgres in associated widgets.
  * Improve UX: When sorting form collections, the trash symbol now is hidden to prevent confusion.
  * Fix: add extra check to see if instance marked for removal has already been deleted.
  * Improve UX: Make disabled `Selectize` widgets better distinguishable by applying opacity to 
    the whole widget.
  * Fix regression from 2.1.3: Hover in Calendar over prev and next button highlights until start
    or begin of calendar sheet, even in non-range mode.

- 2.1.3
  * The `Selectize` widget never renders the `empty_label` provided by the field. Instead, the user
    can remove the selected option, unless the field is marked as required.
  * Refactor conversion of initial value into string from fields `DateRangeField`,
    `DateTimeRangeField` to widgets `DateRangePicker`, `DateRangeTextbox`, `DateRangeCalendar`,
    `DateTimeRangePicker`, `DateTimeRangeTextbox` and `DateTimeRangeCalendar`.
  * Consistently align placeholder in `SelectizeMultiple` widget with that of the `Selectize`
    widget.
  * In `DjangoFormset.ts`, use `location.assign()` instead of assigning value directly to
    `location.href`.
  * Fix #214: `list_filter` in `ModelAdmin` now keeps querystring when switching from detail view to
    list view.

- 2.1.2
  * In `ModelAdminMixin`, after validating a form, method `save_model` is called to save the
    object. This maintains compatibility with the default `ModelAdmin` implementation.
  * Fix #236: `maxLength` in slug field is not ignored when typing into the observed field.
  * Fix: Server side code of widget `RichtextArea` now properly re-validates the length of the
    submitted rich text.
  * Fix #239: `DateRangePicker` and `DateTimeRangePicker` did not correct the local timezone
    offset during string generation.

- 2.1.1
  * Fix #232: In `SelectizeWidget`, when scrolling beyond `max_prefetch_choices`, although options
    with sublabel and itemlabel are added, the options are not rendered properly.
  * Fix #224: Conditional attributes in widgets referring to fields in a `Fieldset` did not work.
  * When using the `df-show`, `df-hide`, `df-disable` or `df-require` attributes with a relative
    path to another field, this path now is evaluated using the current field's `name`. This should
    fix some problems when using a relative path.
  * `DecimalUnitInput` now also works on Chrome for Android.

- 2.1
  * Add special widget `DecimalUnitInput`. It can be used for decimal values with a unit, such
    as money, length, etc.
  * Options in the `Selectize` and `SelectizeMultiple` widgets can now render sublabels below their
    main labels. This is useful to display additional information about the option.
  * Add utility functions `get_related_object` and `get_related_queryset` to deserialize foreign
    key and many-to-many relationships from `JSONField`s.
  * Flags in `PhoneNumberInput`, `CountrySelectize` and `CountrySelectizeMultiple` are now loaded
    as a PNG-sprite rather than through individual SVG-files. Therefore there is no need to
    `npm install flag-icons` anymore.
  * Fix: Setting the value of the HTML field used for `PhoneNumberInput`, now works as exected.
  * Widget `RichtextArea` accepts the extra option `richtext-bidirectional` for mapping between
    dialog forms and editor state. The behaviour of `richtext-map-to` and `richtext-map-from`
    changed slightly. Read the documentation on how to use it.
  * Fix: Handle widget attribute `df-require` as intended.
  * Fix: Regressions by allowing empty label in `Selectize` widget.
  * Fix: Fields using a filter are always considered as incomplete.
  * Fix: django-formset's `ModelAdmin.get_model()` allows to override the model form.
  * In `Selectize` and `SelectizeMultiple`, hide search input field, if number of options is <25.


- 2.0.1
  * Fix regression introduced in 2.0: Attribute `filter_by` in widgets `Selectize`,
    `SelectizeMultiple` and `DualSelector` did not trigger a reload if observer field changed.
  * Prevent double loading of options in widgets `Selectize`, `SelectizeMultiple` and
    `DualSelector`.

- 2.0
  * **Main feature of this release:** It now is possible to use a **django-formset** aware
    `ModelForm` or `FormCollection` inside the Django-Admin.
    Read the [documentation](https://django-formset.fly.dev/admin-integration/) on how to use this
    feature.
  * A **django-formset** aware `ModelForm` can use the attribute `fields_map` in its `Meta` class.
    This allows to map fields from a `Fieldset` to any arbitrary model field. It also allows to
    map multiple form fields into a `JSONField` offered by the model. 
  * A **django-formset** aware `ModelForm` can use the new `CollectionField` in combination with the
    just mentioned `fields_map`. This allows to store the complete content of a form collection
    inside JSON.
  * **Breaking Change:** The `Fieldset` class is a standalone entity to group multiple input fields
    into a ``<fieldset>``-element. It is not a subclass of Django's `Form` class anymore. Read the
    [documentation](https://django-formset.fly.dev/fieldsets/) on how to use it.
  * **Breaking Change:** The `FormMixin` class has been moved from `formset.utils` to
    `formset.forms`. There are two new classes `formset.forms.Form` and `formset.forms.ModelForm`
    which shall be used as base classes for forms and model forms.
  * **Breaking Change:** The form field class `formset.richtext.fields.RichTextField` has been
    moved from `formset.richtext.fields` to `formset.formfields.richtext`. The model field class
    `formset.richtext.fields.RichTextField` has been moved from `formset.richtext.models.fields` to
    `formset.modelfields`. The widget class `formset.richtext.widgets.RichTextArea` has been moved
    from `formset.richtext.widgets` to `formset.widgets`. This change was made to create a
    consistent naming convention across all widgets, form- and model fields.
  * **Breaking Change:** The classes `DateRangeField` and `DateTimeRangeField` have been moved from
    `formset.ranges` to `formset.formfields`.
    The classes `DateRangeCalendar`, `DateRangeTextbox`, `DateRangePicker`, `DateTimeRangeCalendar`,
    `DateTimeRangeTextbox` and `DateTimeRangePicker` have been moved from `formset.ranges` to
    `formset.widgets`.
  * **Drop support for Django-4.2**.
  * Semantically improve HTML: The `<div class="dj-form">`-element to wrap forms now is rendered as 
    `<div role="form">`. 
  * The `Selectize` widget now uses a search box inside the dropdown instead of a search box inside
    the selection area.
  * The `Selectize` widget now scrolls infinite, i.e., it loads the remaining options from the
    server when scolling to the end of the listbox.
  * Error messages shown for invalid fields hide as soon as the field is focused. This is to
    prevent the user from being unsettled by an error message while filling out the form.
  * In input fields, show the success tick for validated fields after blurring and not while typing,
    for the same reason as above.
  * After submitting a form containing the field `RichTextField`, the uploaded image is copied
    from the temporary upload folder into its final destination.
  * Add management command `./manage.py cleanup_files` to delete dangling files. This is because the
    `UploadedFileInput` widget accepts files before their form is submitted and hence processed.
  * Fix: Border of Richtext Area and Selectize widgets now has the same (green) feedback border as
    other input fields on blur after entering a valid value.
  * Fix: Calendar widget inside a form collection was not rendered properly.
  * Fix: Selectize widget had alignment problems with its lookup field. 
  * Fix: Placement of dialog for phone number and date picker now also considers left offset.

- 1.7.8
  * Fix #236: `maxLength` in slug field has been ignored. If set, `DjangoSlugElement` now truncates
    this string.

- 1.7.7
  * Add support for Django-5.2.

- 1.7.6
  * Fix #209: Induce button now also work for fresh form collections.

- 1.7.5
  * Fix #208: Closed form dialogs are always considered as valid.
  * Fix in web component ``date-picker`` and ``date-time-picker``: On submission the timezone offset
    now is removed, this sometimes caused the submission of incorrect date/time stamps.

- 1.7.4
  * Fix #80: Allow to use `django_filters.FilterSet` on filtered widgets.

- 1.7.3
  * Fix: Adopt signature of `clean()` method to Django's clean form.
  * Fix #196: Temporarily disable Calendar while fetching new sheet.

- 1.7.2
  * Fix: Aggregate data before submitting untouched form collections.
  * Fix: Dispatch `Event('invalid')` for invalid fields only if form validation didn't do it during
    validation.

- 1.7.1
  * Stepper was not invalidated if invalid data was filled into previous form. 
  * Richtext Area (fix #198): Styles of separator in menubar of RichtextArea were not aligned properly.
  * Richtext Area: Fix scoping problem with nested Richtext editors.
  * Richtext Area: Make scrollbar appear in contenteditable only.
  * Richtext Area: Upgrade to TipTap version 2.11.5.
  * Richtext Area (fix #191): Do not blur wrapper element if clicked element is part of it.

- 1.7
  * Main feature of this release: Add component ``StepperCollection`` allowing to fill out forms
    step by step.
  * Fix #192: In `RichtextArea`, the border was not rendered showing invalid state, if this field
    remained untouched with the form being submitted.

- 1.6.1
  * Fix: `DatePicker` and `DateCalendar` sometimes had an offset of one day, if timezone caused a
    shift after midnight.
  * Fix: Adding `<html data-bs-theme="…">` now also causes a color adjustment for widgets.
  * Improve styling of the dropbox in `FileUploadWidget`.
  * Prevent flickering of submenus in `RichtextArea` during initialization.

- 1.6
  * Main feature of this release: Full support for dark mode.
  * Add support for Django-5.1.
  * Always apply 6 rows to the calendar widget to prevent resizing when paginating.
  * To `RichtextArea` widget, add control elements to select font family, font size and line
    spacing.
  * Fix: Only find direct dialog element for a menu button. This caused problems when nesting
    multiple richtext areas.
  * Fix: `Selectize` widget did not apply proper styles if group elements are nested.
  * Fix: `FormDialog` loaded main stylesheet unnecessarily
  * Fix: `RichtextArea` now limits the width of sub-dialogs to main textarea.
  * Feature: In `RichtextArea` menu items can be grouped in menubar to wrap consistently.
  * Feature: In `RichtextArea` add class-based Node- and Mark control-elements.
  * The build target has been renamed from `esbuild` to `esbuild.modular`.

- 1.5.6
  * Fix: In `RichtextArea`, wait until the web component is completely initialized before validating
    its content.

- 1.5.5
  * Fix: Regression in `FileUploadWidget`, drag and drop of file into drag area does not work.

- 1.5.4
  * yanked

- 1.5.3
  * Fix: Regression in `RichtextArea`, heading with a single level does not work.

- 1.5.2
  * Fix naming issue in interactive docs, preventing the dialog not to close.
  * Fix in RichtextArea: Dropdown menu did not show up at the right position.

- 1.5.1
  * The published version of **django-formset** now also includes the monolithic build of all
    JavaScript files.
  * In RichtextArea: Add control element to select font family.
  * Date- and DateTime-widgets as Calendar representation now always apply 6 rows to prevent widget
    resizing when paginating.
  * Fixing RichtextArea: Only find direct dialog element for a menu button.
  * Fixing Selectize widget: Apply proper styles if group elements are nested. Happened when using
    the widget in a RichtextArea's dialog.
  * Fixed: Main stylesheet sometimes was loaded more than once.

- 1.5
  * **Breaking Change:** Always include `<script src="{% url 'javascript-catalog' %}"></script>` to
    the `<head>`-section of an HTML template. This is because `gettext` is used inside many
    JavaScript files. 
  * Drop support for Django-4.1 and Python-3.9.
  * Add support for Python-3.12.
  * Fix #142: A `FormCollection` with siblings and multiple `RichtextArea` widgets did not work.
  * Fix #140: Adding `default_renderer` to `FormCollection` did not always have the intended effect.
  * Fix #138: Selectize widget in sortable collection raises JavaScript error.
  * Fix monolithic build.
  * Attribute `<button df-click="…">` now accepts function `setFieldValue()`. This can be used to
    transfer values from one field to another one.
  * Introduce partial submits and prefilling of dialog forms in collections.
  * The parser generator allows whitespace inside parentheses.
  * Perform all E2E tests by also using the monolithic build. 
  * Add `jest` to explicitly test the parser generator.

- 1.4.5
  * Fix: When submitting a form with a `FileField`, the `UploadedFileInput` widget returns ``None``
    to signalize that nothing changed. Then however, the `clean()`-method did not access the initial
    value of the field. This is fixed now.
  * Fix: Using the value `cleaned_data` from a FormCollection, always started to validate and then
    returned values. Now, one must explicitly call `is_valid()`, otherwise an `AttributeError` is
    raised. 

- 1.4.4
  * Fix: In widget `PhoneNumberInput`, the country lookup field did not behave es expected when
    using the up- or down-arrow keys to navigate through the list of countries.
  * In widget `PhoneNumberInput`, entering "0" into the search field now does not filter the list
    of countries anymore. This is because country codes starting with "00" is not a valid E.164
    format.

- 1.4.3
  * Fix regression in widget `UploadedFileInput` introduced in 1.4: The Delete button did not work
    for files added through the `initial` parameter.
  * Prevent uploading files with an unmatching accept attribute.
  * In widget `PhoneNumberInput`, set focus on country lookup field after opening dropdown box with
    international prefixes.

- 1.4.2
  * Fix: `SlugInput` widget used an invalid `pattern` attribute in its input field.
  * Removed `^…` and `…$` from all `pattern` attributes in all fields using regular expressions.
  * Add delay on `reload()` handler to prevent early firing of restore.

- 1.4.1
  * Fix #136: Submit button shows bummer symbol after okay symbol.
  * Fix #132: The size of the input window does not change as the window size changes.

- 1.4
  * Add support for form dialogs. They can be used standalone or to add complex extensions to the
    Richtext editor.
  * **Breaking change:** `controls.Link()` must be replaced by
    `controls.DialogControl(SimpleLinkDialogForm())`. Check documentation for details.
  * Add control element for footnotes to the Richtext editor.
  * The ternary operator can be used in button actions to distinguish between two possible queues. 
  * The ``require`` attribute of input fields can be made conditional.
  * The ``Selectize`` widget now passes the value to and from the underlying implementation.
  * Activators can be added to ``Form`` and ``FormCollection`` classes. They allow the usage of
    buttons as first class input fields.
  * Add support for Django-5.0.

- 1.3.10
  * Fix #125: IncompleteSelect can't handle collections with siblings.
  * Fix #128: Boolean field shows label twice.
  * In webcomponents, separate constructor from connectedCallback.
  * Fix problem in `Selectize` widget when using `filter_by` with lazy loading.
  * postcss-nested-include@1.3 requires relative paths.
  * Upgrade to `flyctl` version 0.2.28.

- 1.3.9
  * Fix widget `Selectize` losing borders when used in a collection with siblings after a form
    reset.
  * Add support for UTF-8 characters when using the `Selectize` widget with lazy loading.
  * On reset, the number of siblings is set to the initial value.

- 1.3.8
  * Fail silently if package 'phonenumbers' is not installed.
  * Adopt to Django-5.0
  * In RichtextArea, add padding to placeholder field.
  * In DjangoSelectize make background color almost white.

- 1.3.7
  * Disable unique checks for Django<4.0, because they are not compatible.

- 1.3.6
  * Backport to Django-4.0.

- 1.3.5
  * Fix #99: File upload is not compatible with generic Django storage class.

- 1.3.4
  * Fix #97: Forms and FormCollections with disabled fields and initial data, now are validated
    using that initial data.
  * The filter in the widget for the `PhoneNumberField` now is cleared after reopening the selector.

- 1.3.3
  * Fix #96: In `FormCollection` with siblings, the `<form>`'s ID sometimes was not unique.
  * The selector for international prefixes of the `PhoneNumberField`, now offers a search box.
  * Prevent loading styles for `PhoneNumberField` more than once.

- 1.3.2
  * Handle form reset for `PhoneNumberField` properly.
  * Fix: Monolithic build did not include `PhoneNumberField`.
  * Use cached translation in demo project.

- 1.3.1
  * Improved the usability of the `PhoneNumberField`. The user is now forced to select the country
    code from a dropdown list, whenever the phone number does not start with `+`.
  * The dropdown list of the `PhoneNumberField` now shows the countries name in the current
    language.
  
- 1.3
  * New widget: `PhoneNumberField` which can be used to improve the user experience when entering 
    phone numbers.

- 1.2.2
  * Nicer outline and box-shadow, whenever a `DualSelector` element receives input focus. It now
    surrounds the complete field.
  * In the Calendar and DateRange pickers, the cursor changes to a symbol signalizing into which
    direction the second date choice is going to be made.
  * New widgets: `CountrySelectize` and `CountrySelectizeMultiple` which prefix the country name
    with the corresponding flag.

- 1.2.1
  * Fix: Ignore key press events for pure calendar widgets. Since a pure calendar widget can not be
    focused, handling key press events does not make sense.
  * Fix: Calendar cells with attribute `disabled` are not selectable anymore.

- 1.2
  * Add widgets `DatePicker`, `DateTextbox`, `DateCalendar`, `DateTimePicker`, `DateTimeTextbox`
    and `DateTimeCalendar`. They can be used as alternative widgets to Django's `DateInput` and
    `DateTimeInput` widgets.
  * Add range fields `DateRangeField` and `DateTimeRangeField` which can be used in forms to query
    for a date- or datetime range. With these two fields six more widgets are added to the library:
    `DateRangeCalendar`, `DateRangeTextbox`, `DateRangePicker`, `DateTimeRangeCalendar`,
    `DateTimeRangeTextbox` and `DateTimeRangePicker`.
  * The calendar widget now supports 12 hours time format.
  * Fix: In rare occasions, the styling of widgets has been loaded twice.
  * Fix: Field choices declared as callables are now supported.
  * Prepared rendering for Django-5.0.

- 1.1.2
  * Drop support for Django-4.0.

- 1.1.1
  * Fix problems in widgets `Selectize` and `DualSelector` when used with `filter_by`. Selectable
    choices now are always updated using the proper filter values.

- 1.1
  * Form collections containing only empty fields won't be submitted. This applies to collections
    added using `extra_siblings` as to collections added using the appropriate "Add <label>" button.
  * Fix problem when using MultiWidget widgets. Under some configurations an error was raised
    stating “Duplicate name 'xxx' on multiple input fields”.

- 1.0.1
  * Fix: When using the Selectize widgets, using the arrow-up/down buttons did not highlight the
    selected option.
  * Officially support for Django-4.2. 

- 1.0
  * **Breaking change:** Class `FormCollection` is validated entirely and only after all checks
    passed, models are created out of the cleaned data. This means that the method
    `construct_instance` and `model_to_dict` changed their signature. Please read the docs on how to
    use them now.
  * **Breaking change:** In all rendered forms, `<django-field-group>` is replaced against
    `<div role="group">` because self-declared elements shall only be used as web components.
  * **Breaking change:** In all rendered forms groups, `<django-error-messages>` is replaced against
    `<meta name="error-messages">` because self-declared elements shall only be used as web
    components.
  * **Breaking change:** Attribute `click`, which is used to specify action queues in submit
    buttons, has been renamed to `df-click` in order to prevent naming collisions.
  * **Breaking change:** Attributes `show-if`, `hide-if` and `disable-if` which are used to hide or
    disable fields, fieldsets and buttons, have been renamed to `df-show`,  `df-hide` and
    `df-disable` in order to prevent naming collisions.
  * The documentation now is interactive integrating the many working examples.
  * Fix: In `DualSortableSelector` the initial ordering of options, sometimes did not correspond to
    the intermediate's model entries. 
  * Add view class `BulkEditCollectionView` to edit a collection with siblings without any main
    object. Also add method `models_to_list` as a counterpart to `model_to_dict` for list views.
  * Constructor of `FormCollection` additionally accepts `auto_id`. This can be used to set the
    format of the `id` field in form fields.
  * Constructor of `FormCollection` additionally accepts `instance`. This helps to build the models
    out of a collection.
  * Class `FormCollection` performs a unique validating check while performing a `full_clean`.
  * Add a date- and datetime picker rendered by the server using the Python `Calendar` class.
  * Widget ``UploadedFileInput`` accepts `{…, max-size: <bytes>, …}` in its `attrs` to limit the
    uploadable file size.
  * Add control elements for to RichTextarea: `TextAlign`, `TextColor`, `TextIndent`, `TextMargin`,
    `Blockquote`, `Codeblock`, `HardBreak`, `Subscript`, `Superscript`, `Placeholder`.
  * Add check to determine if the same id is used by more than one field inside `<django-formset…>`
    elements on a single page.
  * In `RichtextArea` replace `popper.js` against `floating-ui`.
    

- 0.13.4
  * Fix: On the Javascript console, library TonSelect complained to be initialized already, if more
    than one `Selectize` or `SelectizeMultiple` widget were used.
  * Some valid Python regular expressions were rejected by the Javascript implementation when used
    as pattern in a `RegexField`.
  * When building the project, now one can use the comman line options `--debug` and `--monolith` to
    control how the client code shall be generated.

- 0.13.3
  * Fix initialization problem: Webcomponents loaded through templates in a FormCollection with
    multiple instances were not loaded.
  * Fix problem in client code: Collections with siblings did not aggregate data for submission
    correctly in all circumstances. 

- 0.13.2
  * Add polyfill `@ungap/custom-elements` to fix compatibility issues on Safari.

- 0.13.1
  * Fix broken merge.

- 0.13
  * Add feature to preselect choices in one select field using a value from another field.
  * Remove function `getValue()` from widgets `RichtextArea` and `DjangoSelectize`; use property
    `value` instead.

- 0.12
  * Add feature to work with option groups when using the ``Selectize``, ``SelectizeMultiple``,
    ``DualSelector`` and ``DualSortableSelector`` widget.
  * Fix border shadow after submitting invalid form data.

- 0.11.1
  * In `DjangoButton`'s `reload()` action, add a Boolean argument to optionally ignore query strings.
  * In `DjangoSelectize` fix handling of `line-height: normal` by settings it to value 1.2.
  * In `DjangoSelectize` change `background-color` for mouse over on `<option>` elements.

- 0.11
  * Add widget for Django's [SlugField](https://docs.djangoproject.com/en/latest/ref/forms/fields/#slugfield).
  * Add widget to handle rich text using the [Tiptap](https://tiptap.dev/) editor framework.
  * Load submodules with 3rd party dependencies dynamically. This decreases the initial Javascript
    payload by ~90% compared to a monolithic build.
  * In addition to the [esbuild compiler](https://esbuild.github.io/), add scripts to compile the
    TypeScript code using [rollup](https://rollupjs.org/guide/en/) + [babel](https://babeljs.io/) +
    [terser](https://terser.org/).
  * Web components are initialized on the `DOMContentLoaded` (instead of `load`) Event.
  * Fix: The `Selectize` widget now uses the same border styles for feedback as other input/select
    fields.
  * Fix: Forms which do not provide data are not validated.
  * Add handler to listen for an external `reset` Event.
  * Fix: `FileUpload` widget now loses focus after file submission.
  * Handle input fields for URLs properly.
  * Fix missing feedback on datetime and password fields.
  * Fix: An initialized `FormCollection` with siblings but `max_siblings=None`, raised a TypeError.
  * Fix: Forms now pay attention to form attribute `novalidate`.
  * All `<form>` elements are empty and referred by form=… attribute from their input fields.
  * Add Python utility class `ClassList` which behaves similar to its Javascript counterpart
    `HTMLElement`.
  * Unify the styling of animated icons, such as "Okay", "Bummer" and "Spinner".
  * On HTML placeholders used to display feedback errors, add `role="alert"`.
  * Fix: Uploading more than one file caused the ``UploadWidget`` to complain with "File upload
    still in progress."
  * Add button actions ``confirm()`` and ``alertOnError`` to the possible queue of actions.

- 0.10.3
  * Fix: Widget `DualSortableSelector` now checks bounds for provided values. This in rare occasions
    raised an exception.
  * Both CSS files `collections.css` and `bootstrap5-extra.css` now are compiled from a SCSS source.

- 0.10.2
  * In sortable form collections, add a CSS ghost class to make moved item more opaque. This is for
    a better usability experience.
  * In sortable form collections, change the form name after moving a collection. This fixes a
    problem with form validation.
  * Fix: On forms created from a model, method `IncompleteSelectResponseMixin.fetch_options()`
    raised an AttributeError.
  * Class `FormCollection` and class `Fieldset` accept an optional help text which is rendered at
    the bottom of a `<django-form-collection>` or `<fieldset>`.
  * Some rendering templates remove whitespace using templatetag `{% spaceless %}`.
  * Django-4.1 now is officially supported.

- 0.10.1
  * The HTML tags for `<select is="django-selectize">` and `<select is="django-dual-selector">`
    declare their own webcomponents which now add their own HTML elements in front of themselves,
    before hiding. Instead of hiding via `display: none;` they now "conceal" so that the browser
    can set focus on input fields not validating.
  * Replace `uglify` against `terser` to minify JavaScript files.
  * In webcomponent `<select is="django-dual-selector">`, replace `elem.getValue()` against
    `elem.value`.
  * Simplify the way events handlers are called.
  * Remove the CSRF-Token from the request header of webcomponents `<select is="django-selectize">`
    and `<select is="django-dual-selector">`, since they exclusively use GET requests.
  * The right selector box of the webcomponent `<select is="django-dual-selector" required …>`
    highlights as invalid (by rendering a red border), if input data is missing.

- 0.10
  * The right part of the widget `DualSelector` optionally is sortable now. Views accepting forms
    with this widget can rely upon that sorting order and store it.
  * Form collections with siblings can optionally be declared as sortable. A drag handle is then
    rendered above the collection, which can be used for sorting.
  * Add Germans translations text readable by the end user.

- 0.9.1
  * The optional URL parameter passed into button action `proceed(...)` now takes precedence over
    the `success_url` returned inside the response object.
  * Allow wrapping HTML elements between a `<django-formset>` and its immediate
    `<django-form-collection>`-elements.
  * Add German translations.

- 0.9
  * Fixed problems when resetting a formset containing multiple collections with siblings: All just
    added collections are removed on reset.
  * Distinguish while removing a collection: A just added collection is removed, while existing
    collections are marked for removal.
  * On cleaning post data while processing collections, one can choose whether to keep existig but
    removed colections for further processing, or ignore them.
  * Allow extra label to be added inside the "Add collection" button.
  * Handle CSRF token via attribute to `<django-formset csrf-token="…">` rather than using a cookie.
  * Fix typo: Rename  `IncompleSelectResponseMixin` -> `IncompleteSelectResponseMixin`.
  * Fix some issues with `FormCollection`-s: Invoking `replicate` now creates a deep copy of all
    children.
  * Fix in widget `FileInput`: On reloading the form, the provided value is kept to its initial
    state.

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
