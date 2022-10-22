import TomSelect from 'tom-select/src/tom-select';
import { TomSettings } from 'tom-select/src/types/settings';
import { RecursivePartial, TomInput, TomTemplates } from 'tom-select/src/types';
import TomSelect_remove_button from 'tom-select/src/plugins/remove_button/plugin';
import { IncompleteSelect } from './IncompleteSelect';
import template from 'lodash.template';
import { StyleHelpers } from './helpers';
import styles from 'sass:./DjangoSelectize.scss';

TomSelect.define('remove_button', TomSelect_remove_button);


class DjangoSelectize extends IncompleteSelect {
	private readonly numOptions: number = 12;
	private readonly tomInput: TomInput;
	private readonly tomSelect: TomSelect;
	private readonly shadowRoot: ShadowRoot;
	private readonly observer: MutationObserver;
	private readonly initialValue: string | string[];

	constructor(tomInput: HTMLSelectElement) {
		super(tomInput);
		this.tomInput = tomInput;
		const config: RecursivePartial<TomSettings> = {
			create: false,
			valueField: 'id',
			labelField: 'label',
			maxItems: 1,
			searchField: ['label'],
			render: this.setupRender(tomInput),
			onFocus: this.touch,
			onBlur: this.blurred,
			onChange: this.changed,
			onType: this.inputted,
		};
		if (this.isIncomplete) {
			config.load = (query: string, callback: Function) => this.loadOptions(`query=${encodeURIComponent(query)}`, callback);
		}
		let isMultiple = false;
		if (tomInput.hasAttribute('multiple')) {
			config.maxItems = parseInt(tomInput.getAttribute('max_items') ?? '3');
			const translation = tomInput.parentElement?.querySelector('template.selectize-remove-item');
			if (translation) {
				config.plugins = {remove_button: {title: translation.innerHTML}};
			}
			// tom-select has some issues to initialize items using the original input element
			const scriptId = `${tomInput.getAttribute('id')}_initial`;
			config.items = JSON.parse(document.getElementById(scriptId)?.textContent ?? '[]');

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
		this.tomSelect = new TomSelect(tomInput, config);
		this.observer = new MutationObserver(this.attributesChanged);
		this.observer.observe(this.tomInput, {attributes: true});
		this.initialValue = this.tomSelect.getValue();
		this.shadowRoot = this.wrapInShadowRoot();
		this.transferStyles(tomInput, nativeStyles);
		tomInput.classList.add('dj-concealed');
		this.validateInput(this.initialValue as string);
		this.tomSelect.on('change', (value: String) => this.validateInput(value));
	}

	protected formResetted(event: Event) {
		this.tomSelect.setValue(this.initialValue);
	}

	protected formSubmitted(event: Event) {}

	private wrapInShadowRoot() : ShadowRoot {
		const shadowWrapper = document.createElement('div');
		shadowWrapper.classList.add('shadow-wrapper');
		const shadowRoot = shadowWrapper.attachShadow({mode: 'open', delegatesFocus: true});
		const shadowStyleElement = document.createElement('style');
		shadowRoot.appendChild(shadowStyleElement).textContent = styles;
		this.tomInput.insertAdjacentElement('beforebegin', shadowWrapper);
		const wrapper = (this.tomInput.parentElement as HTMLElement).removeChild(this.tomSelect.wrapper);
		shadowRoot.appendChild(wrapper);
		return shadowRoot;
	}

	private blurred = () => {
		const wrapper = this.shadowRoot.querySelector('.ts-wrapper');
		wrapper?.classList.remove('dirty');
	}

	private changed = () => {
		this.tomSelect.setTextboxValue('');
		if (this.tomSelect.dropdown_content.childElementCount <= 1) {
			this.tomSelect.close();
		}
	}

	private inputted = (event: Event) => {
		const value = event as unknown as string;
		const wrapper = this.shadowRoot.querySelector('.ts-wrapper');
		wrapper?.classList.toggle('dirty', value.length > 0);
	}

	private validateInput(value: String | Array<string>) {
		const wrapper = this.shadowRoot.querySelector('.ts-wrapper');
		wrapper?.classList.remove('dirty');
		const selectElem = this.tomInput as HTMLSelectElement;
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
			this.tomInput.value = value as string;
		}
	}

