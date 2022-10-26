import { DjangoFormsetElement } from "./django-formset/DjangoFormset";
import { StyleHelpers } from './django-formset/helpers';

window.addEventListener('load', (event) => {
	const pseudoStylesElement = StyleHelpers.convertPseudoClasses();
	const promises = Array<Promise<any>>();
	if (document.querySelector('select[is="django-selectize"]')) {
		const promise = import('./django-formset/DjangoSelectize');
		promises.push(promise);
		promise.then(({DjangoSelectizeElement}) => {
			window.customElements.define('django-selectize', DjangoSelectizeElement, {extends: 'select'});
		});
	}
	if (document.querySelector('django-sortable-select')) {
		const promise = import('./django-formset/SortableSelect');
		promises.push(promise);
		promise.then(({ SortableSelectElement }) => {
			window.customElements.define('django-sortable-select', SortableSelectElement);
		});
	}
	if (document.querySelector('select[is="django-dual-selector"]')) {
		const promise = import('./django-formset/DualSelector');
		promises.push(promise);
		promise.then(({ DualSelectorElement }) => {
			window.customElements.define('django-dual-selector', DualSelectorElement, {extends: 'select'});
		});
	}
	if (document.querySelector('textarea[is="django-richtext"]')) {
		const promise = import('./django-formset/RichtextArea');
		promises.push(promise);
		promise.then(({ RichTextAreaElement }) => {
	 		window.customElements.define('django-richtext', RichTextAreaElement, {extends: 'textarea'});
		});
	}
	if (document.querySelector('input[is="django-slug"]')) {
		const promise = import('./django-formset/DjangoSlug');
		promises.push(promise);
		promise.then(({ DjangoSlugElement }) => {
	 		window.customElements.define('django-richtext', DjangoSlugElement, {extends: 'input'});
		});
	}
	Promise.all(promises).then(() => {
		window.customElements.define('django-formset', DjangoFormsetElement);
		pseudoStylesElement.remove();
	});
});
