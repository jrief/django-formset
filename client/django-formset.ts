import { DjangoFormsetElement } from "./django-formset/DjangoFormset";
import { DjangoSelectizeElement } from "./django-formset/DjangoSelectize";
import { DualSelectorElement } from "./django-formset/DualSelector";
import { SortableSelectElement } from "./django-formset/SortableSelect";
import { StyleHelpers } from './django-formset/helpers';

window.addEventListener('load', (event) => {
	const pseudoStylesElement = StyleHelpers.convertPseudoClasses();
	window.customElements.define('django-selectize', DjangoSelectizeElement, {extends: 'select'});
	window.customElements.define('django-sortable-select', SortableSelectElement);
	window.customElements.define('django-dual-selector', DualSelectorElement, {extends: 'select'});
	window.customElements.define('django-formset', DjangoFormsetElement);
	pseudoStylesElement.remove();
});
