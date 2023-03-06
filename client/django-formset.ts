import '@ungap/custom-elements';
import { DjangoFormsetElement } from "./django-formset/DjangoFormset";
import { StyleHelpers } from './django-formset/helpers';


window.addEventListener('DOMContentLoaded', (event) => {
	const pseudoStylesElement = StyleHelpers.convertPseudoClasses();
	const promises = Array<Promise<void>>();

	function domLookup(fragmentRoot: Document | DocumentFragment) {
		if (fragmentRoot.querySelector('select[is="django-selectize"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('./django-formset/DjangoSelectize').then(({DjangoSelectizeElement}) => {
					if (customElements.get('django-selectize') instanceof Function) {
						resolve();
					} else {
						window.customElements.define('django-selectize', DjangoSelectizeElement, {extends: 'select'});
						window.customElements.whenDefined('django-selectize').then(() => resolve());
					}
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('django-sortable-select')) {
			promises.push(new Promise((resolve, reject) => {
				import('./django-formset/SortableSelect').then(({SortableSelectElement}) => {
					if (customElements.get('django-sortable-select') instanceof Function) {
						resolve();
					} else {
						window.customElements.define('django-sortable-select', SortableSelectElement);
					}
					import('./django-formset/DualSelector').then(({DualSelectorElement}) => {
						if (customElements.get('django-dual-selector') instanceof Function) {
							resolve();
						} else {
							window.customElements.define('django-dual-selector', DualSelectorElement, {extends: 'select'});
							Promise.all([
								window.customElements.whenDefined('django-sortable-select'),
								window.customElements.whenDefined('django-dual-selector'),
							]).then(() => resolve());
						}
					}).catch(err => reject(err));
				}).catch(err => reject(err));
			}));
		} else if (fragmentRoot.querySelector('select[is="django-dual-selector"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('./django-formset/DualSelector').then(({DualSelectorElement}) => {
					if (customElements.get('django-dual-selector') instanceof Function) {
						resolve();
					} else {
						window.customElements.define('django-dual-selector', DualSelectorElement, {extends: 'select'});
						window.customElements.whenDefined('django-dual-selector').then(() => resolve());
					}
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('textarea[is="django-richtext"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('./django-formset/RichtextArea').then(({RichTextAreaElement}) => {
					if (customElements.get('django-richtext') instanceof Function) {
						resolve();
					} else {
						window.customElements.define('django-richtext', RichTextAreaElement, {extends: 'textarea'});
						window.customElements.whenDefined('django-richtext').then(() => resolve());
					}
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-slug"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('./django-formset/DjangoSlug').then(({DjangoSlugElement}) => {
					if (customElements.get('django-slug') instanceof Function) {
						resolve();
					} else {
						window.customElements.define('django-slug', DjangoSlugElement, {extends: 'input'});
						window.customElements.whenDefined('django-slug').then(() => resolve());
					}
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-datepicker"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('./django-formset/DateTimePicker').then(({ DatePickerElement }) => {
					if (customElements.get('django-datepicker') instanceof Function) {
						resolve();
					} else {
						window.customElements.define('django-datepicker', DatePickerElement, {extends: 'input'});
						window.customElements.whenDefined('django-datepicker').then(() => resolve());
					}
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-datetimepicker"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('./django-formset/DateTimePicker').then(({ DateTimePickerElement }) => {
					if (customElements.get('django-datetimepicker') instanceof Function) {
						resolve();
					} else {
						window.customElements.define('django-datetimepicker', DateTimePickerElement, {extends: 'input'});
						window.customElements.whenDefined('django-datetimepicker').then(() => resolve());
					}
				}).catch(err => reject(err));
			}));
		}

	}

	document.querySelectorAll('template.empty-collection').forEach(element => {
		if (element instanceof HTMLTemplateElement && element.content instanceof DocumentFragment) {
			domLookup(element.content);
		}
	});
	domLookup(document);

	Promise.all(promises).then(() => {
		window.customElements.define('django-formset', DjangoFormsetElement);
		pseudoStylesElement.remove();
	}).catch(error => console.error(`Failed to initialize django-formset: ${error}`));
});
