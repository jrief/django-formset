import {autoUpdate, computePosition, flip, shift} from '@floating-ui/dom';
import {Calendar, CalendarSettings} from "./Calendar";
import {Widget} from './Widget';
import {StyleHelpers} from './helpers';
import styles from './DateTime.scss';
import calendarIcon from './icons/calendar.svg';


enum FieldPart {
	year,
	month,
	day,
	hour,
	minute,
	yearExt,
	monthExt,
	dayExt,
	hourExt,
	minuteExt,
}


class DateTimeField extends Widget {
	private readonly inputElement: HTMLInputElement;
	private readonly textBox: HTMLElement;
	private readonly dateOnly: boolean;
	private readonly withRange: boolean;
	private readonly calendar: Calendar | null = null;
	private readonly inputFields: Array<HTMLElement> = [];
	private readonly inputFieldsOrder: Array<number> = [];
	private readonly baseSelector = '[is^="django-date"]';
	private hour12: boolean = false;
	private currentDate: Date | null = null;  // when withRange=true, this is the lower bound
	private extendedDate: Date | null = null;  // when withRange=true, this is the upper bound, otherwise unused
	private calendarOpener: HTMLElement | null = null;
	private dateTimeFormat?: Intl.DateTimeFormat;
	private hasFocus: HTMLElement | null = null;
	private cleanup?: Function;
	private isOpen: boolean = false;

	constructor(inputElement: HTMLInputElement, calendarElement: HTMLElement | null) {
		super(inputElement);
		this.inputElement = inputElement;
		this.dateOnly = ['django-datefield', 'django-datepicker', 'django-daterangefield', 'django-daterangepicker'].includes(inputElement.getAttribute('is') ?? '');
		this.withRange = ['django-daterangefield', 'django-daterangepicker', 'django-datetimerangefield', 'django-datetimerangepicker'].includes(inputElement.getAttribute('is') ?? '');
		this.textBox = this.createTextBox();
		this.setInitialDate();
		if (calendarElement) {
			this.calendar = new Calendar(calendarElement, this.getCalendarSettings());
			const calendarOpener = this.textBox.querySelector('.calendar-picker-indicator');
			if (!(calendarOpener instanceof HTMLElement))
				throw new Error("Missing selector .calendar-picker-indicator");
			this.calendarOpener = calendarOpener;
			this.calendarOpener.innerHTML = calendarIcon;
		}
		this.installEventHandlers();
		if (!StyleHelpers.stylesAreInstalled(this.baseSelector)) {
			this.transferStyles();
		}
		this.transferClasses();
		this.updateInputFields();
	}

	private setInitialDate() {
		const value = this.inputElement.value;
		if (value) {
			if (this.withRange) {
				const [start, end] = value.split(';');
				this.currentDate = start ? new Date(start) : null;
				this.extendedDate = end ? new Date(end) : null;
			} else {
				this.currentDate = new Date(value);
				this.extendedDate = null;
			}
		} else {
			this.currentDate = this.extendedDate = null;
		}
	}

	private updateDate(currentDate: Date, extendedDate: Date|null|boolean) {
		if (this.withRange && extendedDate instanceof Date) {
			this.currentDate = currentDate;
			this.extendedDate = extendedDate;
		} else {
			this.currentDate = currentDate;
		}
		this.updateInputFields();
		if (extendedDate) {
			this.inputElement.dispatchEvent(new Event('input'));
			this.inputElement.dispatchEvent(new Event('blur'));
		}
	}

