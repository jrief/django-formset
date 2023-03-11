import { createPopper, Instance } from '@popperjs/core';
import { StyleHelpers, Widget } from './helpers';
import styles from './DateTimePicker.scss';


enum ViewMode {
	hours = 'h',
	weeks = 'w',
	months = 'm',
	years = 'y',
}


enum Direction {
	up,
	right,
	down,
	left,
}


class Calendar extends Widget {
	private readonly inputElement: HTMLInputElement;
	private readonly dateOnly: Boolean;
	private readonly localTime: Boolean;
	private readonly calendarElement: HTMLElement;
	private viewMode!: ViewMode;
	private initialDate?: Date;
	private dateTimeFormat?: Intl.DateTimeFormat;
	private dateTimeRegExp?: RegExp;
	private autoZeroRegExps: Array<RegExp> = [];
	private autoDelimiterRegExps: Array<RegExp> = [];
	private autoSpaceRegExp?: RegExp;
	private autoColonRegExp?: RegExp;
	private delimiter = '-';
	private dropdownInstance?: Instance;
	private minDate?: Date;
	private maxDate?: Date;
	private minWeekDate?: Date;
	private maxWeekDate?: Date;
	private minMonthDate?: Date;
	private maxMonthDate?: Date;
	private minYearDate?: Date;
	private maxYearDate?: Date;
	private interval?: number;
	private isOpen = false;
	private prevSheetDate!: Date;
	private nextSheetDate!: Date;
	private narrowSheetDate?: Date;
	private extendSheetDate?: Date;
	private todayDate!: Date;
	private calendarItems!: NodeListOf<HTMLLIElement>;

	constructor(inputElement: HTMLInputElement, calendarElement: Element | null) {
		super(inputElement);
		this.inputElement = inputElement;
		this.dateOnly = inputElement.getAttribute('is') === 'django-datepicker';
		this.localTime = inputElement.hasAttribute('local-time');
		this.setDateTimeFormat();
		this.setInitialDate();
		if (calendarElement instanceof HTMLElement) {
			this.calendarElement = calendarElement;
		} else {
			this.calendarElement = document.createElement('div');
			this.fetchCalendar(new Date(), ViewMode.weeks);
		}
		this.setBounds();
		this.installEventHandlers();
		const observer = new MutationObserver(() => this.registerElement());
		observer.observe(this.calendarElement, {childList: true});
		this.transferStyles();
		this.registerElement();
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
		if (this.inputElement.value) {
			this.initialDate = this.convertDate(new Date(this.inputElement.value));
			this.inputElement.value = this.asString(this.initialDate);
		}
	}

	private convertDate(date: Date, force=false) : Date {
		if (this.localTime || force) {
			date.setTime(date.getTime() - 60000 * date.getTimezoneOffset());
		}
		return date;
	}

