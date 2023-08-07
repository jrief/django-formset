import {autoUpdate, computePosition, flip, shift} from '@floating-ui/dom';
import {StyleHelpers, Widget} from './helpers';
import styles from './DateTimePicker.scss';
import calendarIcon from './icons/calendar.svg';


enum ViewMode {
	hours = 'h',
	weeks = 'w',
	months = 'm',
	years = 'y',
}


enum FieldPart {
	year,
	month,
	day,
	hour,
	minute,
}


enum Direction {
	up,
	right,
	down,
	left,
}


class Calendar extends Widget {
	private readonly inputElement: HTMLInputElement;
	private readonly textBox: HTMLElement;
	private readonly dateOnly: Boolean;
	private readonly calendarElement: HTMLElement;
	private readonly inputFields: Array<HTMLElement> = [];
	private readonly inputFieldsOrder: Array<number> = [];
	private currentDate: Date | null = null;
	private calendarOpener: HTMLElement;
	private viewMode!: ViewMode;
	private dateTimeFormat?: Intl.DateTimeFormat;
	private cleanup?: Function;
	private minDate?: Date;
	private maxDate?: Date;
	private minWeekDate?: Date;
	private maxWeekDate?: Date;
	private minMonthDate?: Date;
	private maxMonthDate?: Date;
	private minYearDate?: Date;
	private maxYearDate?: Date;
	private interval?: number;
	private hasFocus: HTMLElement | null = null;
	private isOpen = false;
	private prevSheetDate!: Date;
	private nextSheetDate!: Date;
	private narrowSheetDate?: Date;
	private extendSheetDate?: Date;
	private calendarItems!: NodeListOf<HTMLLIElement>;

	constructor(inputElement: HTMLInputElement, calendarElement: Element | null) {
		super(inputElement);
		this.inputElement = inputElement;
		this.dateOnly = inputElement.getAttribute('is') === 'django-datepicker';
		this.textBox = this.createTextBox();
		this.setInitialDate();
		if (calendarElement instanceof HTMLElement) {
			this.calendarElement = calendarElement;
		} else {
			this.calendarElement = document.createElement('div');
			this.fetchCalendar(new Date(), ViewMode.weeks);
		}
		const calendarOpener = this.textBox.querySelector('.calendar-picker-indicator');
		if (!(calendarOpener instanceof HTMLElement))
			throw new Error("Missing selectot .calendar-picker-indicator");
		this.calendarOpener = calendarOpener;
		this.calendarOpener.innerHTML = calendarIcon;
		this.setBounds();
		this.installEventHandlers();
		const observer = new MutationObserver(() => this.registerCalendar());
		observer.observe(this.calendarElement, {childList: true});
		this.transferStyles();
		this.transferClasses();
		this.registerCalendar();
		this.updateInputFields(this.currentDate);
	}

	private get currentDateString() : string {
		return this.currentDate ? this.asUTCDate(this.currentDate).toISOString().slice(0, 16) : '';
	}

	private get todayDateString() : string {
		return this.asUTCDate(new Date()).toISOString().slice(0, 16);
	}

	private getViewMode() : ViewMode {
		const label = this.calendarElement.querySelector(':scope > [aria-label]')?.getAttribute('aria-label');
		switch (label) {
			case 'hours-view':
				return ViewMode.hours;
			case 'weeks-view':
				return ViewMode.weeks;
			case 'months-view':
				return ViewMode.months;
			case 'years-view':
				return ViewMode.years;
			default:
				throw new Error(`Unknown aria-label on ${this.calendarElement}`);
		}
	}

	private setInitialDate() {
		this.currentDate = this.inputElement.value ? new Date(this.inputElement.value) : null;
	}

