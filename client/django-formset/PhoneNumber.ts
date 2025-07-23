import {autoUpdate, computePosition, flip, shift} from '@floating-ui/dom';
import {AsYouType, CountryCode, CountryCallingCode, getCountries, getCountryCallingCode} from 'libphonenumber-js/max';
import {StyleHelpers} from './helpers';
import {countries} from './countries';
import styles from './PhoneNumber.scss';


class PhoneNumberField {
	private readonly inputElement: HTMLInputElement;
	private readonly textBox: HTMLElement;
	private readonly editField: HTMLElement;
	private readonly baseSelector = '[is="django-phone-number"]';
	private readonly styleSheet: CSSStyleSheet;
	private hasFocus = false;
	private readonly defaultCountryCode?: CountryCode;
	private readonly mobileOnly: boolean;
	private readonly asYouType: AsYouType;
	private readonly internationalOpener: HTMLElement;
	private readonly internationalSelector: HTMLElement;
	private readonly countryLookupField: HTMLInputElement;
	private readonly codeCountryMap: [string, CountryCallingCode, CountryCode][];
	private isOpen = false;
	private cleanup = () => {};

	constructor(element: HTMLInputElement) {
		this.inputElement = element;
		this.codeCountryMap = this.createCountriesMap();
		const compare = new Intl.Collator(document.documentElement.lang ?? 'en').compare;
		this.codeCountryMap = this.codeCountryMap.sort(
			(a, b) => compare(a[0], b[0])
		);
		const countryCode = element.getAttribute('default-country-code') as CountryCode | undefined;
		this.defaultCountryCode = countryCode ? countryCode.toUpperCase() as CountryCode : undefined;
		this.mobileOnly = element.hasAttribute('mobile-only');
		this.asYouType = new AsYouType(this.defaultCountryCode);
		this.textBox = this.createTextBox();
		this.editField = this.textBox.querySelector('.phone-number-edit') as HTMLElement;
		this.internationalOpener = this.textBox.querySelector('.international-picker') as HTMLElement;
		this.internationalSelector = this.textBox.nextElementSibling as HTMLElement;
		this.countryLookupField = this.internationalSelector.querySelector('input[type="search"]') as HTMLInputElement;
		StyleHelpers.addSpriteFlags(document.head);
		this.styleSheet = StyleHelpers.stylesAreInstalled(this.baseSelector) ?? this.transferStyles();
		this.transferClasses();
	}

	private createCountriesMap() : [string, CountryCallingCode, CountryCode][] {
		return getCountries().map(
			countryCode => [gettext(countries.get(countryCode) ?? ''), getCountryCallingCode(countryCode), countryCode]
		);
	}

	private createTextBox() {
		const htmlTags = [
			'<div role="textbox" aria-expanded="false" aria-haspopup="dialog">',
			'<div class="international-picker"></div>',
			'<div class="phone-number-edit" contenteditable="true"></div>',
			'</div>',
			'<div role="dialog" aria-modal="true">',
			`<input type="search" placeholder="${gettext('Search …')}">`,
			'<ul>',
		];
		for (let [countryName, callingCode, countryCode] of this.codeCountryMap) {
			htmlTags.push(`<li data-country="${countryCode}" data-calling-code="${callingCode}">`);
			htmlTags.push(`<span class="flag-${countryCode.toLowerCase()} flag-icon"></span>${countryName} <strong>+${callingCode}</strong>`);
			htmlTags.push('</li>');
		}
		htmlTags.push('</div>');
		this.inputElement.insertAdjacentHTML('afterend', htmlTags.join(''));
		return this.inputElement.nextElementSibling as HTMLElement;
	}

	private formResetted = (event: Event) => {
		this.inputElement.value = this.inputElement.defaultValue;
	};

	private handleFocus = (event: Event) => {
		if (this.editField !== event.target)
			return;
		this.editField.ariaBusy = 'true';
		this.textBox.classList.add('focus');
		this.inputElement.dispatchEvent(new Event('focus'));
		event.preventDefault();
		this.hasFocus = true;
	};

	private setCaretToEnd() {
		const textNode = this.editField.childNodes[0] as Text;
		if (!textNode)
			return;
		const range = document.createRange();
		range.setStart(textNode, textNode.length);
		range.collapse(true);
		const selection = window.getSelection()!;
		selection.removeAllRanges();
		selection.addRange(range);
	}

	private handleInput = (event: Event) => {
		if (event.target instanceof HTMLElement && this.editField === event.target) {
			this.updateInputField(this.editField.innerText);
		}
	};

