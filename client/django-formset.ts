import '@ungap/custom-elements';
import {DjangoFormsetElement} from 'django-formset/DjangoFormset';
import {StyleHelpers} from 'django-formset/helpers';


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

	function domLookup(fragmentRoot: Document|DocumentFragment) {
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
		if (fragmentRoot.querySelector('django-sortable-select')) {
			promises.push(new Promise((resolve, reject) => {
				import('django-formset/SortableSelect').then(({SortableSelectElement}) => {
					if (customElements.get('django-sortable-select') instanceof Function) {
						resolve();
					} else {
						window.customElements.define('django-sortable-select', SortableSelectElement);
					}
					import('django-formset/DualSelector').then(({DualSelectorElement}) => {
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
				import('django-formset/DualSelector').then(({DualSelectorElement}) => {
					defineComponent(resolve, 'django-dual-selector', DualSelectorElement, {extends: 'select'});
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
		const textareaElements = fragmentRoot.querySelectorAll('textarea[is="django-richtext"]');
		textareaElements.forEach(textareaElement => {
			promises.push(new Promise((resolve, reject) => {
				const resolveWhenConnected = () => {
					// RichtextArea connects asynchronously, so we need to wait until it is connected to the DOM
					if ((textareaElement as any).isInitialized) {
						// <textarea is="django-richtext"> is already connected and initialized
						resolve();
					} else {
						// <textarea is="django-richtext"> is waiting to be connected and initialized
						textareaElement.addEventListener('connected', () => resolve(), {once: true});
					}
				};

				import('django-formset/RichtextArea').then(({RichTextAreaElement}) => {
					if (customElements.get('django-richtext') instanceof Function) {
						resolveWhenConnected();
					} else {
						window.customElements.define('django-richtext', RichTextAreaElement, {extends: 'textarea'});
						window.customElements.whenDefined('django-richtext').then(resolveWhenConnected);
					}
				}).catch(err => reject(err));
			}));
		});
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
