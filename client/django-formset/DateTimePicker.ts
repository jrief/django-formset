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
	private readonly calendarElement: HTMLElement;
	private viewMode?: ViewMode;
	private dropdownInstance?: Instance;
	private minDate?: Date;
	private maxDate?: Date;
	private interval?: number;
	private isOpen = false;

	constructor(inputElement: HTMLInputElement, calendarElement: Element | null) {
		super(inputElement);
		this.inputElement = inputElement;
		this.dateOnly = inputElement.getAttribute('is') === 'django-datepicker';
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

	private setBounds() {
		const minValue = this.inputElement.getAttribute('min');
		if (minValue) {
			this.minDate = new Date(minValue);
		}
		const maxValue = this.inputElement.getAttribute('max');
		if (maxValue) {
			this.maxDate = new Date(maxValue);
		}
		const step = this.inputElement.getAttribute('step');
		if (step) {
			const d1 = new Date('1970-01-01 0:00:00');
			const d2 = new Date(`1970-01-01 ${step}`);
			this.interval = (d2.getTime() - d1.getTime()) / 60000;
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

	private getDate(selector: string | Element) : Date {
		const element = selector instanceof Element ? selector : this.calendarElement.querySelector(selector);
		if (!(element instanceof Element))
			throw new Error(`Element ${selector} is missing`);
		const dateValue = element.getAttribute('data-date') ?? element.getAttribute('datetime');
		const date = new Date(dateValue ?? '');
		return date;
	}

	private registerElement() {
		this.viewMode = this.getViewMode();
		this.calendarElement.querySelector('button.prev')?.addEventListener('click', this.paginate, {once: true});
		this.calendarElement.querySelector('button.back')?.addEventListener('click', this.jumpBack, {once: true});
		this.calendarElement.querySelector('button.today')?.addEventListener('click', this.selectToday, {once: true});
		this.calendarElement.querySelector('button.next')?.addEventListener('click', this.paginate, {once: true});
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
			const today = new Date(Date.now());
			textElem.textContent = String(today.getDate());
		}

		// since each datetime-picker can have different values, set this on element level
		if (this.interval) {
			const num = Math.min(60 / this.interval!, 6);
			const gridTemplateColumns = `repeat(${num}, 1fr)`;
			this.calendarElement.querySelectorAll('.ranges ul.minutes').forEach(minutesElement => {
				(minutesElement as HTMLElement).style.gridTemplateColumns = gridTemplateColumns;
			});
		}
	}

	private registerHoursView() {
		this.calendarElement.querySelector('button.extend')?.addEventListener('click', this.switchWeeksView, {once: true});
		this.calendarElement.querySelectorAll('li[aria-label]').forEach(elem => {
			const label = elem.getAttribute('aria-label');
			if (label!.replace('T', ' ').slice(0, 13) === this.inputElement.value.slice(0, 13)) {
				elem.classList.add('preselected');
				this.calendarElement.querySelector(`ul[aria-labelledby="${label}"]`)?.removeAttribute('hidden');
			}
			elem.addEventListener('click', (event: Event) => {
				if (event.target instanceof HTMLLIElement) {
					this.selectHour(event.target);
				}
			});
		});
		this.calendarElement.querySelectorAll('li[data-date]').forEach(elem => {
			const date = elem.getAttribute('data-date')!.replace('T', ' ');
			elem.classList.toggle('selected', date === this.inputElement.value);
			elem.addEventListener('click', event => {
				if (event.target instanceof HTMLLIElement) {
					this.selectDate(event.target);
				}
			}, {once: true});
		});
	}

	private registerWeeksView() {
		this.calendarElement.querySelector('button.extend')?.addEventListener('click', this.switchMonthsView, {once: true});
		const today = new Date(Date.now());
		this.calendarElement.querySelectorAll('li[data-date]').forEach(elem => {
			const date = this.getDate(elem);
			elem.classList.toggle('today', today.getDate() === date.getDate() && today.getMonth() === date.getMonth() && today.getFullYear() === date.getFullYear());
			elem.classList.toggle('selected', elem.getAttribute('data-date') === this.inputElement.value.slice(0, 10));
			if (this.minDate && date < this.minDate || this.maxDate && date > this.maxDate) {
				elem.setAttribute('disabled', 'disabled');
			} else {
				elem.addEventListener('click', this.selectDay);
			}
		});
	}

	private registerMonthsView() {
		this.calendarElement.querySelector('button.extend')?.addEventListener('click', this.switchYearsView, {once: true});
		this.calendarElement.querySelectorAll('li[data-date]').forEach(elem => {
			elem.classList.toggle('selected', elem.getAttribute('data-date')!.slice(0, 7) === this.inputElement.value.slice(0, 7));
			elem.addEventListener('click', this.selectMonth);
		});
	}

	private registerYearsView() {
		this.calendarElement.querySelectorAll('li[data-date]').forEach(elem => {
			elem.classList.toggle('selected', elem.getAttribute('data-date')!.slice(0, 4) === this.inputElement.value.slice(0, 4));
			elem.addEventListener('click', this.selectYear);
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
		this.inputElement.setAttribute('aria-expanded', 'true')
		this.inputElement.value = this.inputElement.value.trimEnd();  // remove white space eventually added by handleChange
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
			if (this.inputElement.value.match(/^\d{4}$/) || this.inputElement.value.match(/^\d{4}-\d{2}$/)) {
				this.inputElement.value = this.inputElement.value.concat('-');
			} else if (this.inputElement.value.match(/^\d{4}-\d{2}-\d{2}$/)) {
				this.validate();
				window.setTimeout(() => this.inputElement.blur(), 0);
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
					this.selectDate(element);
				}
				break;
			default:
				return;
		}
		event.preventDefault();
	}

	private readonly offsets = new Map<ViewMode, Map<Direction, number>>([
		[ViewMode.weeks, new Map<Direction, number>([
			[Direction.up, -7],
			[Direction.right, +1],
			[Direction.down, +7],
			[Direction.left, -1],
		])],
		[ViewMode.months, new Map<Direction, number>([
			[Direction.up, -3],
			[Direction.right, +1],
			[Direction.down, +3],
			[Direction.left, -1],
		])],
		[ViewMode.years, new Map<Direction, number>([
			[Direction.up, -4],
			[Direction.right, +1],
			[Direction.down, +4],
			[Direction.left, -1],
		])],
	]);

	private readonly deltas = new Map<ViewMode, Function>([
		[ViewMode.weeks, function (direction: Direction, lastDate: Date) {
			let nextDate : Date;
			switch (direction) {
				case Direction.up: case Direction.left:
					nextDate = new Date(lastDate.getTime() - 86400000);
					break;
				case Direction.right: case Direction.down:
					nextDate = new Date(lastDate.getTime() + 86400000);
					break;
			}
			return nextDate;
		}],
		[ViewMode.months, function (direction: Direction, lastDate: Date) {
			const nextDate = new Date(lastDate);
			switch (direction) {
				case Direction.up: case Direction.left:
					nextDate.setFullYear(lastDate.getFullYear() - 1);
					nextDate.setMonth(11);
					break;
				case Direction.right: case Direction.down:
					nextDate.setFullYear(lastDate.getFullYear() + 1);
					nextDate.setMonth(0);
					break;
			}
			return nextDate;
		}],
		[ViewMode.years, function (direction: Direction, lastDate: Date) {
			const nextDate = new Date(lastDate);
			switch (direction) {
				case Direction.up: case Direction.left:
					nextDate.setFullYear(lastDate.getFullYear() - 1);
					break;
				case Direction.right: case Direction.down:
					nextDate.setFullYear(lastDate.getFullYear() + 1);
					break;
			}
			return nextDate;
		}],
	]);

	private async navigateHourly(currentItem: Element, direction: Direction) {
		const lastDate = this.getDate(currentItem);
		if (this.interval) {
			let nextDate : Date;
			switch (direction) {
				case Direction.up:
					nextDate = new Date(lastDate.getTime() - (60 + lastDate.getTimezoneOffset()) * 60000);
					break;
				case Direction.right:
					nextDate = new Date(lastDate.getTime() + (this.interval - lastDate.getTimezoneOffset()) * 60000);
					break;
				case Direction.down:
					nextDate = new Date(lastDate.getTime() + (60 - lastDate.getTimezoneOffset()) * 60000);
					break;
				case Direction.left:
					nextDate = new Date(lastDate.getTime() - (this.interval + lastDate.getTimezoneOffset()) * 60000);
					break;
			}
			let nextItem = this.calendarElement.querySelector(`li[data-date="${nextDate.toISOString().slice(0, 16)}"]`);
			if (!nextItem) {
				await this.fetchCalendar(nextDate, this.viewMode);
				nextItem = this.calendarElement.querySelector(`.ranges li[data-date="${nextDate.toISOString().slice(0, 16)}"]`);
			}
			if (nextItem instanceof HTMLLIElement) {
				this.selectHour(nextItem);
				this.setDate(nextItem);
			}
		}
	}

	private async navigate(direction: Direction) {
		const currentItem = this.calendarElement.querySelector('.ranges .selected') ?? this.calendarElement.querySelector('.ranges li[data-date]:nth-of-type(4)')!;
		if (this.viewMode === ViewMode.hours) {
			this.navigateHourly(currentItem, direction);
		} else {
			let nextItem : Element | null = currentItem;
			let offset = this.offsets.get(this.viewMode as ViewMode)!.get(direction)!;
			while (offset) {
				const lastDate = this.getDate(nextItem!);
				if (offset > 0) {
					nextItem = nextItem!.nextElementSibling;
					--offset;
				} else {
					nextItem = nextItem!.previousElementSibling;
					++offset;
				}
				if (!nextItem) {
					const nextDate = this.deltas.get(this.viewMode as ViewMode)!(direction, lastDate);
					await this.fetchCalendar(nextDate, this.viewMode);
					nextItem = this.calendarElement.querySelector(`.ranges li[data-date="${nextDate.toISOString().slice(0, 10)}"]`);
				}
			}
			if (nextItem) {
				this.setDate(nextItem);
			}
		}
	}

	private validate() : Date | undefined {
		const newDate = this.getValidDate();
		if (newDate)
			return newDate;
		// enforce a pattern validation error
		this.inputElement.value = this.inputElement.value.concat(' ');
	}

	private getValidDate() : Date | undefined {
		const newDate = new Date(this.inputElement.value);
		if (!isNaN(newDate.getTime()) && newDate.toISOString().slice(0, 10) === this.inputElement.value.slice(0, 10))
			return newDate;
	}

	private jumpBack = (event: Event) => {
		const date = this.getDate(this.controlButton(event.target));
		if (this.viewMode === ViewMode.months) {
			this.fetchCalendar(date, ViewMode.weeks);
		} else if (this.viewMode === ViewMode.years) {
			this.fetchCalendar(date, ViewMode.months);
		} else {
			this.fetchCalendar(date, this.viewMode);
		}
	}

	private paginate = (event: Event) => {
		const button = this.controlButton(event.target);
		this.fetchCalendar(this.getDate(button), this.viewMode);
	}

	private selectToday = (event: Event) => {
		const button = this.controlButton(event.target);
		const dateValue = this.getDate(button);
		if (this.dateOnly) {
			this.inputElement.value = dateValue.toISOString().slice(0, 10);
			const todayElem = this.calendarElement.querySelector(`li[data-date="${this.inputElement.value}"]`);
			this.calendarElement.querySelectorAll('li[data-date]').forEach(elem => {
				elem.classList.toggle('selected', elem.isSameNode(todayElem));
			});
			this.close();
			this.inputElement.blur();
			this.inputElement.dispatchEvent(new Event('input'));
		} else {
			this.fetchCalendar(this.getDate(button), ViewMode.hours);
		}
	}

	private setDate(element: Element) {
		this.calendarElement.querySelectorAll('li[data-date]').forEach(elem => {
			elem.classList.toggle('selected', elem.isSameNode(element));
		});
		const dateValue = element.getAttribute('data-date') ?? '';
		if (this.dateOnly) {
			this.inputElement.value = dateValue.slice(0, 10);
		} else {
			this.inputElement.value = dateValue.length === 10 ? dateValue.concat(' 00:00') : dateValue.replace('T', ' ');
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
			elem.setAttribute('hidden', '');
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

	private switchWeeksView = (event: Event) => {
		if (event.target instanceof HTMLTimeElement) {
			this.fetchCalendar(this.getDate(event.target), ViewMode.weeks);
		}
	}

	private switchMonthsView = (event: Event) => {
		if (event.target instanceof HTMLTimeElement) {
			this.fetchCalendar(this.getDate(event.target), ViewMode.months);
		}
	}

	private switchYearsView = (event: Event) => {
		if (event.target instanceof HTMLTimeElement) {
			this.fetchCalendar(this.getDate(event.target), ViewMode.years);
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

	private async fetchCalendar(newDate: Date, viewMode?: ViewMode) {
		const query = new URLSearchParams('calendar');
		query.set('date', newDate.toISOString().slice(0, 10));
		if (viewMode) {
			query.set('mode', viewMode);
		}
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
					extraStyles = StyleHelpers.extractStyles(this.inputElement, [
						'padding']);
					declaredStyles.sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case ':is([is="django-datepicker"], [is="django-datetimepicker"]) + .dj-calendar .ranges':
					extraStyles = StyleHelpers.extractStyles(this.inputElement, [
						'padding']);
					declaredStyles.sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case ':is([is="django-datepicker"], [is="django-datetimepicker"]) + .dj-calendar .ranges ul:not(.weekdays)':
					extraStyles = `line-height: ${inputHeight};`;
					declaredStyles.sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				default:
					break;
			}
		}
	}

	protected formResetted(event: Event) {}

	protected formSubmitted(event: Event) {}
}


export class DatePickerElement extends HTMLInputElement {
	private connectedCallback() {
		const fieldGroup = this.closest('django-field-group');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		const calendarElement = fieldGroup.querySelector('[aria-label="calendar"]');
		new Calendar(this, calendarElement);
	}
}


export class DateTimePickerElement extends HTMLInputElement {
	private connectedCallback() {
		const fieldGroup = this.closest('django-field-group');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		const calendarElement = fieldGroup.querySelector('[aria-label="calendar"]');
		new Calendar(this, calendarElement);
	}
}
