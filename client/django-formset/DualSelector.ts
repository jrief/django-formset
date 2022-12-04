import { IncompleteSelect } from './IncompleteSelect';
import { SortableSelectElement } from './SortableSelect';
import { StyleHelpers } from "./helpers";
import template from 'lodash.template';
import styles from "./SortableSelect.scss";


export class DualSelector extends IncompleteSelect {
	private readonly selectorElement: HTMLSelectElement;
	private readonly declaredStyles: HTMLStyleElement;
	private readonly containerElement: HTMLElement | null;
	private readonly searchLeftInput?: HTMLInputElement;
	private readonly searchRightInput?: HTMLInputElement;
	private readonly selectLeftElement: HTMLSelectElement;
	private readonly selectRightElement: HTMLSelectElement | SortableSelectElement;
	private readonly moveAllRightButton: HTMLButtonElement;
	private readonly moveSelectedRightButton: HTMLButtonElement;
	private readonly moveAllLeftButton: HTMLButtonElement;
	private readonly moveSelectedLeftButton: HTMLButtonElement;
	private readonly undoButton?: HTMLButtonElement;
	private readonly redoButton?: HTMLButtonElement;
	private historicalValues: string[][] = [];
	private historyCursor: number = 0;
	private lastRemoteQuery?: string;
	private readonly renderNoResults: Function;

	constructor(selectorElement: HTMLSelectElement, name: string) {
		super(selectorElement);
		this.declaredStyles = document.createElement('style');
		this.declaredStyles.innerText = styles;
		document.head.appendChild(this.declaredStyles);

		this.selectorElement = selectorElement;
		this.containerElement = this.fieldGroup.querySelector('.dj-dual-selector');
		selectorElement.setAttribute('multiple', 'multiple');
		const inputs = this.fieldGroup.querySelectorAll('input[type="text"]');
		if (inputs.length === 2) {
			this.searchLeftInput = inputs[0] as HTMLInputElement;
			this.searchRightInput = inputs[1] as HTMLInputElement;
			this.searchLeftInput.addEventListener('input', evt => this.leftLookup());
			this.searchRightInput.addEventListener('input', evt => this.rightLookup());
		}
		const selectors = this.fieldGroup.querySelectorAll(`select:not([is="${name}"])`);
		if (selectors.length >= 1) {
			this.selectLeftElement = selectors.item(0) as HTMLSelectElement;
			if (selectors.length === 2) {
				this.selectRightElement = selectors.item(1) as HTMLSelectElement;
			} else {
				const selector = this.fieldGroup.querySelector('django-sortable-select');
				this.selectRightElement = selector as SortableSelectElement;
			}
		} else {
			throw new Error(`<select is="${name}"> requires two <select>-elements`);
		}
		this.moveAllRightButton = this.fieldGroup.querySelector('button.dj-move-all-right') as HTMLButtonElement;
		this.moveSelectedRightButton = this.fieldGroup.querySelector('button.dj-move-selected-right') as HTMLButtonElement;
		this.moveSelectedLeftButton = this.fieldGroup.querySelector('button.dj-move-selected-left') as HTMLButtonElement;
		this.moveAllLeftButton = this.fieldGroup.querySelector('button.dj-move-all-left') as HTMLButtonElement;
		this.undoButton = this.fieldGroup.querySelector('button.dj-undo-selected') as HTMLButtonElement;
		this.redoButton = this.fieldGroup.querySelector('button.dj-redo-selected') as HTMLButtonElement;
		this.selectorElement.classList.add('dj-concealed');
		const templ = selectorElement.parentElement?.querySelector('template.select-no-results');
		this.renderNoResults = (data: any) => templ ? template(templ.innerHTML)(data) : "No results";
		this.installEventHandlers();
		this.initialize();
		this.transferStyles();
		this.setButtonsState();
	}