	private setBounds() {
		const minValue = this.inputElement.getAttribute('min');
		if (minValue) {
			this.minDate = this.convertDate(new Date(minValue));
			this.minWeekDate = new Date(this.minDate);
			this.minWeekDate.setHours(0, 0, 0);
			this.minMonthDate = new Date(this.minWeekDate);
			this.minMonthDate.setDate(1);
			this.minYearDate = new Date(this.minMonthDate);
			this.minYearDate.setMonth(0);
		}
		const maxValue = this.inputElement.getAttribute('max');
		if (maxValue) {
			this.maxDate = this.convertDate(new Date(maxValue));
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

	private setDateTimeFormat() {
		const phBits = Array<string>();
		const patBits = Array<string>();
		const regexBits = Array<string>();
		if (this.inputElement.getAttribute('date-format') === 'iso') {
			this.autoZeroRegExps.length = this.autoDelimiterRegExps.length = 0;
			this.autoZeroRegExps.push(new RegExp( '^(\\d{4}-)(\\d{1}-)$'));
			this.autoZeroRegExps.push(new RegExp( '^(\\d{4}-\\d{2}-)(\\d{1}\\s)$'));
			this.autoDelimiterRegExps.push(new RegExp('^\\d{4}$'));
			this.autoDelimiterRegExps.push(new RegExp('^\\d{4}-\\d{2}$'));
			if (!this.dateOnly) {
				this.autoZeroRegExps.push(new RegExp( '^(\\d{4}-\\d{2}-\\d{2}\\s)(\\d{1}:)$'));
				this.autoSpaceRegExp = new RegExp( '^\\d{4}-\\d{2}-\\d{2}$');
				this.autoColonRegExp = new RegExp('^\\d{4}-\\d{2}-\\d{2}\\s\\d{2}$');
			}
			if (this.dateOnly) {
				this.setExtraAttributes('yyyy-mm-dd', '\\d{4}-\\d{2}-\\d{2}');
			} else {
				this.setExtraAttributes('yyyy-mm-dd HH:MM', '\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}');
			}
			return;
		}

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
				case 'day':
					phBits.push('dd');
					patBits.push('\\d{2}');
					regexBits.push('(?<day>\\d{1,2})');
					break;
				case 'month':
					phBits.push('mm');
					patBits.push('\\d{2}');
					regexBits.push('(?<month>\\d{1,2})');
					break;
				case 'year':
					phBits.push('yyyy');
					patBits.push('\\d{4}');
					regexBits.push('(?<year>\\d{4})');
					break;
				case 'literal':
					if (['.', '/', '-'].includes(part.value)) {
						this.delimiter = part.value;
						phBits.push(part.value);
						patBits.push(part.value);
						regexBits.push(part.value);
					}
					if (!this.dateOnly) {
						if ([', ', ' '].includes(part.value)) {
							phBits.push(' ');
							patBits.push('\\s');
							regexBits.push('\\s');
						}
						if ([':'].includes(part.value)) {
							phBits.push(part.value);
							patBits.push(part.value);
							regexBits.push(part.value);
						}
					}
					break;
				case 'hour':
					if (!this.dateOnly) {
						phBits.push('HH');
						patBits.push('\\d{2}');
						regexBits.push('(?<hour>\\d{1,2})');
					}
					break;
				case 'minute':
					if (!this.dateOnly) {
						phBits.push('MM');
						patBits.push('\\d{2}');
						regexBits.push('(?<minute>\\d{1,2})');
					}
					break;
				default:
					break;
			}
		});
		this.dateTimeRegExp = new RegExp(regexBits.join(''));
		this.autoZeroRegExps.length = this.autoDelimiterRegExps.length = 0;
		this.autoDelimiterRegExps.push(new RegExp('^\\d{2}$'));
		if (this.delimiter === '.') {
			this.autoZeroRegExps.push(new RegExp( '^(\\D*)(\\d{1}\\.)$'));
			this.autoZeroRegExps.push(new RegExp( '^(\\d{2}\\.)(\\d{1}\\.)$'));
			this.autoDelimiterRegExps.push(new RegExp('^\\d{2}\\.\\d{2}$'));
			if (!this.dateOnly) {
				this.autoZeroRegExps.push(new RegExp( '^(\\d{2}\\.\\d{2}\\.\\d{4}\\s)(\\d{1}:)$'));
				this.autoSpaceRegExp = new RegExp( '^(\\d{2}\\.\\d{2}\\.\\d{4})$');
				this.autoColonRegExp = new RegExp('^\\d{2}\\.\\d{2}\\.\\d{4}\\s\\d{2}$');
			}
		} else {
			this.autoZeroRegExps.push(new RegExp( '^(\\D*)(\\d{1}/)$'));
			this.autoZeroRegExps.push(new RegExp( '^(\\d{2}/)(\\d{1}/)$'));
			this.autoDelimiterRegExps.push(new RegExp('^\\d{2}/\\d{2}$'));
			if (!this.dateOnly) {
				this.autoZeroRegExps.push(new RegExp( '^(\\d{2}/\\d{2}/\\d{4}\\s)(\\d{1}:)$'));
				this.autoSpaceRegExp = new RegExp( '^(\\d{2}/\\d{2}/\\d{4})$');
				this.autoColonRegExp = new RegExp('^\\d{2}/\\d{2}/\\d{4}\\s\\d{2}$');
			}
		}
		this.setExtraAttributes(phBits.join(''), patBits.join(''));
	}

	private setExtraAttributes(placeholder: string, pattern: string) {
		if (!this.inputElement.hasAttribute('placeholder')) {
			this.inputElement.setAttribute('placeholder', placeholder);
		}
		if (!this.inputElement.hasAttribute('pattern')) {
			this.inputElement.setAttribute('pattern', pattern);
		}
	}

	private installEventHandlers() {
		this.inputElement.addEventListener('focus', this.handleFocus);
		this.inputElement.addEventListener('blur', this.handleBlur);
		this.inputElement.addEventListener('input', this.handleInput);
		this.inputElement.addEventListener('change', this.handleChange);
		document.addEventListener('click', this.handleClick);
		document.addEventListener('keydown', this.handleKeypress);
	}

	private close() {
		this.isOpen = false;
		this.inputElement.setAttribute('aria-expanded', 'false')
		this.dropdownInstance?.destroy();
	}

	private asDate() : Date | undefined {
		if (this.inputElement.value) {
			if (this.dateTimeRegExp) {
				const matches = this.inputElement.value.match(this.dateTimeRegExp);
				if (matches && matches.groups) {
					if (this.dateOnly)
						return new Date(parseInt(matches.groups.year), parseInt(matches.groups.month) - 1, parseInt(matches.groups.day))
					return new Date(parseInt(matches.groups.year), parseInt(matches.groups.month) - 1, parseInt(matches.groups.day), parseInt(matches.groups.hour), parseInt(matches.groups.minute));
				}
			} else {
				const newDate = new Date(this.inputElement.value);
				if (!isNaN(newDate.getTime()))
					return newDate;
			}
		}
	}

	private asUTCDate(date: Date) : Date {
		return new Date(date.getTime() - date.getTimezoneOffset() * 60000);
	}

	private asString(date: Date) : string {
		const dateString = this.dateTimeFormat
			? this.dateTimeFormat.format(date).replace(', ', ' ')
			: this.asUTCDate(date).toISOString().replace('T', ' ');
		return dateString.slice(0, this.dateOnly ? 10 : 16);
	}

	private getDate(selector: string | Element) : Date {
		const element = selector instanceof Element ? selector : this.calendarElement.querySelector(selector);
		if (!(element instanceof Element))
			throw new Error(`Element ${selector} is missing`);
		const dateValue = element.getAttribute('data-date') ?? element.getAttribute('datetime');
		return new Date(dateValue ?? '');
	}

	private registerElement() {
		this.viewMode = this.getViewMode();
		this.prevSheetDate = this.getDate('button.prev');
		const narrowButton = this.calendarElement.querySelector('button.narrow');
		this.narrowSheetDate = narrowButton ? this.getDate(narrowButton) : undefined;
		this.todayDate = this.convertDate(new Date(Date.now()), true);
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
		const todayHourString = this.todayDate.toISOString().slice(0, 13).concat(':00');
		const inputDate = this.asDate();
		const inputDateString = inputDate ? this.asUTCDate(inputDate).toISOString() : '';

		// since each datetime-picker can have different values, set this on element level
		if (this.interval) {
			const num = Math.min(60 / this.interval!, 6);
			const gridTemplateColumns = `repeat(${num}, 1fr)`;
			this.calendarElement.querySelectorAll('.ranges ul.minutes').forEach(minutesElement => {
				(minutesElement as HTMLElement).style.gridTemplateColumns = gridTemplateColumns;
			});
		}

		this.calendarItems.forEach(elem => {
			elem.classList.toggle('selected', elem.getAttribute('data-date') === inputDateString.slice(0, 16));
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

		this.calendarElement.querySelectorAll('li[aria-label]').forEach(elem => {
			const label = elem.getAttribute('aria-label')!;
			elem.classList.toggle('today', label === todayHourString);
			const selector = `ul[aria-labelledby="${label}"]`;
			if (label.slice(0, 13) === inputDateString.slice(0, 13)) {
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
		const todayDateString = this.todayDate.toISOString().slice(0, 10);
		const inputDate = this.asDate();
		const inputDateString = inputDate ? this.asUTCDate(inputDate).toISOString().slice(0, 10) : null;
		this.calendarItems.forEach(elem => {
			elem.classList.toggle('today', elem.getAttribute('data-date') === todayDateString);
			elem.classList.toggle('selected', elem.getAttribute('data-date') === inputDateString);
			const date = this.getDate(elem);
			if (this.minWeekDate && date < this.minWeekDate || this.maxWeekDate && date > this.maxWeekDate) {
				elem.toggleAttribute('disabled', true);
			} else {
				elem.addEventListener('click', this.selectDay);
			}
		});
	}

	private registerMonthsView() {
		const todayMonthString = this.todayDate.toISOString().slice(0, 7);
		const inputDate = this.asDate();
		const inputMonthString = inputDate ? this.asUTCDate(inputDate).toISOString().slice(0, 7) : null;
		this.calendarItems.forEach(elem => {
			const date = this.getDate(elem);
			const monthString = elem.getAttribute('data-date')?.slice(0, 7);
			elem.classList.toggle('today', monthString === todayMonthString);
			elem.classList.toggle('selected', monthString === inputMonthString);
			if (this.minMonthDate && date < this.minMonthDate || this.maxMonthDate && date > this.maxMonthDate) {
				elem.toggleAttribute('disabled', true);
			} else {
				elem.addEventListener('click', this.selectMonth);
			}
		});
	}

	private registerYearsView() {
		const todayYearString = this.todayDate.toISOString().slice(0, 4);
		const inputDate = this.asDate();
		const inputYearString = inputDate ? this.asUTCDate(inputDate).toISOString().slice(0, 4) : null;
		this.calendarItems.forEach(elem => {
			const date = this.getDate(elem);
			const yearString = elem.getAttribute('data-date')?.slice(0, 4);
			elem.classList.toggle('today', yearString === todayYearString);
			elem.classList.toggle('selected', yearString === inputYearString);
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
			if (element.isSameNode(this.calendarElement) || element.isSameNode(this.inputElement))
				return;
			element = element.parentElement;
		}
		this.close();
		this.inputElement.blur();
	}

	private handleFocus = (event: Event) => {
		this.dropdownInstance = createPopper(this.inputElement, this.calendarElement, {
			placement: 'bottom-start',
		});
		this.inputElement.setAttribute('aria-expanded', 'true');
		const prevValue = this.inputElement.value;
		this.inputElement.value = prevValue.trimEnd();  // remove white space eventually added by failed validation
		if (this.inputElement.value !== prevValue) {
			this.inputElement.dispatchEvent(new Event('input'));  // triggers validation
		}
		this.isOpen = true;
	}

	private handleBlur = (event: Event) => {
		if (this.isOpen) {
			this.inputElement.focus();
		} else {
			this.validate();
		}
	}

	private handleInput = (event: Event) => {
		if (this.isOpen) {
			this.close();
		}
		if (event instanceof InputEvent && event.inputType === 'insertText') {
			this.inputElement.value = this.inputElement.value
				.replace('  ', ' ')
				.replace(this.delimiter.concat(this.delimiter), this.delimiter)
				.replace('::', ':');
			this.autoZeroRegExps.forEach(re => {
				if (this.inputElement.value.match(re)) {
					this.inputElement.value = this.inputElement.value.replace(re, '$10$2');
				}
			});
			this.autoDelimiterRegExps.forEach(re => {
				if (this.inputElement.value.match(re)) {
					this.inputElement.value = this.inputElement.value.concat(this.delimiter);
				}
			});
			if (this.autoSpaceRegExp && this.inputElement.value.match(this.autoSpaceRegExp)) {
				this.inputElement.value = this.inputElement.value.concat(' ');
			}
			if (this.autoColonRegExp && this.inputElement.value.match(this.autoColonRegExp)) {
				this.inputElement.value = this.inputElement.value.concat(':');
			}
		}
	}

	private handleChange = (event: Event) => {
		const newDate = this.validate();
		if (newDate) {
			this.fetchCalendar(newDate, this.viewMode);
		}
	}

	private handleKeypress = async (event: KeyboardEvent) => {
		if (!this.isOpen)
			return;
		let element = null;
		const nextViewMode = new Map<ViewMode, ViewMode>([
			[ViewMode.years, ViewMode.months],
			[ViewMode.months, ViewMode.weeks],
			[ViewMode.weeks, ViewMode.hours],
		]);
		switch (event.key) {
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
				this.close();
				break;
			case 'Tab':
				this.close();
				this.inputElement.blur();
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
						this.fetchCalendar(this.getDate(element), nextViewMode.get(this.viewMode)!);
					}
				}
				break;
			default:
				return;
		}
		event.preventDefault();
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
		const nextDate = this.convertDate(lastDate, true);
		switch (this.viewMode) {
		  case ViewMode.hours:
			return new Date(nextDate.getTime() + 60000 * deltaHours.get(direction)!);
		  case ViewMode.weeks:
			return new Date(nextDate.getTime() + 60000 * deltaWeeks.get(direction)!);
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
			const dataDate = (date: Date) => date.toISOString().slice(0, this.viewMode === ViewMode.hours ? 16 : 10);
			let nextItem: Element|null = null;
			if (this.viewMode !== ViewMode.weeks || selectedDate.getMonth() === nextDate.getMonth()) {
				nextItem = this.calendarElement.querySelector(`.ranges li[data-date="${dataDate(nextDate)}"]`);
			}
			if (!nextItem) {
				await this.fetchCalendar(nextDate, this.viewMode);
				nextItem = this.calendarElement.querySelector(`.ranges li[data-date="${dataDate(nextDate)}"]`);
			}
			if (nextItem instanceof HTMLLIElement) {
				if (this.viewMode === ViewMode.hours) {
					this.selectHour(nextItem);
				}
				this.setDate(nextItem);
			}
		}
	}

	private validate() : Date | undefined {
		const newDate = this.getValidDate();
		if (newDate)
			return newDate;
		if (this.inputElement.value.length > 0) {
			// enforce a pattern validation error
			this.inputElement.value = this.inputElement.value.concat(' ');
		}
	}

	private getValidDate() : Date | undefined {
		const newDate = this.asDate();
		if (newDate) {
			if (this.asString(newDate) === this.inputElement.value)
				return newDate;
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
			this.fetchCalendar(this.todayDate, ViewMode.hours);
		}
	}

	private async selectToday() {
		const dateString = this.todayDate.toISOString().slice(0, 10);
		let todayElem = this.calendarElement.querySelector(`li[data-date="${dateString}"]`);
		if (!todayElem) {
			await this.fetchCalendar(this.todayDate, ViewMode.weeks);
			todayElem = this.calendarElement.querySelector(`li[data-date="${dateString}"]`);
		}
		this.selectDate(todayElem!);
	}

	private setDate(element: Element) {
		this.calendarItems.forEach(elem => {
			elem.classList.toggle('selected', elem.isSameNode(element));
		});
		let dateString = element.getAttribute('data-date')!;
		if (this.dateTimeFormat) {
			dateString = this.asString(new Date(dateString));
		}
		if (this.dateOnly) {
			this.inputElement.value = dateString.slice(0, 10);
		} else if (dateString.length === 10) {
			this.inputElement.value = dateString.concat(' 12:00');
		} else {
			this.inputElement.value = dateString.replace('T', ' ');
		}
	}

	private selectDate(element: Element) {
		this.setDate(element);
		this.close();
		this.inputElement.blur();
		this.inputElement.dispatchEvent(new Event('input'));
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
			const labeledby = liElement.parentElement.getAttribute('aria-labelledby');
			this.calendarElement.querySelector(`li[aria-label="${labeledby}"]`)?.classList.add('preselected');
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

	private controlButton(target: EventTarget | null) : HTMLButtonElement {
		let button = target;
		while (!(button instanceof HTMLButtonElement)) {
			if (!(button instanceof Element))
				throw new Error(`Element ${target} not part of button`);
			button = button.parentElement;
		}
		return button;
	}

	private async fetchCalendar(newDate: Date, viewMode: ViewMode) {
		const query = new URLSearchParams('calendar');
		query.set('date', newDate.toISOString().slice(0, 10));
		query.set('mode', viewMode);
		if (this.interval) {
			query.set('interval', String(this.interval));
		}
		const response = await fetch(`${this.endpoint}?${query.toString()}`, {
			method: 'GET',
		});
		if (response.status === 200) {
			const innerHTML = await response.text();
			this.calendarElement.innerHTML = innerHTML;
		} else {
			console.error(`Failed to fetch from ${this.endpoint} (status=${response.status})`);
		}
	}

	private transferStyles() {
		for (let k = 0; k < document.styleSheets.length; ++k) {
			// prevent adding <styles> multiple times with the same content by checking if they already exist
			const cssRule = document?.styleSheets?.item(k)?.cssRules?.item(0);
			if (cssRule instanceof CSSStyleRule && cssRule.selectorText! === ':is([is="django-datepicker"], [is="django-datetimepicker"])')
				return;
		}
		const declaredStyles = document.createElement('style');
		declaredStyles.innerText = styles;
		document.head.appendChild(declaredStyles);
		const inputHeight = window.getComputedStyle(this.inputElement).getPropertyValue('height');
		for (let index = 0; declaredStyles.sheet && index < declaredStyles.sheet.cssRules.length; index++) {
			const cssRule = declaredStyles.sheet.cssRules.item(index) as CSSStyleRule;
			let extraStyles: string;
			switch (cssRule.selectorText) {
				case ':is([is="django-datepicker"], [is="django-datetimepicker"]) + .dj-calendar':
					extraStyles = StyleHelpers.extractStyles(this.inputElement, [
						'background-color', 'border', 'border-radius',
						'font-family', 'font-size', 'font-strech', 'font-style', 'font-weight',
						'letter-spacing', 'white-space', 'line-height']);
					declaredStyles.sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case ':is([is="django-datepicker"], [is="django-datetimepicker"]) + .dj-calendar .controls':
					extraStyles = StyleHelpers.extractStyles(this.inputElement, ['padding']);
					declaredStyles.sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case ':is([is="django-datepicker"], [is="django-datetimepicker"]) + .dj-calendar .ranges':
					extraStyles = StyleHelpers.extractStyles(this.inputElement, ['padding']);
					declaredStyles.sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case ':is([is="django-datepicker"], [is="django-datetimepicker"]) + .dj-calendar .ranges ul:not(.weekdays)':
					extraStyles = `line-height: ${inputHeight};`;
					declaredStyles.sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case ':is([is="django-datepicker"], [is="django-datetimepicker"]) + .dj-calendar .ranges ul.hours > li.preselected':
				case ':is([is="django-datepicker"], [is="django-datetimepicker"]) + .dj-calendar .ranges ul.minutes':
					this.inputElement.style.transition = 'none';
					this.inputElement.classList.add('-focus-');
					extraStyles = StyleHelpers.extractStyles(this.inputElement, ['border-color']);
					declaredStyles.sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					this.inputElement.classList.remove('-focus-');
					this.inputElement.style.transition = '';
					if (cssRule.selectorText === ':is([is="django-datepicker"], [is="django-datetimepicker"]) + .dj-calendar .ranges ul.hours > li.preselected') {
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

	protected formResetted(event: Event) {}

	protected formSubmitted(event: Event) {}

	public valueAsDate() : Date | null {
		const date = this.asDate();
		if (date) {
			if (!this.localTime) {
				date.setTime(date.getTime() + 60000 * date.getTimezoneOffset());
			}
			return date;
		}
		return null;
	}
}

const CAL = Symbol('DateTimePickerElement');

export class DatePickerElement extends HTMLInputElement {
	private [CAL]!: Calendar;  // hides internal implementation

	private connectedCallback() {
		const fieldGroup = this.closest('django-field-group');
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
		const fieldGroup = this.closest('django-field-group');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		const calendarElement = fieldGroup.querySelector('[aria-label="calendar"]');
		this[CAL] = new Calendar(this, calendarElement);
	}

	public get valueAsDate() : Date | null {
		return this[CAL].valueAsDate();
	}
}
