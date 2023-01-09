import { createPopper, Instance } from '@popperjs/core';
import { Widget } from './helpers';
import styles from './DatePicker.scss';


class Calendar extends Widget {
	private readonly inputElement: HTMLInputElement;
	private readonly calendarElement: HTMLElement;
	private dropdownInstance?: Instance;
	private startDate!: Date;
	private hasFocus = false;

	constructor(inputElement: HTMLInputElement, calendarElement: HTMLElement) {
		super(inputElement);
		this.inputElement = inputElement;
		this.calendarElement = calendarElement;
		this.registerElement();
		inputElement.addEventListener('focus', this.handleFocus);
		inputElement.addEventListener('blur', this.handleBlur);
		inputElement.addEventListener('change', this.handleChange);
		document.addEventListener('click', this.handleClick);
	}

	private registerElement() {
		this.calendarElement.querySelector('button.prev-month')?.addEventListener('click', event => this.changeMonth(-1), {once: true});
		this.calendarElement.querySelector('button.next-month')?.addEventListener('click', event => this.changeMonth(+1), {once: true});
		const today = new Date(Date.now());
		this.calendarElement.querySelectorAll('li[data-date]').forEach(elem => {
			const date1 = new Date(elem.getAttribute('data-date') ?? '');
			const date2 = new Date(date1.getTime() + 86400000);
			elem.classList.toggle('today', today >= date1 && today < date2);
			elem.classList.toggle('selected', date1.getTime() === this.inputElement.valueAsDate?.getTime());
			elem.addEventListener('click', this.selectDate);
		});
		this.startDate = new Date(this.calendarElement.querySelector('time')?.getAttribute('datetime') as string);
	}

	private handleClick = (event: Event) => {
		let element = event.target instanceof Element ? event.target : null;
		while (element) {
			if (element.isSameNode(this.calendarElement) || element.isSameNode(this.inputElement))
				return;
			element = element.parentElement;
		}
		this.hasFocus = false;
		this.inputElement.blur();
		this.inputElement.ariaExpanded = 'false';
		this.dropdownInstance?.destroy();
	}

	private handleFocus = (event: Event) => {
		this.dropdownInstance = createPopper(this.inputElement, this.calendarElement, {
			placement: 'bottom-start',
		});
		this.inputElement.ariaExpanded = 'true';
		this.hasFocus = true;
	}

	private handleBlur = (event: Event) => {
		if (this.hasFocus) {
			this.inputElement.focus();
		}
	}

	private handleChange = (event: Event) => {
		const newDate = this.inputElement.valueAsDate;
		if (newDate) {
			this.fetchMonth(new URLSearchParams({'calendar': newDate.toISOString().slice(0, 10)}));
		}
	}

	private selectDate = (event: Event) => {
		if (event.target instanceof HTMLElement) {
			const date = new Date(event.target.getAttribute('data-date') ?? '');
			this.calendarElement.querySelectorAll('li[data-date]').forEach(elem => {
				elem.classList.toggle('selected', elem.isSameNode(event.target as HTMLElement));
			});
			date.setTime(date.getTime() - date.getTimezoneOffset() * 60000);
			this.inputElement.valueAsDate = date;
			this.hasFocus = false;
			this.inputElement.blur();
		 	this.inputElement.ariaExpanded = 'false';
			this.inputElement.dispatchEvent(new Event('input'));
		 	this.dropdownInstance?.destroy();
		}
	}

	private async changeMonth(dir: number) {
		const newDate = new Date(this.startDate);
		newDate.setTime(newDate.getTime() - newDate.getTimezoneOffset() * 60000);
		if (this.startDate.getMonth() === 12 && dir > 0) {
			newDate.setUTCMonth(1);
			newDate.setUTCFullYear(newDate.getUTCFullYear() + 1);
		} else if (this.startDate.getMonth() === 1 && dir < 0) {
			newDate.setUTCMonth(12);
			newDate.setUTCFullYear(newDate.getUTCFullYear() - 1);
		} else {
			newDate.setUTCMonth(newDate.getUTCMonth() + dir);
		}
		this.fetchMonth(new URLSearchParams({'calendar': newDate.toISOString().slice(0, 10)}));
	}

	private async fetchMonth(query: URLSearchParams) {
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


class DjangoDatePicker {
	// private readonly inputElement: HTMLInputElement;
	// private readonly calendar: Calendar;

	constructor(inputElement: HTMLInputElement) {
		// this.inputElement = inputElement;
		const fieldGroup = inputElement.closest('django-field-group');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${inputElement} outside <django-formset>`);
		const calendarElement = fieldGroup.querySelector('[aria-label="calendar"]');
		if (!(calendarElement instanceof HTMLElement))
			throw new Error(`Attempt to initialize ${inputElement} with sibling <ANY aria-label="calendar">`);
		new Calendar(inputElement, calendarElement as HTMLElement);
	}
}


const DP = Symbol('DatePickerElement');


export class DatePickerElement extends HTMLInputElement {
	private [DP]?: DjangoDatePicker;  // hides internal implementation

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
