import '@ungap/custom-elements';
import {DjangoFormsetElement} from './django-formset/DjangoFormset';
import {StyleHelpers} from './django-formset/helpers';

// remember to always reflect imports below here also in django-formset.ts
import {DjangoSelectizeElement} from './django-formset/DjangoSelectize';
import {CountrySelectizeElement} from './django-formset/CountrySelectize';
import {SortableSelectElement} from './django-formset/SortableSelect';
import {DualSelectorElement} from './django-formset/DualSelector';
import {RichTextAreaElement} from './django-formset/RichtextArea';
import {DjangoSlugElement} from './django-formset/DjangoSlug';
import {DateFieldElement, DatePickerElement, DateTimeFieldElement, DateTimePickerElement} from './django-formset/DateTime';


window.addEventListener('DOMContentLoaded', (event) => {
	const pseudoStylesElement = StyleHelpers.convertPseudoClasses();
	const customElementNames = Array<string>();

	window.customElements.define('django-selectize', DjangoSelectizeElement, {extends: 'select'});
	customElementNames.push('django-selectize');
	window.customElements.define('django-country-selectize', CountrySelectizeElement, {extends: 'select'});
	customElementNames.push('django-country-selectize');
	window.customElements.define('django-sortable-select', SortableSelectElement);
	customElementNames.push('django-sortable-select');
	window.customElements.define('django-dual-selector', DualSelectorElement, {extends: 'select'});
	customElementNames.push('django-dual-selector');
	window.customElements.define('django-phone-number', DualSelectorElement, {extends: 'input'});
	customElementNames.push('django-phone-number');
	window.customElements.define('django-richtext', RichTextAreaElement, {extends: 'textarea'});
	customElementNames.push('django-richtext');
	window.customElements.define('django-slug', DjangoSlugElement, {extends: 'input'});
	customElementNames.push('django-slug');
	window.customElements.define('django-datefield', DateFieldElement, {extends: 'input'});
	customElementNames.push('django-datefield');
	window.customElements.define('django-datecalendar', DateFieldElement, {extends: 'input'});
	customElementNames.push('django-datecalendar');
	window.customElements.define('django-datepicker', DatePickerElement, {extends: 'input'});
	customElementNames.push('django-datepicker');
	window.customElements.define('django-datetimefield', DateTimeFieldElement, {extends: 'input'});
	customElementNames.push('django-datetimefield');
	window.customElements.define('django-datetimecalendar', DateFieldElement, {extends: 'input'});
	customElementNames.push('django-datetimecalendar');
	window.customElements.define('django-datetimepicker', DateTimePickerElement, {extends: 'input'});
	customElementNames.push('django-datetimepicker');
	window.customElements.define('django-daterangefield', DateTimePickerElement, {extends: 'input'});
	customElementNames.push('django-daterangefield');
	window.customElements.define('django-daterangecalendar', DateTimePickerElement, {extends: 'input'});
	customElementNames.push('django-daterangecalendar');
	window.customElements.define('django-daterangepicker', DateTimePickerElement, {extends: 'input'});
	customElementNames.push('django-daterangepicker');
	window.customElements.define('django-datetimerangefield', DateTimePickerElement, {extends: 'input'});
	customElementNames.push('django-datetimerangefield');
	window.customElements.define('django-datetimerangecalendar', DateTimePickerElement, {extends: 'input'});
	customElementNames.push('django-datetimerangecalendar');
	window.customElements.define('django-datetimerangepicker', DateTimePickerElement, {extends: 'input'});
	customElementNames.push('django-datetimerangepicker');

	const foundIds = new Set<string>();
	document.querySelectorAll('django-formset [id]').forEach(element => {
		const foundId = element.getAttribute('id')!;
		if (foundIds.has(foundId))
			throw new Error(`There are at least two elements with attribute id="${foundId}"`);
		foundIds.add(foundId);
	});

	const promises = customElementNames.map(name => window.customElements.whenDefined(name));
	Promise.all(promises).then(() => {
		window.customElements.define('django-formset', DjangoFormsetElement);
		window.customElements.whenDefined('django-formset').then(() => {
			pseudoStylesElement.remove();
		});
	}).catch(error => console.error(`Failed to initialize django-formset: ${error}`));
});