	private handleBlur = () => {
		requestIdleCallback(() => {
			if (this.hasFocus) {
				this.editField.ariaBusy = 'false';
				this.textBox.classList.remove('focus');
				this.hasFocus = false;
				this.inputElement.dispatchEvent(new Event('blur'));
			}
		});
	};

	private handleClick = (event: Event) => {
		let countryCode: string | null = null;
		let callingCode: string | null = null;
		let element = event.target instanceof Element ? event.target : null;
		while (element) {
			if (element === this.countryLookupField)
				return;
			if (element.hasAttribute('data-country')) {
				countryCode = element.getAttribute('data-country');
				callingCode = element.getAttribute('data-calling-code');
			}
			if (element === this.internationalSelector && countryCode && callingCode) {
				this.setInternationalCode(countryCode as CountryCode, callingCode as CountryCallingCode);
				break;
			}
			if (element === this.internationalOpener) {
				this.openInternationalSelector();
				return;
			}
			element = element.parentElement;
		}
		this.closeInternationalSelector();
	};

	private handleSearch = (event: Event) => {
 		let search = this.countryLookupField.value.toLowerCase();
		while (search.startsWith('0')) {
			// no international dialing code starts with 0
			search = search.slice(1);
		}
		this.internationalSelector.querySelectorAll('li[data-country]').forEach(element => {
			const countryName = (element as HTMLElement).innerText.toLowerCase();
			(element as HTMLElement).hidden = !countryName.includes(search);
		});
	};

	private handleKeypress = (event: KeyboardEvent) => {
		const selectElement = (element: HTMLLIElement) => {
			this.deselectAll();
			element.classList.add('selected');
			element.scrollIntoView();
		};

		if (!this.isOpen)
			return;
		const visibleCountries = Array.from(this.internationalSelector.querySelectorAll('li[data-country]:not([hidden])'));
		const selectedIndex = visibleCountries.findIndex(li => li.classList.contains('selected'));
		switch (event.key) {
			case 'Enter':
				const element = this.internationalSelector.querySelector('li[data-country].selected');
				if (element instanceof HTMLLIElement) {
					const countryCode = element.getAttribute('data-country');
					const callingCode = element.getAttribute('data-calling-code');
					this.closeInternationalSelector();
					this.setInternationalCode(countryCode as CountryCode, callingCode as CountryCallingCode);
				}
				break;
			case 'Escape':
				this.closeInternationalSelector();
				break;
			case 'ArrowUp':
				const prevItem = visibleCountries[selectedIndex - 1] ?? visibleCountries.slice(-1)[0];
				if (prevItem instanceof HTMLLIElement) {
					selectElement(prevItem);
				}
				event.preventDefault();
				break;
			case 'ArrowDown':
				const nextItem = visibleCountries[selectedIndex + 1] ?? visibleCountries[0];
				if (nextItem instanceof HTMLLIElement) {
					selectElement(nextItem);
				}
				event.preventDefault();
				break;
			case '+':
				this.closeInternationalSelector();
				this.editField.focus();
				this.updateInputField(event.key);
				event.preventDefault();
				break;
			default:
				break;
		}
	};

	private updatePosition = () => {
		const zIndex = this.textBox.style.zIndex ? parseInt(this.textBox.style.zIndex) : 0;
		computePosition(this.textBox, this.internationalSelector, {
			placement: 'bottom-start',
			middleware: [flip(), shift()],
		}).then(({x, y}) => Object.assign(
			this.internationalSelector.style, {left: `${x}px`, top: `${y}px`, zIndex: `${zIndex + 2}`}
		));
	};

	private deselectAll = () => {
		this.internationalSelector.querySelectorAll('li[data-country]').forEach(element => {
			element.classList.remove('selected');
		});
	};

	private clearSearch = () => {
		this.internationalSelector.querySelectorAll('li[data-country]').forEach(element => {
			(element as HTMLElement).hidden = false;
		});
	};

	private openInternationalSelector() {
		this.internationalSelector.parentElement!.style.position = 'relative';
		this.cleanup = autoUpdate(this.textBox, this.internationalSelector, this.updatePosition);
		this.textBox.setAttribute('aria-expanded', 'true');
		const selectorRect = this.internationalSelector.getBoundingClientRect();
		this.internationalSelector.style.width = `${Math.round(selectorRect.width)}px`;  // prevent resizing while searching
		this.isOpen = true;
		this.countryLookupField.value = '';
		this.deselectAll();
		this.clearSearch();
		const country = this.asYouType.getCountry();
		if (country) {
			const liElem = this.internationalSelector.querySelector(`[data-country="${country}"]`);
			if (liElem instanceof HTMLLIElement) {
				liElem.classList.add('selected');
				liElem.scrollIntoView();
			}
		}
		this.countryLookupField.focus();
	}

