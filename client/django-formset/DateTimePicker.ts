import {autoUpdate, computePosition, flip, shift} from '@floating-ui/dom';
import {Calendar, CalendarSettings} from "./Calendar";
import {StyleHelpers, Widget} from './helpers';
import styles from './DateTimePicker.scss';
import calendarIcon from './icons/calendar.svg';


enum FieldPart {
	year,
	month,
	day,
	hour,
	minute,
}


class DateTimePicker extends Widget {
	private readonly inputElement: HTMLInputElement;
	private readonly textBox: HTMLElement;
	private readonly dateOnly: boolean;
	private readonly calendar: Calendar;
	private readonly inputFields: Array<HTMLElement> = [];
	private readonly inputFieldsOrder: Array<number> = [];
	private currentDate: Date | null = null;
	private calendarOpener: HTMLElement;
	private dateTimeFormat?: Intl.DateTimeFormat;
	private hasFocus: HTMLElement | null = null;
	private cleanup?: Function;
	private isOpen: boolean = false;

	constructor(inputElement: HTMLInputElement, calendarElement: HTMLElement | null) {
		super(inputElement);
		this.inputElement = inputElement;
		this.dateOnly = inputElement.getAttribute('is') === 'django-datepicker';
		this.textBox = this.createTextBox();
		this.setInitialDate();
		this.calendar = new Calendar(calendarElement, this.getCalendarSettings());
		const calendarOpener = this.textBox.querySelector('.calendar-picker-indicator');
		if (!(calendarOpener instanceof HTMLElement))
			throw new Error("Missing selectot .calendar-picker-indicator");
		this.calendarOpener = calendarOpener;
		this.calendarOpener.innerHTML = calendarIcon;
		this.installEventHandlers();
		this.transferStyles();
		this.transferClasses();
		this.updateInputFields(this.currentDate);
	}

	private setInitialDate() {
		this.currentDate = this.inputElement.value ? new Date(this.inputElement.value) : null;
	}

	private updateDate(date: Date) {
		this.currentDate = date;
		this.updateInputFields(this.currentDate);
		this.inputElement.dispatchEvent(new Event('input'));
		this.inputElement.dispatchEvent(new Event('blur'));
	}

	private getCalendarSettings() : CalendarSettings {
		const settings: CalendarSettings = {
			dateOnly: this.dateOnly,
			initialDate: this.currentDate ?? undefined,
			endpoint: this.endpoint!,
			inputElement: this.inputElement,
			updateDate: (date: Date) => this.updateDate(date),
			close: () => this.closeCalendar(),
		};
		const minValue = this.inputElement.getAttribute('min');
		if (minValue) {
			settings.minDate = new Date(minValue);
		}
		const maxValue = this.inputElement.getAttribute('max');
		if (maxValue) {
			settings.maxDate = new Date(maxValue);
		}
		const step = this.inputElement.getAttribute('step');
		if (step) {
			const d1 = new Date('1970-01-01 0:00:00');
			const d2 = new Date(`1970-01-01 ${step}`);
			settings.interval = (d2.getTime() - d1.getTime()) / 60000;
		}
		return settings;
	}

