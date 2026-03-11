import {StyleHelpers, asUTCDate} from './helpers';
import {Widget} from './Widget';
import styles from './Calendar.scss';


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


enum SheetType {
	compact,
	plain,
	lower,
	upper,
	dual,
}


export type CalendarSettings = {
	dateOnly: boolean,  // if true, time is not displayed
	withRange: boolean,  // if true, a range of dates can be selected
	hour12: boolean,  // if true, use 12-hour format
	sheetType: SheetType,
	inputElement: HTMLInputElement,  // input element to pilfer styles from
	updateDate: Function,  // callback to update date input
	close: Function,  // callback to close calendar
};

export namespace CalendarSettings {
	export function layoutToSheetType(calendarElement?: HTMLElement) {
		const layout = calendarElement?.getAttribute('layout');
		switch (layout) {
			case 'c':
				return SheetType.compact;
			case 'p':
				return SheetType.plain;
			case 'd':
				return SheetType.dual;
			default:
				throw new Error("Unknown attribute 'layout' on calendar element");
		}
	}
}


type DateRange = [Date|null, Date|null];


function minDate(date1: Date, date2: any) : Date {
	return !(date2 instanceof Date) || date1 < date2 ? date1 : date2;
}


function maxDate(date1: Date, date2: any) : Date {
	return !(date2 instanceof Date) || date1 > date2 ? date1 : date2;
}


class CalendarSheet {
	private readonly calendar: CalendarWidget;
	public readonly element: HTMLElement;
	private readonly sheetType: SheetType;
	private viewMode!: ViewMode;
	private upperRange;
	private preselectedDate: Date|null = null;
	private sheetBounds: [Date, Date];
	private prevSheetDate!: Date;
	private nextSheetDate!: Date;
	private narrowSheetDate?: Date;
	private extendSheetDate?: Date;
	private calendarItems!: NodeListOf<HTMLLIElement>;
	private interval?: number;
	private minDate?: Date;
	private maxDate?: Date;
	private minWeekDate?: Date;
	private maxWeekDate?: Date;
	private minMonthDate?: Date;
	private maxMonthDate?: Date;
	private minYearDate?: Date;
	private maxYearDate?: Date;
	private readonly rangeSelectCssRule: CSSStyleRule;
	private readonly rangeSelectorText: string;

	constructor(calendar: CalendarWidget, element: HTMLElement, sheetType: SheetType) {
		this.calendar = calendar;
		this.element = element;
		const observer = new MutationObserver(() => this.registerCalendar());
		observer.observe(this.element, {childList: true});
		this.setInterval();
		this.setMinMaxBounds();
		this.sheetType = sheetType;
		this.upperRange = sheetType === SheetType.upper;
		this.rangeSelectCssRule = this.getRangeSelectCssRule();
		this.rangeSelectorText = this.rangeSelectCssRule.selectorText;
		this.registerCalendar();
		this.sheetBounds = this.getSheetBounds();
	}

	private get todayDateString(): string {
		const isoString = asUTCDate(new Date()).toISOString();
		return this.calendar.settings.dateOnly ? `${isoString.slice(0, 10)}T00:00` : isoString.slice(0, 16);
	}

	private get sheetSelector(): string {
		switch (this.sheetType) {
			case SheetType.compact:
				return `${this.calendar.baseSelector} .compact-datetime`;
			case SheetType.plain:
				return `${this.calendar.baseSelector} .plain-datetime`;
			case SheetType.lower:
				return `${this.calendar.baseSelector} .lower-datetime`;
			case SheetType.upper:
				return `${this.calendar.baseSelector} .upper-datetime`;
			case SheetType.dual:
				throw new Error("Sheet type ‘dual’ not allowed on CalendarSheet");
		}
	}

