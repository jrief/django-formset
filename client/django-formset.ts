import '@ungap/custom-elements';
import {DjangoFormsetElement} from 'django-formset/DjangoFormset';
import {StyleHelpers} from 'django-formset/helpers';


window.addEventListener('DOMContentLoaded', (event) => {
	const pseudoStylesElement = StyleHelpers.convertPseudoClasses();
	const promises = Array<Promise<void>>();

	function defineComponent(resolve: Function, selector: string, newComponent: CustomElementConstructor, options: ElementDefinitionOptions|undefined=undefined) {
		window.customElements.whenDefined(selector).then(() => resolve());
		if (!(window.customElements.get(selector) instanceof Function)) {
			window.customElements.define(selector, newComponent, options);
		}
	}

	function domLookup(fragmentRoot: Document|DocumentFragment, isTemplate: boolean=false) {
		// remember to always reflect imports below here also in django-formset.monolith.ts
		if (fragmentRoot.querySelector('select[is="django-selectize"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('django-formset/DjangoSelectize').then(({DjangoSelectizeElement}) => {
					defineComponent(resolve, 'django-selectize', DjangoSelectizeElement, {extends: 'select'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('select[is="django-country-selectize"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('django-formset/CountrySelectize').then(({CountrySelectizeElement}) => {
					defineComponent(resolve, 'django-country-selectize', CountrySelectizeElement, {extends: 'select'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('select[is="django-dual-selector"], django-sortable-select')) {
			promises.push(new Promise((resolve, reject) => {
				import('django-formset/DualSelector').then(({DualSelectorElement, SortableSelectElement}) => {
					Promise.all([
						window.customElements.whenDefined('django-sortable-select'),
						window.customElements.whenDefined('django-dual-selector'),
					]).then(() => resolve());
					if (!(window.customElements.get('django-sortable-select') instanceof Function)) {
						window.customElements.define('django-sortable-select', SortableSelectElement);
					}
					if (!(window.customElements.get('django-dual-selector') instanceof Function)) {
						window.customElements.define('django-dual-selector', DualSelectorElement, {extends: 'select'});
					}
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-phone-number"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('django-formset/PhoneNumber').then(({PhoneNumberElement}) => {
					defineComponent(resolve, 'django-phone-number', PhoneNumberElement, {extends: 'input'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('textarea[is="django-richtext"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('django-formset/RichtextArea').then(({RichTextAreaElement}) => {
					const textareaElements = fragmentRoot.querySelectorAll('textarea[is="django-richtext"]');
					window.customElements.whenDefined('django-richtext').then(() => {
						Promise.all(Array.from(textareaElements).map(textareaElement => new Promise<void>(resolve => {
							if (isTemplate || (textareaElement as any).isInitialized) {
								resolve();
							} else {
								textareaElement.addEventListener('connected', () => resolve(), {once: true});
							}
						}))).then(() => resolve());
					}).then(() => resolve());
					if (!(window.customElements.get('django-richtext') instanceof Function)) {
						window.customElements.define('django-richtext', RichTextAreaElement, {extends: 'textarea'});
					}
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-slug"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('django-formset/DjangoSlug').then(({DjangoSlugElement}) => {
					defineComponent(resolve, 'django-slug', DjangoSlugElement, {extends: 'input'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-datefield"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('django-formset/DateTime').then(({DateFieldElement}) => {
					defineComponent(resolve, 'django-datefield', DateFieldElement, {extends: 'input'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-datecalendar"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('django-formset/Calendar').then(({DateCalendarElement}) => {
					defineComponent(resolve, 'django-datecalendar', DateCalendarElement, {extends: 'input'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-datepicker"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('django-formset/DateTime').then(({DatePickerElement}) => {
					defineComponent(resolve, 'django-datepicker', DatePickerElement, {extends: 'input'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-datetimefield"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('django-formset/DateTime').then(({DateTimeFieldElement}) => {
					defineComponent(resolve, 'django-datetimefield', DateTimeFieldElement, {extends: 'input'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-datetimecalendar"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('django-formset/Calendar').then(({DateTimeCalendarElement}) => {
					defineComponent(resolve, 'django-datetimecalendar', DateTimeCalendarElement, {extends: 'input'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-datetimepicker"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('django-formset/DateTime').then(({DateTimePickerElement}) => {
					defineComponent(resolve, 'django-datetimepicker', DateTimePickerElement, {extends: 'input'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-daterangefield"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('django-formset/DateTime').then(({DateRangeFieldElement}) => {
					defineComponent(resolve, 'django-daterangefield', DateRangeFieldElement, {extends: 'input'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-daterangecalendar"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('django-formset/Calendar').then(({DateRangeCalendarElement}) => {
					defineComponent(resolve, 'django-daterangecalendar', DateRangeCalendarElement, {extends: 'input'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-daterangepicker"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('django-formset/DateTime').then(({DateRangePickerElement}) => {
					defineComponent(resolve, 'django-daterangepicker', DateRangePickerElement, {extends: 'input'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-datetimerangefield"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('django-formset/DateTime').then(({DateTimeRangeFieldElement}) => {
					defineComponent(resolve, 'django-datetimerangefield', DateTimeRangeFieldElement, {extends: 'input'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-datetimerangecalendar"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('django-formset/Calendar').then(({DateTimeRangeCalendarElement}) => {
					defineComponent(resolve, 'django-datetimerangecalendar', DateTimeRangeCalendarElement, {extends: 'input'});
				}).catch(err => reject(err));
			}));
		}
		if (fragmentRoot.querySelector('input[is="django-datetimerangepicker"]')) {
			promises.push(new Promise((resolve, reject) => {
				import('django-formset/DateTime').then(({DateTimeRangePickerElement}) => {
					defineComponent(resolve, 'django-datetimerangepicker', DateTimeRangePickerElement, {extends: 'input'});
				}).catch(err => reject(err));
			}));
		}
	}

	document.querySelectorAll('template.empty-collection').forEach(element => {
		if (element instanceof HTMLTemplateElement && element.content instanceof DocumentFragment) {
			domLookup(element.content, true);
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
