import {StyleHelpers} from "./helpers";
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


export type CalendarSettings = {
	dateOnly: boolean,  // if true, time is not displayed
	withRange: boolean,  // if true, a range of dates can be selected
	minDate?: Date,  // if set, dates before this are disabled
	maxDate?: Date,  // if set, dates after this are disabled
	interval?: number,  // granularity of entries in time picker
	endpoint: string,  // URL to fetch calendar data from
	inputElement: HTMLInputElement,  // input element to pilfer styles from
	updateDate: Function,  // callback to update date input
	close: Function,  // callback to close calendar
};


type DateRange = [Date, Date] | [Date, null] | [null, null];

export class Calendar {
	public readonly element: HTMLElement;
	private viewMode!: ViewMode;
	private settings: CalendarSettings;
	private upperRange = false;
	private preselectedDate: Date|null = null;
	private dateRange: DateRange = [null, null];
	private sheetBounds: [Date, Date];
	private prevSheetDate!: Date;
	private nextSheetDate!: Date;
	private narrowSheetDate?: Date;
	private extendSheetDate?: Date;
	private calendarItems!: NodeListOf<HTMLLIElement>;
	private minDate?: Date;
	private maxDate?: Date;
	private minWeekDate?: Date;
	private maxWeekDate?: Date;
	private minMonthDate?: Date;
	private maxMonthDate?: Date;
	private minYearDate?: Date;
	private maxYearDate?: Date;
	private readonly baseSelector = '[aria-haspopup="dialog"] + .dj-calendar';
	private readonly rangeSelectCssRule: CSSStyleRule;
	private readonly rangeSelectorText: string;

	constructor(calendarElement: HTMLElement | null, settings: CalendarSettings) {
		this.settings = settings;
		if (calendarElement instanceof HTMLElement) {
			this.element = calendarElement;
		} else {
			this.element = document.createElement('div');
			this.fetchCalendar(new Date(), ViewMode.weeks);
		}
		const observer = new MutationObserver(() => this.registerCalendar());
		observer.observe(this.element, {childList: true});
		this.setMinMaxBounds();
		if (!StyleHelpers.stylesAreInstalled(this.baseSelector)) {
			this.transferStyles();
		}
		this.rangeSelectCssRule = this.getRangeSelectCssRule();
		this.rangeSelectorText = this.rangeSelectCssRule.selectorText;
		this.registerCalendar();
		this.sheetBounds = this.getSheetBounds();
	}

	private get currentDateString() : string {
		if (!this.dateRange[0])
			return '';
		return this.asUTCDate(this.dateRange[0]).toISOString().slice(0, this.settings.dateOnly ? 10 : 16);
	}

	private get todayDateString() : string {
		return this.asUTCDate(new Date()).toISOString().slice(0, this.settings.dateOnly ? 10 : 16);
	}

	private asUTCDate(date: Date) : Date {
		return new Date(date.getTime() - date.getTimezoneOffset() * 60000);
	}