	private getCalendarSettings() : CalendarSettings {
		const settings: CalendarSettings = {
			dateOnly: this.dateOnly,
			withRange: this.withRange,
			pure: false,
			inputElement: this.inputElement,
			hour12: this.hour12,
			updateDate: (currentDate: Date, extendedDate: Date|null|boolean) => this.updateDate(currentDate, extendedDate),
			close: () => this.closeCalendar(),
		};
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
			htmlIsoTags.push('<span role="separator" class="datetime-delimiter wide" aria-hidden="true"> </span>');
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
				calendar: 'iso8601',
			});
			this.hour12 = this.dateTimeFormat.resolvedOptions().hour12 ?? false;
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
		if (this.withRange) {
			htmlTags.push('<span role="separator" class="datetime-delimiter wide" aria-hidden="true">–</span>');
			htmlTags.push(...htmlTags.slice(2, -1));
			this.inputFieldsOrder.push(...this.inputFieldsOrder.map(i => i + 5));
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
		if (this.withRange) {
			this.inputFields[FieldPart.yearExt] = this.textBox.querySelector('.datetime-edit-year-field ~ .datetime-edit-year-field')!;
			this.inputFields[FieldPart.monthExt] = this.textBox.querySelector('.datetime-edit-month-field ~ .datetime-edit-month-field')!;
			this.inputFields[FieldPart.dayExt] = this.textBox.querySelector('.datetime-edit-day-field ~ .datetime-edit-day-field')!;
			if (!this.dateOnly) {
				this.inputFields[FieldPart.hourExt] = this.textBox.querySelector('.datetime-edit-hour-field ~ .datetime-edit-hour-field')!;
				this.inputFields[FieldPart.minuteExt] = this.textBox.querySelector('.datetime-edit-minute-field ~ .datetime-edit-minute-field')!;
			}
		}
		this.inputFields.forEach(inputField => {
			inputField.addEventListener('focus', this.handleFocus);
			inputField.addEventListener('blur', this.handleBlur);
		});
		document.addEventListener('click', this.handleClick);
		document.addEventListener('keydown', this.handleKeypress);
	}

	private openCalendar() {
		if (!this.calendarOpener)
			return;
		this.calendar!.element.parentElement!.style.position = 'relative';
		this.cleanup = autoUpdate(this.textBox, this.calendar!.element, this.updatePosition);
		this.textBox.setAttribute('aria-expanded', 'true');
		this.isOpen = true;
		this.calendar!.updateDate(this.currentDate, this.extendedDate);
	}

	private closeCalendar() {
		this.isOpen = false;
		this.textBox.setAttribute('aria-expanded', 'false');
		this.cleanup?.();
	}

	private updateInputFields() {
		const setDateParts = (newDate: Date, year: FieldPart, month: FieldPart, day: FieldPart, hour: FieldPart, minute: FieldPart) => {
			this.inputFields[year].innerText = String(newDate.getFullYear());
			this.inputFields[month].innerText = String(newDate.getMonth() + 1).padStart(2, '0');
			this.inputFields[day].innerText = String(newDate.getDate()).padStart(2, '0');
			if (!this.dateOnly) {
				this.inputFields[hour].innerText = String(newDate.getHours()).padStart(2, '0');
				this.inputFields[minute].innerText = String(newDate.getMinutes()).padStart(2, '0');
			}
		}
		if (this.currentDate) {
			setDateParts(this.currentDate, FieldPart.year, FieldPart.month, FieldPart.day, FieldPart.hour, FieldPart.minute);
			this.inputElement.value = this.currentDate.toISOString().slice(0, this.dateOnly ? 10 : 16);
			if (this.extendedDate) {
				setDateParts(this.extendedDate, FieldPart.yearExt, FieldPart.monthExt, FieldPart.dayExt, FieldPart.hourExt, FieldPart.minuteExt);
				this.inputElement.value = [
					this.inputElement.value,
					this.extendedDate.toISOString().slice(0, this.dateOnly ? 10 : 16),
				].join(';');
			}
		} else {
			this.inputFields.forEach(field => field.innerText = '');
			this.inputElement.value = '';
		}
	}

	private parseInputFields() {
		const getDateParts = (year: FieldPart, month: FieldPart, day: FieldPart, hour: FieldPart, minute: FieldPart) : string[] => {
			const dateParts = [
				Math.min(Math.max(parseInt(this.inputFields[year].innerText), 1700), 2300).toString(),
				'-',
				Math.min(Math.max(parseInt(this.inputFields[month].innerText), 1), 12).toString().padStart(2, '0'),
				'-',
				Math.min(Math.max(parseInt(this.inputFields[day].innerText), 1), 31).toString().padStart(2, '0'),
			];
			if (!this.dateOnly) {
				dateParts.push('T');
				dateParts.push(Math.min(Math.max(parseInt(this.inputFields[hour].innerText), 0), 23).toString().padStart(2, '0'));
				dateParts.push(':');
				dateParts.push(Math.min(Math.max(parseInt(this.inputFields[minute].innerText), 0), 59).toString().padStart(2, '0'));
			}
			return dateParts;
		};
		const dateParts = getDateParts(FieldPart.year, FieldPart.month, FieldPart.day, FieldPart.hour, FieldPart.minute);
		const newDate = new Date(dateParts.join(''));
		if (newDate && !isNaN(newDate.getTime())) {
			this.currentDate = newDate;
			if (this.withRange) {
				const datePartsExt = getDateParts(FieldPart.yearExt, FieldPart.monthExt, FieldPart.dayExt, FieldPart.hourExt, FieldPart.minuteExt);
				const newDateExt = new Date(datePartsExt.join(''));
				if (newDateExt && !isNaN(newDateExt.getTime())) {
					this.extendedDate = newDateExt;
				} else {
					this.extendedDate = null;
				}
			}
		} else {
			this.currentDate = this.extendedDate = null;
		}
	}


	private handleClick = (event: Event) => {
		if (!this.calendar)
			return;
		let element = event.target instanceof Element ? event.target : null;
		while (element) {
			if (element === this.calendar.element)
				return;
			if (element === this.calendarOpener)
				return this.isOpen ? this.closeCalendar() : this.openCalendar();
			element = element.parentElement;
		}
		this.closeCalendar();
	}

	private updatePosition = () => {
		if (!this.calendar)
			return;
		const zIndex = this.textBox.style.zIndex ? parseInt(this.textBox.style.zIndex) : 0;
		computePosition(this.textBox, this.calendar.element, {
			middleware: [flip(), shift()],
		}).then(({y}) => Object.assign(
			this.calendar!.element.style, {top: `${y}px`, zIndex: `${zIndex + 1}`}
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
				this.parseInputFields();
				this.updateInputFields();
				this.calendar?.updateDate(this.currentDate, this.extendedDate);
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
			preventDefault = await this.calendar?.navigate(event.key) ?? false;
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
					let value = parseInt(hasFocus.ariaValueMax ?? '0');
					value = Math.min(value, parseInt(hasFocus.innerText) + 1);
					hasFocus.innerText = value.toString().padStart(2, '0');
				} else {
					if (this.inputFields.indexOf(hasFocus) < 5) {
						this.currentDate = new Date();
					} else if (this.withRange) {
						this.currentDate = this.currentDate ?? new Date();
						this.extendedDate = new Date();
					}
					this.updateInputFields();
				}
				return true;
			case 'ArrowDown':
				if (hasFocus.innerText) {
					let value = parseInt(hasFocus.ariaValueMin ?? '0');
					value = Math.max(value, parseInt(hasFocus.innerText) - 1);
					hasFocus.innerText = value.toString().padStart(2, '0');
				} else {
					if (this.inputFields.indexOf(hasFocus) < 5) {
						this.currentDate = new Date();
					} else if (this.withRange) {
						this.currentDate = this.currentDate ?? new Date();
						this.extendedDate = new Date();
					}
					this.updateInputFields();
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
		const declaredStyles = document.createElement('style');
		let loaded = false;
		declaredStyles.innerText = styles;
		document.head.appendChild(declaredStyles);
		this.inputElement.style.transition = 'none';  // prevent transition while pilfering styles
		for (let index = 0; declaredStyles.sheet && index < declaredStyles.sheet.cssRules.length; index++) {
			const cssRule = declaredStyles.sheet.cssRules.item(index) as CSSStyleRule;
			let extraStyles: string;
			switch (cssRule.selectorText) {
				case this.baseSelector:
					loaded = true;
					break;
				case `${this.baseSelector} + [role="textbox"]`:
					extraStyles = StyleHelpers.extractStyles(this.inputElement, [
						'background-color', 'border', 'color', 'outline', 'height', 'line-height', 'padding']);
					declaredStyles.sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case `${this.baseSelector} + [role="textbox"].focus`:
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
		if (!loaded)
			throw new Error(`Could not load styles for ${this.baseSelector}`);
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
		this.updateInputFields();
	}

	protected formSubmitted(event: Event) {}

	public valueAsDate() : Date | null {
		return this.currentDate;
	}

	public checkValidity() : boolean {
		if (this.withRange && this.currentDate && this.extendedDate) {
			if (this.currentDate > this.extendedDate) {
				const message = this.errorMessages.get('customError') ?? "Start date must be before end date";
				this.inputElement.setCustomValidity(message);
				return false;
			}
		}
		return true;
	}
}

const DT = Symbol('DateTime');

export class DateFieldElement extends HTMLInputElement {
	private [DT]!: DateTimeField;  // hides internal implementation

	connectedCallback() {
		const fieldGroup = this.closest('[role="group"]');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		this[DT] = new DateTimeField(this, null);
	}

	get valueAsDate() : Date | null {
		return this[DT].valueAsDate();
	}
}

export class DatePickerElement extends HTMLInputElement {
	private [DT]!: DateTimeField;  // hides internal implementation

	connectedCallback() {
		const fieldGroup = this.closest('[role="group"]');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		const calendarElement = fieldGroup.querySelector('[aria-label="calendar"]');
		this[DT] = new DateTimeField(this, calendarElement as HTMLElement);
	}

	get valueAsDate() : Date | null {
		return this[DT].valueAsDate();
	}
}

export class DateTimeFieldElement extends HTMLInputElement {
	private [DT]!: DateTimeField;  // hides internal implementation

	connectedCallback() {
		const fieldGroup = this.closest('[role="group"]');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		this[DT] = new DateTimeField(this, null);
	}

	get valueAsDate() : Date | null {
		return this[DT].valueAsDate();
	}
}

export class DateTimePickerElement extends HTMLInputElement {
	private [DT]!: DateTimeField;  // hides internal implementation

	connectedCallback() {
		const fieldGroup = this.closest('[role="group"]');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		const calendarElement = fieldGroup.querySelector('[aria-label="calendar"]');
		this[DT] = new DateTimeField(this, calendarElement as HTMLElement);
	}

	get valueAsDate() : Date | null {
		return this[DT].valueAsDate();
	}
}

export class DateRangeFieldElement extends HTMLInputElement {
	private [DT]!: DateTimeField;  // hides internal implementation

	connectedCallback() {
		const fieldGroup = this.closest('[role="group"]');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		this[DT] = new DateTimeField(this, null);
	}

	public checkValidity() {
		if (!super.checkValidity())
			return false;
		return this[DT].checkValidity();
	}
}


export class DateRangePickerElement extends HTMLInputElement {
	private [DT]!: DateTimeField;  // hides internal implementation

	connectedCallback() {
		const fieldGroup = this.closest('[role="group"]');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		const calendarElement = fieldGroup.querySelector('[aria-label="calendar"]');
		this[DT] = new DateTimeField(this, calendarElement as HTMLElement);
	}

	public checkValidity() {
		if (!super.checkValidity())
			return false;
		return this[DT].checkValidity();
	}
}

export class DateTimeRangeFieldElement extends HTMLInputElement {
	private [DT]!: DateTimeField;  // hides internal implementation

	connectedCallback() {
		const fieldGroup = this.closest('[role="group"]');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		this[DT] = new DateTimeField(this, null);
	}

	public checkValidity() {
		if (!super.checkValidity())
			return false;
		return this[DT].checkValidity();
	}
}

export class DateTimeRangePickerElement extends HTMLInputElement {
	private [DT]!: DateTimeField;  // hides internal implementation

	connectedCallback() {
		const fieldGroup = this.closest('[role="group"]');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		const calendarElement = fieldGroup.querySelector('[aria-label="calendar"]');
		this[DT] = new DateTimeField(this, calendarElement as HTMLElement);
	}

	public checkValidity() {
		if (!super.checkValidity())
			return false;
		return this[DT].checkValidity();
	}
}
