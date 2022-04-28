import Sortable, { MultiDrag, SortableEvent } from 'sortablejs';
import styles from 'sass:./SortableSelect.scss';

Sortable.mount(new MultiDrag());


export class SortableSelectElement extends HTMLElement {
	private constructor() {
		super();
		const style = document.createElement('style');
		style.innerText = styles;
		document.head.appendChild(style)
	}

	private connectedCallback() {
		console.log('connected django-sortable-select');
	}

	public transferStyles(selectElement: HTMLSelectElement) {
		const nativeStyles = window.getComputedStyle(selectElement);
		console.log(nativeStyles);
		//for (let k = 0; k < nativeStyles.length; ++k) {
		//	const key = nativeStyles.item(k);
		//	this.style.setProperty(key, nativeStyles.getPropertyValue(key));
		//}
		this.style.setProperty('height', nativeStyles.getPropertyValue('height'));
		const optionElement = selectElement.querySelector('option');
		if (optionElement) {
		}
	}

	public add(option: HTMLOptionElement) {
		console.log('add option');
		this.appendChild(option);
	}
}
