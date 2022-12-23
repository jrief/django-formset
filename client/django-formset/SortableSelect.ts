import Sortable, { MultiDrag, SortableEvent } from 'sortablejs';
import { StyleHelpers } from './helpers';
import styles from './SortableSelect.scss';

Sortable.mount(new MultiDrag());


export class SortableSelectElement extends HTMLElement {
	private readonly declaredStyles: HTMLStyleElement;
	private lastSelected: HTMLOptionElement | null = null;

	public constructor() {
		super();
		this.declaredStyles = document.createElement('style');
		this.declaredStyles.innerText = styles;
		document.head.appendChild(this.declaredStyles);

		this.addEventListener('click', event => this.optionSelected(event));
		window.addEventListener('click', event => this.elementFocus(event));
	}

	public initialize(selectElement: HTMLSelectElement) {
		this.transferStyles(selectElement);
		Sortable.create(this, {
			animation: 150,
			fallbackOnBody: true,
			multiDrag: true,
			onEnd: event => this.onEnd(event),
		});
		this.querySelectorAll('optgroup').forEach(optgroup => {
			Sortable.create(this, {
				animation: 150,
				fallbackOnBody: true,
				multiDrag: true,
				onEnd: event => this.onEnd(event),
				handle: '>option',
				group: optgroup.label,
			});
		});
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
			this.classList.add('focus');
		} else {
			this.classList.remove('focus');
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

	private transferStyles(selectElement: HTMLSelectElement) {
		const sheet = this.declaredStyles.sheet;
		const optionElement = selectElement.querySelector('option');
		for (let index = 0; sheet && index < sheet.cssRules.length; index++) {
			const cssRule = sheet.cssRules.item(index) as CSSStyleRule;
			let extraStyles: string;
			switch (cssRule.selectorText) {
				case 'django-sortable-select':
					extraStyles = StyleHelpers.extractStyles(selectElement, [
						'display', 'width', 'height', 'border', 'box-shadow', 'outline', 'overflow',
						'font-family', 'font-size', 'font-strech', 'font-style', 'font-weight',
						'letter-spacing', 'white-space', 'line-height']);
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case 'django-sortable-select.focus':
					selectElement.style.transition = 'none';
					selectElement.focus();
					extraStyles = StyleHelpers.extractStyles(selectElement, [
						'border', 'box-shadow', 'outline']);
					selectElement.blur();
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					selectElement.style.transition = '';
					break;
				case 'django-sortable-select option.sortable-chosen, django-sortable-select option.sortable-selected':
					if (optionElement) {
						optionElement.selected = true;
						extraStyles = StyleHelpers.extractStyles(optionElement, [
							'color', 'background-color']);
						sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
						optionElement.selected = false;
					}
					break;
				case 'django-sortable-select.focus option.sortable-chosen, django-sortable-select.focus option.sortable-selected':
					selectElement.focus();
					if (optionElement) {
						optionElement.selected = true;
						extraStyles = StyleHelpers.extractStyles(optionElement, [
							'color', 'background-color']);
						sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
						optionElement.selected = false;
					}
					selectElement.blur();
					break;
				case 'django-sortable-select optgroup option::before':
					sheet.insertRule(`${cssRule.selectorText}{content:"\\0000a0\\0000a0\\0000a0\\0000a0";}`, ++index);
					break;
				default:
					break;
			}
		}
	}

	public add(element: HTMLOptionElement | HTMLOptGroupElement) {
		if (element instanceof HTMLOptionElement) {
			this.appendChild(element);
			Sortable.utils.select(element);
		} else if (element instanceof HTMLOptGroupElement) {
			this.appendChild(element);
			Sortable.create(element, {
				animation: 150,
				fallbackOnBody: true,
				multiDrag: true,
				onEnd: event => this.onEnd(event),
				handle: '>option',
			});
		}
	}
}


export class SortableOptGroupElement extends HTMLOptGroupElement {
	private lastSelected: HTMLOptionElement | null = null;

	public constructor() {
		super();
	}
}