	private installEventHandlers() {
		this.selectLeftElement.addEventListener('focus', this.touch);
		this.selectLeftElement.addEventListener('dblclick', evt => this.moveOptionRight(evt.target));
		this.selectLeftElement.addEventListener('scroll', evt => this.selectLeftScrolled());
		this.selectRightElement.addEventListener('focus', this.touch);
		this.selectRightElement.addEventListener('dblclick', evt => this.moveOptionLeft(evt.target));
		this.selectRightElement.addEventListener('options-sorted', evt => this.optionsSorted());
		this.moveAllRightButton?.addEventListener('click', evt => this.moveAllOptionsRight());
		this.moveSelectedRightButton?.addEventListener('click', evt => this.moveSelectedOptionsRight());
		this.moveSelectedLeftButton?.addEventListener('click', evt => this.moveSelectedOptionsLeft());
		this.moveAllLeftButton?.addEventListener('click', evt => this.moveAllOptionsLeft());
		this.undoButton?.addEventListener('click', evt => this.unOrRedo(-1));
		this.redoButton?.addEventListener('click', evt => this.unOrRedo(+1));
	}

	private initialize() {
		const initialValues: string[] = [];
		const optionElemens = this.selectorElement.querySelectorAll(':scope > option') as NodeListOf<HTMLOptionElement>;
		optionElemens.forEach(option => {
			const clone = option.cloneNode() as HTMLOptionElement;
			if (option.selected) {
				option.selected = false;
				this.selectRightElement.add(option);
				initialValues.push(option.value);
			} else {
				this.selectLeftElement.add(option);
			}
			this.selectorElement.add(clone);  // add clone without inner text
		});
		const optionGroupElements = this.selectorElement.querySelectorAll(':scope > optgroup') as NodeListOf<HTMLOptGroupElement>;
		optionGroupElements.forEach(optGroupElement => {
			const selectedOptions = optGroupElement.querySelectorAll('option:checked') as NodeListOf<HTMLOptionElement>;
			if (selectedOptions.length > 0) {
				const newOptGroup = document.createElement('optgroup');
				newOptGroup.label = optGroupElement.label;
				this.selectRightElement.add(newOptGroup);
				selectedOptions.forEach(option => {
					const clone = option.cloneNode() as HTMLOptionElement;
					option.selected = false;
					newOptGroup.appendChild(option);
					initialValues.push(option.value);
					this.selectorElement.add(clone);  // add clone without inner text
				});
			}
			const unselectedOptions = optGroupElement.querySelectorAll('option:not(:checked)');
			if (unselectedOptions.length > 0) {
				const newOptGroup = document.createElement('optgroup');
				newOptGroup.label = optGroupElement.label;
				this.selectLeftElement.add(newOptGroup);
				unselectedOptions.forEach(option => {
					const clone = option.cloneNode() as HTMLOptionElement;
					newOptGroup.appendChild(option);
					this.selectorElement.add(clone);  // add clone without inner text
				});
			}
			this.selectorElement.removeChild(optGroupElement);
		});
		this.historicalValues.push(initialValues);
		this.setHistoryCursor(0);
		if (this.selectRightElement instanceof SortableSelectElement) {
			this.selectRightElement.initialize(this.selectLeftElement);
		}
	}

	private addNoResultsOption(selectElement: HTMLSelectElement | SortableSelectElement, query: string) {
		const option = new Option(this.renderNoResults({input: query}));
		option.disabled = true;
		selectElement.add(option);
	}

	private addOptionToSelectElement(option: OptionData, target: HTMLSelectElement | SortableSelectElement) {
		if (this.selectorElement.querySelector(`option[value="${option.id}"]`))
			return;
		const newOptionElement = new Option(option.label, option.id);
		if (typeof option.optgroup === 'string') {
			const optGroupElement = target.querySelector(`optgroup[label="${option.optgroup}"]`);
			if (optGroupElement instanceof HTMLOptGroupElement) {
				optGroupElement.appendChild(newOptionElement);
			} else {
				const newOptGroupElement = document.createElement('optgroup');
				newOptGroupElement.label = option.optgroup;
				newOptGroupElement.appendChild(newOptionElement);
				target.add(newOptGroupElement);
			}
		} else {
			target.add(newOptionElement);
		}
		this.selectorElement.add(newOptionElement.cloneNode() as HTMLOptionElement);
	}

