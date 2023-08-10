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
	initialDate?: Date,  // if set, this date is selected initially
	minDate?: Date,  // if set, dates before this are disabled
	maxDate?: Date,  // if set, dates after this are disabled
	interval?: number,  // granularity of entries in time picker
	endpoint: string,  // URL to fetch calendar data from
	updateDate: Function,  // callback to update date input
	close: Function,  // callback to close calendar
};


export class Calendar {
	public readonly element: HTMLElement;
	private viewMode!: ViewMode;
	private settings: CalendarSettings;
	private currentDateString: string = '';
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

	constructor(calendarElement: any, settings: CalendarSettings) {
		this.settings = settings;
		if (calendarElement instanceof HTMLElement) {
			this.element = calendarElement;
		} else {
			this.element = document.createElement('div');
			this.fetchCalendar(new Date(), ViewMode.weeks);
		}
		const observer = new MutationObserver(() => this.registerCalendar());
		observer.observe(this.element, {childList: true});
		this.currentDateString = settings.initialDate ? this.asUTCDate(settings.initialDate).toISOString().slice(0, 16) : '';
		this.setBounds()
		this.registerCalendar();
	}

	private get todayDateString() : string {
		return this.asUTCDate(new Date()).toISOString().slice(0, 16);
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

	private setBounds() {
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
	}

	private registerHoursView() {
		// since each datetime-picker can have different values, set this on element level
		if (this.settings.interval) {
			const num = Math.min(60 / this.settings.interval!, 6);
			const gridTemplateColumns = `repeat(${num}, 1fr)`;
			this.element.querySelectorAll('.ranges ul.minutes').forEach(minutesElement => {
				(minutesElement as HTMLElement).style.gridTemplateColumns = gridTemplateColumns;
			});
		}

		this.calendarItems.forEach(elem => {
			elem.classList.toggle('selected', elem.getAttribute('data-date') === this.currentDateString);
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
		this.element.querySelectorAll('li[aria-label]').forEach(elem => {
			const label = elem.getAttribute('aria-label')!;
			elem.classList.toggle('today', label === todayHourString);
			const selector = `ul[aria-labelledby="${label}"]`;
			if (label.slice(0, 13) === this.currentDateString.slice(0, 13)) {
				elem.classList.add('preselected');
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
			}
		});
	}

	private registerWeeksView() {
		const todayDateString = this.todayDateString.slice(0, 10);
		const currentDateString = this.currentDateString.slice(0, 10);
		if (this.settings.minDate) {
			this.minWeekDate = new Date(this.settings.minDate);
			this.minWeekDate.setHours(0, 0, 0);
		}
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
				element = this.element.querySelector('.ranges .selected');
				if (element) {
					if (this.viewMode === ViewMode.hours || this.viewMode === ViewMode.weeks && this.settings.dateOnly) {
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

	private setDate(element: Element) {
		this.calendarItems.forEach(elem => {
			elem.classList.toggle('selected', elem === element);
		});
		const newDate = new Date(element.getAttribute('data-date')!);
		this.currentDateString = newDate.toISOString().slice(0, 16);
		this.settings.updateDate(newDate);
	}

	private async selectToday() {
		const todayDateString = this.todayDateString.slice(0, 10);
		let todayElem = this.element.querySelector(`li[data-date="${todayDateString}"]`);
		if (!todayElem) {
			await this.fetchCalendar(new Date(), ViewMode.weeks);
			todayElem = this.element.querySelector(`li[data-date="${todayDateString}"]`);
		}
		this.selectDate(todayElem!);
	}

	private selectDate(element: Element) {
		this.setDate(element);
		this.settings.close();
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

		this.element.querySelectorAll('li[aria-label]').forEach(elem => {
			elem.classList.remove('selected', 'preselected');
		});
		this.element.querySelectorAll('ul[aria-labelledby]').forEach(elem => {
			elem.toggleAttribute('hidden', true);
		});
		const label = liElement.getAttribute('aria-label');
		if (label) {
			const ulElem = this.element.querySelector(`ul[aria-labelledby="${label}"]`);
			if (ulElem instanceof HTMLUListElement) {
				liElement.classList.add('preselected');
				ulElem.removeAttribute('hidden');
				selectMinute(ulElem);
			}
		} else if (liElement.parentElement instanceof HTMLUListElement && liElement.parentElement.hasAttribute('aria-labelledby')) {
			const labelledby = liElement.parentElement.getAttribute('aria-labelledby');
			this.element.querySelector(`li[aria-label="${labelledby}"]`)?.classList.add('preselected');
			liElement.parentElement.removeAttribute('hidden');
			selectMinute(liElement.parentElement);
		}
	}

	private selectDay = (event: Event) => {
		if (event.target instanceof HTMLLIElement) {
			if (this.settings.dateOnly) {
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

	private async goto(direction: Direction) {
		let selectedItem = this.element.querySelector('li[data-date].selected');
		if (!selectedItem) {
			selectedItem = this.calendarItems.item(this.calendarItems.length / 2);
		}
		if (selectedItem) {
			const selectedDate = this.getDate(selectedItem);
			const nextDate = this.getDelta(direction, selectedDate);
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
				this.setDate(nextItem);
			}
		}
	}

	private async fetchCalendar(atDate: Date, viewMode: ViewMode) {
		const query = new URLSearchParams('calendar');
		query.set('date', this.asUTCDate(atDate).toISOString().slice(0, 10));
		query.set('mode', viewMode);
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

	public updateDate(date: Date) {
		this.currentDateString = this.asUTCDate(date).toISOString().slice(0, 16);
		this.fetchCalendar(date, this.viewMode);
	}
}