	private closeInternationalSelector() {
		if (this.isOpen) {
			this.textBox.setAttribute('aria-expanded', 'false');
			this.cleanup();
			this.inputElement.dispatchEvent(new Event('focusout'));
			this.isOpen = false;
		}
	}

	private setInternationalCode(countryCode: CountryCode, callingCode: CountryCallingCode) {
		const nationalNumber = this.asYouType.getNumber()?.nationalNumber ?? '';
		this.inputElement.value = `+${callingCode}${nationalNumber}`;
		this.inputElement.dispatchEvent(new Event('input'));
		this.editField.focus();
		requestIdleCallback(() => this.setCaretToEnd());
	}

	private getCaretPosition() {
		const selection = window.getSelection();
		if (selection && selection.rangeCount === 1) {
			const range = selection.getRangeAt(0);
			return range.startOffset;
		}
		return 0;
	}

	private setCaretPosition(position: number) {
		const range = document.createRange();
		const selection = window.getSelection();
		if (!this.editField.childNodes.length || !selection)
			return;
		const textNode = this.editField.childNodes[0] as Text;
		position = Math.max(0, Math.min(position, textNode.length));
		range.setStart(textNode, position);
		selection.removeAllRanges();
		selection.addRange(range);
	}

	private updateInputField(phoneNumber: string) {
		let caretPosition = this.getCaretPosition();
		if (this.editField.innerText.length === caretPosition) {
			++caretPosition;
		}
		this.asYouType.reset();
		this.asYouType.input(phoneNumber);
		this.inputElement.value = this.asYouType.getChars() === '+' ? '+' : this.asYouType.getNumberValue() ?? '';
		this.setCaretPosition(caretPosition);
		this.inputElement.dispatchEvent(new Event('input'));
	}

	private decorateInputField(countryCode?: CountryCode) {
		if (countryCode) {
			this.internationalOpener.innerHTML = `<span class="flag-${countryCode.toLowerCase()} flag-icon"></span>`;
		} else {
			this.internationalOpener.innerHTML = '';
		}
	}

	private transferStyles() : CSSStyleSheet {
		const declaredStyles = document.createElement('style');
		let loaded = false;
		declaredStyles.innerText = styles;
		document.head.appendChild(declaredStyles);
		this.inputElement.style.transition = 'none';  // prevent transition while pilfering styles
		for (let index = 0; declaredStyles.sheet && index < declaredStyles.sheet.cssRules.length; index++) {
			const cssRule = declaredStyles.sheet.cssRules.item(index) as CSSStyleRule;
			const selector = cssRule.selectorText.trim();
			let extraStyles = '';
			switch (selector) {
				case this.baseSelector:
					loaded = true;
					break;
				case `${this.baseSelector} + [role="textbox"]`:
					extraStyles = StyleHelpers.extractStyles(this.inputElement, [
						'line-height', 'padding',
					]).concat(StyleHelpers.extractStyles(this.inputElement, {
						'--border-style': 'border-style',
						'--border-width': 'border-width',
						'--border-radius': 'border-radius',
					}));
					break;
				case `${this.baseSelector} + [role="textbox"] > .phone-number-edit`:
					extraStyles = `line-height:${window.getComputedStyle(document.querySelector(selector)!).height};`;
					break;
				case `${this.baseSelector} + [role="textbox"][aria-haspopup="dialog"] + [role="dialog"]`:
					extraStyles = StyleHelpers.extractStyles(this.inputElement, ['line-height', 'padding']).concat(
						`--border-style: ${window.getComputedStyle(this.inputElement).getPropertyValue('border-style')};`,
						`--border-width: ${window.getComputedStyle(this.inputElement).getPropertyValue('border-width')};`,
						`--border-radius: ${window.getComputedStyle(this.inputElement).getPropertyValue('border-radius')};`,
					);
					break;
				case `${this.baseSelector} + [role="textbox"][aria-haspopup="dialog"] + [role="dialog"] input[type="search"]`:
					extraStyles = StyleHelpers.extractStyles(this.inputElement, ['padding']);
					break;
				case `${this.baseSelector} + [role="textbox"][aria-haspopup="dialog"] + [role="dialog"] input[type="search"]:focus`:
					this.inputElement.classList.add('⁝focus');
					extraStyles = StyleHelpers.extractStyles(this.inputElement, [
						'border', 'box-shadow', 'outline', 'transition']);
					this.inputElement.classList.remove('⁝focus');
					break;
				case `${this.baseSelector} + [role="textbox"][aria-haspopup="dialog"] + [role="dialog"] ul`:
					extraStyles = `${selector}{height:${Math.floor(window.innerHeight / 3)}px;}`;
					break;
				default:
					break;
			}
			if (extraStyles) {
				declaredStyles.sheet.insertRule(`${selector}{${extraStyles}}`, ++index);
			}
		}
		this.inputElement.style.transition = '';
		if (!loaded)
			throw new Error(`Could not load styles for ${this.baseSelector}`);
		return declaredStyles.sheet as CSSStyleSheet;
	}

