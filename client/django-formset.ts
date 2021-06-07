import styles from 'sass:./django-formset/DjangoFormset.scss';
import { DjangoFormsetElement } from "./django-formset/DjangoFormset";
import { DjangoSelectizeElement } from "./django-formset/DjangoSelectize";

const style = document.createElement('style');
style.innerText = styles;
document.head.appendChild(style)
window.customElements.define('django-formset', DjangoFormsetElement);
window.customElements.define('django-selectize', DjangoSelectizeElement, {extends: 'select'});
