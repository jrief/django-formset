import isFinite from 'lodash.isfinite';
import isString from 'lodash.isstring';
import TomSelect from 'tom-select';
import {RecursivePartial, TomSettings} from 'tom-select/src/types';
import {IncompleteSelect} from './IncompleteSelect';
import {StyleHelpers} from './helpers';
import wrapperStyles from './DjangoSelectizeWrapper.scss';
import shadowStyles from './DjangoSelectizeShadow.scss';


export class DjangoSelectize extends IncompleteSelect {
	protected readonly shadowRoot: ShadowRoot;
	private static styleSheet: CSSStyleSheet = new CSSStyleSheet();
	private readonly nativeStyles: CSSStyleDeclaration;
	private readonly numOptions: number = 12;
	public readonly tomSelect: TomSelect;
	private readonly observer: MutationObserver;
	private readonly initialValues: string[] = [];
	private readonly baseSelector = '.ts-wrapper';
	private readonly wrapperSelector = '[is="django-selectize"] + .shadow-wrapper';
	private readonly shadowWrapper: HTMLElement;
	private readonly uniqueIdentifier: string;

	constructor(tomInput: HTMLSelectElement) {
		super(tomInput);
		let isMultiple = false;
		if (tomInput.hasAttribute('multiple')) {
			// We want to use the CSS styles for <select> without multiple
			tomInput.removeAttribute('multiple');
			isMultiple = true;
		}
		this.nativeStyles = {...window.getComputedStyle(tomInput)} as CSSStyleDeclaration;
		const nativeClasses = [...tomInput.classList];
		if (isMultiple) {
			// revert the above
			tomInput.setAttribute('multiple', 'multiple');
		}
		this.numOptions = parseInt(tomInput.getAttribute('options') ?? this.numOptions.toString());
		this.initialValues = this.getInitialValues(tomInput);
		this.tomSelect = new TomSelect(tomInput, this.getSettings(tomInput));
		this.tomSelect.wrapper.classList.remove(...nativeClasses);
		this.observer = new MutationObserver(this.attributesChanged);
		this.observer.observe(tomInput, {attributes: true});
		this.uniqueIdentifier = `ds-${Math.random().toString(36).substring(2, 15)}`;
		this.shadowRoot = this.wrapInShadowRoot();
		if (!(tomInput.nextElementSibling instanceof HTMLElement))
			throw new Error('<select is="django-selectize" requires a sibling to wrap the shadow root');
		this.shadowWrapper = tomInput.nextElementSibling;
		this.shadowWrapper.classList.add(...nativeClasses);
		if (nativeClasses.length === 0) {
			// Bulma and Unstyled do not set a CSS class. At least set the min-width of the select element.
			this.shadowWrapper.style.setProperty('min-width', this.nativeStyles.width);
		}
		if (!StyleHelpers.stylesAreInstalled(this.wrapperSelector)) {
			this.applyWrapperStyles();
		}
		this.transferStyles();
		this.appendIndividualStyleSheet();
		tomInput.classList.add('dj-concealed');
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
			plugins: {},
			onFocus: this.focused,
			onBlur: this.blurred,
			onType: this.inputted,
			onChange: this.changed,
			onItemRemove: this.itemRemoved,
			render: {
				no_results: `<div class="no-results">${gettext("No results found for '${input}'")}</div>`,
			}
		};
		if (this.isIncomplete) {
			settings.load = this.load;
		}
		if (tomInput.hasAttribute('multiple')) {
			settings.maxItems = parseInt(tomInput.getAttribute('max_items') ?? '3');
			settings.plugins = {...settings.plugins, remove_button: {title: gettext("Remove item")}};
		}
		return settings;
	}

	private getInitialValues(tomInput: HTMLSelectElement): string[] {
		const scriptId = `${tomInput.getAttribute('id')}_initial`;
		return JSON.parse(document.getElementById(scriptId)?.textContent ?? '[]');
	}

	protected getValue = () : string|string[] => this.initialValues;

	protected async formResetted(event: Event) {
		this.getValue = () => this.initialValues;
		this.tomSelect.setValue(this.initialValues, true);
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

	private get currentValue(): string|string[] {
		const currentValue = this.tomSelect.getValue();
		// make a deep copy because TomSelect mutates the array
		return Array.isArray(currentValue) ? [...currentValue] : currentValue;
	}

	private extractOptGroups(options: Array<OptionData>) {
		const groupnames = new Set<string>();
		options.forEach(o => {
			if (isString(o.optgroup)) {
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

	private focused = () => {
		this.shadowWrapper.classList.add('focus');
		this.tomSelect.input.dispatchEvent(new Event('focusin'));
	};

	private blurred = () => {
		this.tomSelect.input.dispatchEvent(new Event('focusout'));
		this.shadowWrapper.classList.remove('focus');
	};

	private inputted = (value: string|string[]) => {
		const wrapper = this.shadowRoot.querySelector(this.baseSelector);
		wrapper?.classList.toggle('dirty', value.length > 0);
	};

	private changed = (value: string|string[]) => {
		this.tomSelect.input.dispatchEvent(new Event('change'));
	};

	private itemRemoved = (value: string|string[]) => {
		this.tomSelect.input.dispatchEvent(new Event('focusin'));
		this.tomSelect.input.dispatchEvent(new Event('focusout'));
	};

	private wrapInShadowRoot() : ShadowRoot {
		const group = this.tomSelect.input.parentElement;
		if (!(group instanceof HTMLElement))
			throw new Error("Could not find parent element");
		group.classList.add(this.uniqueIdentifier);  // see appendIndividualStyleSheet() for usage of this CSS class
		const shadowWrapper = document.createElement('div');
		shadowWrapper.classList.add('shadow-wrapper');
		const shadowRoot = shadowWrapper.attachShadow({mode: 'open', delegatesFocus: true});
		shadowRoot.adoptedStyleSheets = [new CSSStyleSheet()];
		this.tomSelect.input.insertAdjacentElement('afterend', shadowWrapper);
		const wrapper = group.removeChild(this.tomSelect.wrapper);
		shadowRoot.appendChild(wrapper);
		return shadowRoot;
	}

	private applyWrapperStyles() {
		const declaredStyles = document.createElement('style');
		declaredStyles.innerText = wrapperStyles;
		document.head.appendChild(declaredStyles);
		if (!declaredStyles.sheet)
			throw new Error("Could not create <style> element");
	}

	private transferStyles() {
		const sheet = DjangoSelectize.styleSheet;
		const wrapperStyle = (this.shadowRoot.host as HTMLElement).style;
		wrapperStyle.setProperty('display', this.nativeStyles.display);
		sheet.replaceSync(shadowStyles);
		const tomInput = this.tomSelect.input;
		const lineHeight = window.getComputedStyle(tomInput).getPropertyValue('line-height');
		const optionElement = tomInput.querySelector('option');
		const displayNumOptions = Math.min(Math.max(this.numOptions, 8), 25);
		let loaded = false;
		for (let index = 0; sheet && index < sheet.cssRules.length; index++) {
			const cssRule = sheet.cssRules.item(index) as CSSStyleRule;
			const selectorText = cssRule.selectorText.trim();
			let extraStyles: string|null = null;
			switch (selectorText) {
				case this.baseSelector:
					extraStyles = StyleHelpers.extractStyles(tomInput, [
						'font-family', 'font-size', 'font-stretch', 'font-style', 'font-weight',
						'letter-spacing', 'white-space'
					]).concat(StyleHelpers.extractStyles(tomInput, {
						'--border-style': 'border-style',
						'--border-width': 'border-width',
						'--border-radius': 'border-radius',
					}));
					loaded = true;
					break;
				case `${this.baseSelector} .ts-control`:
					extraStyles = StyleHelpers.extractStyles(tomInput, [
						'padding', 'transition'
					]).concat(
						`min-height: ${this.nativeStyles['height']};`,
					);
					break;
				case `${this.baseSelector} .ts-control > input`:
				case `${this.baseSelector} .ts-control > div`:
					if (optionElement) {
						extraStyles = StyleHelpers.extractStyles(optionElement, ['padding-left', 'padding-right']);
					}
					break;
				case `${this.baseSelector} .ts-dropdown`:
					extraStyles = parseFloat(lineHeight) > 0 ? `line-height: calc(${lineHeight} * 1.2);` : 'line-height: 1.4em;';
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
					tomInput.classList.add('⁝focus', '⁝invalid', 'is-invalid');  // is-invalid is a Bootstrap hack
					extraStyles = StyleHelpers.extractStyles(tomInput, [
						'background-color', 'border-color', 'box-shadow', 'color', 'outline', 'transition'
					]);
					tomInput.classList.remove('⁝focus', '⁝invalid', 'is-invalid');
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
	}

	private appendIndividualStyleSheet() {
		// `:host-context()` does not work with `:has()` or other complex selectors. Therefore, it is impossible to
		// use it as a selector for the shadow-root of this individual component. To apply styles to this shadow-root's
		// instance, depending on context of the host element, we use a unique CSS class. This class is added during
		// initialization to the wrapping element of the shadow-root, see `wrapInShadowRoot()`.
		// Here we replace the `:host-context()`-selectors with that individual class.
		const sheet = DjangoSelectize.styleSheet;
		const individualSheet = new CSSStyleSheet();
		for (let index = 0; sheet && index < sheet.cssRules.length; index++) {
			const cssRule = sheet.cssRules.item(index) as CSSStyleRule;
			const selectorText = cssRule.selectorText.trim();
			switch (selectorText) {
				case ':host-context([role="group"].dj-touched.ds-unique-identifier) .ts-wrapper:not(.invalid).has-items:not(.input-active) .ts-control':
				case ':host-context([role="group"].dj-touched.ds-unique-identifier) .ts-wrapper.invalid:not(.input-active) .ts-control':
					individualSheet.insertRule(cssRule.cssText.replace('.ds-unique-identifier', `.${this.uniqueIdentifier}`));
					break;
				default:
					break;
			}
		}
		this.shadowRoot.adoptedStyleSheets.push(individualSheet);
	}

	public async initialize() {
		// this function is called whenever an instance of <django-selectize> is added to the DOM
		const sheet = this.shadowRoot.adoptedStyleSheets[0];
		if (!DjangoSelectize.styleSheet)
			throw new Error('Stylesheet not loaded');

		// transfer static styles to the <style> element in the shadow root
		for (let index = 0; index < DjangoSelectize.styleSheet.cssRules.length; index++) {
			const cssRule = DjangoSelectize.styleSheet.cssRules.item(index) as CSSStyleRule;
			sheet.insertRule(cssRule.cssText);
		}

		const tomInput = this.tomSelect.input as HTMLSelectElement;

		// some styles change when switching light/dark mode, so we need to update them
		StyleHelpers.pushMediaQueryStyles(
			sheet,
			this.baseSelector, {
				'--border-color': 'border-color',
				'color': 'color',
			},
			tomInput
		);
		StyleHelpers.pushMediaQueryStyles(
			sheet,
			`${this.baseSelector}.focus .ts-control`, {
				'box-shadow': 'box-shadow',
				'border-color': 'border-color',
				'outline': 'outline',
			},
			tomInput, '⁝focus'
		);
		StyleHelpers.pushMediaQueryStyles(
			sheet,
			`${this.baseSelector}.disabled .ts-control`, {
				'background-color': 'background-color',
				'border-color': 'border-color',
				'color': 'color',
				'outline': 'outline',
			},
			tomInput, '⁝disabled'
		);
		this.setupFilters(tomInput);
		if (this.mustReloadOptions()) {
			await this.reloadOptions();
		} else {
			this.tomSelect.setValue(this.initialValues, true);
		}

		this.getValue = () => this.currentValue;

		// The built-in HTML select element can receive focus, but does not open the dropdown.
		// Make TomSelect behave the same way.
		this.tomSelect.input.addEventListener('focus', () => {
			this.tomSelect.wrapper.classList.add('focus')
		});
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

		if (isFinite(value)) {
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
		} else if (isString(value)) {
			this.tomSelect.setValue(value, true);
			emitChangeEvent();
		}
	}

	public setValues(values: string[]) {
		this.tomSelect.setValue(values, true);
	}
}

const DS = Symbol('DjangoSelectize');

export class DjangoSelectizeElement extends HTMLSelectElement {
	private [DS]?: DjangoSelectize;  // hides internal implementation

	constructor() {
		super();
		if (this.form) {
			this[DS] = new DjangoSelectize(this);
		}
	}

	connectedCallback() {
		this[DS]?.initialize();
	}

	get value() {
		const value = this[DS]?.tomSelect.getValue();
	 	return Array.isArray(value) ? value.join(',') : value;
	}

	set value(val: any) {
		if (this.multiple) {
			if (isString(val)) {
				this[DS]?.setValues(val.split(','));
			} else if (Array.isArray(val)) {
				this[DS]?.setValues(val);
			}
		} else {
			if (isString(val) || isFinite(val)) {
				this[DS]?.setValue(val);
			}
		}
	}
}
