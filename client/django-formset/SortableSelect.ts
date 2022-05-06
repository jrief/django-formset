import Sortable, { MultiDrag, SortableEvent } from 'sortablejs';
import styles from 'sass:./SortableSelect.scss';

Sortable.mount(new MultiDrag());


export class SortableSelectElement extends HTMLElement {
	private readonly sortable: Sortable;
	private lastSelected: HTMLOptionElement | null = null;

	private constructor() {
		super();
		const style = document.createElement('style');
		style.innerText = styles;
		document.head.appendChild(style)
		this.sortable = Sortable.create(this, {
			animation: 150,
			fallbackOnBody: true,
			multiDrag: true,
			onEnd: event => this.onEnd(event),
		});

		this.addEventListener('click', event => this.optionSelected(event));
		window.addEventListener('click', event => this.elementFocus(event));
	}

	private onEnd(event: SortableEvent) {
		this.deselectAllOptions();
		const sortedEvent = new Event('options-sorted', {
			bubbles: true,
			cancelable: true,
			composed: false
		});
		this.dispatchEvent(sortedEvent);
	}

	private elementFocus(event: Event) {
		if (event.target instanceof HTMLElement && this.contains(event.target)) {
			this.classList.add('has-focus');
		} else {
			this.classList.remove('has-focus');
		}
	}

	private optionSelected(event: Event) {
		if (!(event.target instanceof HTMLOptionElement))
			return;
		const selectedOption = event.target;
		if (event instanceof PointerEvent && event.metaKey) {
			if (selectedOption.selected = !selectedOption.selected) {
				Sortable.utils.select(selectedOption);
			} else {
				Sortable.utils.deselect(selectedOption);
			}
		} else if (event instanceof PointerEvent && event.shiftKey && this.lastSelected) {
			this.deselectAllOptions();
			let setSeleted = false;
			for (let option of this.getElementsByTagName('option')) {
				if (option === selectedOption || option === this.lastSelected) {
					option.selected = true;
					setSeleted = !setSeleted;
				} else {
					option.selected = setSeleted;
				}
				if (option.selected) {
					Sortable.utils.select(option);
				}
			}
		} else {
			this.deselectAllOptions();
			selectedOption.selected = true;
			Sortable.utils.select(selectedOption);
		}
		this.lastSelected = selectedOption;
		event.preventDefault();
	}

	private deselectAllOptions() {
		for (let option of this.getElementsByTagName('option')) {
			option.selected = false;
			Sortable.utils.deselect(option);
		}
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
			const nativeStyles = window.getComputedStyle(optionElement);
			console.log(nativeStyles.getPropertyValue('background-color'));
		}
	}

	public add(option: HTMLOptionElement) {
		this.appendChild(option);
		Sortable.utils.select(option);
	}
}
