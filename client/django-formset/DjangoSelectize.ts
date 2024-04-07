import TomSelect from 'tom-select/src/tom-select';
import {TomSettings} from 'tom-select/src/types/settings';
import {RecursivePartial, TomOption} from 'tom-select/src/types';
import TomSelect_remove_button from 'tom-select/src/plugins/remove_button/plugin';
import {IncompleteSelect} from './IncompleteSelect';
import template from 'lodash.template';
import {StyleHelpers} from './helpers';
import styles from './DjangoSelectize.scss';

TomSelect.define('remove_button', TomSelect_remove_button);


export class DjangoSelectize extends IncompleteSelect {
	protected readonly shadowRoot: ShadowRoot;
	private readonly extraStyleSheet: CSSStyleSheet = new CSSStyleSheet();
	private readonly numOptions: number = 12;
	private readonly tomSelect: TomSelect;
	private readonly observer: MutationObserver;
	private initialValue: string | string[] = '';
	private readonly baseSelector = '.ts-wrapper';

	constructor(tomInput: HTMLSelectElement) {
		super(tomInput);
		let isMultiple = false;
		if (tomInput.hasAttribute('multiple')) {
			// We want to use the CSS styles for <select> without multiple
			tomInput.removeAttribute('multiple');
			isMultiple = true;
		}
		const nativeStyles = {...window.getComputedStyle(tomInput)} as CSSStyleDeclaration;
		if (isMultiple) {
			// revert the above
			tomInput.setAttribute('multiple', 'multiple');
		}
		this.numOptions = parseInt(tomInput.getAttribute('options') ?? this.numOptions.toString());
		this.tomSelect = new TomSelect(tomInput, this.getSettings(tomInput));
		this.observer = new MutationObserver(this.attributesChanged);
		this.observer.observe(tomInput, {attributes: true});
		this.initialValue = this.currentValue;
		this.shadowRoot = this.wrapInShadowRoot();
		this.transferStyles(nativeStyles);
		tomInput.classList.add('dj-concealed');
		this.validateInput(this.initialValue as string);
	}

	protected getSettings(tomInput: HTMLSelectElement) : RecursivePartial<TomSettings> {
		const settings: RecursivePartial<TomSettings> = {
			create: false,
			valueField: 'id',
			labelField: 'label',
			maxItems: 1,
			maxOptions: undefined,
			sortField: [{field: '$order'}, {field: '$score'}],
			lockOptgroupOrder: true,
			searchField: ['label'],
			render: {},
			plugins: {},
			onFocus: this.touch,
			onBlur: this.blurred,
			onType: this.inputted,
		};
		const templ = tomInput.parentElement?.querySelector('template.select-no-results');
		if (templ) {
			settings.render = {...settings.render, no_results: (data: TomOption) => template(templ.innerHTML)(data)};
		}
		if (this.isIncomplete) {
			settings.load = this.load;
		}
		if (tomInput.hasAttribute('multiple')) {
			settings.maxItems = parseInt(tomInput.getAttribute('max_items') ?? '3');
			const translation = tomInput.parentElement?.querySelector('template.selectize-remove-item');
			settings.plugins = {...settings.plugins, remove_button: {title: translation?.innerHTML ?? "Remove item"}};
			// tom-select has some issues to initialize items using the original input element
			const scriptId = `${tomInput.getAttribute('id')}_initial`;
			settings.items = JSON.parse(document.getElementById(scriptId)?.textContent ?? '[]');
		}
		return settings;
	}

	protected getValue = () => this.currentValue;

	protected async formResetted(event: Event) {
		this.getValue = () => this.initialValue;
		this.tomSelect.setValue(this.initialValue, true);
		await this.reloadOptions();
		this.getValue = () => this.currentValue;
	}

	protected formSubmitted(event: Event) {}

	protected async reloadOptions(silent?: boolean) {
		const currentValue = this.getValue();
		this.tomSelect.clear(true);
		this.fieldGroup.classList.remove('dj-dirty', 'dj-touched', 'dj-validated');
		this.fieldGroup.classList.add('dj-untouched', 'dj-pristine');
		const errorPlaceholder = this.fieldGroup.querySelector('.dj-errorlist > .dj-placeholder');
		if (errorPlaceholder) {
			errorPlaceholder.innerHTML = '';
		}
		if (this.isIncomplete) {
			this.tomSelect.clearOptions();
			this.tomSelect.input.replaceChildren();
			await this.loadOptions(this.buildFetchQuery(0), (options: Array<OptionData>) => {
				this.tomSelect.addOptions(options);
			});
		}
		this.tomSelect.setValue(currentValue, silent);
	}