	private async selectLeftScrolled() {
		if (!this.isIncomplete)
			return;
		const selectLeftScroll = this.selectLeftElement.scrollHeight - this.selectLeftElement.scrollTop;
		if (selectLeftScroll <= this.selectLeftElement.offsetHeight) {
			// triggers whenever the last <option>-element becomes visible inside its parent <select>
			await this.remoteLookup();
		}
	}

	private async remoteLookup() {
		let query: string;
		const searchString = this.searchLeftInput?.value;
		if (searchString) {
			const offset = this.selectLeftElement.querySelectorAll('option:not([hidden])').length;
			query = `query=${searchString}&offset=${offset}`;
		} else {
			query = `offset=${this.selectorElement.childElementCount}`;
		}
		if (this.lastRemoteQuery === query)
			return;
		this.lastRemoteQuery = query;
		await this.loadOptions(query, (options: Array<OptionData>) => options.forEach(option => {
			this.addOptionToSelectElement(option, this.selectLeftElement);
		}));
	}

	private selectorChanged() {
		this.selectorElement.querySelectorAll('option').forEach(option => {
			option.selected = !!this.selectRightElement.querySelector(`option[value="${option.value}"]`);
		});
		this.setButtonsState();
		this.containerElement?.classList.toggle('invalid', !this.selectorElement.checkValidity());
		this.selectorElement.dispatchEvent(new Event('change'));
	}

	private setButtonsState() {
		let disabled = !this.selectLeftElement.querySelector('option:not([hidden])');
		this.moveAllRightButton.disabled = disabled;
		this.moveSelectedRightButton.disabled = disabled;
		disabled = !this.selectRightElement.querySelector('option:not([hidden])');
		this.moveAllLeftButton.disabled = disabled;
		this.moveSelectedLeftButton.disabled = disabled;
	}

	private clearSearchFields() {
		if (this.searchLeftInput) {
			this.searchLeftInput.value = '';
		}
		if (this.searchRightInput) {
			this.searchRightInput.value = '';
		}
		this.selectLeftElement.querySelector('option[disabled]')?.remove();
		this.selectRightElement.querySelector('option[disabled]')?.remove();
		this.selectLeftElement.querySelectorAll('option').forEach(o => o.hidden = false);
		this.selectRightElement.querySelectorAll('option').forEach(o => o.hidden = false);
	}

	private optionsMoved() {
		const rightOptions = Array.from(this.selectRightElement.querySelectorAll('option'));
		this.historicalValues.splice(this.historyCursor + 1);
		this.historicalValues.push(rightOptions.map(o => o.value));
		this.setHistoryCursor(this.historicalValues.length - 1);
		this.selectorChanged();
	}

	private optionsSorted() {
		this.selectorElement.querySelectorAll('option:checked').forEach(o => o.remove());
		this.selectRightElement.querySelectorAll('option').forEach(optionElement => {
			const clone = optionElement.cloneNode() as HTMLOptionElement;
			clone.selected = true;
			this.selectorElement.add(clone);
		});
		this.optionsMoved();
	}

	private moveOptionToSelectElement(optionElement: HTMLOptionElement, selectElement: HTMLSelectElement | SortableSelectElement) {
		const sourceOptGroupElement = optionElement.parentElement;
		if (sourceOptGroupElement instanceof HTMLOptGroupElement) {
			const targetOptGroupElement = selectElement.querySelector(`optgroup[label="${sourceOptGroupElement.label}"]`);
			if (targetOptGroupElement instanceof HTMLOptGroupElement) {
				targetOptGroupElement.appendChild(optionElement);
				targetOptGroupElement.hidden = false;
			} else {
				const newOptGroupElement = document.createElement('optgroup');
				newOptGroupElement.label = sourceOptGroupElement.label;
				newOptGroupElement.appendChild(optionElement)
				selectElement.add(newOptGroupElement);
			}
			if (!sourceOptGroupElement.querySelector('option')) {
				// remove empty <optgroup>-element
				sourceOptGroupElement.remove();
			}
		} else {
			selectElement.add(optionElement);
		}
	}