	private transferClasses() {
		this.inputElement.style.transition = '';
	}

	private initialize() {
		// some styles change when switching light/dark mode, so we need to update them
		StyleHelpers.pushMediaQueryStyles(
			this.styleSheet,
			`${this.baseSelector} + [role="textbox"]`,
			{
				'--border-color': 'border-color',
				'--outline': 'outline',
			},
			this.inputElement,
		);
		StyleHelpers.pushMediaQueryStyles(
			this.styleSheet,
			`${this.baseSelector} + [role="textbox"].focus`,
			{
				'border-color': 'border-color',
				'box-shadow': 'box-shadow',
				'outline': 'outline',
			},
			this.inputElement, '⁝focus',
		);
		StyleHelpers.pushMediaQueryStyles(
			this.styleSheet,
			`${this.baseSelector} + [role="textbox"][aria-haspopup="dialog"] + [role="dialog"]`,
			{
				'--border-color': 'border-color',
				'--outline': 'outline',
			},
			this.inputElement,
		);
		StyleHelpers.pushMediaQueryStyles(
			this.styleSheet,
			`${this.baseSelector} + [role="textbox"][aria-haspopup="dialog"] + [role="dialog"] input[type="search"]:focus`,
			{
				'border-color': 'border-color',
				'box-shadow': 'box-shadow',
				'outline': 'outline',
				'transition': 'transition',
			},
			this.inputElement, '⁝focus',
		);
	}

	public connect() {
		this.initialize();
		this.editField.addEventListener('focus', this.handleFocus);
		this.editField.addEventListener('input', this.handleInput);
		this.editField.addEventListener('blur', this.handleBlur);
		this.countryLookupField.addEventListener('input', this.handleSearch);
		document.addEventListener('click', this.handleClick);
		document.addEventListener('keydown', this.handleKeypress);
		if (this.inputElement.form) {
			this.inputElement.form.addEventListener('reset', this.formResetted);
		}
		this.inputElement.hidden = true;  // setting type="hidden" prevents dispatching events
		this.inputElement.value = this.inputElement.defaultValue;
	}

	public disconnect() {
		this.editField.removeEventListener('focus', this.handleFocus);
		this.editField.removeEventListener('input', this.handleInput);
		this.editField.removeEventListener('blur', this.handleBlur);
		this.countryLookupField.removeEventListener('input', this.handleSearch);
		document.removeEventListener('click', this.handleClick);
		document.removeEventListener('keydown', this.handleKeypress);
		if (this.inputElement.form) {
			this.inputElement.form.removeEventListener('reset', this.formResetted);
		}
	}

	public setValue(value: string) {
		this.asYouType.reset();
		this.editField.innerText = this.asYouType.input(value);
		this.decorateInputField(this.asYouType.getCountry());
	}

	public checkValidity() : boolean {
		if (this.asYouType.isValid()) {
			if (this.mobileOnly && this.asYouType.getNumber()?.getType() !== 'MOBILE') {
				this.inputElement.setCustomValidity("Invalid mobile number");
				return false;
			}
		} else {
			this.inputElement.setCustomValidity("Invalid phone number");
			return false;
		}
		return true;
	}
}


const PN = Symbol('DjangoPhoneNumberElement');

export class PhoneNumberElement extends HTMLInputElement {
	private [PN]: PhoneNumberField;  // hides internal implementation

	constructor() {
		super();
		this[PN] = new PhoneNumberField(this);
	}

	connectedCallback() {
		this[PN].connect();
	}

	disconnectedCallback() {
		this[PN].disconnect();
	}

	get value() : string {
		return super.value;
	}

	set value(value: string) {
		super.value = value;
		this[PN].setValue(value);
	}

	checkValidity() {
		if (!super.checkValidity()) {
			return false;
		}
		return this[PN].checkValidity();
	}
}