	private setBounds() {
		const minValue = this.inputElement.getAttribute('min');
		if (minValue) {
			this.minDate = new Date(minValue);
			this.minWeekDate = new Date(this.minDate);
			this.minWeekDate.setHours(0, 0, 0);
			this.minMonthDate = new Date(this.minWeekDate);
			this.minMonthDate.setDate(1);
			this.minYearDate = new Date(this.minMonthDate);
			this.minYearDate.setMonth(0);
		}
		const maxValue = this.inputElement.getAttribute('max');
		if (maxValue) {
			this.maxDate = new Date(maxValue);
			this.maxWeekDate = new Date(this.maxDate);
			this.maxWeekDate.setHours(23, 59, 59);
			this.maxMonthDate = new Date(this.maxWeekDate);
			this.maxMonthDate.setDate(28);
			this.maxYearDate = new Date(this.maxMonthDate);
			this.maxYearDate.setMonth(11);
		}
		const step = this.inputElement.getAttribute('step');
		if (step) {
			const d1 = new Date('1970-01-01 0:00:00');
			const d2 = new Date(`1970-01-01 ${step}`);
			this.interval = (d2.getTime() - d1.getTime()) / 60000;
		}
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
		this.calendarElement.parentElement!.style.position = 'relative';
		this.cleanup = autoUpdate(this.textBox, this.calendarElement, this.updatePosition);
		this.textBox.setAttribute('aria-expanded', 'true');
		this.isOpen = true;
	}

	private closeCalendar() {
		this.isOpen = false;
		this.textBox.setAttribute('aria-expanded', 'false');
		this.cleanup?.();
	}

	private asUTCDate(date: Date) : Date {
		return new Date(date.getTime() - date.getTimezoneOffset() * 60000);
	}