	private async moveOptionRight(target: EventTarget | null) {
		if (target instanceof HTMLOptionElement) {
			this.moveOptionToSelectElement(target, this.selectRightElement);
			await this.selectLeftScrolled();
			this.hideOptionGroups(this.selectLeftElement);
			this.optionsMoved();
		}
	}

	private async moveAllOptionsRight() {
		this.selectLeftElement.querySelectorAll('option:not([hidden])').forEach(option => {
			this.moveOptionToSelectElement(option as HTMLOptionElement, this.selectRightElement);
		});
		this.clearSearchFields();
		await this.selectLeftScrolled();
		this.optionsMoved();
	}

	private moveSelectedOptionsRight() {
		this.selectLeftElement.querySelectorAll('option:checked').forEach(option => {
			this.moveOptionToSelectElement(option as HTMLOptionElement, this.selectRightElement);
		});
		this.hideOptionGroups(this.selectLeftElement);
		this.optionsMoved();
	}

	private moveSelectedOptionsLeft() {
		this.selectRightElement.querySelectorAll('option:checked').forEach(option => {
			this.moveOptionToSelectElement(option as HTMLOptionElement, this.selectLeftElement);
		});
		this.hideOptionGroups(this.selectRightElement);
		this.optionsMoved();
	}

	private moveAllOptionsLeft() {
		this.selectRightElement.querySelectorAll('option:not([hidden])').forEach(option => {
			this.moveOptionToSelectElement(option as HTMLOptionElement, this.selectLeftElement);
		});
		this.clearSearchFields();
		this.optionsMoved();
	}

	private moveOptionLeft(target: EventTarget | null) {
		if (target instanceof HTMLOptionElement) {
			this.moveOptionToSelectElement(target, this.selectLeftElement);
			this.hideOptionGroups(this.selectRightElement);
			this.optionsMoved();
		}
	}

	private hideOptionGroups(selectElement: HTMLSelectElement | SortableSelectElement) {
		selectElement.querySelectorAll('optgroup').forEach(optGroup => {
			optGroup.hidden = !optGroup.querySelector('option:not([hidden])');
		});
	}

	private async leftLookup() {
		const query = this.searchLeftInput?.value ?? '';
		let numFoundOptions = this.lookup(this.selectLeftElement, query);
		// first we look up for matching options ...
		if (this.isIncomplete && numFoundOptions < this.selectLeftElement.size) {
			// if we find less options than the <select> element can depict,
			// query for additional matching options from the server.
			await this.remoteLookup();
			numFoundOptions = this.lookup(this.selectLeftElement, query);
		}
		this.setButtonsState();
		if (numFoundOptions === 0) {
			this.addNoResultsOption(this.selectLeftElement, query);
		}
	}

	private rightLookup() {
		const query = this.searchRightInput?.value ?? '';
		if (this.lookup(this.selectRightElement, query) === 0) {
			this.addNoResultsOption(this.selectRightElement, query);
		}
	}

	private lookup(selectElement: HTMLSelectElement | SortableSelectElement, query: string) : number {
		selectElement.querySelector('option[disabled]')?.remove();
		const optionElements = selectElement.querySelectorAll('option');
		if (query) {
			query = query.toLowerCase();
			let hiddenOptions = 0;
			optionElements.forEach(option => {
				if (option.hidden = (option.text.toLowerCase().indexOf(query) === -1)) {
					hiddenOptions++;
				}
			});
			this.hideOptionGroups(selectElement);
			return optionElements.length - hiddenOptions;
		}
		optionElements.forEach(option => option.hidden = false);
		selectElement.querySelectorAll('optgroup').forEach(optgroup => optgroup.hidden = false);
		return optionElements.length;
	}

