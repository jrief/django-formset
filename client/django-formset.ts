import '@ungap/custom-elements';
import { DjangoFormsetElement } from "./django-formset/DjangoFormset";
import { StyleHelpers } from './django-formset/helpers';


window.addEventListener('DOMContentLoaded', (event) => {
	const pseudoStylesElement = StyleHelpers.convertPseudoClasses();
	const promises = Array<Promise<void>>();

	function defineComponent(resolve: Function, selector: string, newComponent: CustomElementConstructor, options: ElementDefinitionOptions|undefined=undefined) {
		if (customElements.get(selector) instanceof Function) {
			resolve();
		} else {
			window.customElements.define(selector, newComponent, options);
			window.customElements.whenDefined(selector).then(() => resolve());
		}
	}

	function domLookup(fragmentRoot: Document | DocumentFragment) {
		// remember to always reflect imports below here also in django-formset.monolith.ts
		if (fragmentRoot.querySelector('select[is="django-selectize"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('./django-formset/DjangoSelectize').then(({DjangoSelectizeElement}) => {
					defineComponent(resolve, 'django-selectize', DjangoSelectizeElement, {extends: 'select'});
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
					defineComponent(resolve, 'django-dual-selector', DualSelectorElement, {extends: 'select'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('textarea[is="django-richtext"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('./django-formset/RichtextArea').then(({RichTextAreaElement}) => {
					defineComponent(resolve, 'django-richtext', RichTextAreaElement, {extends: 'textarea'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-slug"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('./django-formset/DjangoSlug').then(({DjangoSlugElement}) => {
					defineComponent(resolve, 'django-slug', DjangoSlugElement, {extends: 'input'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-datefield"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('./django-formset/DateTime').then(({DateFieldElement}) => {
					defineComponent(resolve, 'django-datefield', DateFieldElement, {extends: 'input'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-datepicker"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('./django-formset/DateTime').then(({DatePickerElement}) => {
					defineComponent(resolve, 'django-datepicker', DatePickerElement, {extends: 'input'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-datetimefield"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('./django-formset/DateTime').then(({DateTimeFieldElement}) => {
					defineComponent(resolve, 'django-datetimefield', DateTimeFieldElement, {extends: 'input'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-datetimepicker"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('./django-formset/DateTime').then(({DateTimePickerElement}) => {
					defineComponent(resolve, 'django-datetimepicker', DateTimePickerElement, {extends: 'input'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-daterangepicker"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('./django-formset/DateTime').then(({DateRangePickerElement}) => {
					defineComponent(resolve, 'django-daterangepicker', DateRangePickerElement, {extends: 'input'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-datetimerangepicker"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('./django-formset/DateTime').then(({DateTimeRangePickerElement}) => {
					defineComponent(resolve, 'django-datetimerangepicker', DateTimeRangePickerElement, {extends: 'input'});
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

	const foundIds = new Set<string>();
	document.querySelectorAll('django-formset [id]').forEach(element => {
		const foundId = element.getAttribute('id')!;
		if (foundIds.has(foundId))
			throw new Error(`There are at least two elements with attribute id="${foundId}"`);
		foundIds.add(foundId);
	});

	Promise.all(promises).then(() => {
		window.customElements.define('django-formset', DjangoFormsetElement);
		window.customElements.whenDefined('django-formset').then(() => {
			pseudoStylesElement.remove();
		});
	}).catch(error => console.error(`Failed to initialize django-formset: ${error}`));
});
