## Changes

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
