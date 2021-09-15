import TomSelect from 'tom-select/src/tom-select';
import { TomSettings } from 'tom-select/src/types/settings';
import { TomInput } from 'tom-select/src/types';
import template from 'lodash.template';

const shadowStyleElement = document.createElement('style');
import styles from 'sass:./DjangoSelectize.scss';
import {escape_html} from "tom-select/src/utils";
shadowStyleElement.textContent = styles;


type Renderer = {
	[key:string]: (data:any, escape:typeof escape_html) => string|HTMLElement
}

class DjangoSelectize {
	private readonly endpoint?: string;
	private readonly fieldName?: string;
	private readonly numOptions: number = 12;
	private readonly tomInput: TomInput;
	private readonly tomSelect: TomSelect;
	private readonly shadowRoot: ShadowRoot;
	private readonly extraCSSRules: Array<[number, number]> = [];

	constructor(tomInput: TomInput) {
		this.convertPseudoClasses();
		this.tomInput = tomInput;
		const fieldGroup = tomInput.closest('django-field-group');
		const form = tomInput.closest('form');
		const formset = tomInput.closest('django-formset');
		if (!fieldGroup || !form || !formset)
			throw new Error("Attempt to initialize <django-selectize> outside <django-formset>")
		// @ts-ignore
		const config: TomSettings = {
			create: false,
			valueField: 'id',
			labelField: 'label',
			searchField: ['label'],
			render: this.setupRender(tomInput),
		};
		if (!tomInput.getAttribute('multiple')) {
			config.maxItems = 1;
		}
		if (tomInput.hasAttribute('uncomplete')) {
			// select fields marked as "uncomplete" will fetch additional data from their backend
			const formName = form.getAttribute('name') || '__default__';
			this.endpoint = formset.getAttribute('endpoint') || '';
			this.fieldName = `${formName}.${tomInput.getAttribute('name')}`;
			config.load = (query: string, callback: Function) => this.loadOptions(query, callback);
		}
		const numOptions = tomInput.getAttribute('options');
		if (numOptions) {
			this.numOptions = parseInt(numOptions);
		}
		const nativeStyles = {...window.getComputedStyle(tomInput)} as CSSStyleDeclaration;

		this.tomSelect = new TomSelect(tomInput, config);
		this.shadowRoot = this.wrapInShadowRoot();
		this.transferStyles(tomInput as unknown as HTMLElement, nativeStyles);
		this.validateInput(this.tomSelect.getValue() as String);
		this.tomSelect.on('change', (value: String) => this.validateInput(value));
		this.removeConvertedClasses();
	}

	private wrapInShadowRoot() : ShadowRoot {
		const shadowWrapper = document.createElement('div');
		shadowWrapper.classList.add('shadow-wrapper');
		const shadowRoot = shadowWrapper.attachShadow({mode: 'open', delegatesFocus: true});
		shadowRoot.appendChild(shadowStyleElement);
		this.tomInput.insertAdjacentElement('afterend', shadowWrapper);
		const wrapper = (this.tomInput.parentElement as HTMLElement).removeChild(this.tomSelect.wrapper);
		shadowRoot.appendChild(wrapper);
		return shadowRoot;
	}

	private validateInput(value: String) {
		if (this.tomSelect.isRequired && !value) {
			this.tomInput.setCustomValidity("Value is missing.");
		}
	}

