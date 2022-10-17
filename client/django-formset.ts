import { DjangoFormsetElement } from "./django-formset/DjangoFormset";
import { StyleHelpers } from './django-formset/helpers';

window.addEventListener('load', (event) => {
	const pseudoStylesElement = StyleHelpers.convertPseudoClasses();
	const promises = Array<Promise<any>>();
	if (document.querySelector('select[is="django-selectize"]')) {
		const promise = import('./django-formset/DjangoSelectize');
		promise.then(({DjangoSelectizeElement}) => {
			window.customElements.define('django-selectize', DjangoSelectizeElement, {extends: 'select'});
		});
		promises.push(promise);
	}
	if (document.querySelector('django-sortable-select')) {
		const promise = import('./django-formset/SortableSelect');
		promise.then(({ SortableSelectElement }) => {
			window.customElements.define('django-sortable-select', SortableSelectElement);
		});
		promises.push(promise);
	}
	if (document.querySelector('select[is="django-dual-selector"]')) {
		const promise = import('./django-formset/DualSelector');
		promise.then(({ DualSelectorElement }) => {
			window.customElements.define('django-dual-selector', DualSelectorElement, {extends: 'select'});
		});
		promises.push(promise);
	}
	if (document.querySelector('textarea[is="django-richtext"]')) {
		const promise = import('./django-formset/RichTextArea');
		promise.then(({ RichTextAreaElement }) => {
	 		window.customElements.define('django-richtext', RichTextAreaElement, {extends: 'textarea'});
		});
		promises.push(promise);
	}
	Promise.all(promises).then(() => {
		window.customElements.define('django-formset', DjangoFormsetElement);
		pseudoStylesElement.remove();
	});
});
