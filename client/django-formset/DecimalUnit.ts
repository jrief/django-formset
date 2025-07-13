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
	private readonly precision: number;
	private readonly blockLength: number;
	private readonly separator = ' ';

	constructor(inputElement: HTMLInputElement, calendarElement: HTMLElement | null) {
		super(inputElement);
		this.inputElement = inputElement;
		this.textBox = this.createTextBox();
		this.editField = this.textBox.querySelector('span[contenteditable="true"]') as HTMLElement;
		this.step = inputElement.step ? parseFloat(inputElement.step) : null;
		this.precision = parseInt(inputElement.getAttribute('precision') ?? '0');
		this.blockLength = parseInt(inputElement.getAttribute('block-length') ?? '3');
		this.styleSheet = StyleHelpers.stylesAreInstalled(this.baseSelector) ?? this.transferStyles();
	}

	private createTextBox(): HTMLElement {
		const htmlTag = `
			<div role="textbox">
			<div class="decimal-unit-edit">
			<span contenteditable="true"></span>
			</div>
			</div>`;
		this.inputElement.insertAdjacentHTML('afterend', htmlTag);
		return this.inputElement.nextElementSibling as HTMLElement;
	}

	private handleMousedown = (event: Event) => {
		console.log("down", event.target);
		// Here we handle potential clicks inside the text box:
		// They should focus or keep focus on the edit field which otherwise would blur.
		if (event.target instanceof HTMLElement && event.target.closest('[role="textbox"]') === this.textBox) {
			if (event.target === this.editField) {
				// click detected inside the edit field
				this.hasFocus = true;
			} else {
				// click detected outside the edit field, but inside the text box
				requestIdleCallback(() => {
					console.log("focus edit field");
					const hasFocus = this.hasFocus;
					this.hasFocus = false;  // ignores handleFocus
					this.editField.focus();
					this.setCaretPosition(Number.MAX_VALUE);
					this.hasFocus = true;
					if (!hasFocus) {
						console.log("dispatch focus");
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
		console.log("focus", event);
		this.textBox.classList.add('focus');
		this.inputElement.dispatchEvent(new Event('focus'));
		this.hasFocus = true;
		event.preventDefault();
	};

	private handleBlur = (event: Event) => {
		if (this.hasFocus)
			return;
		console.log("blur", event.target);
		this.textBox.classList.remove('focus');
		requestIdleCallback(() => {
			this.inputElement.dispatchEvent(new Event('blur'));
			console.log('blur');
		});
		this.hasFocus = false;
		this.inputElement.dispatchEvent(new Event('input'));
	};

	private handleCopy = (event: ClipboardEvent) => {
		event.clipboardData?.setData('text/plain', this.inputElement.value);
		event.preventDefault();
	};

	private handleCut = (event: ClipboardEvent) => {
		event.clipboardData?.setData('text/plain', this.inputElement.value);
		// clear the input value on cut
		this.inputElement.value = this.editField.innerText = '';
		this.inputElement.dispatchEvent(new Event('input'));
		event.preventDefault();
	};

	private handlePaste = (event: ClipboardEvent) => {
		console.log(event);
		requestIdleCallback(() => {
			this.updateInputValue(true);
			this.setCaretPosition(Number.MAX_VALUE);
		});
	};

	private handleKeypress = (event: KeyboardEvent) => {
		let preventDefault = false;
		if (this.hasFocus) {
			const caretPosition = this.getCaretPosition();
			const reversePosition = this.editField.innerText.length - caretPosition;
			if (['ArrowUp', 'ArrowDown'].includes(event.key)) {
				preventDefault = true;
			} else if (event.key === 'ArrowRight') {
				if (!event.shiftKey && reversePosition % (this.blockLength + 1) === 1) {
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
				requestIdleCallback(() => this.updateInputValue(false));
			} else if (event.key === 'Delete') {
				requestIdleCallback(() => this.updateInputValue(false));
			} else if (event.key >= '0' && event.key <= '9') {
				requestIdleCallback(() => this.updateInputValue(true));
			} else if (['c', 'v', 'x'].includes(event.key)) {
				// allow copy/cut/paste
				if (!event.ctrlKey && !event.metaKey && !event.shiftKey) {
					preventDefault = true;
				}
			} else {
				console.log(event.key);
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

	private setCaretPosition(position: number) {
		const range = document.createRange();
		const selection = window.getSelection();
		if (!this.editField.childNodes.length || !selection)
			return;
		const textNode = this.editField.childNodes[0] as Text;
		position = Math.max(0, Math.min(position, textNode.length));
		range.setStart(textNode, position);
		// range.collapse(true);  range is already collapsed
		selection.removeAllRanges();
		selection.addRange(range);
	}

	private updateInputValue(insertDigit: boolean) {
		let caretPosition = this.getCaretPosition();
		const numberRegex = new RegExp('[^0-9.-]', 'g');
		const [integerPart, fraction] = this.editField.innerText.replace(',', '.').replaceAll(numberRegex, '').split('.');
		const parts = Array<string>();
		for (let k = integerPart.length; k >= 0; k -= this.blockLength) {
			const part = integerPart.slice(Math.max(0, k - this.blockLength), k);
			if (part.length > 0) {
				parts.unshift(part);
			}
		}
		this.editField.innerText = `${parts.join(this.separator)}`; // ${fraction ? `.${fraction}` : ''}`;
		// console.log(integerPart.length, caretPosition, parts[0].length);
		if (insertDigit === true && caretPosition > this.blockLength && parts[0].length === 1) {
			// caret is after newly created first block, so we need to adjust the caret position
			caretPosition++;
		} else if (insertDigit === false && parts[0].length === 3) {
			// first block collapsed after deletion, so we need to adjust the caret position
			caretPosition--;
		}
		// const reversePosition = this.editField.innerText.length - caretPosition;
		// console.log(reversePosition, parts[0].length, reversePosition % (this.blockLength + 1));
		if ((this.editField.innerText.length - caretPosition) % (this.blockLength + 1) === 0) {
			// moves caret on the right part of the separator
			caretPosition++;
		}
		this.setCaretPosition(caretPosition);
		this.inputElement.value = `${integerPart}${fraction ? `.${fraction}` : ''}`;
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
		this.editField.addEventListener('focus', this.handleFocus);
		this.editField.addEventListener('blur', this.handleBlur);
		this.editField.addEventListener('copy', this.handleCopy);
		this.editField.addEventListener('cut', this.handleCut);
		this.editField.addEventListener('paste', this.handlePaste);
		document.addEventListener('mousedown', this.handleMousedown);
		document.addEventListener('keydown', this.handleKeypress);
	}

	public disconnect() {
		this.editField.removeEventListener('focus', this.handleFocus);
		this.editField.removeEventListener('blur', this.handleBlur);
		this.editField.removeEventListener('copy', this.handleCopy);
		this.editField.removeEventListener('cut', this.handleCut);
		this.editField.removeEventListener('paste', this.handlePaste);
		document.removeEventListener('mousedown', this.handleMousedown);
		document.removeEventListener('keydown', this.handleKeypress);
	}

	public checkValidity(): boolean {
		return true;  // TODO: implement validation logic
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
		return this[DU].checkValidity();
	}
}