	private transferStyles(tomInput: HTMLElement, nativeStyles: CSSStyleDeclaration) {
		const wrapperStyle = (this.shadowRoot.host as HTMLElement).style;
		wrapperStyle.setProperty('display', nativeStyles.display);
		const sheet = shadowStyleElement.sheet as CSSStyleSheet;
		for (let index = 0; index < sheet.cssRules.length; index++) {
			const cssRule = sheet.cssRules.item(index) as CSSStyleRule;
			console.log(cssRule.selectorText);
			const lineHeight = window.getComputedStyle(tomInput).getPropertyValue('line-height');
			let extraStyles: string;
			const optionElement = tomInput.querySelector('option');
			switch (cssRule.selectorText) {
				case '.ts-control':
					extraStyles = this.extractStyles(tomInput, [
						'font-family', 'font-size', 'font-strech', 'font-style', 'font-weight',
						'letter-spacing', 'white-space']);
					console.log(extraStyles);
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.ts-control .ts-input':
					extraStyles = this.extractStyles(tomInput, [
						'background-color', 'border', 'border-radius', 'box-shadow', 'color',
						'padding']).concat(`width: ${nativeStyles['width']}; height: ${nativeStyles['height']};`);
					console.log(extraStyles);
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.ts-control .ts-input > input':
				case '.ts-control .ts-input > div':
					extraStyles = this.extractStyles(tomInput, ['line-height']);
					if (optionElement) {
						extraStyles = extraStyles.concat(this.extractStyles(optionElement, ['padding-left']));
					}
					console.log(extraStyles);
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.ts-control .ts-input > input::placeholder':
					tomInput.classList.add('-placeholder-');
					extraStyles = this.extractStyles(tomInput, ['background-color', 'color'])
					console.log(extraStyles);
					tomInput.classList.remove('-placeholder-');
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.ts-control .ts-input.focus':
					tomInput.classList.add('-focus-');
					extraStyles = this.extractStyles(tomInput, [
							'background-color', 'border', 'box-shadow', 'color', 'outline', 'transition'])
					console.log(extraStyles);
					tomInput.classList.remove('-focus-');
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.ts-control .ts-input.has-items':
					extraStyles = 'border-color: var(--django-formset-color-valid);'
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.ts-control .ts-dropdown':
					extraStyles = this.extractStyles(tomInput, [
						'border-right', 'border-bottom', 'border-left', 'color', 'padding-left'])
						.concat(parseFloat(lineHeight) > 0 ? `line-height: calc(${lineHeight} * 1.2);` : 'line-height: 1.2em;');
					console.log(extraStyles);
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.ts-control .ts-dropdown .ts-dropdown-content':
					if (parseFloat(lineHeight) > 0) {
						extraStyles =  `max-height: calc(${lineHeight} * 1.2 * ${this.numOptions});`;
					} else {
						extraStyles =  `max-height: ${this.numOptions * 1.2}em;`;
					}
					console.log(extraStyles);
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

	private setupRender(tomInput: TomInput): Renderer {
		const templ = tomInput.parentElement ? tomInput.parentElement.querySelector('template.selectize-no-results') : null;
		if (!templ)
			return {};
		return {
			no_results: (data: any, escape: Function) => template(templ.innerHTML)(data),
		};
	}

	private async loadOptions(query: string, callback: Function) {
		const headers = new Headers();
		headers.append('Accept', 'application/json');
		const csrfToken = this.CSRFToken;
		if (csrfToken) {
			headers.append('X-CSRFToken', csrfToken);
		}
		const url = `${this.endpoint}?field=${this.fieldName}&query=${encodeURIComponent(query)}`;
		const response = await fetch(url, {
			method: 'GET',
			headers: headers,
		});
		if (response.status === 200) {
			response.json().then(data => {
				callback(data.items);
			});
		} else {
			console.error(`Failed to fetch from ${url}`);
		}
	}

	private get CSRFToken(): string | undefined {
		const value = `; ${document.cookie}`;
		const parts = value.split('; csrftoken=');

		if (parts.length === 2) {
			return parts[1].split(';').shift();
		}
	}

	private convertPseudoClasses() {
		// Iterate over all style sheets, find most pseudo classes and add CSSRules with a
		// CSS selector where the pseudo class has been replaced by a real counterpart.
		// This is required, because browsers can not invoke `window.getComputedStyle(element)`
		// using pseudo classes.
		// With function `removeConvertedClasses()` the added CSSRules are removed again.
		for (let index = 0; index < document.styleSheets.length; index++) {
			const sheet = document.styleSheets[index];
			for (let k = 0; k < sheet.cssRules.length; k++) {
				const cssRule = sheet.cssRules.item(k) as CSSStyleRule;
				if (!cssRule.selectorText)
					continue;
				const newSelectorText = cssRule.selectorText.
					replaceAll(':focus', '.-focus-').
					replaceAll(':focus-visible', '.-focus-visible-').
					replaceAll(':hover', '.-hover-').
					replaceAll(':invalid', '.-invalid-').
					replaceAll(':valid', '.-valid-').
					replaceAll('::placeholder-shown', '.-placeholder-shown').
					replaceAll(':placeholder-shown', '.-placeholder-shown').
					replaceAll('::placeholder', '.-placeholder-').
					replaceAll(':placeholder', '.-placeholder-');
				if (newSelectorText !== cssRule.selectorText) {
					sheet.insertRule(`${newSelectorText}{${cssRule.style.cssText}}`, ++k);
					this.extraCSSRules.push([index, k]);
				}
			}
		}
	}

	private removeConvertedClasses() {
		// Remove the converted pseudo classes as added by `convertPseudoClasses()`
		// resetting all stylesheets into their starting point.
		for (let [index, k] of this.extraCSSRules.reverse()) {
			document.styleSheets[index].deleteRule(k);
		}
		this.extraCSSRules.splice(0);
	}
}

const DS = Symbol('DjangoSelectize');

export class DjangoSelectizeElement extends HTMLSelectElement {
	private [DS]: DjangoSelectize;  // hides internal implementation

	private connectedCallback() {
		this[DS] = new DjangoSelectize(this as unknown as TomInput);
	}
}