	private get currentValue(): string | string[] {
		const currentValue = this.tomSelect.getValue();
		// make a deep copy because TomSelect mutates the array
		return Array.isArray(currentValue) ? [...currentValue] : currentValue;
	}

	private extractOptGroups(options: Array<OptionData>) {
		const groupnames = new Set<string>();
		options.forEach(o => {
			if (typeof o.optgroup === 'string') {
				groupnames.add(o.optgroup);
			}
		});
		return Array.from(groupnames).map(name => ({label: name, value: name}));
	}

	private load = (query: string, callback: Function) => {
		this.loadOptions(this.buildFetchQuery(0, query), (options: Array<OptionData>) => {
			callback(options, this.extractOptGroups(options));
		});
	}

	private blurred = () => {
		const wrapper = this.shadowRoot.querySelector('.ts-wrapper');
		wrapper?.classList.remove('dirty');
	}

	private inputted = (event: Event) => {
		const value = event as unknown as string;
		const wrapper = this.shadowRoot.querySelector('.ts-wrapper');
		wrapper?.classList.toggle('dirty', value.length > 0);
	}

	private validateInput(value: String | Array<string>) {
		const wrapper = this.shadowRoot.querySelector('.ts-wrapper');
		wrapper?.classList.remove('dirty');
		const selectElem = this.tomSelect.input as HTMLSelectElement;
		if (this.tomSelect.isRequired) {
			selectElem.setCustomValidity(value ? "": "Value is missing.");
		}
		if (selectElem.multiple) {
			for (let k = 0; k < selectElem.options.length; k++) {
				const option = selectElem.options.item(k);
				if (option) {
					option.selected = value.indexOf(option.value) >= 0;
				}
			}
		} else {
			this.tomSelect.input.value = value as string;
		}
	}

	private wrapInShadowRoot() : ShadowRoot {
		const shadowWrapper = document.createElement('div');
		shadowWrapper.classList.add('shadow-wrapper');
		const shadowRoot = shadowWrapper.attachShadow({mode: 'open', delegatesFocus: true});
		const shadowStyleElement = document.createElement('style');
		shadowRoot.appendChild(shadowStyleElement).textContent = styles;
		this.tomSelect.input.insertAdjacentElement('beforebegin', shadowWrapper);
		const wrapper = (this.tomSelect.input.parentElement as HTMLElement).removeChild(this.tomSelect.wrapper);
		shadowRoot.appendChild(wrapper);
		return shadowRoot;
	}

