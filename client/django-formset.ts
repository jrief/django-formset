import '@ungap/custom-elements';
import { DjangoFormsetElement } from "./django-formset/DjangoFormset";
import { StyleHelpers } from './django-formset/helpers';
import { DatePickerElement } from "./django-formset/DatePicker";


window.addEventListener('DOMContentLoaded', (event) => {
	const pseudoStylesElement = StyleHelpers.convertPseudoClasses();
	const promises = Array<Promise<void>>();
	if (document.querySelector('select[is="django-selectize"]')) {
		promises.push(new Promise((resolve, reject) => {
			import('./django-formset/DjangoSelectize').then(({DjangoSelectizeElement}) => {
				window.customElements.define('django-selectize', DjangoSelectizeElement, {extends: 'select'});
				window.customElements.whenDefined('django-selectize').then(() => resolve());
			}).catch(err => reject(err));
		}));
	}
	if (document.querySelector('django-sortable-select')) {
		promises.push(new Promise((resolve, reject) => {
			import('./django-formset/SortableSelect').then(({SortableSelectElement}) => {
				window.customElements.define('django-sortable-select', SortableSelectElement);
				import('./django-formset/DualSelector').then(({DualSelectorElement}) => {
					window.customElements.define('django-dual-selector', DualSelectorElement, {extends: 'select'});
					Promise.all([
						window.customElements.whenDefined('django-sortable-select'),
						window.customElements.whenDefined('django-dual-selector'),
					]).then(() => resolve());
				}).catch(err => reject(err));
			}).catch(err => reject(err));
		}));
	} else if (document.querySelector('select[is="django-dual-selector"]')) {
		promises.push(new Promise((resolve, reject) => {
			import('./django-formset/DualSelector').then(({ DualSelectorElement }) => {
				window.customElements.define('django-dual-selector', DualSelectorElement, {extends: 'select'});
				window.customElements.whenDefined('django-dual-selector').then(() => resolve());
			}).catch(err => reject(err));
		}));
	}
	if (document.querySelector('textarea[is="django-richtext"]')) {
		promises.push(new Promise((resolve, reject) => {
			import('./django-formset/RichtextArea').then(({ RichTextAreaElement }) => {
				window.customElements.define('django-richtext', RichTextAreaElement, {extends: 'textarea'});
				window.customElements.whenDefined('django-richtext').then(() => resolve());
			}).catch(err => reject(err));
		}));
	}
	if (document.querySelector('input[is="django-slug"]')) {
		promises.push(new Promise((resolve, reject) => {
			import('./django-formset/DjangoSlug').then(({ DjangoSlugElement }) => {
		 		window.customElements.define('django-slug', DjangoSlugElement, {extends: 'input'});
				window.customElements.whenDefined('django-slug').then(() => resolve());
			}).catch(err => reject(err));
		}));
	}
	if (document.querySelector('input[is="django-datepicker"]')) {
		promises.push(new Promise((resolve, reject) => {
			import('./django-formset/DatePicker').then(({ DatePickerElement }) => {
		 		window.customElements.define('django-datepicker', DatePickerElement, {extends: 'input'});
				window.customElements.whenDefined('django-datepicker').then(() => resolve());
			}).catch(err => reject(err));
		}));
	}
	Promise.all(promises).then(() => {
		window.customElements.define('django-formset', DjangoFormsetElement);
		pseudoStylesElement.remove();
	}).catch(error => console.error(`Failed to initialize django-formset: ${error}`));
});