	private createTextBox(): HTMLElement {
		const htmlTags: Array<string> = [
			'<div role="textbox" aria-expanded="false" aria-haspopup="dialog">',
			'<div class="datetime-edit">',
		];
		const htmlIsoTags: Array<string> = [
			'<span role="spinbutton" class="datetime-edit-year-field" contenteditable="true" aria-placeholder="yyyy" aria-valuemin="1700" aria-valuemax="2300"></span>',
			'<span role="separator" class="datetime-delimiter" aria-hidden="true">-</span>',
			'<span role="spinbutton" class="datetime-edit-month-field" contenteditable="true" aria-placeholder="mm" aria-valuemin="1" aria-valuemax="12"></span>',
			'<span role="separator" class="datetime-delimiter" aria-hidden="true">-</span>',
			'<span role="spinbutton" class="datetime-edit-day-field" contenteditable="true" aria-placeholder="dd" aria-valuemin="1" aria-valuemax="31"></span>',
		];
		if (!this.dateOnly) {
			htmlIsoTags.push('<span role="separator" class="datetime-delimiter" aria-hidden="true"> </span>');
			htmlIsoTags.push('<span role="spinbutton" class="datetime-edit-hour-field" contenteditable="true" aria-placeholder="hh" aria-valuemin="0" aria-valuemax="23"></span>');
			htmlIsoTags.push('<span role="separator" class="datetime-delimiter" aria-hidden="true">:</span>');
			htmlIsoTags.push('<span role="spinbutton" class="datetime-edit-minute-field" contenteditable="true" aria-placeholder="mm" aria-valuemin="0" aria-valuemax="59"></span>');
		}
		if (this.inputElement.getAttribute('date-format') === 'iso') {
			htmlTags.push(...htmlIsoTags);
			this.inputFieldsOrder.push(...[0, 1, 2]);
		} else {
			// try to determine the desired date format by evaluating the navigator's locale settings
			this.dateTimeFormat = Intl.DateTimeFormat(navigator.language, {
				year: 'numeric',
				month: '2-digit',
				day: '2-digit',
				hour: '2-digit',
				minute: '2-digit',
				hour12: false,
				calendar: 'iso8601',
			});
			this.dateTimeFormat.formatToParts().forEach(part => {
				switch (part.type) {
					case 'year':
						htmlTags.push(htmlIsoTags[0]);
						this.inputFieldsOrder.push(0);
						break;
					case 'month':
						htmlTags.push(htmlIsoTags[2]);
						this.inputFieldsOrder.push(1);
						break;
					case 'day':
						htmlTags.push(htmlIsoTags[4]);
						this.inputFieldsOrder.push(2);
						break;
					case 'literal':
						if (['.', '/', '-'].includes(part.value)) {
							htmlTags.push(`<span role="separator" class="datetime-delimiter" aria-hidden="true">${part.value}</span>`);
						}
						if (!this.dateOnly) {
							if ([', ', ' '].includes(part.value)) {
								htmlTags.push(htmlIsoTags[5]);
							}
							if ([':'].includes(part.value)) {
								htmlTags.push(htmlIsoTags[7]);
							}
						}
						break;
					case 'hour':
						if (!this.dateOnly) {
							htmlTags.push(htmlIsoTags[6]);
							this.inputFieldsOrder.push(3);
						}
						break;
					case 'minute':
						if (!this.dateOnly) {
							htmlTags.push(htmlIsoTags[8]);
							this.inputFieldsOrder.push(4);
						}
						break;
					default:
						break;
				}
			});
		}
		htmlTags.push('</div>');
		htmlTags.push('<span class="calendar-picker-indicator"></span>');
		htmlTags.push('</div>');
		this.inputElement.insertAdjacentHTML('afterend', htmlTags.join(''));
		return this.inputElement.nextElementSibling as HTMLElement;
	}

	private installEventHandlers() {
		this.inputFields[FieldPart.year] = this.textBox.querySelector('.datetime-edit-year-field')!;
		this.inputFields[FieldPart.month] = this.textBox.querySelector('.datetime-edit-month-field')!;
		this.inputFields[FieldPart.day] = this.textBox.querySelector('.datetime-edit-day-field')!;
		if (!this.dateOnly) {
			this.inputFields[FieldPart.hour] = this.textBox.querySelector('.datetime-edit-hour-field')!;
			this.inputFields[FieldPart.minute] = this.textBox.querySelector('.datetime-edit-minute-field')!;
		}
		this.inputFields.forEach(inputField => {
			inputField.addEventListener('focus', this.handleFocus);
			inputField.addEventListener('blur', this.handleBlur);
		});
		document.addEventListener('click', this.handleClick);
		document.addEventListener('keydown', this.handleKeypress);
	}

	private openCalendar() {
		this.calendar.element.parentElement!.style.position = 'relative';
		this.cleanup = autoUpdate(this.textBox, this.calendar.element, this.updatePosition);
		this.textBox.setAttribute('aria-expanded', 'true');
		this.isOpen = true;
	}

	private closeCalendar() {
		this.isOpen = false;
		this.textBox.setAttribute('aria-expanded', 'false');
		this.cleanup?.();
	}

	private updateInputFields(newDate: Date | null) {
		if (newDate) {
			this.inputFields[FieldPart.year].innerText = String(newDate.getFullYear());
			this.inputFields[FieldPart.month].innerText = String(newDate.getMonth() + 1).padStart(2, '0');
			this.inputFields[FieldPart.day].innerText = String(newDate.getDate()).padStart(2, '0');
			if (!this.dateOnly) {
				this.inputFields[FieldPart.hour].innerText = String(newDate.getHours()).padStart(2, '0');
				this.inputFields[FieldPart.minute].innerText = String(newDate.getMinutes()).padStart(2, '0');
			}
			this.inputElement.value = newDate.toISOString().slice(0, this.dateOnly ? 10 : 16);
		} else {
			this.inputFields.forEach(field => field.innerText = '');
			this.inputElement.value = '';
		}
	}

