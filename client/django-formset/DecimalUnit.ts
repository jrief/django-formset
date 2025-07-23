import {Widget} from './Widget';
import {StyleHelpers} from './helpers';
import styles from './DecimalUnit.scss';


class DecimalUnitField extends Widget {
	private readonly inputElement: HTMLInputElement;
	private readonly textBox: HTMLElement;
	private readonly editField: HTMLElement;
	private readonly baseSelector = '[is^="django-decimal-unit"]';
	private readonly styleSheet: CSSStyleSheet;
	private hasFocus: boolean = false;
	private readonly step: number|null;
	private readonly minValue: number;
	private readonly maxValue: number;
	private readonly maxDigits: number;
	private readonly decimalPlaces: number;
	private readonly blockLength: number;
	// alternative: private readonly separator = ' ';  // Unicode character "Medium Mathematical Space", U+205F
	private readonly separator = ' ';  // Unicode character "Thin Space", U+2009
	private readonly decSep: string;

	constructor(inputElement: HTMLInputElement, calendarElement: HTMLElement | null) {
		super(inputElement);
		this.inputElement = inputElement;
		this.textBox = this.createTextBox();
		this.editField = this.textBox.querySelector('span[contenteditable="true"]') as HTMLElement;
		this.maxDigits = parseInt(inputElement.getAttribute('max-digits') ?? '');
		this.decimalPlaces = parseInt(inputElement.getAttribute('decimal-places') ?? '0');
		this.step = inputElement.step ? parseFloat(inputElement.step) : null;
		this.minValue = inputElement.min ? parseFloat(inputElement.min) : Number.MIN_SAFE_INTEGER;
		this.maxValue = inputElement.max ? parseFloat(inputElement.max) : Number.MAX_SAFE_INTEGER;
		this.blockLength = parseInt(inputElement.getAttribute('block-length') ?? '3');
		this.styleSheet = StyleHelpers.stylesAreInstalled(this.baseSelector) ?? this.transferStyles();
		const formatter = new Intl.NumberFormat(navigator.language);
		this.decSep = formatter.format(1.1)[1];
	}

	private createTextBox(): HTMLElement {
		const prefix = this.inputElement.getAttribute('prefix');
		const suffix = this.inputElement.getAttribute('suffix');
		const htmlTag = `
			<div role="textbox">
			<div class="decimal-unit-edit">
			${prefix ? `<span class="prefix">${prefix}</span>` : ''}
			<span contenteditable="true"></span>
			${suffix ? `<span class="suffix">${suffix}</span>` : ''}
			</div>
			</div>`;
		this.inputElement.insertAdjacentHTML('afterend', htmlTag);
		return this.inputElement.nextElementSibling as HTMLElement;
	}

	private handleMousedown = (event: Event) => {
		// Here we handle potential clicks inside the text box:
		// They should focus or keep focus on the edit field which otherwise would blur.
		if (event.target instanceof HTMLElement && event.target.closest('[role="textbox"]') === this.textBox) {
			if (event.target === this.editField) {
				// click detected inside the edit field
				this.hasFocus = true;
			} else {
				// click detected outside the edit field, but inside the text box
				requestIdleCallback(() => {
					const hasFocus = this.hasFocus;
					this.hasFocus = false;  // ignores handleFocus
					this.editField.focus();
					this.setCaretPosition(Number.MAX_SAFE_INTEGER);
					this.hasFocus = true;
					if (!hasFocus) {
						this.editField.dispatchEvent(new Event('focus'));
					}
				});
			}
		} else {
			// click detected outside the text box
			this.hasFocus = false;
		}
	};

	private handleFocus = (event: FocusEvent) => {
		if (!this.hasFocus)
			return;
		this.textBox.classList.add('focus');
		this.inputElement.dispatchEvent(new Event('focus'));
		this.hasFocus = true;
		event.preventDefault();
	};

	private handleBlur = (event: Event) => {
		if (this.hasFocus)
			return;
		this.textBox.classList.remove('focus');
		requestIdleCallback(() => {
			this.inputElement.dispatchEvent(new Event('blur'));
		});
		this.hasFocus = false;
	};

	private handleCopy = (event: ClipboardEvent) => {
		event.clipboardData?.setData('text/plain', this.inputElement.value);
		event.preventDefault();
	};

