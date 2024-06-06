import TomSelect from 'tom-select/src/tom-select';
import {TomSettings} from 'tom-select/src/types/settings';
import {RecursivePartial, TomOption} from 'tom-select/src/types';
import TomSelect_remove_button from 'tom-select/src/plugins/remove_button/plugin';
import template from 'lodash.template';
import {IncompleteSelect} from 'django-formset/IncompleteSelect';
import {StyleHelpers} from 'django-formset/helpers';
import styles from './DjangoSelectize.scss';

TomSelect.define('remove_button', TomSelect_remove_button);


export class DjangoSelectize extends IncompleteSelect {
	protected readonly shadowRoot: ShadowRoot;
	private static styleSheet: CSSStyleSheet|null = null;
	private readonly numOptions: number = 12;
	public readonly tomSelect: TomSelect;
	private readonly observer: MutationObserver;
	private readonly initialValue: string|string[] = '';
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
		DjangoSelectize.styleSheet = DjangoSelectize.styleSheet ?? this.transferStyles(nativeStyles);
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

	private load = (search: string, callback: Function) => {
		this.loadOptions(this.buildFetchQuery(0, {search}), (options: Array<OptionData>) => {
			callback(options, this.extractOptGroups(options));
		});
	};

	private blurred = () => {
		const wrapper = this.shadowRoot.querySelector(this.baseSelector);
		wrapper?.classList.remove('dirty');
	};

	private inputted = (event: Event) => {
		const value = event as unknown as string;
		const wrapper = this.shadowRoot.querySelector(this.baseSelector);
		wrapper?.classList.toggle('dirty', value.length > 0);
	};

	private validateInput(value: String | Array<string>) {
		const wrapper = this.shadowRoot.querySelector(this.baseSelector);
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
		shadowRoot.adoptedStyleSheets = [new CSSStyleSheet()];
		this.tomSelect.input.insertAdjacentElement('beforebegin', shadowWrapper);
		const wrapper = (this.tomSelect.input.parentElement as HTMLElement).removeChild(this.tomSelect.wrapper);
		shadowRoot.appendChild(wrapper);
		return shadowRoot;
	}

	private transferStyles(nativeStyles: CSSStyleDeclaration) : CSSStyleSheet {
		const wrapperStyle = (this.shadowRoot.host as HTMLElement).style;
		wrapperStyle.setProperty('display', nativeStyles.display);
		const sheet = new CSSStyleSheet();
		sheet.replaceSync(styles);
		const tomInput = this.tomSelect.input;
		const lineHeight = window.getComputedStyle(tomInput).getPropertyValue('line-height');
		const optionElement = tomInput.querySelector('option');
		const displayNumOptions = Math.min(Math.max(this.numOptions, 8), 25);
		let loaded = false;
		for (let index = 0; sheet && index < sheet.cssRules.length; index++) {
			const cssRule = sheet.cssRules.item(index) as CSSStyleRule;
			let extraStyles: string | null = null;
			switch (cssRule.selectorText.trim()) {
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
						`min-height: ${nativeStyles['height']};`
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
				sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
			}
		}
		if (!loaded)
			throw new Error(`Could not load styles for ${this.baseSelector}`);
		return sheet;
	}

	public initialize() {
		const sheet = this.shadowRoot.adoptedStyleSheets[0];
		const controlStyleStlector = `${this.baseSelector} .ts-control`;
		if (!DjangoSelectize.styleSheet)
			throw new Error('Stylesheet not loaded');
		for (let index = 0; index < DjangoSelectize.styleSheet.cssRules.length; index++) {
			const cssRule = DjangoSelectize.styleSheet.cssRules.item(index) as CSSStyleRule;
			sheet.insertRule(cssRule.cssText);
		}

		const currentWidth = () => window.getComputedStyle(this.tomSelect.input).getPropertyValue('width');
		const widthRuleIndex = sheet.insertRule(`${controlStyleStlector}{width:${currentWidth()};}`);
		addEventListener('resize', (event) => {
			sheet.deleteRule(widthRuleIndex);
			sheet.insertRule(`${controlStyleStlector}{width:${currentWidth()};}`, widthRuleIndex);
		});
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
	};

	public setValue(value: string|number) {
		const emitChangeEvent = () => this.tomSelect.input.dispatchEvent(new Event('change', {bubbles: true}));

		if (typeof value === 'number') {
			// if the value is a number, enforce re-fetching object from the server
			this.loadOptions(this.buildFetchQuery(0, {pk: value.toString()}), (options: Array<OptionData>) => {
				if (this.tomSelect.getValue() === value.toString()) {
					// object already loaded by tom-select
					this.tomSelect.updateOption(value.toString(), options[0]);
				} else {
					// object must be added to tom-select
					this.tomSelect.addOptions(options);
				}
			}).then(() => {
				this.tomSelect.setValue(value.toString(), true);
				emitChangeEvent();
			});
		} else {
			this.tomSelect.setValue(value, true);
			emitChangeEvent();
		}
	}

	public setValues(values: Array<string>) {
		this.tomSelect.setValue(values, true);
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

	get value() {
		const value = this[DS]?.tomSelect.getValue();
	 	return Array.isArray(value) ? value.join(',') : value;
	}

	set value(val: any) {
		if (this.multiple) {
			if (typeof val === 'string') {
				this[DS]?.setValues(val.split(','));
			} else if (Array.isArray(val)) {
				this[DS]?.setValues(val);
			}
		} else {
			if (typeof val === 'string' || typeof val === 'number') {
				this[DS]?.setValue(val);
			}
		}
	}
}