	private getViewMode(): ViewMode {
		const label = this.element.querySelector(':scope > [aria-label]')?.getAttribute('aria-label');
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
				throw new Error(`Unknown aria-label on ${this.element}`);
		}
	}

	private setInterval() {
		const step = this.calendar.settings.inputElement.getAttribute('step');
		if (step) {
			const d1 = new Date('1970-01-01 0:00:00');
			const d2 = new Date(`1970-01-01 ${step}`);
			this.interval = (d2.getTime() - d1.getTime()) / 60000;
		}
	}

	private setMinMaxBounds() {
		const minValue = this.calendar.settings.inputElement.getAttribute('min');
		if (minValue) {
			const date = new Date(minValue);
			this.minDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
			this.minWeekDate = new Date(this.minDate);
			this.minWeekDate.setHours(0, 0, 0);
			this.minMonthDate = new Date(this.minWeekDate);
			this.minMonthDate.setDate(1);
			this.minYearDate = new Date(this.minMonthDate);
			this.minYearDate.setMonth(0);
		}
		const maxValue = this.calendar.settings.inputElement.getAttribute('max');
		if (maxValue) {
			const date = new Date(maxValue);
			this.maxDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
			this.maxWeekDate = new Date(this.maxDate);
			this.maxWeekDate.setHours(23, 59, 59);
			this.maxMonthDate = new Date(this.maxWeekDate);
			this.maxMonthDate.setDate(28);
			this.maxYearDate = new Date(this.maxMonthDate);
			this.maxYearDate.setMonth(11);
		}
	}

	private getDate(selector: string | Element): Date {
		const element = selector instanceof Element ? selector : this.element.querySelector(selector);
		if (!(element instanceof Element))
			throw new Error(`Element ${selector} is missing`);
		const dateValue = element.getAttribute('data-date') ?? element.getAttribute('datetime');
		return new Date(dateValue ?? '');
	}

	private registerCalendar() {
		this.viewMode = this.getViewMode();
		this.prevSheetDate = this.getDate('button.prev');
		const prevButton = this.element.querySelector('button.prev');
		const narrowButton = this.element.querySelector('button.narrow');
		this.narrowSheetDate = narrowButton ? this.getDate(narrowButton) : undefined;
		this.nextSheetDate = this.getDate('button.next');
		const nextButton = this.element.querySelector('button.next');
		const extendButton = this.element.querySelector('button.extend');
		this.extendSheetDate = extendButton ? this.getDate(extendButton) : undefined;
		if (this.calendar.settings.withRange) {
			prevButton?.addEventListener('mouseenter', this.hoverPrevButton);
		}
		prevButton?.addEventListener('click', this.turnPrev, {once: true});
		narrowButton?.addEventListener('click', this.turnNarrow, {once: true});
		extendButton?.addEventListener('click', this.turnExtend, {once: true});
		this.element.querySelector('button.today')?.addEventListener('click', this.turnToday, {once: true});
		if (this.calendar.settings.withRange) {
			nextButton?.addEventListener('mouseenter', this.hoverNextButton);
		}
		nextButton?.addEventListener('click', this.turnNext, {once: true});
		this.calendarItems = this.element.querySelectorAll('li[data-date]');
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
		const textElem = this.element.querySelector('button.today > svg > text');
		if (textElem instanceof SVGTextElement) {
			textElem.textContent = String((new Date()).getDate());
		}
		this.sheetBounds = this.getSheetBounds();
		this.markSelectedDates();
	}

	private registerHoursView() {
		const settings = this.calendar.settings;
		const dateRange = this.calendar.dateRange;
		// since each datetime-picker can have different interval values, set this on element level
		if (this.interval) {
			const num = Math.min(60 / this.interval!, 6);
			const gridTemplateColumns = `repeat(${num}, 1fr)`;
			this.element.querySelectorAll('.sheet-body ul.minutes').forEach(minutesElement => {
				(minutesElement as HTMLElement).style.gridTemplateColumns = gridTemplateColumns;
			});
		}

		this.calendarItems.forEach(elem => {
			const date = this.getDate(elem);
			if (this.minDate && date < this.minDate || this.maxDate && date > this.maxDate) {
				elem.toggleAttribute('disabled', true);
			}
			elem.addEventListener('click', this.selectMinute);
			if (settings.withRange) {
				elem.addEventListener('mouseenter', this.hoverDateItem);
			}
		});

		const lowerHourString = dateRange[0] ? asUTCDate(dateRange[0]).toISOString().slice(0, 13) : '';
		const upperDateString = settings.withRange && dateRange[1] ? asUTCDate(dateRange[1]).toISOString().slice(0, 16) : '';
		const upperHourString = upperDateString.slice(0, 13);
		const todayHourString = this.todayDateString.slice(0, 13).concat(':00');
		this.element.querySelectorAll('li[aria-label]').forEach(elem => {
			const label = elem.getAttribute('aria-label')!;
			elem.classList.toggle('today', label === todayHourString);
			const selector = `ul[aria-labelledby="${label}"]`;
			if (lowerHourString === label.slice(0, 13)) {
				elem.classList.add('constricted', 'lower');
				this.element.querySelector(selector)?.removeAttribute('hidden');
			} else if (upperHourString === label.slice(0, 13)) {
				elem.classList.add('constricted', 'upper');
				this.element.querySelector(selector)?.removeAttribute('hidden');
			}

			if (this.element.querySelectorAll(`${selector} > li[data-date]:not([disabled])`).length === 0) {
				elem.toggleAttribute('disabled', true);
			}
			elem.addEventListener('click', (event: Event) => {
				if (event.target instanceof HTMLLIElement) {
					this.calendar.activateSheet(this);
					this.selectHour(event.target);
				}
			});
			if (settings.withRange) {
				elem.addEventListener('mouseenter', this.hoverDateItem);
			}
		});
		this.toggleMidnightItem();
	}

	private registerWeeksView() {
		const todayDateString = `${this.todayDateString.slice(0, 10)}T00:00`;
		this.calendarItems.forEach(elem => {
			const date = this.getDate(elem);
			elem.classList.toggle('today', elem.dataset.date === todayDateString);
			if (this.minWeekDate && date < this.minWeekDate || this.maxWeekDate && date > this.maxWeekDate) {
				elem.toggleAttribute('disabled', true);
			}
			elem.addEventListener('click', this.selectDay);
			if (this.calendar.settings.withRange) {
				elem.addEventListener('mouseenter', this.hoverDateItem);
			}
		});
	}

	private registerMonthsView() {
		const todayMonthString = `${this.todayDateString.slice(0, 7)}-01T00:00`;
		this.calendarItems.forEach(elem => {
			const date = this.getDate(elem);
			elem.classList.toggle('today', elem.dataset.date === todayMonthString);
			if (this.minMonthDate && date < this.minMonthDate || this.maxMonthDate && date > this.maxMonthDate) {
				elem.toggleAttribute('disabled', true);
			}
			elem.addEventListener('click', this.selectMonth);
			if (this.calendar.settings.withRange) {
				elem.addEventListener('mouseenter', this.hoverDateItem);
			}
		});
	}

	private registerYearsView() {
		const todayYearString = `${this.todayDateString.slice(0, 4)}-01-01T00:00`;
		this.calendarItems.forEach(elem => {
			const date = this.getDate(elem);
			elem.classList.toggle('today', elem.dataset.date === todayYearString);
			if (this.minYearDate && date < this.minYearDate || this.maxYearDate && date > this.maxYearDate) {
				elem.toggleAttribute('disabled', true);
			}
			elem.addEventListener('click', this.selectYear);
			if (this.calendar.settings.withRange) {
				elem.addEventListener('mouseenter', this.hoverDateItem);
			}
		});
	}

	// navigate through the calendar with arrow keys
	// return true if key shall prevent bubbling up the event chain
	public async navigate(key: string) {
		let element = null;
		const settings = this.calendar.settings;
		const nextViewMode = new Map<ViewMode, ViewMode>([
			[ViewMode.years, ViewMode.months],
			[ViewMode.months, ViewMode.weeks],
			[ViewMode.weeks, ViewMode.hours],
		]);
		switch (key) {
			case 'ArrowUp':
				await this.goto(Direction.up);
				break;
			case 'ArrowRight':
				await this.goto(Direction.right);
				break;
			case 'ArrowDown':
				await this.goto(Direction.down);
				break;
			case 'ArrowLeft':
				await this.goto(Direction.left);
				break;
			case 'Escape':
			case 'Tab':
				settings.close();
				break;
			case 'PageUp':
				element = this.element.querySelector('button.prev');
				if (element) {
					await this.fetchCalendar(this.getDate(element));
				}
				break;
			case 'PageDown':
				element = this.element.querySelector('button.next');
				if (element) {
					await this.fetchCalendar(this.getDate(element));
				}
				break;
			case 'Enter':
				if (this.preselectedDate) {
					const dateString = asUTCDate(this.preselectedDate).toISOString().slice(0, 16);
					element = this.element.querySelector(`.sheet-body li[data-date="${dateString}"]`);
				} else {
					const dateRange = this.calendar.dateRange;
					const date = this.upperRange ? dateRange[1] : dateRange[0];
					const dateString = date ? asUTCDate(date).toISOString().slice(0, 16) : '';
					element = this.element.querySelector(`.sheet-body li[data-date="${dateString}"]`);
				}
				if (element instanceof HTMLElement) {
					if (this.viewMode === ViewMode.hours || this.viewMode === ViewMode.weeks && settings.dateOnly) {
						this.preselectedDate = null;
						this.setDate(element);
						this.markSelectedDates();
						this.closeDialogIfNeeded();
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
		const interval = this.interval;
		const deltaHours = (interval ?? 60) < 60 ? new Map<Direction, number>([
			[Direction.up, -60],
			[Direction.right, +interval!],
			[Direction.down, +60],
			[Direction.left, -interval!],
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
		let nextDate: Date;
		switch (this.viewMode) {
		  case ViewMode.hours:
			nextDate = new Date(lastDate.getTime() + 60000 * deltaHours.get(direction)!);
			break;
		  case ViewMode.weeks:
			nextDate = new Date(lastDate.getTime() + 60000 * deltaWeeks.get(direction)!);
			nextDate.setHours(0, 0, 0);
			break;
		  case ViewMode.months:
			nextDate = new Date(lastDate);
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
			nextDate.setDate(1);
			nextDate.setHours(0, 0, 0);
			break;
		  case ViewMode.years:
			nextDate = new Date(lastDate);
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
			nextDate.setMonth(0);
			nextDate.setDate(1);
			nextDate.setHours(0, 0, 0);
			break;
		}
		return nextDate;
	}

	private turnPrev = () => {
		this.fetchCalendar(this.prevSheetDate);
	};

	private turnNext = () => {
		this.fetchCalendar(this.nextSheetDate);
	};

	private turnNarrow = () => {
		if (this.narrowSheetDate) {
			if (this.viewMode === ViewMode.months) {
				this.fetchCalendar(this.narrowSheetDate, ViewMode.weeks);
			} else if (this.viewMode === ViewMode.years) {
				this.fetchCalendar(this.narrowSheetDate, ViewMode.months);
			} else {
				this.fetchCalendar(this.narrowSheetDate);
			}
		}
	};

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
	};

	private turnToday = () => {
		if (this.calendar.settings.dateOnly) {
			this.selectToday();
		} else {
			this.fetchCalendar(new Date(), ViewMode.hours);
		}
	};

	private getDateSelector(date: Date) : string {
		const utcDateString = asUTCDate(date).toISOString();
		let dateString;
		switch (this.viewMode) {
			case ViewMode.hours:
				dateString = utcDateString.slice(0, 16);
				break;
			case ViewMode.weeks:
				dateString = `${utcDateString.slice(0, 10)}T00:00`;
				break;
			case ViewMode.months:
				dateString = `${utcDateString.slice(0, 7)}-01T00:00`;
				break;
			case ViewMode.years:
				dateString = `${utcDateString.slice(0, 4)}-01-01T00:00`;
				break;
		}
		return `li[data-date="${dateString}"]`;
	}

	private indexOfCalendarItem(date: Date) : number {
		const dateSelector = this.getDateSelector(date);
		const selectedElement = this.element.querySelector(dateSelector);
		return Array.from(this.calendarItems).indexOf(selectedElement as HTMLLIElement);
	}

	private hoverPrevButton = (event: Event) => {
		this.extendRangeToListItem(this.calendarItems.item(0));
	};

	private hoverNextButton = (event: Event) => {
		this.extendRangeToListItem(this.calendarItems.item(this.calendarItems.length - 1));
	};

	private hoverDateItem = (event: Event) => {
		if (event.target instanceof HTMLLIElement) {
			this.extendRangeToListItem(event.target);
		}
	};

	private extendRangeToListItem(listItem: HTMLLIElement) {
		const dateRange = this.calendar.dateRange;
		if ([SheetType.compact, SheetType.plain].includes(this.sheetType) && dateRange[0] && !dateRange[1]) {
			const hoverDateString = listItem.dataset.date ?? listItem.getAttribute('aria-label') ?? '';
			const hoverDate = new Date(hoverDateString);
			this.markDateRange(dateRange[0], hoverDate, true);
		}
	}

	private markDateRange(dateFixed: Date, dateCursor: Date, openRange= false) {
		const lowerDate = dateFixed < dateCursor ? dateFixed : dateCursor;
		const upperDate = dateFixed < dateCursor ? dateCursor : dateFixed;
		const lowerIndex = this.indexOfCalendarItem(lowerDate);
		const upperIndex = this.indexOfCalendarItem(upperDate);
		const addLower = openRange && !this.calendarItems.item(lowerIndex)?.classList.contains('selected') ? 1 : 2;
		const addUpper = openRange && !this.calendarItems.item(upperIndex)?.classList.contains('selected') ? 1 : 0;
		const perHour = this.interval ? Math.min(60 / this.interval, 6) : 1;
		const lowerLiIndex = Math.floor(lowerIndex / perHour) % 6 + 1;
		const upperLiIndex = Math.floor(upperIndex / perHour) % 6 + 1;
		let selectors: Array<string>;
		if (lowerIndex === -1 && upperIndex === -1) {
			if (lowerDate < this.sheetBounds[0] && upperDate > this.sheetBounds[1]) {
				selectors = [':not(.weekdays) > li'];  // select all
			} else {
				selectors = [':not(*)'];
			}
		} else if (lowerIndex === -1) {
			if (this.viewMode === ViewMode.hours) {
				const ulIndex = Math.floor(upperIndex / 6 / perHour) + 1;
				selectors = [
					`:nth-child(-n + ${ulIndex - 1} of .hours) > li`,
					`:nth-child(${ulIndex} of .hours) > li:nth-child(-n + ${upperLiIndex - 1})`,
				];
			} else {
				selectors = [`:not(.weekdays) > li:nth-child(-n + ${upperIndex + addUpper})`];
			}
		} else if (upperIndex === -1) {
			if (this.viewMode === ViewMode.hours) {
				const ulIndex = Math.floor(lowerIndex / 6 / perHour) + 1;
				selectors = [
					`:nth-child(${ulIndex} of .hours) > li:nth-child(n + ${lowerLiIndex + 1})`,
					`:nth-child(n + ${ulIndex + 1} of .hours) > li`,
				];
			} else {
				selectors = [`:not(.weekdays) > li:nth-child(n + ${lowerIndex + addLower})`];
			}
		} else {
			if (this.viewMode === ViewMode.hours) {
				const lowerUlIndex = Math.floor(lowerIndex / 6 / perHour) + 1;
				const upperUlIndex = Math.floor(upperIndex / 6 / perHour) + 1;
				if (lowerUlIndex === upperUlIndex) {
					selectors = [
						`:nth-child(${lowerUlIndex} of .hours) > li:nth-child(n + ${lowerLiIndex + 1}):nth-child(-n + ${upperLiIndex - 1})`,
					];
				} else {
					selectors = [
						`:nth-child(${lowerUlIndex} of .hours) > li:nth-child(n + ${lowerLiIndex + 1})`,
						`:nth-child(n + ${lowerUlIndex + 1} of .hours):nth-child(-n + ${upperUlIndex - 1} of .hours) > li`,
						`:nth-child(${upperUlIndex} of .hours) > li:nth-child(-n + ${upperLiIndex - 1})`,
					];
				}
			} else {
				selectors = [`:not(.weekdays) > li:nth-child(n + ${lowerIndex + addLower}):nth-child(-n + ${upperIndex + addUpper})`];
			}
		}
		if (this.viewMode === ViewMode.hours && this.interval && (lowerIndex !== -1 || upperIndex !== -1)) {
			const lowerUlIndex = Math.floor(lowerIndex / perHour) + 1;
			const upperUlIndex = Math.floor(upperIndex / perHour) + 1;
			if (upperIndex === -1) {
				selectors.push(`:nth-child(${lowerUlIndex} of .minutes) > li:nth-child(n + ${lowerIndex % perHour + 2})`);
			} else if (lowerIndex === -1) {
				selectors.push(`:nth-child(${upperUlIndex} of .minutes) > li:nth-child(-n + ${upperIndex % perHour})`);
			} else if (lowerUlIndex === upperUlIndex) {
				selectors.push(`:nth-child(${lowerUlIndex} of .minutes) > li:nth-child(n + ${lowerIndex % perHour + 2}):nth-child(-n + ${upperIndex % perHour})`);
			} else {
				selectors.push(`:nth-child(${lowerUlIndex} of .minutes) > li:nth-child(n + ${lowerIndex % perHour + 2})`);
				selectors.push(`:nth-child(${upperUlIndex} of .minutes) > li:nth-child(-n + ${upperIndex % perHour})`);
			}
			const lowerSelector = `li[aria-label="${asUTCDate(lowerDate).toISOString().slice(0, 13)}:00"].constricted`;
			const lowerClass = this.element.querySelector(lowerSelector)?.classList;
			const upperSelector = `li[aria-label="${asUTCDate(upperDate).toISOString().slice(0, 13)}:00"].constricted`;
			const upperClass = this.element.querySelector(upperSelector)?.classList;
			lowerClass?.remove('lower', 'upper');
			upperClass?.remove('lower', 'upper');
			if (lowerClass === upperClass) {
				if (dateFixed < dateCursor) {
					lowerClass?.add('lower');
				} else if (dateFixed > dateCursor) {
					upperClass?.add('upper');
				}
			} else {
				lowerClass?.add('lower');
				upperClass?.add('upper');
			}
		}
		this.rangeSelectCssRule.selectorText = selectors.map(selector => {
			return this.rangeSelectorText.replace(':not(*)', selector);
		}).join(',');
	}

	public markSelectedDates() {
		this.calendarItems.forEach(elem => elem.classList.remove('selected', 'preselected'));
		const dateRange = this.calendar.dateRange;
		if (this.calendar.settings.withRange) {
			if (dateRange[0] && dateRange[1]) {
				this.markDateRange(dateRange[0], dateRange[1]);
				this.calendarItems.item(this.indexOfCalendarItem(dateRange[0]))?.classList.add('selected');
				const upperIndex = this.indexOfCalendarItem(dateRange[1]);
				this.calendarItems.item(upperIndex)?.classList.add('selected');
			} else if (dateRange[0]) {
				const dateSelector = this.getDateSelector(dateRange[0]);
				this.element.querySelector(dateSelector)?.classList.add('selected');
			} else if (dateRange[1]) {
				const dateSelector = this.getDateSelector(dateRange[1]);
				this.element.querySelector(dateSelector)?.classList.add('selected');
			}
			if (this.preselectedDate) {
				const dateSelector= this.getDateSelector(this.preselectedDate);
				this.element.querySelector(dateSelector)?.classList.add('preselected');
			}
		} else if (dateRange[0]) {
			const dateSelector = this.getDateSelector(dateRange[0]);
			this.element.querySelector(dateSelector)?.classList.add('selected');
		}
	}

	private toggleMidnightItem() {
		// the hour view calendar adds an extra list element for the last hour (24h or 12am), which is only needed in
		// upper range view to help selecting midnight of the next day.
		if (!this.calendar.settings.withRange || this.viewMode !== ViewMode.hours)
			return;
		const midnightElement = this.element.querySelector('.sheet-body ul.hours:last-child > li[aria-details="midnight next day"]');
		if (!(midnightElement instanceof HTMLElement))
			return;
		const dateRange = this.calendar.dateRange;
		if ([SheetType.compact, SheetType.plain].includes(this.calendar.settings.sheetType) && dateRange[1] instanceof Date) {
			const midnightDateString = asUTCDate(dateRange[1]).toISOString().slice(0, 16);
			const showMidnightElement = midnightElement.dataset.date === midnightDateString;
			midnightElement.parentElement?.toggleAttribute('hidden', !showMidnightElement);
			return;
		}
		midnightElement.parentElement?.toggleAttribute('hidden', !this.upperRange);
	}

	private closeDialogIfNeeded() {
		const settings = this.calendar.settings;
		const dateRange = this.calendar.dateRange;
		if (this.sheetType === SheetType.compact && dateRange[0] && dateRange[1]) {
			settings.close();
		}
	}

	private setDate(element: HTMLElement) {
		const newDate = new Date(element.dataset.date!);
		const settings = this.calendar.settings;
		const dateRange = this.calendar.dateRange;
		if (this.sheetType === SheetType.lower) {
			if (dateRange[1] && newDate > dateRange[1]) {
				// swap upper and lower range
				dateRange[0] = dateRange[1];
				dateRange[1] = newDate;
				this.calendar.calendarSheets[1]!.viewMode = this.viewMode;
				this.calendar.calendarSheets[0].fetchCalendar(dateRange[0]);
				this.calendar.calendarSheets[1]!.fetchCalendar(dateRange[1]);
			} else {
				dateRange[0] = newDate;
			}
			this.calendar.activateSheet(this.calendar.calendarSheets[1]!);
			this.calendar.calendarSheets[1]?.markSelectedDates();
		} else if (this.sheetType === SheetType.upper) {
			if (dateRange[0] && newDate < dateRange[0]) {
				// swap upper and lower range
				dateRange[1] = dateRange[0];
				dateRange[0] = newDate;
				this.calendar.calendarSheets[0].viewMode = this.viewMode;
				this.calendar.calendarSheets[0].fetchCalendar(dateRange[0]);
				this.fetchCalendar(dateRange[1]);
			} else {
				dateRange[1] = newDate;
			}
			this.calendar.activateSheet(this.calendar.calendarSheets[0]!);
			this.calendar.calendarSheets[0].markSelectedDates();
		} else if (settings.withRange) {
			// this.sheetType === SheetType.{compact, plain}
 			if (this.upperRange && dateRange[0]) {
 				if (newDate < dateRange[0]) {
 					dateRange[1] = dateRange[0];
					dateRange[0] = newDate;
				} else {
					dateRange[1] = newDate;
				}
				this.upperRange = false;
				this.rangeSelectCssRule.style.cursor = '';
			} else {
				dateRange[0] = newDate;
				dateRange[1] = null;
				this.upperRange = true;
			}
			this.toggleMidnightItem();
		} else {
			dateRange[0] = newDate;
			dateRange[1] = new Date('-');  // invalid date but evaluates to true in `closeDialogIfNeeded`
		}
		if (dateRange[0] instanceof Date) {
			dateRange[0] = maxDate(minDate(dateRange[0], this.maxDate), this.minDate);
		}
		if (dateRange[1] instanceof Date) {
			dateRange[1] = minDate(maxDate(dateRange[1], this.minDate), this.maxDate);
		}
		settings.updateDate(dateRange[0], dateRange[1]);
		if (settings.sheetType === SheetType.plain) {
			this.showDateRange();
		}
	}

	private showDateRange() {
		const setAsideElement = (asideElement: HTMLTimeElement, date: Date) => {
			asideElement.dateTime = date.toISOString();
			asideElement.textContent = this.calendar.settings.dateOnly ? date.toDateString() : date.toLocaleString();
		};
		const dateRange = this.calendar.dateRange;
		const sheetBody = this.element.querySelector('.sheet-body');
		if (!sheetBody)
			throw new Error("Missing sheet body element for showing calendar date range");

		sheetBody.insertAdjacentHTML('afterbegin', '<div class="aside-left"><time></time></div>');
		const leftAsideElement = sheetBody.querySelector('.aside-left > time') as HTMLTimeElement;
		const firstItem = this.element.querySelector('li[data-date]:first-child')!;
		const firstDate = this.getDate(firstItem);
		if (dateRange[1] && dateRange[1] < firstDate) {
			setAsideElement(leftAsideElement, dateRange[1]);
		} else if (dateRange[0] && dateRange[0] < firstDate) {
			setAsideElement(leftAsideElement, dateRange[0]);
		} else {
			leftAsideElement.dateTime = '';
			leftAsideElement.textContent = '';
		}

		sheetBody.insertAdjacentHTML('beforeend', '<div class="aside-right"><time></time></div>');
		const rightAsideElement = sheetBody.querySelector('.aside-right > time') as HTMLTimeElement;
		const lastItem = this.element.querySelector('li[data-date]:last-child')!;
		const lastDate = this.getDate(lastItem);
		if (dateRange[0] && dateRange[0] > lastDate) {
			setAsideElement(rightAsideElement, dateRange[0]);
		} else if (dateRange[1] && dateRange[1] > lastDate) {
			setAsideElement(rightAsideElement, dateRange[1]);
		} else {
			rightAsideElement.dateTime = '';
			rightAsideElement.textContent = '';
		}
	}

	private async selectToday() {
		const todayDateString = this.todayDateString;
		const settings = this.calendar.settings;
		const dateRange = this.calendar.dateRange;
		let todayElem = this.element.querySelector(`li[data-date="${todayDateString}"]`);
		if (!todayElem) {
			await this.fetchCalendar(new Date(), ViewMode.weeks);
			todayElem = this.element.querySelector(`li[data-date="${todayDateString}"]`);
		}
		if (!settings.inputElement.disabled && todayElem instanceof HTMLElement && !todayElem.hasAttribute('disabled')) {
			this.setDate(todayElem);
			this.markSelectedDates();
		}
		this.closeDialogIfNeeded();
	}

	private selectMinute = (event: Event) => {
		if (event.target instanceof HTMLLIElement) {
			this.calendar.activateSheet(this);
			const dateRange = this.calendar.dateRange;
			const liElement = event.target;
			const elementDateString = liElement.dataset.date ?? '–';
			if (elementDateString.endsWith('T00:00') && liElement.getAttribute('aria-details') === 'midnight next day') {
				// selected hour is midnight, remove the constricted from other hour items
				this.element.querySelectorAll('li[aria-label]').forEach(elem => {
					elem.classList.remove('selected', 'preselected', 'constricted', 'lower', 'upper');
				});
				this.element.querySelectorAll('ul[aria-labelledby]').forEach(elem => {
					elem.toggleAttribute('hidden', true);
				});
				if (!this.upperRange) {
					dateRange[0] = dateRange[1] = null;
					liElement.parentElement?.toggleAttribute('hidden', true);
					this.rangeSelectCssRule.selectorText = this.rangeSelectorText;
					return;
				}
			} else if ([SheetType.compact, SheetType.plain].includes(this.calendar.settings.sheetType) && !this.upperRange && dateRange[0]) {
				const labelDateString = `${elementDateString.slice(0, 13)}:00`;
				this.element.querySelectorAll(`li[aria-label]:not([aria-label="${labelDateString}"]), li[aria-details="midnight next day"]`).forEach(elem => {
					elem.classList.remove('selected', 'preselected', 'constricted', 'lower', 'upper');
				});
				this.element.querySelectorAll(`ul[aria-labelledby]:not([aria-labelledby="${labelDateString}"])`).forEach(elem => {
					elem.toggleAttribute('hidden', true);
				});
				this.markDateRange(dateRange[0], new Date(elementDateString), true);
			}
			this.setDate(liElement);
			this.markSelectedDates();
			this.closeDialogIfNeeded();
		}
	};

	private selectHour(liElement: HTMLLIElement) {
		if ([SheetType.compact, SheetType.plain].includes(this.calendar.settings.sheetType) && this.upperRange) {
			const labelDateString = `${asUTCDate(this.calendar.dateRange[0]!).toISOString().slice(0, 13)}:00`;
			this.element.querySelectorAll(`li[aria-label]:not([aria-label="${labelDateString}"]), li[aria-details="midnight next day"]`).forEach(elem => {
				elem.classList.remove('selected', 'preselected', 'constricted', 'lower', 'upper');
			});
			this.element.querySelectorAll(`ul[aria-labelledby]:not([aria-labelledby="${labelDateString}"])`).forEach(elem => {
				elem.toggleAttribute('hidden', true);
			});
		} else {
			this.element.querySelectorAll('li[aria-label], li[aria-details="midnight next day"]').forEach(elem => {
				elem.classList.remove('selected', 'preselected', 'constricted', 'lower', 'upper');
			});
			this.element.querySelectorAll('ul[aria-labelledby]').forEach(elem => {
				elem.toggleAttribute('hidden', true);
			});
		}
		this.rangeSelectCssRule.selectorText = `${this.sheetSelector} .sheet-body ul:not(*)`;
		const label = liElement.getAttribute('aria-label');
		if (label) {
			const ulElem = this.element.querySelector(`ul[aria-labelledby="${label}"]`);
			if (ulElem instanceof HTMLUListElement) {
				liElement.classList.add('constricted');
				ulElem.toggleAttribute('hidden', false);
			}
		} else if (liElement.parentElement instanceof HTMLUListElement && liElement.parentElement.hasAttribute('aria-labelledby')) {
			const labelledby = liElement.parentElement.getAttribute('aria-labelledby');
			this.element.querySelector(`li[aria-label="${labelledby}"]`)?.classList.add('constricted');
			liElement.parentElement.toggleAttribute('hidden', false);
		}
	}

	private selectDay = (event: Event) => {
		const settings = this.calendar.settings;
		if (event.target instanceof HTMLLIElement) {
			this.calendar.activateSheet(this);
			if (settings.dateOnly) {
				this.setDate(event.target);
				this.markSelectedDates();
				this.closeDialogIfNeeded();
			} else {
				this.fetchCalendar(this.getDate(event.target), ViewMode.hours);
			}
		}
	};

	private selectMonth = (event: Event) => {
		if (event.target instanceof HTMLLIElement) {
			this.calendar.activateSheet(this);
			this.fetchCalendar(this.getDate(event.target), ViewMode.weeks);
		}
	};

	private selectYear = (event: Event) => {
		if (event.target instanceof HTMLLIElement) {
			this.calendar.activateSheet(this);
			this.fetchCalendar(this.getDate(event.target), ViewMode.months);
		}
	};

	private async goto(direction: Direction) {
		const dateRange = this.calendar.dateRange;
		let selectedDate: Date|null = null;
		if (this.calendar.settings.withRange) {
			if (this.preselectedDate) {
				selectedDate = this.preselectedDate;
			} else if (!this.upperRange && dateRange[0]) {
				selectedDate = dateRange[0];
			} else if (this.upperRange && dateRange[1]) {
				selectedDate = dateRange[1];
			}
		} else if (dateRange[0]) {
			selectedDate = dateRange[0];
		}
		if (!selectedDate) {
			if (dateRange[0]) {
				selectedDate = dateRange[0];
			} else {
				const selectedItem: Element | null = this.calendarItems.item(this.calendarItems.length / 2);
				selectedDate = this.getDate(selectedItem);
			}
		}
		const nextDate = this.getDelta(direction, selectedDate);
		this.preselectedDate = this.calendar.settings.withRange ? nextDate : null;
		const dataDateString = asUTCDate(nextDate).toISOString().slice(0, 16);
		let nextItem: Element|null = null;
		if (this.viewMode !== ViewMode.weeks || selectedDate.getMonth() === nextDate.getMonth()) {
			nextItem = this.element.querySelector(`.sheet-body li[data-date="${dataDateString}"]`);
		}
		if (!nextItem) {
			await this.fetchCalendar(nextDate);
			nextItem = this.element.querySelector(`.sheet-body li[data-date="${dataDateString}"]`);
		}
		if (nextItem instanceof HTMLLIElement) {
			if (this.viewMode === ViewMode.hours) {
				this.selectHour(nextItem);
			}
			if (!this.preselectedDate) {
				this.setDate(nextItem);
			}
			this.markSelectedDates();
			if (this.upperRange && dateRange[0] && this.preselectedDate) {
				this.markDateRange(dateRange[0], this.preselectedDate, true);
			}
		}
	}

	public async fetchCalendar(atDate: Date, viewMode?: ViewMode) {
		const query = new URLSearchParams([
			['date', asUTCDate(atDate).toISOString().slice(0, 10)],
			['mode', viewMode ?? this.viewMode],
		]);
		if (this.calendar.settings.hour12) {
			query.set('hour12', '');
		}
		if (this.interval) {
			query.set('interval', String(this.interval));
		}
		this.element.classList.add('loading');
		const response = await fetch(`${this.calendar.endpoint}?calendar&${query.toString()}`, {
			method: 'GET',
		});
		this.element.classList.remove('loading');
		if (response.status === 200) {
			this.element.innerHTML = await response.text();
			if (this.calendar.settings.sheetType === SheetType.plain) {
				this.showDateRange();
			}
		} else {
			console.error(`Failed to fetch from ${this.calendar.endpoint} (status=${response.status})`);
		}
	}

	private getSheetBounds() : [Date, Date] {
		const firstItem = this.calendarItems.item(0);
		const lastItem = this.calendarItems.item(this.calendarItems.length - 1);
		const lower= new Date(firstItem.dataset.date!);
		const upper = new Date(lastItem.dataset.date!);
		return [lower, upper];
	}

	private getRangeSelectCssRule() : CSSStyleRule {
		for (let i = document.styleSheets.length - 1; i >= 0; --i) {
			const sheet = document.styleSheets[i];
			for (let k = 0; k < sheet.cssRules.length; ++k) {
				const cssRule = sheet.cssRules[k];
				if (cssRule instanceof CSSStyleRule && cssRule.selectorText === `${this.sheetSelector} .sheet-body ul:not(*)`) {
					const selectorText = `#${CSS.escape(this.calendar.settings.inputElement.id)} ~ ${this.sheetSelector} .sheet-body ul:not(*)`;
					const index = sheet.insertRule(`${selectorText}{${cssRule.style.cssText}}`, sheet.cssRules.length);
					return sheet.cssRules[index] as CSSStyleRule;
				}
			}
		}
		throw new Error(`Could not find CSS rule for '${this.sheetSelector} .sheet-body ul:not(*)'`);
	}
}


export class CalendarWidget extends Widget {
	public readonly element: HTMLElement;
	public readonly settings: CalendarSettings;
	public readonly calendarSheets: [CalendarSheet, CalendarSheet|null];
	private activeSheet: CalendarSheet;
	public readonly baseSelector = '.dj-calendar';
	private readonly styleSheet: CSSStyleSheet;
	public dateRange: DateRange = [null, null];

	constructor(calendarElement: HTMLElement, settings: CalendarSettings) {
		super(settings.inputElement);
		this.settings = settings;
		this.element = calendarElement;
		this.styleSheet = StyleHelpers.stylesAreInstalled(this.baseSelector) ?? this.transferStyles();
		const lowerSheetElement = calendarElement.querySelector('div:is(.compact-datetime, .lower-datetime, .plain-datetime)');
		if (!(lowerSheetElement instanceof HTMLDivElement))
			throw new Error(`Calendar element ${calendarElement} does not contain expected sheet`);
		if (settings.sheetType === SheetType.dual) {
			const upperSheetElement = calendarElement.querySelector('div.upper-datetime');
			if (!(upperSheetElement instanceof HTMLDivElement))
				throw new Error(`Calendar element ${calendarElement} does not contain expected sheet`);
			this.calendarSheets = [
				new CalendarSheet(this, lowerSheetElement as HTMLDivElement, SheetType.lower),
				new CalendarSheet(this, upperSheetElement as HTMLDivElement, SheetType.upper),
			];
		} else {
			this.calendarSheets = [
				new CalendarSheet(this, lowerSheetElement as HTMLDivElement, settings.sheetType),
				null,
			];
		}
		this.activeSheet = this.calendarSheets[0];
	}

	public activateSheet(calendarSheet: CalendarSheet) {
		this.activeSheet = calendarSheet;
	}

	private transferStyles() : CSSStyleSheet {
		const declaredStyles = document.createElement('style');
		declaredStyles.innerText = styles;
		document.head.appendChild(declaredStyles);
		if (!declaredStyles.sheet)
			throw new Error("Could not create <style> element");
		const sheet = declaredStyles.sheet;

		let loaded = false;
		const inputElement = this.settings.inputElement;
		inputElement.style.transition = 'none';  // prevent transition while pilfering styles
		for (let index = 0; index < sheet.cssRules.length; index++) {
			const cssRule = sheet.cssRules.item(index) as CSSStyleRule;
			const selector = cssRule.selectorText.trim();
			let extraStyles = '';
			switch (selector) {
				case this.baseSelector:
					extraStyles = StyleHelpers.extractStyles(inputElement, [
						'font-family', 'font-size', 'font-stretch', 'font-style', 'font-weight',
						'letter-spacing', 'white-space', 'line-height'
					]).concat(StyleHelpers.extractStyles(inputElement, {
						'--border-style': 'border-style',
						'--border-width': 'border-width',
						'--border-radius': 'border-radius',
					}));
					loaded = true;
					break;
				case `${this.baseSelector} .controls`:
					extraStyles = StyleHelpers.extractStyles(inputElement, ['padding']);
					break;
				case `${this.baseSelector} .sheet-body .central`:
					extraStyles = StyleHelpers.extractStyles(inputElement, ['padding']);
					break;
				default:
					break;
			}
			if (extraStyles) {
				sheet.insertRule(`${selector}{${extraStyles}}`, ++index);
			}
		}
		inputElement.style.transition = '';
		StyleHelpers.replaceMediaQueryStyles(
			-1,
			sheet,
			this.baseSelector,
			{
				'--border-color': 'border-color',
				'--outline': 'outline',
			},
			inputElement,
		);
		if (!loaded)
			throw new Error(`Could not load styles for ${this.baseSelector}`);
		return sheet;
	}

	// navigate through the calendar with arrow keys
	// return true if key shall prevent bubbling up the event chain
	public async navigate(key: string) {
		this.activeSheet.navigate(key);
	}

	public updateDate(currentDate: Date|null, extendedDate: Date|null) {
		if (currentDate) {
			this.dateRange = [currentDate, extendedDate];
			this.calendarSheets[0].fetchCalendar(currentDate);
			if (this.calendarSheets[1] && extendedDate) {
				this.calendarSheets[1].fetchCalendar(extendedDate);
			}
		} else {
			this.dateRange = [null, null];
		}
	}

	public valueAsDate() : Date | null {
		return this.dateRange[0];
	}

	protected formResetted(event: Event) {
		this.settings.inputElement.value = this.settings.inputElement.defaultValue;
		if (this.settings.inputElement.value) {
			this.updateDate(new Date(this.settings.inputElement.value), null);
		} else {
			this.updateDate(null, null);
		}
	}

	protected formSubmitted(event: Event) {}
}


const CAL = Symbol('Calendar');

export class DateCalendarElement extends HTMLInputElement {
	private [CAL]!: CalendarWidget;  // hides internal implementation

	connectedCallback() {
		const fieldGroup = this.closest('[role="group"]');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		const calendarElement = fieldGroup.querySelector('[aria-label="calendar"]');
		if (!(calendarElement instanceof HTMLElement))
			throw new Error(`Could not find calendar element for ${this}`);
		const dateTimeFormat = Intl.DateTimeFormat(navigator.language, {hour: '2-digit'});
		const settings: CalendarSettings = {
			dateOnly: true,
			withRange: false,
			inputElement: this,
			hour12: dateTimeFormat.resolvedOptions().hour12 ?? false,
			sheetType: CalendarSettings.layoutToSheetType(calendarElement),
			updateDate: (date: Date) => {
				this.value = date.toISOString().slice(0, 10);
				this.dispatchEvent(new Event('input'));
				this.dispatchEvent(new Event('blur'));
			},
			close: () => {},
		};

		this[CAL] = new CalendarWidget(calendarElement as HTMLElement, settings);
		if (this.value) {
			this[CAL].updateDate(new Date(`${this.value}T00:00`), null);
		}
		this.hidden = true;
	}

	get valueAsDate() : Date|null {
		return this[CAL].valueAsDate();
	}
}


export class DateTimeCalendarElement extends HTMLInputElement {
	private [CAL]!: CalendarWidget;  // hides internal implementation

	connectedCallback() {
		const fieldGroup = this.closest('[role="group"]');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		const calendarElement = fieldGroup.querySelector('[aria-label="calendar"]');
		if (!(calendarElement instanceof HTMLElement))
			throw new Error(`Could not find calendar element for ${this}`);
		const dateTimeFormat = Intl.DateTimeFormat(navigator.language, {hour: '2-digit'});
		const settings: CalendarSettings = {
			dateOnly: false,
			withRange: false,
			inputElement: this,
			hour12: dateTimeFormat.resolvedOptions().hour12 ?? false,
			sheetType: CalendarSettings.layoutToSheetType(calendarElement),
			updateDate: (date: Date) => {
				this.value = date.toISOString().slice(0, 16);
				this.dispatchEvent(new Event('input'));
				this.dispatchEvent(new Event('blur'));
			},
			close: () => {},
		};

		this[CAL] = new CalendarWidget(calendarElement as HTMLElement, settings);
		if (this.value) {
			this[CAL].updateDate(new Date(this.value), null);
		}
		this.hidden = true;
	}

	get valueAsDate() : Date|null {
		return this[CAL].valueAsDate();
	}
}


export class DateRangeCalendarElement extends HTMLInputElement {
	private [CAL]!: CalendarWidget;  // hides internal implementation

	connectedCallback() {
		const fieldGroup = this.closest('[role="group"]');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		const calendarElement = fieldGroup.querySelector('[aria-label="calendar"]');
		if (!(calendarElement instanceof HTMLElement))
			throw new Error(`Could not find calendar element for ${this}`);
		const dateTimeFormat = Intl.DateTimeFormat(navigator.language, {hour: '2-digit'});
		const settings: CalendarSettings = {
			dateOnly: true,
			withRange: true,
			inputElement: this,
			hour12: dateTimeFormat.resolvedOptions().hour12 ?? false,
			sheetType: CalendarSettings.layoutToSheetType(calendarElement),
			updateDate: (lowerDate: Date, upperDate?: Date) => {
				const dateStrings = [
					`${asUTCDate(lowerDate).toISOString().slice(0, 10)}T00:00`,
					upperDate ? `${asUTCDate(upperDate).toISOString().slice(0, 10)}T00:00` : '',
				];
				this.value = dateStrings.join(';');
				this.dispatchEvent(new Event('input'));
				this.dispatchEvent(new Event('blur'));
			},
			close: () => {},
		};

		this[CAL] = new CalendarWidget(calendarElement as HTMLElement, settings);
		if (this.value) {
			const [start, end] = this.value.split(';');
			this[CAL].updateDate(new Date(start), new Date(end));
		}
		this.hidden = true;
	}

	get valueAsDate() : Date|null {
		return this[CAL].valueAsDate();
	}
}


export class DateTimeRangeCalendarElement extends HTMLInputElement {
	private [CAL]!: CalendarWidget;  // hides internal implementation

	connectedCallback() {
		const fieldGroup = this.closest('[role="group"]');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		const calendarElement = fieldGroup.querySelector('[aria-label="calendar"]');
		if (!(calendarElement instanceof HTMLElement))
			throw new Error(`Could not find calendar element for ${this}`);
		const dateTimeFormat = Intl.DateTimeFormat(navigator.language, {hour: '2-digit'});
		const settings: CalendarSettings = {
			dateOnly: false,
			withRange: true,
			inputElement: this,
			hour12: dateTimeFormat.resolvedOptions().hour12 ?? false,
			sheetType: CalendarSettings.layoutToSheetType(calendarElement),
			updateDate: (lowerDate: Date, upperDate?: Date) => {
				const dateStrings = [
					asUTCDate(lowerDate).toISOString().slice(0, 16),
					upperDate ? asUTCDate(upperDate).toISOString().slice(0, 16) : '',
				];
				this.value = dateStrings.join(';');
				this.dispatchEvent(new Event('input'));
				this.dispatchEvent(new Event('blur'));
			},
			close: () => {},
		};

		this[CAL] = new CalendarWidget(calendarElement as HTMLElement, settings);
		if (this.value) {
			const [start, end] = this.value.split(';');
			this[CAL].updateDate(new Date(start), new Date(end));
		}
		this.hidden = true;
	}

	get valueAsDate() : Date|null {
		return this[CAL].valueAsDate();
	}
}