	private transferStyles(nativeStyles: CSSStyleDeclaration) {
		const wrapperStyle = (this.shadowRoot.host as HTMLElement).style;
		wrapperStyle.setProperty('display', nativeStyles.display);
		const tomInput = this.tomSelect.input;
		const lineHeight = window.getComputedStyle(tomInput).getPropertyValue('line-height');
		const optionElement = tomInput.querySelector('option');
		const sheet = this.shadowRoot.styleSheets.item(0);
		const displayNumOptions = Math.min(Math.max(this.numOptions, 8), 25);

		let loaded = false;
		for (let index = 0; sheet && index < sheet.cssRules.length; index++) {
			const cssRule = sheet.cssRules.item(index) as CSSStyleRule;
			let extraStyles: string | null = null;
			switch (cssRule.selectorText) {
				case this.baseSelector:
					extraStyles = StyleHelpers.extractStyles(tomInput, [
						'font-family', 'font-size', 'font-stretch', 'font-style', 'font-weight',
						'letter-spacing', 'white-space'
					]);
					loaded = true;
					break;
				case `${this.baseSelector} .ts-control`:
					extraStyles = StyleHelpers.extractStyles(tomInput, [
						'background-color', 'border', 'border-radius', 'box-shadow', 'color',
						'padding']).concat(
						`width: ${nativeStyles['width']}; min-height: ${nativeStyles['height']};`
					);
					break;
				case `${this.baseSelector} .ts-control > input`:
				case `${this.baseSelector} .ts-control > div`:
					if (optionElement) {
						extraStyles = StyleHelpers.extractStyles(optionElement, ['padding-left', 'padding-right']);
					}
					break;
				case `${this.baseSelector} .ts-control > input::placeholder`:
					tomInput.classList.add('-placeholder-');
					extraStyles = StyleHelpers.extractStyles(tomInput, ['background-color', 'color']);
					tomInput.classList.remove('-placeholder-');
					break;
				case `${this.baseSelector}.focus .ts-control`:
					tomInput.style.transition = 'none';
					tomInput.classList.add('-focus-');
					extraStyles = StyleHelpers.extractStyles(tomInput, [
						'background-color', 'border', 'box-shadow', 'color', 'outline', 'transition'
					]);
					tomInput.classList.remove('-focus-');
					tomInput.style.transition = '';
					break;
				case `${this.baseSelector}.disabled .ts-control`:
					tomInput.classList.add('-disabled-');
					extraStyles = StyleHelpers.extractStyles(tomInput, [
						'background-color', 'border', 'box-shadow', 'color', 'opacity', 'outline', 'transition'
					]);
					tomInput.classList.remove('-disabled-');
					break;
				case `${this.baseSelector} .ts-dropdown`:
					extraStyles = StyleHelpers.extractStyles(tomInput, [
						'border-right', 'border-bottom', 'border-left', 'color'
					]).concat(
						parseFloat(lineHeight) > 0 ? `line-height: calc(${lineHeight} * 1.2);` : 'line-height: 1.4em;'
					);
					break;
				case `${this.baseSelector} .ts-dropdown .ts-dropdown-content`:
					if (parseFloat(lineHeight) > 0) {
						extraStyles =  `max-height: calc(${lineHeight} * 1.2 * ${displayNumOptions});`;
					} else {
						extraStyles =  `max-height: ${displayNumOptions * 1.4}em;`;
					}
					break;
				case `${this.baseSelector} .ts-dropdown [data-selectable]`:
					extraStyles = StyleHelpers.extractStyles(tomInput, ['padding-left']);
					break;
				case ':host-context([role="group"].dj-submitted) .ts-wrapper.invalid.focus .ts-control':
					tomInput.style.transition = 'none';
					tomInput.classList.add('-focus-', '-invalid-', 'is-invalid');  // is-invalid is a Bootstrap hack
					extraStyles = StyleHelpers.extractStyles(tomInput, [
						'background-color', 'border', 'box-shadow', 'color', 'outline', 'transition'
					]);
					tomInput.classList.remove('-focus-', '-invalid-', 'is-invalid');
					tomInput.style.transition = '';
					break;
				default:
					break;
			}
			if (extraStyles) {
				this.extraStyleSheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`);
			}
		}
		if (!loaded)
			throw new Error(`Could not load styles for ${this.baseSelector}`);
	}

	public initialize() {
		const sheet = this.shadowRoot.styleSheets.item(0)!;
		for (let index = 0; index < this.extraStyleSheet.cssRules.length; index++) {
			const cssRule = this.extraStyleSheet.cssRules.item(index) as CSSStyleRule;
			sheet.insertRule(cssRule.cssText);
		}
		this.setupFilters(this.tomSelect.input as HTMLSelectElement);
		this.tomSelect.on('change', (value: String) => this.validateInput(value));
	}

	private attributesChanged = (mutationsList: Array<MutationRecord>) => {
		for (const mutation of mutationsList) {
			if (mutation.type === 'attributes' && mutation.attributeName === 'disabled') {
				if (this.tomSelect.input.disabled) {
					if (!this.tomSelect.isDisabled) {
						this.tomSelect.disable();
					}
				} else {
					if (this.tomSelect.isDisabled) {
						this.tomSelect.enable();
					}
				}
			}
		}
	}
}

const DS = Symbol('DjangoSelectize');

export class DjangoSelectizeElement extends HTMLSelectElement {
	private [DS]: DjangoSelectize;  // hides internal implementation

	constructor() {
		super();
		this[DS] = new DjangoSelectize(this);
	}

	connectedCallback() {
		this[DS].initialize();
	}
}
