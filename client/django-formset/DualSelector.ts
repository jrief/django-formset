import { IncompleteSelect } from './IncompleteSelect';
import template from 'lodash.template';

class DualSelector extends IncompleteSelect {
	private readonly selectorElement: HTMLSelectElement;
	private readonly searchLeftInput?: HTMLInputElement;
	private readonly searchRightInput?: HTMLInputElement;
	private readonly selectLeftElement: HTMLSelectElement;
	private readonly selectRightElement: HTMLSelectElement;
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

	constructor(selectorElement: HTMLSelectElement) {
		super(selectorElement);
		this.selectorElement = selectorElement
		selectorElement.setAttribute('multiple', 'multiple');
		const inputs = this.fieldGroup.querySelectorAll('input[type="text"]');
		if (inputs.length === 2) {
			this.searchLeftInput = inputs[0] as HTMLInputElement;
			this.searchRightInput = inputs[1] as HTMLInputElement;
			this.searchLeftInput.addEventListener('input', evt => this.leftLookup());
			this.searchRightInput.addEventListener('input', evt => this.rightLookup());
		}
		const selectors = this.fieldGroup.querySelectorAll('select:not([is="django-dual-selector"])');
		if (selectors.length !== 2)
			throw new Error("<select is=\"django-dual-selector\"> requires two <select>-elements");
		this.selectLeftElement = selectors[0] as HTMLSelectElement;
		this.selectRightElement = selectors[1] as HTMLSelectElement;
		this.moveAllRightButton = this.fieldGroup.querySelector('button.dj-move-all-right') as HTMLButtonElement;
		this.moveSelectedRightButton = this.fieldGroup.querySelector('button.dj-move-selected-right') as HTMLButtonElement;
		this.moveSelectedLeftButton = this.fieldGroup.querySelector('button.dj-move-selected-left') as HTMLButtonElement;
		this.moveAllLeftButton = this.fieldGroup.querySelector('button.dj-move-all-left') as HTMLButtonElement;
		this.undoButton = this.fieldGroup.querySelector('button.dj-undo-selected') as HTMLButtonElement;
		this.redoButton = this.fieldGroup.querySelector('button.dj-redo-selected') as HTMLButtonElement;
		const templ = selectorElement.parentElement?.querySelector('template.select-no-results');
		this.renderNoResults = (data: any) => templ ? template(templ.innerHTML)(data) : "No results";
		this.installEventHandlers();
		this.initialize();
		this.setButtonsState();
	}

	private installEventHandlers() {
		this.selectLeftElement.addEventListener('focus', () => this.touch());
		this.selectLeftElement.addEventListener('dblclick', evt => this.moveOptionRight(evt.target));
		this.selectLeftElement.addEventListener('scroll', evt => this.selectLeftScrolled());
		this.selectRightElement.addEventListener('focus', () => this.touch());
		this.selectRightElement.addEventListener('dblclick', evt => this.moveOptionLeft(evt.target));
		this.moveAllRightButton?.addEventListener('click', evt => this.moveAllOptionsRight());
		this.moveSelectedRightButton?.addEventListener('click', evt => this.moveSelectedOptionsRight());
		this.moveSelectedLeftButton?.addEventListener('click', evt => this.moveSelectedOptionsLeft());
		this.moveAllLeftButton?.addEventListener('click', evt => this.moveAllOptionsLeft());
		this.undoButton?.addEventListener('click', evt => this.unOrRedo(-1));
		this.redoButton?.addEventListener('click', evt => this.unOrRedo(+1));
	}

	private getOptions(selectElement: HTMLSelectElement) : Array<HTMLOptionElement> {
		return Array.from(selectElement.getElementsByTagName('option'));
	}

	private initialize() {
		const initialValues: string[] = [];
		for (let option of this.getOptions(this.selectorElement)) {
			const clone = option.cloneNode() as HTMLOptionElement;
			if (option.selected) {
				option.selected = false;
				this.selectRightElement.add(option);
				initialValues.push(option.value);
			} else {
				this.selectLeftElement.add(option);
			}
			this.selectorElement.add(clone);  // add clone without inner text
		}
		this.historicalValues.push(initialValues);
		this.setHistoryCursor(0);
	}

	private addNoResultsOption(selectElement: HTMLSelectElement, query: string) {
		const option = new Option(this.renderNoResults({input: query}));
		option.disabled = true;
		selectElement.add(option);
	}

	private prepareOptions(selectElement: HTMLSelectElement) : Array<HTMLOptionElement> {
		const options = this.getOptions(selectElement);
		options.filter(o => o.disabled).forEach(o => o.remove());
		return options;
	}