	private parseInputFields() : Date | null {
		const dateParts = [
			Math.min(Math.max(parseInt(this.inputFields[FieldPart.year].innerText), 1700), 2300).toString(),
			'-',
			Math.min(Math.max(parseInt(this.inputFields[FieldPart.month].innerText), 1), 12).toString().padStart(2, '0'),
			'-',
			Math.min(Math.max(parseInt(this.inputFields[FieldPart.day].innerText), 1), 31).toString().padStart(2, '0'),
		];
		if (!this.dateOnly) {
			dateParts.push('T');
			dateParts.push(Math.min(Math.max(parseInt(this.inputFields[FieldPart.hour].innerText), 0), 23).toString().padStart(2, '0'));
			dateParts.push(':');
			dateParts.push(Math.min(Math.max(parseInt(this.inputFields[FieldPart.minute].innerText), 0), 59).toString().padStart(2, '0'));
		}
		const newDate = new Date(dateParts.join(''));
		return newDate && !isNaN(newDate.getTime()) ? newDate : null;
	}


	private handleClick = (event: Event) => {
		let element = event.target instanceof Element ? event.target : null;
		while (element) {
			if (element === this.calendar.element)
				return;
			if (element === this.calendarOpener!)
				return this.isOpen ? this.closeCalendar() : this.openCalendar();
			element = element.parentElement;
		}
		this.closeCalendar();
	}

	private updatePosition = () => {
		const zIndex = this.textBox.style.zIndex ? parseInt(this.textBox.style.zIndex) : 0;
		computePosition(this.textBox, this.calendar.element, {
			middleware: [flip(), shift()],
		}).then(({y}) => Object.assign(
			this.calendar.element.style, {top: `${y}px`, zIndex: `${zIndex + 1}`}
		));
	}

	private handleFocus = (event: Event) => {
		if (this.inputFields.some(inputField => {
			if (event.target instanceof HTMLElement && inputField === event.target) {
				inputField.ariaBusy = 'true';
				this.hasFocus = inputField;
				return true;
			}
		})) {
			this.textBox.classList.add('focus');
			this.inputElement.dispatchEvent(new Event('focus'));
			event.preventDefault();
		} else {
			this.hasFocus = null;
		}
	}

	private handleBlur = () => {
		setTimeout(() => {
			if (!this.hasFocus) {
				this.textBox.classList.remove('focus');
				this.currentDate = this.parseInputFields();
				this.updateInputFields(this.currentDate);
				if (this.currentDate) {
					this.calendar.updateDate(this.currentDate);
				}
				this.inputElement.dispatchEvent(new Event('blur'));
			}
		}, 0);
		this.hasFocus = null;
		this.inputElement.dispatchEvent(new Event('input'));
	}

	private handleKeypress = async (event: KeyboardEvent) => {
		let preventDefault = false;
		if (this.hasFocus) {
			preventDefault = this.editTextBox(event.key);
		} else if (this.isOpen) {
			preventDefault = await this.calendar.navigate(event.key);
		}
		if (preventDefault) {
			event.preventDefault();
		}
	}

	private editTextBox(key: string) : boolean {
		const hasFocus = this.hasFocus!;
		switch (key) {
			case 'ArrowRight':
				this.nextInputField?.focus();
				return true;
			case 'ArrowLeft':
				this.previousInputField?.focus();
				return true;
			case 'ArrowUp':
				if (hasFocus.innerText) {
					hasFocus.innerText = (parseInt(hasFocus.innerText) + 1).toString().padStart(2, '0');
				} else {
					this.updateInputFields(new Date());
				}
				return true;
			case 'ArrowDown':
				if (hasFocus.innerText) {
					hasFocus.innerText = (parseInt(hasFocus.innerText) - 1).toString().padStart(2, '0');
				} else {
					this.updateInputFields(new Date());
				}
				return true;
			case 'Backspace': case 'Delete':
				if (hasFocus.ariaBusy === 'true') {
					hasFocus.innerText = '';
					hasFocus.ariaBusy = 'false';
					return true;
				}
				return false;
			case '-': case '/': case '.': case ':': case ' ':
				if (hasFocus.ariaBusy === 'false') {
					this.nextInputField?.focus();
				}
				return true;
			case '0': case '1': case '2': case '3': case '4': case '5': case '6': case '7': case '8': case '9':
				if (hasFocus.ariaBusy === 'true') {
					hasFocus.innerText = '';
					hasFocus.ariaBusy = 'false';
				}
				const maxLength = hasFocus.ariaPlaceholder?.length ?? 0;
				if (hasFocus.innerText.length === maxLength - 1) {
					setTimeout(() => this.nextInputField?.focus(), 0);
				}
				return hasFocus.innerText.length === maxLength;
			default:
				return true;
		}
	}