	private handleCut = (event: ClipboardEvent) => {
		event.clipboardData?.setData('text/plain', this.inputElement.value);
		// clear the input value on cut
		this.inputElement.value = this.editField.innerText = '';
		this.inputted();
		event.preventDefault();
	};

	private handlePaste = (event: ClipboardEvent) => {
		requestIdleCallback(() => {
			this.updateInputValue(true);
			this.setCaretPosition(Number.MAX_SAFE_INTEGER);
			this.inputted();
		});
	};

	private handleKeypress = (event: KeyboardEvent) => {
		let preventDefault = false;
		if (this.hasFocus) {
			const caretPosition = this.getCaretPosition();
			const reversePosition = this.getReversePosition();
			if (['ArrowUp', 'ArrowDown'].includes(event.key)) {
				if (this.inputElement.value.length && typeof this.step === 'number' && this.step > 0) {
					const stepValue = event.key === 'ArrowUp' ? this.step : -this.step;
					const caretAtEnd = caretPosition === this.editField.innerText.length;
					const value = parseFloat(this.inputElement.value) + stepValue;
					this.editField.innerText = String(Math.min(Math.max(value, this.minValue), this.maxValue));
					this.updateInputValue();
					this.setCaretPosition(caretAtEnd ? Number.MAX_SAFE_INTEGER : caretPosition);
					this.inputted();
				}
				preventDefault = true;
			} else if (event.key === 'ArrowRight') {
				if (!event.shiftKey && reversePosition > 1 && reversePosition % (this.blockLength + 1) === 1) {
					this.setCaretPosition(caretPosition + 1);
				}
			} else if (event.key === 'ArrowLeft') {
				if (!event.shiftKey && reversePosition % (this.blockLength + 1) === this.blockLength) {
					this.setCaretPosition(caretPosition - 1);
				}
			} else if (event.key === 'Backspace') {
				if (reversePosition % (this.blockLength + 1) === this.blockLength) {
					this.setCaretPosition(caretPosition - 1);
				}
				requestIdleCallback(() => {
					this.updateInputValue(false);
					this.inputted();
				});
			} else if (event.key === 'Delete') {
				requestIdleCallback(() => {
					this.updateInputValue(false);
					this.inputted();
				});
			} else if (event.key >= '0' && event.key <= '9' || this.decimalPlaces > 0 && ['.', ','].includes(event.key)) {
				requestIdleCallback(() => {
					this.updateInputValue(true);
					this.inputted();
				});
			} else if (event.key === '-') {
				if (this.minValue < 0 && caretPosition === 0) {
					requestIdleCallback(() => {
						this.updateInputValue(true);
						this.inputted();
					});
				} else {
					preventDefault = true;
				}
			} else if (['c', 'v', 'x', 'z'].includes(event.key)) {
				// allow copy/cut/paste/undo
				if (!event.ctrlKey && !event.metaKey && !event.shiftKey) {
					preventDefault = true;
				}
			} else {
				preventDefault = true;
			}
		}
		if (preventDefault) {
			event.preventDefault();
		}
	};

	private getCaretPosition() {
		const selection = window.getSelection();
		if (selection && selection.rangeCount === 1) {
			const range = selection.getRangeAt(0);
			return range.startOffset;
		}
		return 0;
	}

