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
		this.precision = Number(inputElement.getAttribute('precision')) || 0;
		this.blockLength = Number(inputElement.getAttribute('block-length')) || 3;
		this.styleSheet = StyleHelpers.stylesAreInstalled(this.baseSelector) ?? this.transferStyles();
	}

	private createTextBox(): HTMLElement {
		const htmlTags: Array<string> = [
			'<div role="textbox">',
			'<div class="decimal-unit-edit">',
			'<span contenteditable="true"></span>',
			'</div>',
			'</div>',
		];
		this.inputElement.insertAdjacentHTML('afterend', htmlTags.join(''));
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

	private handleKeypress = (event: KeyboardEvent) => {
		let preventDefault = false;
		if (this.hasFocus) {
			switch (event.key) {
				case 'ArrowRight':
				case 'ArrowLeft':
					requestIdleCallback(() => console.log(this.getCaretPosition()));
					break;
				case 'ArrowUp':
				case 'ArrowDown':
					if (this.step !== null) {
					}
					preventDefault = true;
					break;
				case 'Backspace': case 'Delete':
					requestIdleCallback(() => {
						this.updateInputValue(true);
					});
					break;
				case '-': case '+':
					const selection = window.getSelection();
					if (selection && selection.rangeCount > 0) {
						// allow sign only at the beginning
						const range = selection.getRangeAt(0);
						const firstChar = this.editField.innerText.charAt(0);
						preventDefault = range.startOffset !== 0 || ['-', '+'].includes(firstChar);
					}
					break;
				case '.': case ',':
					break;
				case '0': case '1': case '2': case '3': case '4': case '5': case '6': case '7': case '8': case '9':
					requestIdleCallback(() => {
						this.updateInputValue();
					});
					break;
				default:
					preventDefault = true;
					break;
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

	private updateInputValue(del=false) {
		let caretPosition = this.getCaretPosition();
		const [integerPart, fraction] = this.editField.innerText.replaceAll(this.separator, '').replace(',', '.').split('.');
		const parts = Array<string>();
		for (let k = integerPart.length; k >= 0; k -= this.blockLength) {
			const part = integerPart.slice(Math.max(0, k - this.blockLength), k);
			if (part.length > 0) {
				parts.unshift(part);
			}
		}
		this.editField.innerText = `${parts.join(this.separator)}`; // ${fraction ? `.${fraction}` : ''}`;
		console.log(integerPart.length, caretPosition, parts[0].length);
		if (caretPosition > this.blockLength && parts[0].length === 1) {
			// caret is after newly created first block, so we need to adjust it
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
		document.addEventListener('mousedown', this.handleMousedown);
		document.addEventListener('keydown', this.handleKeypress);
	}

	public disconnect() {
		this.editField.removeEventListener('focus', this.handleFocus);
		this.editField.removeEventListener('blur', this.handleBlur);
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
