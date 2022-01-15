import styles from 'sass:./django-formset/DjangoFormset.scss';
import { DjangoFormsetElement } from "./django-formset/DjangoFormset";
import { DjangoSelectizeElement } from "./django-formset/DjangoSelectize";
import { DualSelectorElement } from "./django-formset/DualSelector";

const style = document.createElement('style');
style.innerText = styles;
document.head.appendChild(style)
window.customElements.define('django-formset', DjangoFormsetElement);
window.addEventListener('load', (event) => {
	window.customElements.define('django-selectize', DjangoSelectizeElement, {extends: 'select'});
	window.customElements.define('django-dual-selector', DualSelectorElement, {extends: 'select'})
});