	private getReversePosition() {
		const caretPosition = this.getCaretPosition();
		const [integerPart] = this.editField.innerText.replace(',', '.').split('.');
		return Math.max(integerPart.length - caretPosition, 0);
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

	private updateInputValue(insertDigit?: boolean) {
		let caretPosition = this.getCaretPosition();
		const numberRegex = new RegExp('[^0-9]', 'g');
		const sign = this.editField.innerText.startsWith('-') ? '-' : '';
		const [leftPart, rightPart] = this.editField.innerText.replace(',', '.').split('.').map(part => part.replace(numberRegex, ''));
		const integerLength = isFinite(this.maxDigits) ? Math.min(this.maxDigits - this.decimalPlaces, leftPart.length) : leftPart.length;
		const parts = Array<string>();
		for (let k = integerLength; k >= 0; k -= this.blockLength) {
			const part = leftPart.slice(Math.max(0, k - this.blockLength), k);
			if (part.length > 0) {
				parts.unshift(part);
			}
		}
		const integerPart = parts.join(this.separator);
		const fraction = (() => {
			if (rightPart === undefined)
				return null;
			if (rightPart.length === 0)
				return '';
			const endCaret = Math.min(this.decimalPlaces, rightPart.length);
			return parseFloat(`.${rightPart}`).toFixed(this.decimalPlaces).slice(2, 2 + endCaret);
		})();
		this.editField.innerText = `${sign}${integerPart}${fraction !== null ? `${this.decSep}${fraction}` :  ''}`;
		const decimalSeparatorIndex = this.inputElement.value.indexOf('.');
		if (insertDigit !== undefined && caretPosition <= integerPart.length && (
			decimalSeparatorIndex === -1 && fraction === null || decimalSeparatorIndex >= 0 && fraction !== null
		)) {
			if (insertDigit === true && caretPosition > this.blockLength && parts[0].length === 1) {
				// caret is after newly created first block, so we need to adjust the caret position
				caretPosition++;
			} else if (insertDigit === false && parts.length && parts[0].length === 3) {
				// first block collapsed after deletion, so we need to adjust the caret position
				caretPosition--;
			}
			const signedIntegerLength = integerPart.length + (sign ? 1 : 0);
			if (caretPosition < signedIntegerLength && (signedIntegerLength - caretPosition) % (this.blockLength + 1) === 0) {
				// moves caret on the right part of the separator
				caretPosition++;
			}
		}
		if (this.hasFocus) {
			this.setCaretPosition(caretPosition);
		}
		this.inputElement.value = `${sign}${leftPart}${fraction !== null ? `.${fraction}` : ''}`;
	}

	private inputted() {
		this.inputElement.dispatchEvent(new Event('input'));
	}

	private transferStyles() : CSSStyleSheet {
		const declaredStyles = document.createElement('style');
		declaredStyles.innerText = styles;
		document.head.appendChild(declaredStyles);
		this.inputElement.style.transition = 'none';  // prevent transition while pilfering styles
		let loaded = false;
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
						'height', 'line-height', 'padding',
					]).concat(StyleHelpers.extractStyles(this.inputElement, {
						'--border-style': 'border-style',
						'--border-width': 'border-width',
						'--border-radius': 'border-radius',
					}));
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

	protected formResetted(event: Event) {
		this.inputElement.value = this.inputElement.defaultValue;
		this.editField.innerText = this.inputElement.value;
		this.updateInputValue();
	}

	protected formSubmitted(event: Event) {}

	public connect() {
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

		this.inputElement.hidden = true;  // setting type="hidden" prevents dispatching events
		this.inputElement.addEventListener('reset', this.formResetted);
		this.editField.addEventListener('focus', this.handleFocus);
		this.editField.addEventListener('blur', this.handleBlur);
		this.editField.addEventListener('copy', this.handleCopy);
		this.editField.addEventListener('cut', this.handleCut);
		this.editField.addEventListener('paste', this.handlePaste);
		document.addEventListener('mousedown', this.handleMousedown);
		document.addEventListener('keydown', this.handleKeypress);
		this.editField.innerText = this.inputElement.value;
		this.updateInputValue();
	}

	public disconnect() {
		this.inputElement.removeEventListener('reset', this.formResetted);
		this.editField.removeEventListener('focus', this.handleFocus);
		this.editField.removeEventListener('blur', this.handleBlur);
		this.editField.removeEventListener('copy', this.handleCopy);
		this.editField.removeEventListener('cut', this.handleCut);
		this.editField.removeEventListener('paste', this.handlePaste);
		document.removeEventListener('mousedown', this.handleMousedown);
		document.removeEventListener('keydown', this.handleKeypress);
	}
}

const DU = Symbol('DecimalUnit');

export class DecimalUnitElement extends HTMLInputElement {
	private [DU]: DecimalUnitField;  // hides internal implementation

	constructor() {
		super();
		const fieldGroup = this.closest('[role="group"]');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		const calendarElement = fieldGroup.querySelector('[aria-label="calendar"]');
		this[DU] = new DecimalUnitField(this, calendarElement as HTMLElement);
	}

	connectedCallback() {
		this[DU].connect();
	}

	disconnectedCallback() {
		this[DU].disconnect();
	}

	checkValidity() {
		if (!super.checkValidity())
			return false;
		return true;
	}
}
