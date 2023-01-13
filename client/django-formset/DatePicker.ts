import { createPopper, Instance } from '@popperjs/core';
import { Widget } from './helpers';
import styles from './DatePicker.scss';


enum ViewMode {
	weeks = 'w',
	months = 'm',
	years = 'y',
}


class Calendar extends Widget {
	private readonly inputElement: HTMLInputElement;
	private readonly calendarElement: HTMLElement;
	private readonly declaredStyles: HTMLStyleElement;
	private viewMode = ViewMode.weeks;
	private dropdownInstance?: Instance;
	private minDate?: Date;
	private maxDate?: Date;
	private isOpen = false;

	constructor(inputElement: HTMLInputElement, calendarElement: HTMLElement) {
		super(inputElement);
		this.inputElement = inputElement;
		this.calendarElement = calendarElement;
		this.declaredStyles = document.createElement('style');
		this.declaredStyles.innerText = styles;
		document.head.appendChild(this.declaredStyles);
		this.setBounds();
		this.installEventHandlers();
		this.registerElement();
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
	}

	private installEventHandlers() {
		this.inputElement.addEventListener('focus', this.handleFocus);
		this.inputElement.addEventListener('blur', this.handleBlur);
		this.inputElement.addEventListener('change', this.handleChange);
		document.addEventListener('click', this.handleClick);
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
		switch (this.viewMode) {
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
	}

	private registerWeeksView() {
		this.calendarElement.querySelector('button.prev')?.addEventListener('click', this.paginate, {once: true});
		this.calendarElement.querySelector('button.today')?.addEventListener('click', this.jumpToday, {once: true});
		this.calendarElement.querySelector('time')?.addEventListener('click', this.switchMonthsView, {once: true});
		this.calendarElement.querySelector('button.next')?.addEventListener('click', this.paginate, {once: true});
		const today = new Date(Date.now());
		this.calendarElement.querySelectorAll('li[data-date]').forEach(elem => {
			const date = this.getDate(elem);
			elem.classList.toggle('today', today.getDate() === date.getDate() && today.getMonth() === date.getMonth() && today.getFullYear() === date.getFullYear());
			elem.classList.toggle('selected', elem.getAttribute('data-date') === this.inputElement.value);
			if (this.minDate && date < this.minDate || this.maxDate && date > this.maxDate) {
				elem.setAttribute('disabled', 'disabled');
			} else {
				elem.addEventListener('click', this.selectDate);
			}
		});
	}

	private registerMonthsView() {
		this.calendarElement.querySelector('button.prev')?.addEventListener('click', this.paginate, {once: true});
		this.calendarElement.querySelector('button.today')?.addEventListener('click', this.jumpToday, {once: true});
		this.calendarElement.querySelector('time')?.addEventListener('click', this.switchYearsView, {once: true});
		this.calendarElement.querySelector('button.next')?.addEventListener('click', this.paginate, {once: true});
		this.calendarElement.querySelectorAll('li[data-date]').forEach(elem => {
			elem.addEventListener('click', this.selectMonth);
		});
	}

	private registerYearsView() {
		this.calendarElement.querySelector('button.prev')?.addEventListener('click', this.paginate, {once: true});
		this.calendarElement.querySelector('button.today')?.addEventListener('click', this.jumpToday, {once: true});
		this.calendarElement.querySelector('button.next')?.addEventListener('click', this.paginate, {once: true});
		this.calendarElement.querySelectorAll('li[data-date]').forEach(elem => {
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
		this.isOpen = false;
		this.inputElement.blur();
		this.inputElement.setAttribute('aria-expanded', 'false')
		this.dropdownInstance?.destroy();
	}

	private handleFocus = (event: Event) => {
		this.dropdownInstance = createPopper(this.inputElement, this.calendarElement, {
			placement: 'bottom-start',
		});
		this.inputElement.setAttribute('aria-expanded', 'true')
		this.isOpen = true;
	}

	private handleBlur = (event: Event) => {
		if (this.isOpen) {
			this.inputElement.focus();
		}
	}

	private handleChange = (event: Event) => {
		const newDate = new Date(this.inputElement.value);
		if (isNaN(newDate.getTime())) {
			this.inputElement.value = 'yyyy-mm-dd';  // enforce a pattern validation error
		} else {
			this.fetchCalendar(newDate);
		}
	}

	private jumpToday = (event: Event) => {
		const button = this.controlButton(event.target);
		this.viewMode = ViewMode.weeks;
		this.fetchCalendar(this.getDate(button));
	}

	private selectDate = (event: Event) => {
		if (event.target instanceof HTMLLIElement) {
			const target = event.target;
			const dateValue = target.getAttribute('data-date') ?? '';
			this.calendarElement.querySelectorAll('li[data-date]').forEach(elem => {
				elem.classList.toggle('selected', elem.isSameNode(target));
			});
			this.inputElement.value = dateValue;
			this.isOpen = false;
			this.inputElement.blur();
			this.inputElement.setAttribute('aria-expanded', 'false')
			this.inputElement.dispatchEvent(new Event('input'));
		 	this.dropdownInstance?.destroy();
			this.fetchCalendar(this.getDate(target));
		}
	}

	private selectMonth = (event: Event) => {
		if (event.target instanceof HTMLLIElement) {
			this.viewMode = ViewMode.weeks;
			this.fetchCalendar(this.getDate(event.target));
		}
	}

	private selectYear = (event: Event) => {
		if (event.target instanceof HTMLLIElement) {
			this.viewMode = ViewMode.months;
			this.fetchCalendar(this.getDate(event.target));
		}
	}

	private switchMonthsView = (event: Event) => {
		if (event.target instanceof HTMLTimeElement) {
			this.viewMode = ViewMode.months;
			this.fetchCalendar(this.getDate(event.target));
		}
	}

	private switchYearsView = (event: Event) => {
		if (event.target instanceof HTMLTimeElement) {
			this.viewMode = ViewMode.years;
			this.fetchCalendar(this.getDate(event.target));
		}
	}

	private paginate = (event: Event) => {
		const button = this.controlButton(event.target);
		this.fetchCalendar(this.getDate(button));
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

	private async fetchCalendar(newDate: Date) {
		const query = new URLSearchParams('calendar');
		query.set('date', newDate.toISOString().slice(0, 10));
		query.set('mode', this.viewMode);
		const response = await fetch(`${this.endpoint}?${query.toString()}`, {
			method: 'GET',
		});
		if (response.status === 200) {
			const innerHTML = await response.text();
			this.calendarElement.innerHTML = innerHTML;
			this.registerElement();
		} else {
			console.error(`Failed to fetch from ${this.endpoint} (status=${response.status})`);
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
		if (!(calendarElement instanceof HTMLElement))
			throw new Error(`Attempt to initialize ${this} with sibling <ANY aria-label="calendar">`);
		new Calendar(this, calendarElement as HTMLElement);
	}
}
