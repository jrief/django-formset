import {IncompleteSelect} from './IncompleteSelect';
import {SortableSelectElement} from './SortableSelect';
import {StyleHelpers} from "./helpers";
import template from 'lodash.template';


export class DualSelector extends IncompleteSelect {
	private readonly selectorElement: HTMLSelectElement;
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
	private historicValues: string[][] = [];
	private historyCursor: number = 0;
	private lastRemoteQuery = new URLSearchParams();
	private readonly renderNoResults: Function;
	private readonly baseSelector = 'django-formset [role="group"] .dj-dual-selector';

	constructor(selectorElement: HTMLSelectElement, name: string) {
		super(selectorElement);
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
		if (!StyleHelpers.stylesAreInstalled(this.baseSelector)) {
			this.transferStyles();
		}
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

	public initialize() {
		const initialValues: string[] = [];
		const optionElements = this.selectorElement.querySelectorAll(':scope > option') as NodeListOf<HTMLOptionElement>;
		optionElements.forEach(option => {
			const optionData : OptionData = {id: option.value, label: option.label};
			if (option.selected) {
				this.addOptionToSelectElement(optionData, this.selectRightElement);
				initialValues.push(option.value);
			} else {
				this.addOptionToSelectElement(optionData, this.selectLeftElement);
			}
			option.replaceChildren();  // selectorElement is shadowed
		});
		const optionGroupElements = this.selectorElement.querySelectorAll(':scope > optgroup') as NodeListOf<HTMLOptGroupElement>;
		optionGroupElements.forEach(optGroupElement => {
			optGroupElement.querySelectorAll('option').forEach(option => {
				const optionData : OptionData = {id: option.value, label: option.label, optgroup: optGroupElement.label};
				if (option.selected) {
					this.addOptionToSelectElement(optionData, this.selectRightElement);
					initialValues.push(option.value);
				} else {
					this.addOptionToSelectElement(optionData, this.selectLeftElement);
				}
				option.replaceChildren();  // selectorElement is shadowed
			});
			optGroupElement.replaceWith(...optGroupElement.childNodes);
		});
		this.historicValues.push(initialValues);
		this.setHistoryCursor(0);
		if (this.selectRightElement instanceof SortableSelectElement) {
			this.selectRightElement.initialize(this.selectLeftElement);
		}
		this.setButtonsState();
		this.setupFilters(this.selectorElement);
		this.installEventHandlers();
	}

	private addNoResultsOption(selectElement: HTMLSelectElement | SortableSelectElement, query: string) {
		const option = new Option(this.renderNoResults({input: query}));
		option.disabled = true;
		selectElement.add(option);
	}

	private addOptionToSelectElement(option: OptionData, target: HTMLSelectElement | SortableSelectElement) : HTMLOptionElement {
		const optionElement = target.querySelector(`option[value="${option.id}"]`);
		if (optionElement instanceof HTMLOptionElement)
			return optionElement;  // prevent duplicates
		const newOptionElement = new Option(option.label, option.id);
		if (typeof option.optgroup === 'string') {
			let optGroupElement = target.querySelector(`optgroup[label="${option.optgroup}"]`);
			if (!optGroupElement) {
				optGroupElement = document.createElement('optgroup');
				if (optGroupElement instanceof HTMLOptGroupElement) {
					optGroupElement.label = option.optgroup;
					target.add(optGroupElement);
				}
			}
			optGroupElement.appendChild(newOptionElement);
		} else {
			target.add(newOptionElement);
		}
		return newOptionElement;
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
		let query: URLSearchParams;
		const search = this.searchLeftInput?.value;
		if (search) {
			const offset = this.selectLeftElement.querySelectorAll('option:not([hidden])').length;
			query = this.buildFetchQuery(offset, {search});
		} else {
			query = this.buildFetchQuery(this.selectorElement.childElementCount);
		}
		if (this.lastRemoteQuery === query)
			return;
		this.lastRemoteQuery = query;
		await this.loadOptions(query, (options: Array<OptionData>) => options.forEach(option => {
			if (!(this.selectorElement.querySelector(`option[value="${option.id}"]`))) {
				const optionElement = this.addOptionToSelectElement(option, this.selectLeftElement).cloneNode(false) as HTMLOptionElement;
				this.selectorElement.add(optionElement);
			}
			this.setButtonsState();
		}));
	}

	private selectorChanged() {
		this.selectorElement.querySelectorAll('option').forEach(option => {
			option.selected = !!this.selectRightElement.querySelector(`option[value="${option.value}"]`);
		});
		this.setButtonsState();
		this.containerElement?.classList.toggle('invalid', !this.selectorElement.checkValidity());
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
		this.historicValues.splice(this.historyCursor + 1);
		this.historicValues.push(rightOptions.map(o => o.value));
		this.setHistoryCursor(this.historicValues.length - 1);
		this.selectorChanged();
		this.selectorElement.dispatchEvent(new Event('change'));
	}

	private optionsSorted() {
		this.selectorElement.querySelectorAll('option:checked').forEach(o => o.remove());
		this.selectRightElement.querySelectorAll('option').forEach(optionElement => {
			const clone = optionElement.cloneNode(false) as HTMLOptionElement;
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

	private moveOptionRight(target: EventTarget | null) {
		if (target instanceof HTMLOptionElement) {
			this.moveOptionToSelectElement(target, this.selectRightElement);
			this.selectLeftScrolled();
			this.hideOptionGroups(this.selectLeftElement);
			this.optionsMoved();
		}
	}

	private moveAllOptionsRight() {
		this.selectLeftElement.querySelectorAll('option:not([hidden])').forEach(option => {
			this.moveOptionToSelectElement(option as HTMLOptionElement, this.selectRightElement);
		});
		this.clearSearchFields();
		this.selectLeftScrolled();
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

	private leftLookup() {
		const query = this.searchLeftInput?.value ?? '';
		let numFoundOptions = this.lookup(this.selectLeftElement, query);
		// first we look up for matching options ...
		if (this.isIncomplete && numFoundOptions < this.selectLeftElement.size) {
			// if we find less options than the <select> element can depict,
			// query for additional matching options from the server.
			this.remoteLookup();
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
		if (nextCursor < 0 || nextCursor >= this.historicValues.length)
			return;
		const nextValues = this.historicValues[nextCursor];

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
				const optionElem = this.selectRightElement.querySelector(`:scope > option[value="${val}"]`);
				if (optionElem) {
					this.selectRightElement.insertAdjacentElement('beforeend', optionElem);
				} else {
					const optionElem = this.selectRightElement.querySelector(`:scope > optgroup > option[value="${val}"]`);
					if (optionElem) {
						optionElem.parentElement?.insertAdjacentElement('beforeend', optionElem);
					}
				}
			});
			this.optionsSorted();
		}
		this.setHistoryCursor(nextCursor);
		this.selectorChanged();
		this.selectorElement.dispatchEvent(new Event('change'));
	}

	private setHistoryCursor(historyCursor: number) {
		this.historyCursor = historyCursor;
		if (this.undoButton) {
			this.undoButton.disabled = historyCursor === 0;
		}
		if (this.redoButton) {
			this.redoButton.disabled = historyCursor === this.historicValues.length - 1;
		}
	}

	private transferStyles() {
		const declaredStyles = document.createElement('style');
		document.head.appendChild(declaredStyles);
		if (!declaredStyles.sheet)
			throw new Error("Could not create <style> element");
		const sheet = declaredStyles.sheet;

		// set dummy style to check if styles have been loaded for this widget
		sheet.insertRule(`${this.baseSelector}{--dummy-style: none;}`, 0);

		// extract focused styles from the <select>-elements
		let index = 0;
		this.selectLeftElement.style.transition = this.selectRightElement.style.transition = 'none';
		this.selectLeftElement.classList.add('-focus-');
		let extraStyles = StyleHelpers.extractStyles(this.selectLeftElement, ['box-shadow']);
		sheet.insertRule(`${this.baseSelector} .left-column:has(>input:focus, >select:focus){${extraStyles}}`, ++index);
		sheet.insertRule(`${this.baseSelector} .left-column>:is(input:focus, select:focus){box-shadow: none; outline: none;}`, ++index);
		extraStyles = StyleHelpers.extractStyles(this.selectLeftElement, ['border-color', 'outline']);
		sheet.insertRule(`${this.baseSelector} .left-column:has(>input:focus)>select{${extraStyles}}`, ++index);
		sheet.insertRule(`${this.baseSelector} .left-column:has(>select:focus)>input{${extraStyles}}`, ++index);
		this.selectLeftElement.classList.remove('-focus-');
		if (this.searchLeftInput) {
			extraStyles = StyleHelpers.extractStyles(this.searchLeftInput, ['border-top-left-radius', 'border-top-right-radius']);
			sheet.insertRule(`${this.baseSelector} .left-column{${extraStyles}}`, ++index);
		}
		extraStyles = StyleHelpers.extractStyles(this.selectLeftElement, ['border-bottom-left-radius', 'border-bottom-right-radius']);
		sheet.insertRule(`${this.baseSelector} .left-column{${extraStyles}}`, ++index);
		this.selectRightElement.classList.add('-focus-');
		extraStyles = StyleHelpers.extractStyles(this.selectRightElement, ['box-shadow']);
		sheet.insertRule(`${this.baseSelector} .right-column:has(> input:focus, >select:focus, >django-sortable-select.focus){${extraStyles}}`, ++index);
		sheet.insertRule(`${this.baseSelector} .right-column>:is(input:focus, select:focus, django-sortable-select.focus){box-shadow: none; outline: none;}`, ++index);
		extraStyles = StyleHelpers.extractStyles(this.selectRightElement, ['border-color', 'outline']);
		sheet.insertRule(`${this.baseSelector} .right-column:has(>input:focus)>:is(select, django-sortable-select){${extraStyles}}`, ++index);
		sheet.insertRule(`${this.baseSelector} .right-column:has(>select:focus, django-sortable-select.focus)>input{${extraStyles}}`, ++index);
		this.selectRightElement.classList.remove('-focus-');
		if (this.searchRightInput) {
			extraStyles = StyleHelpers.extractStyles(this.searchRightInput, ['border-top-left-radius', 'border-top-right-radius']);
			sheet.insertRule(`${this.baseSelector} .right-column{${extraStyles}}`, ++index);
		}
		extraStyles = StyleHelpers.extractStyles(this.selectRightElement, ['border-bottom-left-radius', 'border-bottom-right-radius']);
		sheet.insertRule(`${this.baseSelector} .right-column{${extraStyles}}`, ++index);
		this.selectLeftElement.style.transition = this.selectRightElement.style.transition = '';

		// set background-color to transparent, so that the shadow on a focused input/select field is not cropped
		extraStyles = StyleHelpers.extractStyles(this.selectLeftElement, ['background-color']);
		sheet.insertRule(`${this.baseSelector} .left-column{${extraStyles}}`, ++index);
		extraStyles = StyleHelpers.extractStyles(this.selectRightElement, ['background-color']);
		sheet.insertRule(`${this.baseSelector} .right-column{${extraStyles}}`, ++index);
		sheet.insertRule(`${this.baseSelector} :has(select, input){background-color: transparent;}`, ++index);

		// prevent <select multiple> to have different heights depending on having at least one <option>
		extraStyles = StyleHelpers.extractStyles(this.selectLeftElement, ['height']);
		sheet.insertRule(`${this.baseSelector} select{${extraStyles}}`, ++index);
	}

	protected getValue = () => this.historicValues[this.historicValues.length - 1];

	protected async formResetted(event: Event) {
		this.historicValues.splice(1);
		this.setHistoryCursor(0);
		await this.reloadOptions();
		this.selectorChanged();
		this.containerElement?.classList.remove('invalid');
		const errorPlaceholder = this.fieldGroup.querySelector('.dj-errorlist > .dj-placeholder');
		if (errorPlaceholder) {
			errorPlaceholder.innerHTML = '';
		}
	}

	protected formSubmitted(event: Event) {
		this.clearSearchFields();
		this.historicValues.splice(0, this.historicValues.length - 1);
		this.setHistoryCursor(0);
	}

	protected async reloadOptions(silent?: boolean) {
		const currentValues = this.getValue();
		this.selectorElement.replaceChildren();
		this.selectLeftElement.replaceChildren();
		this.selectRightElement.replaceChildren();
		this.clearSearchFields();
		this.fieldGroup.classList.remove('dj-dirty', 'dj-touched', 'dj-validated');
		this.fieldGroup.classList.add('dj-untouched', 'dj-pristine');
		this.containerElement?.classList.remove('invalid');
		const errorPlaceholder = this.fieldGroup.querySelector('.dj-errorlist > .dj-placeholder');
		if (errorPlaceholder) {
			errorPlaceholder.innerHTML = '';
		}
		await this.remoteLookup();
		this.historicValues.splice(1);
		this.setHistoryCursor(0);

		let selectorChanged = false;
		const leftOptions = Array.from(this.selectLeftElement.querySelectorAll('option'))
		leftOptions.filter(o => currentValues.includes(o.value)).forEach(optionElement => {
			this.moveOptionToSelectElement(optionElement, this.selectRightElement);
			selectorChanged = true;
		});
		if (selectorChanged) {
			this.selectorChanged();
		}
	}
}

const DS = Symbol('DualSelectorElement');

export class DualSelectorElement extends HTMLSelectElement {
	private [DS]: DualSelector;  // hides internal implementation

	constructor() {
		super();
		this[DS] = new DualSelector(this, 'django-dual-selector');
	}

	connectedCallback() {
		this[DS].initialize();
	}
}
