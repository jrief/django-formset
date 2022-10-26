import { DjangoFormsetElement } from "./django-formset/DjangoFormset";
import { StyleHelpers } from './django-formset/helpers';

window.addEventListener('load', (event) => {
	const pseudoStylesElement = StyleHelpers.convertPseudoClasses();
	const promises = Array<Promise<void>>();
	if (document.querySelector('select[is="django-selectize"]')) {
		promises.push(new Promise((resolve, reject) => {
			import('./django-formset/DjangoSelectize').then(({DjangoSelectizeElement}) => {
				window.customElements.define('django-selectize', DjangoSelectizeElement, {extends: 'select'});
				resolve();
			}).catch(() => reject());
		}));
	}
	if (document.querySelector('django-sortable-select')) {
		promises.push(new Promise((resolve, reject) => {
			import('./django-formset/SortableSelect').then(({ SortableSelectElement }) => {
				window.customElements.define('django-sortable-select', SortableSelectElement);
				resolve();
			}).catch(() => reject());
		}));
	}
	if (document.querySelector('select[is="django-dual-selector"]')) {
		promises.push(new Promise((resolve, reject) => {
			import('./django-formset/DualSelector').then(({ DualSelectorElement }) => {
				window.customElements.define('django-dual-selector', DualSelectorElement, {extends: 'select'});
				resolve();
			}).catch(() => reject());
		}));
	}
	if (document.querySelector('textarea[is="django-richtext"]')) {
		promises.push(new Promise((resolve, reject) => {
			import('./django-formset/RichtextArea').then(({ RichTextAreaElement }) => {
				window.customElements.define('django-richtext', RichTextAreaElement, {extends: 'textarea'});
				resolve();
			}).catch(() => reject());
		}));
	}
	if (document.querySelector('input[is="django-slug"]')) {
		promises.push(new Promise((resolve, reject) => {
			import('./django-formset/DjangoSlug').then(({ DjangoSlugElement }) => {
		 		window.customElements.define('django-richtext', DjangoSlugElement, {extends: 'input'});
				resolve();
			}).catch(() => reject());
		}));
	}
	Promise.all(promises).then(() => {
		window.customElements.define('django-formset', DjangoFormsetElement);
		pseudoStylesElement.remove();
	}).catch(() => console.error("Failed to initialize django-formset"));
});