	private addMoreOptions(items: Array<any>) {
		const selectorOptions = this.getOptions(this.selectorElement);
		for (let item of items) {
			if (selectorOptions.filter(o => o.value == item.id).length === 0) {
				const option = new Option(item.label, item.id);
				this.selectorElement.add(option.cloneNode() as HTMLOptionElement);
				this.selectLeftElement.add(option);
			}
		}
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
			const offset = this.getOptions(this.selectLeftElement).filter(o => !o.hidden).length;
			query = `query=${searchString}&offset=${offset}`;
		} else {
			query = `offset=${this.selectorElement.childElementCount}`;
		}
		if (this.lastRemoteQuery === query)
			return;
		this.lastRemoteQuery = query;
		await this.loadOptions(query, (items: Array<any>) => {
			this.addMoreOptions(items);
		});
	}

	private selectorChanged() {
		const rightOptions = this.getOptions(this.selectRightElement);
		const selectorOptions = this.getOptions(this.selectorElement);
		for (let option of selectorOptions) {
			option.selected = rightOptions.filter(o => o.value === option.value).length === 1;
		}
		this.setButtonsState();
		this.selectorElement.dispatchEvent(new Event('change'));
	}

	private setButtonsState() {
		let disabled = this.getOptions(this.selectLeftElement).filter(o => !o.hidden).length === 0;
		this.moveAllRightButton.disabled = disabled;
		this.moveSelectedRightButton.disabled = disabled;
		disabled = this.getOptions(this.selectRightElement).filter(o => !o.hidden).length === 0;
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
		this.prepareOptions(this.selectLeftElement).forEach(o => o.hidden = false);
		this.prepareOptions(this.selectRightElement).forEach(o => o.hidden = false);
	}

	private optionsMoved() {
		const rightOptions = this.getOptions(this.selectRightElement);
		this.historicalValues.splice(this.historyCursor + 1);
		this.historicalValues.push(rightOptions.map(o => o.value));
		this.setHistoryCursor(this.historicalValues.length - 1);
		this.selectorChanged();
	}

	private async moveOptionRight(target: EventTarget | null) {
		if (target instanceof HTMLOptionElement) {
			this.selectRightElement.add(target);
			await this.selectLeftScrolled();
			this.optionsMoved();
		}
	}

	private async moveAllOptionsRight() {
		this.getOptions(this.selectLeftElement).filter(o => !o.hidden).forEach(o => this.selectRightElement.add(o));
		this.clearSearchFields();
		await this.selectLeftScrolled();
		this.optionsMoved();
	}

	private moveSelectedOptionsRight() {
		this.getOptions(this.selectLeftElement).filter(o => o.selected).forEach(o => this.selectRightElement.add(o));
		this.optionsMoved();
	}

	private moveSelectedOptionsLeft() {
		this.getOptions(this.selectRightElement).filter(o => o.selected).forEach(o => this.selectLeftElement.add(o));
		this.optionsMoved();
	}

	private moveAllOptionsLeft() {
		this.getOptions(this.selectRightElement).filter(o => !o.hidden).forEach(o => this.selectLeftElement.add(o));
		this.clearSearchFields();
		this.optionsMoved();
	}

	private moveOptionLeft(target: EventTarget | null) {
		if (target instanceof HTMLOptionElement) {
			this.selectLeftElement.add(target);
			this.optionsMoved();
		}
	}

	private async leftLookup() {
		const query = this.searchLeftInput?.value ?? '';
		let numFoundOptions = this.lookup(this.prepareOptions(this.selectLeftElement), query);
		// first we lookup for matching options ...
		if (this.isIncomplete && numFoundOptions < this.selectLeftElement.size) {
			// if we find less options than the <select> element can depict,
			// query for additional matching options from the server.
			await this.remoteLookup();
			numFoundOptions = this.lookup(this.getOptions(this.selectLeftElement), query);
		}
		this.setButtonsState();
		if (numFoundOptions === 0) {
			this.addNoResultsOption(this.selectLeftElement, query);
		}
	}

	private rightLookup() {
		const query = this.searchRightInput?.value ?? '';
		if (this.lookup(this.prepareOptions(this.selectRightElement), query) === 0) {
			this.addNoResultsOption(this.selectRightElement, query);
		}
	}

	private lookup(options: Array<HTMLOptionElement>, query: string) : number {
		if (query) {
			query = query.toLowerCase();
			options.forEach(o => o.hidden = o.text.toLowerCase().indexOf(query) === -1);
			return options.length - options.filter(o => o.hidden).length;
		}
		options.forEach(o => o.hidden = false);
		return options.length;
	}

	private unOrRedo(direction: number) {
		this.clearSearchFields();
		const nextCursor = this.historyCursor + direction;
		if (nextCursor < 0 || nextCursor >= this.historicalValues.length)
			return;
		const nextValues = this.historicalValues[nextCursor];
		this.getOptions(this.selectRightElement).filter(o => nextValues.indexOf(o.value) === -1).forEach(o => this.selectLeftElement.add(o));
		this.getOptions(this.selectLeftElement).filter(o => nextValues.indexOf(o.value) !== -1).forEach(o => this.selectRightElement.add(o));
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

	public formResetted(event: Event) {
		this.clearSearchFields();
		const initialValues = this.historicalValues[0];
		this.historicalValues.splice(1);
		this.setHistoryCursor(0);
		this.getOptions(this.selectRightElement).filter(o => initialValues.indexOf(o.value) === -1).forEach(o => this.selectLeftElement.add(o));
		this.getOptions(this.selectLeftElement).filter(o => initialValues.indexOf(o.value) !== -1).forEach(o => this.selectRightElement.add(o));
		this.selectorChanged();
	}

	public formSubmitted(event: Event) {
		this.clearSearchFields();
		this.historicalValues.splice(0, this.historicalValues.length - 1);
		this.setHistoryCursor(0);
	}

	public get value() : string[] {
		return this.getOptions(this.selectorElement).filter(o => o.selected).map(o => o.value);
	}
}

const DS = Symbol('DualSelectorElement');

export class DualSelectorElement extends HTMLSelectElement {
	private [DS]: DualSelector;  // hides internal implementation

	connectedCallback() {
		this[DS] = new DualSelector(this);
	}

	public async getValue() {
		return this[DS].value;
	}
}
