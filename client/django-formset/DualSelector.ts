import { IncompleteSelect } from './IncompleteSelect';
import template from 'lodash.template';

class DualSelector extends IncompleteSelect {
	private readonly selectorElement: HTMLSelectElement;
	private readonly searchLeftInput?: HTMLInputElement;
	private readonly searchRightInput?: HTMLInputElement;
	private readonly selectLeftElement: HTMLSelectElement;
	private readonly selectRightElement: HTMLSelectElement;
	private readonly initialValues: string[] = [];
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
		this.fieldGroup.querySelector('button.dj-move-all-right')?.addEventListener('click', evt => this.moveAllOptionsRight());
		this.fieldGroup.querySelector('button.dj-move-selected-right')?.addEventListener('click', evt => this.moveSelectedOptionsRight());
		this.fieldGroup.querySelector('button.dj-move-selected-left')?.addEventListener('click', evt => this.moveSelectedOptionsLeft());
		this.fieldGroup.querySelector('button.dj-move-all-left')?.addEventListener('click', evt => this.moveAllOptionsLeft());
		const templ = selectorElement.parentElement?.querySelector('template.select-no-results');
		this.renderNoResults = (data: any) => templ ? template(templ.innerHTML)(data) : "No results";
		this.initialize();
	}

	private getOptions(selectElement: HTMLSelectElement) : Array<HTMLOptionElement> {
		return Array.from(selectElement.getElementsByTagName('option'));
	}

	private initialize() {
		for (let option of this.getOptions(this.selectorElement)) {
			const clone = option.cloneNode() as HTMLOptionElement;
			if (option.selected) {
				option.selected = false;
				this.selectRightElement.add(option);
				this.initialValues.push(option.value);
			} else {
				this.selectLeftElement.add(option);
			}
			this.selectorElement.add(clone);  // add clone without inner text
		}
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

	private updateSelector() {
		const selectorOptions = this.getOptions(this.selectorElement);
		const leftOptions = this.getOptions(this.selectLeftElement);
		const rightOptions = this.getOptions(this.selectRightElement);
		for (let option of selectorOptions) {
			option.selected = rightOptions.filter(o => o.value === option.value).length === 1;
		}
		const selectLeftScroll = this.selectLeftElement.scrollHeight - this.selectLeftElement.scrollTop;
		const visibleOptions = leftOptions.filter(o => !o.hidden);
		if (visibleOptions.length === 0 || selectLeftScroll <= this.selectLeftElement.offsetHeight) {
			// triggers whenever the last <option>-element becomes visible inside its parent <select>
			this.loadOptions(`offset=${selectorOptions.length}`, (items: any) => this.addMoreOptions(items));
		}
		this.selectorElement.dispatchEvent(new Event('change'));
	}

	private prepareOptions(selectElement: HTMLSelectElement) : Array<HTMLOptionElement> {
		const options = this.getOptions(selectElement);
		options.filter(o => o.disabled).forEach(o => o.remove());
		return options;
	}

	private clearSearchFields() {
		this.searchLeftInput!.value = this.searchRightInput!.value = '';
		this.prepareOptions(this.selectLeftElement).forEach(o => o.hidden = false);
		this.prepareOptions(this.selectRightElement).forEach(o => o.hidden = false);
	}

	private moveAllOptionsRight() {
		this.clearSearchFields();
		this.getOptions(this.selectLeftElement).forEach(o => this.selectRightElement.add(o));
		this.updateSelector();
	}

	private moveSelectedOptionsRight() {
		this.clearSearchFields();
		this.getOptions(this.selectLeftElement).filter(o => o.selected).forEach(o => this.selectRightElement.add(o));
		this.updateSelector();
	}

	private moveSelectedOptionsLeft() {
		this.clearSearchFields();
		this.getOptions(this.selectRightElement).filter(o => o.selected).forEach(o => this.selectLeftElement.add(o));
		this.updateSelector();
	}

	private moveAllOptionsLeft() {
		this.clearSearchFields();
		this.getOptions(this.selectRightElement).forEach(o => this.selectLeftElement.add(o));
		this.updateSelector();
	}

	private leftLookup() {
		const query = this.searchLeftInput?.value ?? '';
		// first we lookup for matching options ...
		if (this.lookup(this.prepareOptions(this.selectLeftElement), query) < this.selectLeftElement.size) {
			// if we find less than the <select> element can depict, query for more matching items from the server
			this.loadOptions(`query=${query}`, (items: any) => {
				this.addMoreOptions(items);
				if (this.lookup(this.prepareOptions(this.selectLeftElement), query) === 0) {
					const option = new Option(this.renderNoResults({input: query}));
					option.disabled = true;
					this.selectLeftElement.add(option);
				}
			});
		}
	}

	private rightLookup() {
		const query = this.searchRightInput?.value ?? '';
		if (this.lookup(this.prepareOptions(this.selectRightElement), query) === 0) {
			const option = new Option(this.renderNoResults({input: query}));
			option.disabled = true;
			this.selectRightElement.add(option);
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

	formResetted(event: Event) {
		this.clearSearchFields();
		for (let option of this.getOptions(this.selectRightElement)) {
			if (this.initialValues.indexOf(option.value) === -1) {
				this.selectLeftElement.add(option);
			}
		}
		for (let option of this.getOptions(this.selectLeftElement)) {
			if (this.initialValues.indexOf(option.value) !== -1) {
				this.selectRightElement.add(option);
			}
		}
	}

	public get value() : string[] {
		const result = [];
		for (let option of this.getOptions(this.selectorElement)) {
			result.push(option.value);
		}
		return result;
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