	private getViewMode() : ViewMode {
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

	private setMinMaxBounds() {
		if (this.settings.minDate) {
			this.minWeekDate = new Date(this.settings.minDate);
			this.minWeekDate.setHours(0, 0, 0);
			this.minMonthDate = new Date(this.minWeekDate);
			this.minMonthDate.setDate(1);
			this.minYearDate = new Date(this.minMonthDate);
			this.minYearDate.setMonth(0);
		}
		if (this.settings.maxDate) {
			this.maxWeekDate = new Date(this.settings.maxDate);
			this.maxWeekDate.setHours(23, 59, 59);
			this.maxMonthDate = new Date(this.maxWeekDate);
			this.maxMonthDate.setDate(28);
			this.maxYearDate = new Date(this.maxMonthDate);
			this.maxYearDate.setMonth(11);
		}
	}

	private getDate(selector: string | Element) : Date {
		const element = selector instanceof Element ? selector : this.element.querySelector(selector);
		if (!(element instanceof Element))
			throw new Error(`Element ${selector} is missing`);
		const dateValue = element.getAttribute('data-date') ?? element.getAttribute('datetime');
		return new Date(dateValue ?? '');
	}

	private registerCalendar() {
		this.viewMode = this.getViewMode();
		this.prevSheetDate = this.getDate('button.prev');
		const narrowButton = this.element.querySelector('button.narrow');
		this.narrowSheetDate = narrowButton ? this.getDate(narrowButton) : undefined;
		this.nextSheetDate = this.getDate('button.next');
		const extendButton = this.element.querySelector('button.extend');
		this.extendSheetDate = extendButton ? this.getDate(extendButton) : undefined;
		this.element.querySelector('button.prev')?.addEventListener('click', this.turnPrev, {once: true});
		this.element.querySelector('button.narrow')?.addEventListener('click', this.turnNarrow, {once: true});
		this.element.querySelector('button.extend')?.addEventListener('click', this.turnExtend, {once: true});
		this.element.querySelector('button.today')?.addEventListener('click', this.turnToday, {once: true});
		this.element.querySelector('button.next')?.addEventListener('click', this.turnNext, {once: true});
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
		// since each datetime-picker can have different interval values, set this on element level
		if (this.settings.interval) {
			const num = Math.min(60 / this.settings.interval!, 6);
			const gridTemplateColumns = `repeat(${num}, 1fr)`;
			this.element.querySelectorAll('.ranges ul.minutes').forEach(minutesElement => {
				(minutesElement as HTMLElement).style.gridTemplateColumns = gridTemplateColumns;
			});
		}

		this.calendarItems.forEach(elem => {
			const date = this.getDate(elem);
			if (this.minDate && date < this.minDate || this.maxDate && date > this.maxDate) {
				elem.toggleAttribute('disabled', true);
			} else {
				elem.addEventListener('click', (event: Event) => {
					if (event.target instanceof HTMLLIElement) {
						this.setDate(event.target);
						this.markSelectedDates();
						if (!this.settings.withRange || this.dateRange[0] && this.dateRange[1]) {
							this.settings.close();
						}
					}
				}, {once: true});
				if (this.settings.withRange) {
					elem.addEventListener('mouseenter', this.handleOver);
				}
			}
		});

		const lowerHourString = this.dateRange[0] ? this.asUTCDate(this.dateRange[0]).toISOString().slice(0, 13) : '';
		const upperDateString = this.settings.withRange && this.dateRange[1] ? this.asUTCDate(this.dateRange[1]).toISOString().slice(0, 16) : '';
		const upperHourString = upperDateString.slice(0, 13);
		const todayHourString = this.todayDateString.slice(0, 13).concat(':00');
		this.element.querySelectorAll('li[aria-label]').forEach(elem => {
			const label = elem.getAttribute('aria-label')!;
			elem.classList.toggle('today', label === todayHourString);
			const selector = `ul[aria-labelledby="${label}"]`;
			if (lowerHourString === label.slice(0, 13) || upperHourString === label.slice(0, 13) && upperDateString.slice(11, 16) !== '00:00') {
				elem.classList.add('constricted');
				this.element.querySelector(selector)?.removeAttribute('hidden');
			}

			if (this.element.querySelectorAll(`${selector} > li[data-date]:not([disabled])`).length === 0) {
				elem.toggleAttribute('disabled', true);
			} else {
				elem.addEventListener('click', (event: Event) => {
					if (event.target instanceof HTMLLIElement) {
						this.selectHour(event.target);
					}
				});
				if (this.settings.withRange) {
					elem.addEventListener('mouseenter', this.handleOver);
				}
			}
		});

		// the hour calendar adds an extra ul element for the last hour, which is only needed in upper range view
		this.element.querySelector('.ranges ul.hours:last-child')?.setAttribute('hidden', '');
	}

	private registerWeeksView() {
		const todayDateString = this.todayDateString.slice(0, 10);
		if (this.settings.minDate) {
			this.minWeekDate = new Date(this.settings.minDate);
			this.minWeekDate.setHours(0, 0, 0);
		}
		this.calendarItems.forEach(elem => {
			elem.classList.toggle('today', elem.getAttribute('data-date') === todayDateString);
			const date = this.getDate(elem);
			if (this.minWeekDate && date < this.minWeekDate || this.maxWeekDate && date > this.maxWeekDate) {
				elem.toggleAttribute('disabled', true);
			} else {
				elem.addEventListener('click', this.selectDay);
				if (this.settings.withRange) {
					elem.addEventListener('mouseenter', this.handleOver);
				}
			}
		});
	}

	private registerMonthsView() {
		const todayMonthString = this.todayDateString.slice(0, 7);
		this.calendarItems.forEach(elem => {
			const date = this.getDate(elem);
			const monthString = elem.getAttribute('data-date')?.slice(0, 7);
			elem.classList.toggle('today', monthString === todayMonthString);
			if (this.minMonthDate && date < this.minMonthDate || this.maxMonthDate && date > this.maxMonthDate) {
				elem.toggleAttribute('disabled', true);
			} else {
				elem.addEventListener('click', this.selectMonth);
				if (this.settings.withRange) {
					elem.addEventListener('mouseenter', this.handleOver);
				}
			}
		});
	}

	private registerYearsView() {
		const todayYearString = this.todayDateString.slice(0, 4);
		this.calendarItems.forEach(elem => {
			const date = this.getDate(elem);
			const yearString = elem.getAttribute('data-date')?.slice(0, 4);
			elem.classList.toggle('today', yearString === todayYearString);
			if (this.minYearDate && date < this.minYearDate || this.maxYearDate && date > this.maxYearDate) {
				elem.toggleAttribute('disabled', true);
			} else {
				elem.addEventListener('click', this.selectYear);
				if (this.settings.withRange) {
					elem.addEventListener('mouseenter', this.handleOver);
				}
			}
		});
	}

	// navigate through the calendar with arrow keys
	// return true if key shall prevent bubbling up the event chain
	public async navigate(key: string) {
		let element = null;
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
				this.settings.close();
				break;
			case 'PageUp':
				element = this.element.querySelector('button.prev');
				if (element) {
					await this.fetchCalendar(this.getDate(element), this.viewMode);
				}
				break;
			case 'PageDown':
				element = this.element.querySelector('button.next');
				if (element) {
					await this.fetchCalendar(this.getDate(element), this.viewMode);
				}
				break;
			case 'Enter':
				if (this.preselectedDate) {
					const dateString = this.preselectedDate.toISOString().slice(0, this.viewMode === ViewMode.hours ? 16 : 10) ?? '';
					element = this.element.querySelector(`.ranges li[data-date="${dateString}"]`);
				} else {
					const dateString = (this.upperRange ? this.dateRange[1] : this.dateRange[0])?.toISOString().slice(0, this.viewMode === ViewMode.hours ? 16 : 10) ?? '';
					element = this.element.querySelector(`.ranges li[data-date="${dateString}"]`);
				}
				if (element) {
					if (this.viewMode === ViewMode.hours || this.viewMode === ViewMode.weeks && this.settings.dateOnly) {
						this.preselectedDate = null;
						this.setDate(element);
						this.markSelectedDates();
						if (!this.upperRange) {
							this.settings.close();
						}
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
		const interval = this.settings.interval;
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
		if (this.settings.dateOnly) {
			this.selectToday();
		} else {
			this.fetchCalendar(new Date(), ViewMode.hours);
		}
	}

	private getDateSelector(date: Date) : string {
		const utcDateString = this.asUTCDate(date).toISOString();
		let dateString;
		switch (this.viewMode) {
			case ViewMode.hours:
				dateString = utcDateString.slice(0, 16);
				break;
			case ViewMode.weeks:
				dateString = utcDateString.slice(0, 10);
				break;
			case ViewMode.months:
				dateString = `${utcDateString.slice(0, 7)}-01`;
				break;
			case ViewMode.years:
				dateString = `${utcDateString.slice(0, 4)}-01-01`;
				break;
		}
		return `li[data-date="${dateString}"]`;
	}

	private indexOfCalendarItem(date: Date) : number {
		const dateSelector= this.getDateSelector(date);
		const selectedElement = this.element.querySelector(dateSelector);
		return Array.from(this.calendarItems).indexOf(selectedElement as HTMLLIElement);
	}

	private handleOver = (event: Event) => {
		if (!(event.target instanceof HTMLLIElement))
			return;
		if (this.dateRange[0] && !this.dateRange[1]) {
			const hoverDateString = event.target.getAttribute('data-date') ?? event.target.getAttribute('aria-label') ?? '';
			this.markDateRange(this.dateRange[0], new Date(hoverDateString), true);
		}
	};

	private markDateRange(dateFixed: Date, dateCursor: Date, openRange= false) {
		const lowerDate = dateFixed < dateCursor ? dateFixed : dateCursor;
		const upperDate = dateFixed < dateCursor ? dateCursor : dateFixed;
		const lowerIndex = this.indexOfCalendarItem(lowerDate);
		const upperIndex = this.indexOfCalendarItem(upperDate);
		const addLower = openRange && !this.calendarItems.item(lowerIndex)?.classList.contains('selected') ? 1 : 2;
		const addUpper = openRange && !this.calendarItems.item(upperIndex)?.classList.contains('selected') ? 1 : 0;
		const perHour = this.settings.interval ? Math.min(60 / this.settings.interval, 6) : 1;
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
		if (this.viewMode === ViewMode.hours && this.settings.interval && (lowerIndex !== -1 || upperIndex !== -1)) {
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
		}
		console.log(selectors);
		this.rangeSelectCssRule.selectorText = selectors.map(selector => {
			return this.rangeSelectorText.replace(':not(*)', selector);
		}).join(',');
	}

	private markSelectedDates() {
		this.calendarItems.forEach(elem => elem.classList.remove('selected', 'preselected'));
		if (this.settings.withRange) {
			if (this.dateRange[0] && this.dateRange[1]) {
				this.markDateRange(this.dateRange[0], this.dateRange[1]);
				this.calendarItems.item(this.indexOfCalendarItem(this.dateRange[0]))?.classList.add('selected');
				const upperIndex = this.indexOfCalendarItem(this.dateRange[1])
				if (upperIndex !==0 || this.viewMode !== ViewMode.hours || this.dateRange[1].getHours() !== 0 || this.dateRange[1].getMinutes() !== 0) {
					// if upper range is midnight, mark the last hour as selected instead of the first hour of the next day
					this.calendarItems.item(upperIndex)?.classList.add('selected');
				}
			} else if (this.dateRange[0]) {
				const dateSelector= this.getDateSelector(this.dateRange[0]);
				this.element.querySelector(dateSelector)?.classList.add('selected');
			}
			if (this.preselectedDate) {
				const dateSelector= this.getDateSelector(this.preselectedDate);
				this.element.querySelector(dateSelector)?.classList.add('preselected');
			}
			if (this.viewMode === ViewMode.hours) {
				const label = this.element.querySelector('.ranges ul.hours:last-child > li')?.getAttribute('data-date');
				this.element.querySelector('.ranges ul.hours:last-child')?.toggleAttribute('hidden',
					this.dateRange[1] ? this.asUTCDate(this.dateRange[1]).toISOString().slice(0, 16) !== label : !this.upperRange
				);
			}
		} else if (this.dateRange[0]) {
			const dateSelector= this.getDateSelector(this.dateRange[0]);
			this.element.querySelector(dateSelector)?.classList.add('selected');
		}
	}

	private setDate(element: Element) {
		const newDate = new Date(element.getAttribute('data-date')!);
		if (this.settings.withRange) {
			if (this.upperRange && this.dateRange[0]) {
				this.dateRange = newDate < this.dateRange[0] ? [newDate, this.dateRange[0]] : [this.dateRange[0], newDate];
				this.settings.updateDate(this.dateRange[0], this.dateRange[1]);
				this.upperRange = false;
			} else {
				this.dateRange = [newDate, null];
				this.upperRange = true;
			}
		} else {
			this.dateRange[0] = newDate;
			this.settings.updateDate(this.dateRange[0], true);
		}
		if (this.minDate) {
			if (this.dateRange[0] && this.dateRange[0] < this.minDate) {
				this.dateRange[0] = this.minDate;
			}
			if (this.dateRange[1] && this.dateRange[1] < this.minDate) {
				this.dateRange[1] = this.minDate;
			}
		}
		if (this.maxDate) {
			if (this.dateRange[0] && this.dateRange[0] > this.maxDate) {
				this.dateRange[0] = this.maxDate;
			}
			if (this.dateRange[1] && this.dateRange[1] > this.maxDate) {
				this.dateRange[1] = this.maxDate;
			}
		}
	}

	private async selectToday() {
		const todayDateString = this.todayDateString.slice(0, 10);
		let todayElem = this.element.querySelector(`li[data-date="${todayDateString}"]`);
		if (!todayElem) {
			await this.fetchCalendar(new Date(), ViewMode.weeks);
			todayElem = this.element.querySelector(`li[data-date="${todayDateString}"]`);
		}
		this.setDate(todayElem!);
		this.markSelectedDates();
		if (!this.settings.withRange || this.dateRange[0] && this.dateRange[1]) {
			this.settings.close();
		}
	}

	private selectHour(liElement: HTMLLIElement) {
		this.element.querySelectorAll('li[aria-label]').forEach(elem => {
			elem.classList.remove('selected', 'preselected', 'constricted');
		});
		this.element.querySelectorAll('ul[aria-labelledby]').forEach(elem => {
			elem.toggleAttribute('hidden', true);
		});
		this.rangeSelectCssRule.selectorText = `${this.baseSelector} .ranges ul:not(*)`;
		const label = liElement.getAttribute('aria-label');
		if (label) {
			const ulElem = this.element.querySelector(`ul[aria-labelledby="${label}"]`);
			if (ulElem instanceof HTMLUListElement) {
				liElement.classList.add('constricted');
				ulElem.removeAttribute('hidden');
			}
		} else if (liElement.parentElement instanceof HTMLUListElement && liElement.parentElement.hasAttribute('aria-labelledby')) {
			const labelledby = liElement.parentElement.getAttribute('aria-labelledby');
			this.element.querySelector(`li[aria-label="${labelledby}"]`)?.classList.add('constricted');
			liElement.parentElement.removeAttribute('hidden');
		}
	}

	private selectDay = (event: Event) => {
		if (event.target instanceof HTMLLIElement) {
			if (this.settings.dateOnly) {
				this.setDate(event.target);
				this.markSelectedDates();
				if (!this.settings.withRange || this.dateRange[0] && this.dateRange[1]) {
					this.settings.close();
				}
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

	private async goto(direction: Direction) {
		let selectedDate: Date|null = null;
		if (this.settings.withRange) {
			if (this.preselectedDate) {
				selectedDate = this.preselectedDate;
			} else if (!this.upperRange && this.dateRange[0]) {
				selectedDate = this.dateRange[0];
			} else if (this.upperRange && this.dateRange[1]) {
				selectedDate = this.dateRange[1];
			}
		} else if (this.dateRange[0]) {
			selectedDate = this.dateRange[0];
		}
		if (!selectedDate) {
			if (this.dateRange[0]) {
				selectedDate = this.dateRange[0];
			} else {
				const selectedItem: Element | null = this.calendarItems.item(this.calendarItems.length / 2);
				selectedDate = this.getDate(selectedItem);
			}
		}
		const nextDate = this.getDelta(direction, selectedDate);
		this.preselectedDate = this.settings.withRange ? nextDate : null;
		const dataDateString = this.asUTCDate(nextDate).toISOString().slice(0, this.viewMode === ViewMode.hours ? 16 : 10);
		let nextItem: Element|null = null;
		if (this.viewMode !== ViewMode.weeks || selectedDate.getMonth() === nextDate.getMonth()) {
			nextItem = this.element.querySelector(`.ranges li[data-date="${dataDateString}"]`);
		}
		if (!nextItem) {
			await this.fetchCalendar(nextDate, this.viewMode);
			nextItem = this.element.querySelector(`.ranges li[data-date="${dataDateString}"]`);
		}
		if (nextItem instanceof HTMLLIElement) {
			if (this.viewMode === ViewMode.hours) {
				this.selectHour(nextItem);
			}
			if (!this.preselectedDate) {
				this.setDate(nextItem);
			}
			this.markSelectedDates();
			if (this.upperRange && this.dateRange[0] && this.preselectedDate) {
				this.markDateRange(this.dateRange[0], this.preselectedDate, true);
			}
		}
	}

	private async fetchCalendar(atDate: Date, viewMode: ViewMode) {
		const query = new URLSearchParams('calendar');
		query.set('date', this.asUTCDate(atDate).toISOString().slice(0, 10));
		query.set('mode', viewMode);
		if (this.settings.withRange) {
			query.set('range', '');
		}
		if (this.settings.interval) {
			query.set('interval', String(this.settings.interval));
		}
		const response = await fetch(`${this.settings.endpoint}?${query.toString()}`, {
			method: 'GET',
		});
		if (response.status === 200) {
			this.element.innerHTML = await response.text();
		} else {
			console.error(`Failed to fetch from ${this.settings.endpoint} (status=${response.status})`);
		}
	}

	private getSheetBounds() : [Date, Date] {
		const firstItem = this.calendarItems.item(0);
		const lastItem = this.calendarItems.item(this.calendarItems.length - 1);
		const lower= new Date(firstItem.getAttribute('data-date')!);
		const upper = new Date(lastItem.getAttribute('data-date')!);
		return [lower, upper];
	}

	private transferStyles() {
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
			let extraStyles: string;
			switch (cssRule.selectorText) {
				case this.baseSelector:
					extraStyles = StyleHelpers.extractStyles(inputElement, [
						'background-color', 'border', 'border-radius',
						'font-family', 'font-size', 'font-stretch', 'font-style', 'font-weight',
						'letter-spacing', 'white-space', 'line-height']);
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					loaded = true;
					break;
				case `${this.baseSelector} .controls`:
					extraStyles = StyleHelpers.extractStyles(inputElement, ['padding']);
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case `${this.baseSelector} .ranges`:
					extraStyles = StyleHelpers.extractStyles(inputElement, ['padding']);
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case `${this.baseSelector} .ranges ul.hours > li.constricted`:
				case `${this.baseSelector} .ranges ul.hours > li:has(~ li.constricted)`:
				case `${this.baseSelector} .ranges ul.hours > li.constricted ~ li`:
				case `${this.baseSelector} .ranges ul.minutes`:
					inputElement.classList.add('-focus-');
					extraStyles = StyleHelpers.extractStyles(inputElement, ['border-color']);
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					inputElement.classList.remove('-focus-');
					if (cssRule.selectorText === '[aria-haspopup="dialog"] + .dj-calendar .ranges ul.hours > li.constricted') {
						extraStyles = StyleHelpers.extractStyles(this.element, ['background-color']);
						extraStyles = extraStyles.replace('background-color', 'border-bottom-color');
						sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					}
					break;
				default:
					break;
			}
		}
		inputElement.style.transition = '';
		if (!loaded)
			throw new Error(`Could not load styles for ${this.baseSelector}`);
	}

	private getRangeSelectCssRule() : CSSStyleRule {
		for (let i = document.styleSheets.length - 1; i >= 0; --i) {
			const sheet = document.styleSheets[i];
			for (let k = 0; k < sheet.cssRules.length; ++k) {
				const cssRule = sheet.cssRules[k];
				if (cssRule instanceof CSSStyleRule && cssRule.selectorText === `${this.baseSelector} .ranges ul:not(*)`) {
					const selectorText = `#${this.settings.inputElement.id} + ${this.baseSelector} .ranges ul:not(*)`;
					const index = sheet.insertRule(`${selectorText}{${cssRule.style.cssText}}`, sheet.cssRules.length);
					return sheet.cssRules[index] as CSSStyleRule;
				}
			}
		}
		throw new Error(`Could not find CSS rule for '${this.baseSelector} .ranges ul:not(*)'`);
	}

	public updateDate(currentDate: Date|null, extendedDate: Date|null) {
		this.dateRange = currentDate
			? [currentDate, extendedDate]
			: [null, null];
		this.upperRange = false;
		if (currentDate) {
			this.fetchCalendar(currentDate, this.viewMode);
		}
	}
}
