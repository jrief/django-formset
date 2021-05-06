import styles from 'sass:./django-formset/DjangoFormset.scss';
import {DjangoFormset} from "./django-formset/DjangoFormset";

const style = document.createElement('style');
style.innerText = styles;
document.head.appendChild(style)
window.customElements.define('django-formset', DjangoFormset);
