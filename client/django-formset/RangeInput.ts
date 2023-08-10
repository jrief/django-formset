import {StyleHelpers, Widget} from './helpers';


class RangeInput extends Widget {
	private readonly inputElement: HTMLInputElement;

	constructor(inputElement: HTMLInputElement) {
		super(inputElement);
		this.inputElement = inputElement;
	}

	formResetted(event: Event) {}

	formSubmitted(event: Event) {}

	public value() {
		return "A";
	}
}


const RI = Symbol('RangeInputElement');

export class RangeInputElement extends HTMLInputElement {
	private [RI]!: RangeInput;  // hides internal implementation

	private connectedCallback() {
		const fieldGroup = this.closest('[role="group"]');
		if (!fieldGroup)
			throw new Error(`Attempt to initialize ${this} outside <django-formset>`);
		this[RI] = new RangeInput(this);
	}

	public get value() : string {
		return this[RI].value();
	}
}