	private unOrRedo(direction: number) {
		this.clearSearchFields();
		const nextCursor = this.historyCursor + direction;
		if (nextCursor < 0 || nextCursor >= this.historicalValues.length)
			return;
		const nextValues = this.historicalValues[nextCursor];

		const rightOptions = Array.from(this.selectRightElement.querySelectorAll('option'));
		rightOptions.filter(o => nextValues.indexOf(o.value) === -1).forEach(optionElement => {
			this.moveOptionToSelectElement(optionElement, this.selectLeftElement)
		});
		const leftOptions = Array.from(this.selectLeftElement.querySelectorAll('option'));
		leftOptions.filter(o => nextValues.indexOf(o.value) !== -1).forEach(optionElement => {
			this.moveOptionToSelectElement(optionElement, this.selectRightElement)
		});

		if (this.selectRightElement.tagName === 'DJANGO-SORTABLE-SELECT') {
			nextValues.forEach(val => {
				const optionElem = this.selectRightElement.querySelector(`option[value="${val}"]`);
				if (optionElem) {
					this.selectRightElement.insertAdjacentElement('beforeend', optionElem);
				}
			});
			this.optionsSorted();
		}
		this.setHistoryCursor(nextCursor);
		this.selectorChanged();
	}

	private setHistoryCursor(historyCursor: number) {
		this.historyCursor = historyCursor;
		if (this.undoButton) {
			this.undoButton.disabled = historyCursor === 0;
		}
		if (this.redoButton) {
			this.redoButton.disabled = historyCursor === this.historicalValues.length - 1;
		}
	}

	private transferStyles() {
		const sheet = this.declaredStyles.sheet!;

		// set background-color to transparent, so that the shadow on a focused input/select field is not cropped
		sheet.insertRule('.dj-dual-selector select, .dj-dual-selector input{background-color: transparent;}', 0);
		let extraStyles = StyleHelpers.extractStyles(this.selectorElement, ['background-color']);
		sheet.insertRule(`django-formset django-field-group .dj-dual-selector .left-column{${extraStyles}}`, 1);
		sheet.insertRule(`django-formset django-field-group .dj-dual-selector .right-column{${extraStyles}}`, 2);

		// prevent <select multiple> to have different heights depending on the having at least one <option>
		extraStyles = StyleHelpers.extractStyles(this.selectLeftElement, ['height']);
		sheet.insertRule(`django-formset django-field-group .dj-dual-selector select{${extraStyles}}`, 3);
	}

	protected formResetted(event: Event) {
		this.clearSearchFields();
		const initialValues = this.historicalValues[0];
		this.historicalValues.splice(1);
		this.setHistoryCursor(0);
		const rightOptions = Array.from(this.selectRightElement.querySelectorAll('option'));
		rightOptions.filter(o => initialValues.indexOf(o.value) === -1).forEach(optionElement => {
			this.moveOptionToSelectElement(optionElement, this.selectLeftElement)
		});
		const leftOptions = Array.from(this.selectLeftElement.querySelectorAll('option'))
		leftOptions.filter(o => initialValues.indexOf(o.value) !== -1).forEach(optionElement => {
			this.moveOptionToSelectElement(optionElement, this.selectRightElement)
		});
		this.selectorChanged();
		this.containerElement?.classList.remove('invalid');
	}

	protected formSubmitted(event: Event) {
		this.clearSearchFields();
		this.historicalValues.splice(0, this.historicalValues.length - 1);
		this.setHistoryCursor(0);
	}

	public getValue() : string[] {
		const optionElements = Array.from(this.selectorElement.querySelectorAll('option:checked'));
		return (optionElements as Array<HTMLOptionElement>).map(o => o.value);
	}
}

const DS = Symbol('DualSelectorElement');

export class DualSelectorElement extends HTMLSelectElement {
	private [DS]?: DualSelector;  // hides internal implementation

	connectedCallback() {
		this[DS] = new DualSelector(this, 'django-dual-selector');
	}

	public get value() : any {
		return this[DS]?.getValue();
	}
}