	private get previousInputField() : HTMLElement | undefined {
		const hasFocus = this.hasFocus!;
		const index = this.inputFieldsOrder.indexOf(this.inputFields.indexOf(hasFocus));
		if (index > 0)
			return this.inputFields[this.inputFieldsOrder[index - 1]];
	}

	private get nextInputField() : HTMLElement | undefined {
		const hasFocus = this.hasFocus!;
		const index = this.inputFieldsOrder.indexOf(this.inputFields.indexOf(hasFocus));
		if (index < this.inputFieldsOrder.length - 1)
			return this.inputFields[this.inputFieldsOrder[index + 1]];
	}

	private transferStyles() {
		for (let k = 0; k < document.styleSheets.length; ++k) {
			// prevent adding <styles> multiple times with the same content by checking if they already exist
			const cssRule = document?.styleSheets?.item(k)?.cssRules?.item(0);
			if (cssRule instanceof CSSStyleRule && cssRule.selectorText!.startsWith(':is([is="django-datepicker"], [is="django-datetimepicker"])'))
				return;
		}
		const declaredStyles = document.createElement('style');
		declaredStyles.innerText = styles;
		document.head.appendChild(declaredStyles);
		this.inputElement.style.transition = 'none';  // prevent transition while pilfering styles
		const inputHeight = window.getComputedStyle(this.inputElement).getPropertyValue('height');
		for (let index = 0; declaredStyles.sheet && index < declaredStyles.sheet.cssRules.length; index++) {
			const cssRule = declaredStyles.sheet.cssRules.item(index) as CSSStyleRule;
			let extraStyles: string;
			switch (cssRule.selectorText) {
				case ':is([is="django-datepicker"], [is="django-datetimepicker"])':
					break;
				case ':is([is="django-datepicker"], [is="django-datetimepicker"]) + [role="textbox"]':
					extraStyles = StyleHelpers.extractStyles(this.inputElement, [
						'background-color', 'border', 'color', 'outline', 'height', 'line-height', 'padding']);
					declaredStyles.sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case ':is([is="django-datepicker"], [is="django-datetimepicker"]) + [role="textbox"].focus':
					this.inputElement.classList.add('-focus-');
					extraStyles = StyleHelpers.extractStyles(this.inputElement, [
						'background-color', 'border', 'box-shadow', 'color', 'outline', 'transition']);
					this.inputElement.classList.remove('-focus-');
					declaredStyles.sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				default:
					break;
			}
		}
		this.inputElement.style.transition = '';
	}

	private transferClasses() {
		this.inputElement.classList.forEach(className => {
			this.textBox.classList.add(className);
		});
		this.inputElement.classList.remove(...this.inputElement.classList);
		this.inputElement.style.transition = '';
		this.inputElement.hidden = true;  // setting type="hidden" prevents dispatching events
	}

	protected formResetted(event: Event) {
		this.inputElement.value = this.inputElement.defaultValue;
		this.setInitialDate();
		this.updateInputFields(this.currentDate);
	}

	protected formSubmitted(event: Event) {}

	public valueAsDate() : Date | null {
		return this.currentDate;
	}
}

const DTP = Symbol('DateTimePickerElement');

export class DatePickerElement extends HTMLInputElement {
	private [DTP]!: DateTimePicker;  // hides internal implementation

	connectedCallback() {
		const fieldGroup = this.closest('[role="group"]');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		const calendarElement = fieldGroup.querySelector('[aria-label="calendar"]');
		this[DTP] = new DateTimePicker(this, calendarElement as HTMLElement);
	}

	get valueAsDate() : Date | null {
		return this[DTP].valueAsDate();
	}
}


export class DateTimePickerElement extends HTMLInputElement {
	private [DTP]!: DateTimePicker;  // hides internal implementation

	connectedCallback() {
		const fieldGroup = this.closest('[role="group"]');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		const calendarElement = fieldGroup.querySelector('[aria-label="calendar"]');
		this[DTP] = new DateTimePicker(this, calendarElement as HTMLElement);
	}

	get valueAsDate() : Date | null {
		return this[DTP].valueAsDate();
	}
}
