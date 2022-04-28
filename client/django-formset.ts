import { DjangoFormsetElement } from "./django-formset/DjangoFormset";
import { DjangoSelectizeElement } from "./django-formset/DjangoSelectize";
import { DualSelectorElement } from "./django-formset/DualSelector";

window.addEventListener('load', (event) => {
	window.customElements.define('django-formset', DjangoFormsetElement);
	window.customElements.define('django-selectize', DjangoSelectizeElement, {extends: 'select'});
	window.customElements.define('django-dual-selector', DualSelectorElement, {extends: 'select'})
});