	private transferStyles(tomInput: HTMLElement, nativeStyles: CSSStyleDeclaration) {
		const wrapperStyle = (this.shadowRoot.host as HTMLElement).style;
		wrapperStyle.setProperty('display', nativeStyles.display);
		const lineHeight = window.getComputedStyle(tomInput).getPropertyValue('line-height');
		const optionElement = tomInput.querySelector('option');
		const sheet = this.shadowRoot.styleSheets.item(0);
		for (let index = 0; sheet && index < sheet.cssRules.length; index++) {
			const cssRule = sheet.cssRules.item(index) as CSSStyleRule;
			let extraStyles: string;
			switch (cssRule.selectorText) {
				case '.ts-wrapper':
					extraStyles = StyleHelpers.extractStyles(tomInput, [
						'font-family', 'font-size', 'font-strech', 'font-style', 'font-weight',
						'letter-spacing', 'white-space']);
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.ts-wrapper .ts-control':
					extraStyles = StyleHelpers.extractStyles(tomInput, [
						'background-color', 'border', 'border-radius', 'box-shadow', 'color',
						'padding']).concat(`width: ${nativeStyles['width']}; min-height: ${nativeStyles['height']};`);
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.ts-wrapper .ts-control > input':
				case '.ts-wrapper .ts-control > div':
					if (optionElement) {
						extraStyles = StyleHelpers.extractStyles(optionElement, ['padding-left', 'padding-right']);
						sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					}
					break;
				case '.ts-wrapper .ts-control > input::placeholder':
					tomInput.classList.add('-placeholder-');
					extraStyles = StyleHelpers.extractStyles(tomInput, ['background-color', 'color'])
					tomInput.classList.remove('-placeholder-');
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.ts-wrapper.focus .ts-control':
					tomInput.style.transition = 'none';
					tomInput.classList.add('-focus-');
					extraStyles = StyleHelpers.extractStyles(tomInput, [
						'background-color', 'border', 'box-shadow', 'color', 'outline', 'transition'])
					tomInput.classList.remove('-focus-');
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					tomInput.style.transition = '';
					break;
				case '.ts-wrapper.disabled .ts-control':
					tomInput.classList.add('-disabled-');
					extraStyles = StyleHelpers.extractStyles(tomInput, [
							'background-color', 'border', 'box-shadow', 'color', 'opacity', 'outline', 'transition'])
					tomInput.classList.remove('-disabled-');
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.ts-wrapper .ts-dropdown':
					extraStyles = StyleHelpers.extractStyles(tomInput, [
						'border-right', 'border-bottom', 'border-left', 'color', 'padding-left'])
						.concat(parseFloat(lineHeight) > 0 ? `line-height: calc(${lineHeight} * 1.2);` : 'line-height: 1.2em;');
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.ts-wrapper .ts-dropdown .ts-dropdown-content':
					if (parseFloat(lineHeight) > 0) {
						extraStyles =  `max-height: calc(${lineHeight} * 1.2 * ${this.numOptions});`;
					} else {
						extraStyles =  `max-height: ${this.numOptions * 1.2}em;`;
					}
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				default:
					break;
			}
		}
	}

	private setupRender(tomInput: TomInput) : TomTemplates {
		const templ = tomInput.parentElement?.querySelector('template.select-no-results');
		if (!templ)
			return {} as TomTemplates;
		return {
			no_results: (data, escape) => template(templ.innerHTML)(data)
		} as TomTemplates;
	}

	private attributesChanged = (mutationsList: Array<MutationRecord>) => {
		for (const mutation of mutationsList) {
			if (mutation.type === 'attributes' && mutation.attributeName === 'disabled') {
				if (this.tomInput.disabled) {
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

	public getValue() : string | string[] {
		return this.tomSelect.getValue();
	}
}

const DS = Symbol('DjangoSelectize');

export class DjangoSelectizeElement extends HTMLSelectElement {
	private [DS]?: DjangoSelectize;  // hides internal implementation

	private connectedCallback() {
		this[DS] = new DjangoSelectize(this);
	}

	public async getValue() {
		return this[DS]?.getValue();
	}
}
