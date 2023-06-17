import '@ungap/custom-elements';
import {DjangoFormsetElement} from './django-formset/DjangoFormset';
import {StyleHelpers} from './django-formset/helpers';

// remember to always reflect imports below here also in django-formset.ts
import {DjangoSelectizeElement} from './django-formset/DjangoSelectize';
import {SortableSelectElement} from './django-formset/SortableSelect';
import {DualSelectorElement} from "./django-formset/DualSelector";
import {RichTextAreaElement} from "./django-formset/RichtextArea";
import {DjangoSlugElement} from "./django-formset/DjangoSlug";
import {DatePickerElement, DateTimePickerElement} from "./django-formset/DateTimePicker";


window.addEventListener('DOMContentLoaded', (event) => {
	const pseudoStylesElement = StyleHelpers.convertPseudoClasses();
	const customElementNames = Array<string>();

	window.customElements.define('django-selectize', DjangoSelectizeElement, {extends: 'select'});
	customElementNames.push('django-selectize');
	window.customElements.define('django-sortable-select', SortableSelectElement);
	customElementNames.push('django-sortable-select');
	window.customElements.define('django-dual-selector', DualSelectorElement, {extends: 'select'});
	customElementNames.push('django-dual-selector');
	window.customElements.define('django-richtext', RichTextAreaElement, {extends: 'textarea'});
	customElementNames.push('django-richtext');
	window.customElements.define('django-slug', DjangoSlugElement, {extends: 'input'});
	customElementNames.push('django-slug');
	window.customElements.define('django-datepicker', DatePickerElement, {extends: 'input'});
	customElementNames.push('django-datepicker');
	window.customElements.define('django-datetimepicker', DateTimePickerElement, {extends: 'input'});
	customElementNames.push('django-datetimepicker');

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
