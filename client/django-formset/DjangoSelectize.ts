import TomSelect from 'tom-select/src/tom-select';
import { TomSettings } from 'tom-select/src/types/settings';
import { TomInput } from 'tom-select/src/types';
import TomSelect_remove_button from 'tom-select/src/plugins/remove_button/plugin';
import { escape_html } from 'tom-select/src/utils';
import { IncompleteSelect } from './IncompleteSelect';
import template from 'lodash.template';
import styles from 'sass:./DjangoSelectize.scss';

TomSelect.define('remove_button', TomSelect_remove_button);

type Renderer = {
	[key:string]: (data:any, escape:typeof escape_html) => string | HTMLElement;
}

class DjangoSelectize extends IncompleteSelect {
	private readonly numOptions: number = 12;
	private readonly tomInput: TomInput;
	private readonly tomSelect: TomSelect;
	private readonly shadowRoot: ShadowRoot;
	private readonly observer: MutationObserver;
	private readonly initialValue: string | string[];

	constructor(tomInput: TomInput) {
		super(tomInput);
		const pseudoStylesElement = this.convertPseudoClasses();
		this.tomInput = tomInput;
		// @ts-ignore
		const config: TomSettings = {
			create: false,
			valueField: 'id',
			labelField: 'label',
			maxItems: 1,
			searchField: ['label'],
			render: this.setupRender(tomInput),
			onBlur: () => this.blurred(),
			onChange: () => this.changed(),
			onType: (evt: Event) => this.inputted(evt),
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
		this.observer = new MutationObserver(mutationsList => this.attributesChanged(mutationsList));
		this.observer.observe(this.tomInput, {attributes: true});
		this.initialValue = this.tomSelect.getValue();
		this.shadowRoot = this.wrapInShadowRoot();
		this.transferStyles(tomInput, nativeStyles);
		this.validateInput(this.initialValue as string);
		this.tomSelect.on('change', (value: String) => this.validateInput(value));
		pseudoStylesElement.remove();
	}

	formResetted(event: Event) {
		this.tomSelect.setValue(this.initialValue);
	}

	formSubmitted(event: Event) {}

	private wrapInShadowRoot() : ShadowRoot {
		const shadowWrapper = document.createElement('div');
		shadowWrapper.classList.add('shadow-wrapper');
		const shadowRoot = shadowWrapper.attachShadow({mode: 'open', delegatesFocus: true});
		const shadowStyleElement = document.createElement('style');
		shadowRoot.appendChild(shadowStyleElement).textContent = styles;
		this.tomInput.insertAdjacentElement('afterend', shadowWrapper);
		const wrapper = (this.tomInput.parentElement as HTMLElement).removeChild(this.tomSelect.wrapper);
		shadowRoot.appendChild(wrapper);
		return shadowRoot;
	}

	private blurred() {
		const wrapper = this.shadowRoot.querySelector('.ts-wrapper');
		wrapper?.classList.remove('dirty');
	}

	private changed() {
		this.tomSelect.setTextboxValue('');
		if (this.tomSelect.dropdown_content.childElementCount <= 1) {
			this.tomSelect.close();
		}
	}

	private inputted(event: Event) {
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
		const sheet = this.shadowRoot.styleSheets[0];
		for (let index = 0; index < sheet.cssRules.length; index++) {
			const cssRule = sheet.cssRules.item(index) as CSSStyleRule;
			const lineHeight = window.getComputedStyle(tomInput).getPropertyValue('line-height');
			let extraStyles: string;
			const optionElement = tomInput.querySelector('option');
			switch (cssRule.selectorText) {
				case '.ts-wrapper':
					extraStyles = this.extractStyles(tomInput, [
						'font-family', 'font-size', 'font-strech', 'font-style', 'font-weight',
						'letter-spacing', 'white-space']);
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.ts-wrapper .ts-control':
					extraStyles = this.extractStyles(tomInput, [
						'background-color', 'border', 'border-radius', 'box-shadow', 'color',
						'padding']).concat(`width: ${nativeStyles['width']}; min-height: ${nativeStyles['height']};`);
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.ts-wrapper .ts-control > input':
				case '.ts-wrapper .ts-control > div':
					if (optionElement) {
						extraStyles = this.extractStyles(optionElement, ['padding-left', 'padding-right']);
						sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					}
					break;
				case '.ts-wrapper .ts-control > input::placeholder':
					tomInput.classList.add('-placeholder-');
					extraStyles = this.extractStyles(tomInput, ['background-color', 'color'])
					tomInput.classList.remove('-placeholder-');
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.ts-wrapper.focus .ts-control':
					tomInput.style.transition = 'none';
					tomInput.classList.add('-focus-');
					extraStyles = this.extractStyles(tomInput, [
						'background-color', 'border', 'box-shadow', 'color', 'outline', 'transition'])
					tomInput.classList.remove('-focus-');
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					tomInput.style.transition = '';
					break;
				case '.ts-wrapper.disabled .ts-control':
					tomInput.classList.add('-disabled-');
					extraStyles = this.extractStyles(tomInput, [
							'background-color', 'border', 'box-shadow', 'color', 'opacity', 'outline', 'transition'])
					tomInput.classList.remove('-disabled-');
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.ts-wrapper .ts-dropdown':
					extraStyles = this.extractStyles(tomInput, [
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

	private extractStyles(element: Element, properties: Array<string>): string {
		let styles = Array<string>();
		const style = window.getComputedStyle(element);
		for (let property of properties) {
			styles.push(`${property}:${style.getPropertyValue(property)}`);
		}
		return styles.join('; ').concat('; ');
	}

	private setupRender(tomInput: TomInput) : Renderer {
		const templ = tomInput.parentElement?.querySelector('template.select-no-results');
		return templ ? {
			no_results: (data: any, escape: Function) => template(templ.innerHTML)(data),
		} : {};
	}

	private convertPseudoClasses() : HTMLStyleElement {
		// Iterate over all style sheets, find most pseudo classes and add CSSRules with a
		// CSS selector where the pseudo class has been replaced by a real counterpart.
		// This is required, because browsers can not invoke `window.getComputedStyle(element)`
		// using pseudo classes.
		// With function `removeConvertedClasses()` the added CSSRules are removed again.
		const numStyleSheets = document.styleSheets.length;
		const styleElement = document.createElement('style');
		document.head.appendChild(styleElement);
		for (let index = 0; index < numStyleSheets; index++) {
			const sheet = document.styleSheets[index];
			for (let k = 0; k < sheet.cssRules.length; k++) {
				const cssRule = sheet.cssRules.item(k);
				if (cssRule) {
					this.traverseStyles(cssRule, styleElement.sheet as CSSStyleSheet);
				}
			}
		}
		return styleElement;
	}

	private traverseStyles(cssRule: CSSRule, extraCSSStyleSheet: CSSStyleSheet) {
		if (cssRule instanceof CSSImportRule) {
			if (!cssRule.styleSheet)
				return;
			for (let subRule of cssRule.styleSheet.cssRules) {
				this.traverseStyles(subRule, extraCSSStyleSheet);
			}
		} else if (cssRule instanceof CSSStyleRule) {
			if (!cssRule.selectorText)
				return;
			const newSelectorText = cssRule.selectorText.
				replaceAll(':focus', '.-focus-').
				replaceAll(':focus-visible', '.-focus-visible-').
				replaceAll(':hover', '.-hover-').
				replaceAll(':disabled', '.-disabled-').
				replaceAll(':invalid', '.-invalid-').
				replaceAll(':valid', '.-valid-').
				replaceAll('::placeholder-shown', '.-placeholder-shown').
				replaceAll(':placeholder-shown', '.-placeholder-shown').
				replaceAll('::placeholder', '.-placeholder-').
				replaceAll(':placeholder', '.-placeholder-');
			if (newSelectorText !== cssRule.selectorText) {
				extraCSSStyleSheet.insertRule(`${newSelectorText}{${cssRule.style.cssText}}`);
			}
		} // else handle other CSSRule types
	}

	private attributesChanged(mutationsList: Array<MutationRecord>) {
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

	public get value() : string | string[] {
		return this.tomSelect.getValue();
	}
}

const DS = Symbol('DjangoSelectize');

export class DjangoSelectizeElement extends HTMLSelectElement {
	private [DS]: DjangoSelectize;  // hides internal implementation

	private connectedCallback() {
		this[DS] = new DjangoSelectize(this);
	}

	public async getValue() {
		return this[DS].value;
	}
}
