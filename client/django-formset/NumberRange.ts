import {Widget} from './Widget';
import {StyleHelpers} from './helpers';
import styles from './NumberRange.scss';


class NumberRangeField extends Widget {
	private readonly inputElement: HTMLInputElement;
	private readonly slider: HTMLElement;
	private readonly baseSelector = 'django-formset [is="django-dual-number-range"]';
	private readonly styleSheet: CSSStyleSheet;

	constructor(inputElement: HTMLInputElement) {
		super(inputElement);
		this.inputElement = inputElement;
		this.slider = this.createSlider();
		this.styleSheet = StyleHelpers.stylesAreInstalled(this.baseSelector) ?? this.transferStyles();
	}

	private createSlider(): HTMLElement {
		const htmlTags = [
			'<input type="range" class="form-range" />',
		];
		this.inputElement.insertAdjacentHTML('afterend', htmlTags.join(''));
		return this.inputElement.nextElementSibling as HTMLElement;
	}

	private transferStyles() : CSSStyleSheet {
		const declaredStyles = document.createElement('style');
		declaredStyles.innerText = styles;
		document.head.appendChild(declaredStyles);
		//const sliderThumbStyle = window.getComputedStyle(this.inputElement, '::-webkit-slider-thumb');

		this.inputElement.style.transition = 'none';  // prevent transition while pilfering styles
		let loaded = false;
		for (let index = 0; declaredStyles.sheet && index < declaredStyles.sheet.cssRules.length; index++) {
			const cssRule = declaredStyles.sheet.cssRules.item(index) as CSSStyleRule;
			const selector = cssRule.selectorText.trim();
			let extraStyles = '';
			switch (selector) {
				case this.baseSelector:
					// extraStyles = '--slider-thumb-bg-color: #00af00;';
					loaded = true;
					break;
				case `${this.baseSelector}::-webkit-slider-thumb`:
					extraStyles = StyleHelpers.extractStyles(this.inputElement, ['height']);
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

	private handleInput = (event: Event) => {
		const percentage = parseFloat(this.inputElement.value);
		this.inputElement.style.backgroundImage = `linear-gradient(to right, var(--slider-thumb-fg-color) 0%, var(--slider-thumb-fg-color) ${percentage}%, var(--slider-thumb-bg-color) ${percentage}%, var(--slider-thumb-bg-color) 100%)`;
		console.log(this.inputElement.style.background);
	};

	protected formResetted(event: Event) {
		this.inputElement.value = this.inputElement.defaultValue;
	}

	protected formSubmitted(event: Event) {}

	public connect() {
		// some styles change when switching light/dark mode, so we need to update them
		this.inputElement.addEventListener('input', this.handleInput);
	}

	public disconnect() {
	}
}


export class DualNumberRangeElement extends HTMLInputElement {
	readonly #numberrange: NumberRangeField;

	constructor() {
		super();
		const fieldGroup = this.closest('[role="group"]');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		this.#numberrange = new NumberRangeField(this);
	}

	connectedCallback() {
		this.#numberrange.connect();
	}

	disconnectedCallback() {
		this.#numberrange.disconnect();
	}
}