	private getDate(selector: string | Element) : Date {
		const element = selector instanceof Element ? selector : this.calendarElement.querySelector(selector);
		if (!(element instanceof Element))
			throw new Error(`Element ${selector} is missing`);
		const dateValue = element.getAttribute('data-date') ?? element.getAttribute('datetime');
		return new Date(dateValue ?? '');
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

	private registerCalendar() {
		this.viewMode = this.getViewMode();
		this.prevSheetDate = this.getDate('button.prev');
		const narrowButton = this.calendarElement.querySelector('button.narrow');
		this.narrowSheetDate = narrowButton ? this.getDate(narrowButton) : undefined;
		this.nextSheetDate = this.getDate('button.next');
		const extendButton = this.calendarElement.querySelector('button.extend');
		this.extendSheetDate = extendButton ? this.getDate(extendButton) : undefined;
		this.calendarElement.querySelector('button.prev')?.addEventListener('click', this.turnPrev, {once: true});
		this.calendarElement.querySelector('button.narrow')?.addEventListener('click', this.turnNarrow, {once: true});
		this.calendarElement.querySelector('button.extend')?.addEventListener('click', this.turnExtend, {once: true});
		this.calendarElement.querySelector('button.today')?.addEventListener('click', this.turnToday, {once: true});
		this.calendarElement.querySelector('button.next')?.addEventListener('click', this.turnNext, {once: true});
		this.calendarItems = this.calendarElement.querySelectorAll('li[data-date]');
		switch (this.viewMode) {
			case ViewMode.hours:
				this.registerHoursView();
				break;
			case ViewMode.weeks:
				this.registerWeeksView();
				break;
			case ViewMode.months:
				this.registerMonthsView();
				break;
			case ViewMode.years:
				this.registerYearsView();
				break;
		}
		// insert the date of today into a text element inside the calendar icon
		const textElem = this.calendarElement.querySelector('button.today > svg > text');
		if (textElem instanceof SVGTextElement) {
			textElem.textContent = String((new Date()).getDate());
		}
	}

	private registerHoursView() {
		// since each datetime-picker can have different values, set this on element level
		if (this.interval) {
			const num = Math.min(60 / this.interval!, 6);
			const gridTemplateColumns = `repeat(${num}, 1fr)`;
			this.calendarElement.querySelectorAll('.ranges ul.minutes').forEach(minutesElement => {
				(minutesElement as HTMLElement).style.gridTemplateColumns = gridTemplateColumns;
			});
		}

		const currentDateString = this.currentDateString.slice(0, 16);
		this.calendarItems.forEach(elem => {
			elem.classList.toggle('selected', elem.getAttribute('data-date') === currentDateString);
			const date = this.getDate(elem);
			if (this.minDate && date < this.minDate || this.maxDate && date > this.maxDate) {
				elem.toggleAttribute('disabled', true);
			} else {
				elem.addEventListener('click', (event: Event) => {
					if (event.target instanceof HTMLLIElement) {
						this.selectDate(event.target);
					}
				}, {once: true});
			}
		});

		const todayHourString = this.todayDateString.slice(0, 13).concat(':00');
		this.calendarElement.querySelectorAll('li[aria-label]').forEach(elem => {
			const label = elem.getAttribute('aria-label')!;
			elem.classList.toggle('today', label === todayHourString);
			const selector = `ul[aria-labelledby="${label}"]`;
			if (label.slice(0, 13) === currentDateString.slice(0, 13)) {
				elem.classList.add('preselected');
				this.calendarElement.querySelector(selector)?.removeAttribute('hidden');
			}

			if (this.calendarElement.querySelectorAll(`${selector} > li[data-date]:not([disabled])`).length === 0) {
				elem.toggleAttribute('disabled', true);
			} else {
				elem.addEventListener('click', (event: Event) => {
					if (event.target instanceof HTMLLIElement) {
						this.selectHour(event.target);
					}
				});
			}
		});
	}

	private registerWeeksView() {
		const todayDateString = this.todayDateString.slice(0, 10);
		const currentDateString = this.currentDateString.slice(0, 10);
		this.calendarItems.forEach(elem => {
			elem.classList.toggle('today', elem.getAttribute('data-date') === todayDateString);
			elem.classList.toggle('selected', elem.getAttribute('data-date') === currentDateString);
			const date = this.getDate(elem);
			if (this.minWeekDate && date < this.minWeekDate || this.maxWeekDate && date > this.maxWeekDate) {
				elem.toggleAttribute('disabled', true);
			} else {
				elem.addEventListener('click', this.selectDay);
			}
		});
	}

	private registerMonthsView() {
		const todayMonthString = this.todayDateString.slice(0, 7);
		const currentMonthString = this.currentDateString.slice(0, 7);
		this.calendarItems.forEach(elem => {
			const date = this.getDate(elem);
			const monthString = elem.getAttribute('data-date')?.slice(0, 7);
			elem.classList.toggle('today', monthString === todayMonthString);
			elem.classList.toggle('selected', monthString === currentMonthString);
			if (this.minMonthDate && date < this.minMonthDate || this.maxMonthDate && date > this.maxMonthDate) {
				elem.toggleAttribute('disabled', true);
			} else {
				elem.addEventListener('click', this.selectMonth);
			}
		});
	}

	private registerYearsView() {
		const todayYearString = this.todayDateString.slice(0, 4);
		const currentYearString = this.currentDateString.slice(0, 4);
		this.calendarItems.forEach(elem => {
			const date = this.getDate(elem);
			const yearString = elem.getAttribute('data-date')?.slice(0, 4);
			elem.classList.toggle('today', yearString === todayYearString);
			elem.classList.toggle('selected', yearString === currentYearString);
			if (this.minYearDate && date < this.minYearDate || this.maxYearDate && date > this.maxYearDate) {
				elem.toggleAttribute('disabled', true);
			} else {
				elem.addEventListener('click', this.selectYear);
			}
		});
	}

	private handleClick = (event: Event) => {
		let element = event.target instanceof Element ? event.target : null;
		while (element) {
			if (element === this.calendarElement)
				return;
			if (element === this.calendarOpener!)
				return this.isOpen ? this.closeCalendar() : this.openCalendar();
			element = element.parentElement;
		}
		this.closeCalendar();
	}

	private updatePosition = () => {
		const zIndex = this.textBox.style.zIndex ? parseInt(this.textBox.style.zIndex) : 0;
		computePosition(this.textBox, this.calendarElement, {
			middleware: [flip(), shift()],
		}).then(({y}) => Object.assign(
			this.calendarElement.style, {top: `${y}px`, zIndex: `${zIndex + 1}`}
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

	private handleBlur = (event: Event) => {
		setTimeout(() => {
			if (!this.hasFocus) {
				this.textBox.classList.remove('focus');
				this.currentDate = this.parseInputFields();
				this.updateInputFields(this.currentDate);
				if (this.currentDate) {
					this.fetchCalendar(this.currentDate, this.viewMode);
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
			preventDefault = await this.navigateCalendar(event.key);
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

	private async navigateCalendar(key: string) {
		let element = null;
		const nextViewMode = new Map<ViewMode, ViewMode>([
			[ViewMode.years, ViewMode.months],
			[ViewMode.months, ViewMode.weeks],
			[ViewMode.weeks, ViewMode.hours],
		]);
		switch (key) {
			case 'ArrowUp':
				await this.navigate(Direction.up);
				break;
			case 'ArrowRight':
				await this.navigate(Direction.right);
				break;
			case 'ArrowDown':
				await this.navigate(Direction.down);
				break;
			case 'ArrowLeft':
				await this.navigate(Direction.left);
				break;
			case 'Escape':
				this.closeCalendar();
				break;
			case 'Tab':
				this.closeCalendar();
				this.textBox.blur();
				break;
			case 'PageUp':
				element = this.calendarElement.querySelector('button.prev');
				if (element) {
					await this.fetchCalendar(this.getDate(element), this.viewMode);
				}
				break;
			case 'PageDown':
				element = this.calendarElement.querySelector('button.next');
				if (element) {
					await this.fetchCalendar(this.getDate(element), this.viewMode);
				}
				break;
			case 'Enter':
				element = this.calendarElement.querySelector('.ranges .selected');
				if (element) {
					if (this.viewMode === ViewMode.hours || this.viewMode === ViewMode.weeks && this.dateOnly) {
						this.selectDate(element);
					} else {
						await this.fetchCalendar(this.getDate(element), nextViewMode.get(this.viewMode)!);
					}
				}
				break;
			default:
				break;
		}
		return true;
	}

	private getDelta(direction: Direction, lastDate: Date) : Date {
		const deltaHours = (this.interval ?? 60) < 60 ? new Map<Direction, number>([
			[Direction.up, -60],
			[Direction.right, +this.interval!],
			[Direction.down, +60],
			[Direction.left, -this.interval!],
		]) : new Map<Direction, number>([
			[Direction.up, -360],
			[Direction.right, +60],
			[Direction.down, +360],
			[Direction.left, -60],
		]);
		const deltaWeeks = new Map<Direction, number>([
			[Direction.up, -10080],
			[Direction.right, +1440],
			[Direction.down, +10080],
			[Direction.left, -1440],
		]);
		const nextDate = new Date(lastDate);
		switch (this.viewMode) {
		  case ViewMode.hours:
			return new Date(lastDate.getTime() + 60000 * deltaHours.get(direction)!);
		  case ViewMode.weeks:
			return new Date(lastDate.getTime() + 60000 * deltaWeeks.get(direction)!);
		  case ViewMode.months:
			switch (direction) {
			  case Direction.up:
				nextDate.setMonth(nextDate.getMonth() - 3);
				break;
			  case Direction.right:
				nextDate.setMonth(nextDate.getMonth() + 1);
				break;
			  case Direction.down:
				nextDate.setMonth(nextDate.getMonth() + 3);
				break;
			  case Direction.left:
				nextDate.setMonth(nextDate.getMonth() - 1);
				break;
			}
			break;
		  case ViewMode.years:
			switch (direction) {
			  case Direction.up:
				nextDate.setFullYear(lastDate.getFullYear() - 4);
				break;
			  case Direction.right:
				nextDate.setFullYear(lastDate.getFullYear() + 1);
				break;
			  case Direction.down:
				nextDate.setFullYear(lastDate.getFullYear() + 4);
				break;
			  case Direction.left:
				nextDate.setFullYear(lastDate.getFullYear() - 1);
				break;
			}
			break;
		}
		return nextDate;
	}

	private async navigate(direction: Direction) {
		let selectedItem = this.calendarElement.querySelector('li[data-date].selected');
		if (!selectedItem) {
			selectedItem = this.calendarItems.item(this.calendarItems.length / 2);
		}
		if (selectedItem) {
			const selectedDate = this.getDate(selectedItem);
			const nextDate = this.getDelta(direction, selectedDate);
			const dataDateString = this.asUTCDate(nextDate).toISOString().slice(0, this.viewMode === ViewMode.hours ? 16 : 10);
			let nextItem: Element|null = null;
			if (this.viewMode !== ViewMode.weeks || selectedDate.getMonth() === nextDate.getMonth()) {
				nextItem = this.calendarElement.querySelector(`.ranges li[data-date="${dataDateString}"]`);
			}
			if (!nextItem) {
				await this.fetchCalendar(nextDate, this.viewMode);
				nextItem = this.calendarElement.querySelector(`.ranges li[data-date="${dataDateString}"]`);
			}
			if (nextItem instanceof HTMLLIElement) {
				if (this.viewMode === ViewMode.hours) {
					this.selectHour(nextItem);
				}
				this.setDate(nextItem);
			}
		}
	}

	private turnPrev = () => {
		this.fetchCalendar(this.prevSheetDate, this.viewMode);
	}

	private turnNext = () => {
		this.fetchCalendar(this.nextSheetDate, this.viewMode);
	}

	private turnNarrow = () => {
		if (this.narrowSheetDate) {
			if (this.viewMode === ViewMode.months) {
				this.fetchCalendar(this.narrowSheetDate, ViewMode.weeks);
			} else if (this.viewMode === ViewMode.years) {
				this.fetchCalendar(this.narrowSheetDate, ViewMode.months);
			} else {
				this.fetchCalendar(this.narrowSheetDate, this.viewMode);
			}
		}
	}

	private turnExtend = () => {
		if (this.extendSheetDate) {
			if (this.viewMode === ViewMode.hours) {
				this.fetchCalendar(this.extendSheetDate, ViewMode.weeks);
			} else if (this.viewMode === ViewMode.weeks) {
				this.fetchCalendar(this.extendSheetDate, ViewMode.months);
			} else {
				this.fetchCalendar(this.extendSheetDate, ViewMode.years);
			}
		}
	}

	private turnToday = () => {
		if (this.dateOnly) {
			this.selectToday();
		} else {
			this.fetchCalendar(new Date(), ViewMode.hours);
		}
	}

	private async selectToday() {
		const todayDateString = this.todayDateString.slice(0, 10);
		let todayElem = this.calendarElement.querySelector(`li[data-date="${todayDateString}"]`);
		if (!todayElem) {
			await this.fetchCalendar(new Date(), ViewMode.weeks);
			todayElem = this.calendarElement.querySelector(`li[data-date="${todayDateString}"]`);
		}
		this.selectDate(todayElem!);
	}

	private setDate(element: Element) {
		this.calendarItems.forEach(elem => {
			elem.classList.toggle('selected', elem === element);
		});
		let dateString = element.getAttribute('data-date')!;
		this.currentDate = new Date(dateString);
		this.updateInputFields(this.currentDate);
		this.inputElement.dispatchEvent(new Event('input'));
		this.inputElement.dispatchEvent(new Event('blur'));
	}

	private selectDate(element: Element) {
		this.setDate(element);
		this.closeCalendar();
	}

	private selectHour(liElement: HTMLLIElement) {
		const selectMinute = (ulElem: HTMLUListElement) => {
			ulElem.querySelectorAll('li[data-date]').forEach(elem => {
				elem.addEventListener('click', event => {
					if (event.target instanceof HTMLLIElement) {
						event.target.classList.add('selected');
						this.selectDate(event.target);
					}
				}, {once: true});
			});
		}

		this.calendarElement.querySelectorAll('li[aria-label]').forEach(elem => {
			elem.classList.remove('selected', 'preselected');
		});
		this.calendarElement.querySelectorAll('ul[aria-labelledby]').forEach(elem => {
			elem.toggleAttribute('hidden', true);
		});
		const label = liElement.getAttribute('aria-label');
		if (label) {
			const ulElem = this.calendarElement.querySelector(`ul[aria-labelledby="${label}"]`);
			if (ulElem instanceof HTMLUListElement) {
				liElement.classList.add('preselected');
				ulElem.removeAttribute('hidden');
				selectMinute(ulElem);
			}
		} else if (liElement.parentElement instanceof HTMLUListElement && liElement.parentElement.hasAttribute('aria-labelledby')) {
			const labelledby = liElement.parentElement.getAttribute('aria-labelledby');
			this.calendarElement.querySelector(`li[aria-label="${labelledby}"]`)?.classList.add('preselected');
			liElement.parentElement.removeAttribute('hidden');
			selectMinute(liElement.parentElement);
		}
	}

	private selectDay = (event: Event) => {
		if (event.target instanceof HTMLLIElement) {
			if (this.dateOnly) {
				this.selectDate(event.target);
			} else {
				this.fetchCalendar(this.getDate(event.target), ViewMode.hours);
			}
		}
	}

	private selectMonth = (event: Event) => {
		if (event.target instanceof HTMLLIElement) {
			this.fetchCalendar(this.getDate(event.target), ViewMode.weeks);
		}
	}

	private selectYear = (event: Event) => {
		if (event.target instanceof HTMLLIElement) {
			this.fetchCalendar(this.getDate(event.target), ViewMode.months);
		}
	}

	private async fetchCalendar(atDate: Date, viewMode: ViewMode) {
		const query = new URLSearchParams('calendar');
		query.set('date', this.asUTCDate(atDate).toISOString().slice(0, 10));
		query.set('mode', viewMode);
		if (this.interval) {
			query.set('interval', String(this.interval));
		}
		const response = await fetch(`${this.endpoint}?${query.toString()}`, {
			method: 'GET',
		});
		if (response.status === 200) {
			this.calendarElement.innerHTML = await response.text();
		} else {
			console.error(`Failed to fetch from ${this.endpoint} (status=${response.status})`);
		}
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
				case ':is([is="django-datepicker"], [is="django-datetimepicker"]) + * + .dj-calendar':
					extraStyles = StyleHelpers.extractStyles(this.inputElement, [
						'background-color', 'border', 'border-radius',
						'font-family', 'font-size', 'font-stretch', 'font-style', 'font-weight',
						'letter-spacing', 'white-space', 'line-height']);
					declaredStyles.sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case ':is([is="django-datepicker"], [is="django-datetimepicker"]) + * + .dj-calendar .controls':
					extraStyles = StyleHelpers.extractStyles(this.inputElement, ['padding']);
					declaredStyles.sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case ':is([is="django-datepicker"], [is="django-datetimepicker"]) + * + .dj-calendar .ranges':
					extraStyles = StyleHelpers.extractStyles(this.inputElement, ['padding']);
					declaredStyles.sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case ':is([is="django-datepicker"], [is="django-datetimepicker"]) + * + .dj-calendar .ranges ul:not(.weekdays)':
					extraStyles = `line-height: ${inputHeight};`;
					declaredStyles.sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case ':is([is="django-datepicker"], [is="django-datetimepicker"]) + * + .dj-calendar .ranges ul.hours > li.preselected':
				case ':is([is="django-datepicker"], [is="django-datetimepicker"]) + * + .dj-calendar .ranges ul.minutes':
					this.inputElement.classList.add('-focus-');
					extraStyles = StyleHelpers.extractStyles(this.inputElement, ['border-color']);
					declaredStyles.sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					this.inputElement.classList.remove('-focus-');
					if (cssRule.selectorText === ':is([is="django-datepicker"], [is="django-datetimepicker"]) + * + .dj-calendar .ranges ul.hours > li.preselected') {
						extraStyles = StyleHelpers.extractStyles(this.calendarElement, ['background-color']);
						extraStyles = extraStyles.replace('background-color', 'border-bottom-color');
						declaredStyles.sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					}
					break;
				default:
					break;
			}
		}
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

const CAL = Symbol('DateTimePickerElement');

export class DatePickerElement extends HTMLInputElement {
	private [CAL]!: Calendar;  // hides internal implementation

	private connectedCallback() {
		const fieldGroup = this.closest('[role="group"]');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		const calendarElement = fieldGroup.querySelector('[aria-label="calendar"]');
		this[CAL] = new Calendar(this, calendarElement);
	}

	public get valueAsDate() : Date | null {
		return this[CAL].valueAsDate();
	}
}


export class DateTimePickerElement extends HTMLInputElement {
	private [CAL]!: Calendar;  // hides internal implementation

	private connectedCallback() {
		const fieldGroup = this.closest('[role="group"]');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		const calendarElement = fieldGroup.querySelector('[aria-label="calendar"]');
		this[CAL] = new Calendar(this, calendarElement);
	}

	public get valueAsDate() : Date | null {
		return this[CAL].valueAsDate();
	}
}
