import { Component, Element, Method, Prop } from '@stencil/core';
import getDataValue from 'lodash.get';
import template from 'lodash.template';
import { parse } from './actions';

type FieldElement = HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;

class BoundValue {
	readonly value: string | Array<string | Object>;

	constructor(value: string | Array<string | Object>) {
		this.value = value;
	}

	equals(other: string | Array<string | Object>) {
		if (typeof this.value === 'string') {
			return this.value === other;
		} else {
			return this.value.length === other.length && this.value.every((val, index) => val === other[index]);
		}
	}
}


class FieldGroup {
	declare private form: DjangoForm;
	private pristineValue: BoundValue;
	public readonly name: string;
	public readonly updateVisibility: Function;
	private element: HTMLElement;
	private inputElements: Array<FieldElement>;
	private errorPlaceholder: Element | null = null;
	private errorMessages = new Map<string, string>();
	private uploadedFiles: Array<Object>;
	private dropbox: HTMLUListElement;
	private chooseFileButton: HTMLButtonElement;
	private progressBar: HTMLDivElement | null = null;
	private dropboxItemTemplate: Function;
	private defaultDropboxItem: HTMLLIElement;

	constructor(form: DjangoForm, element: HTMLElement) {
		this.form = form;
		this.element = element;
		this.findErrorPlaceholder();
		this.parseErrorMessages();
		const requiredAny = element.classList.contains('dj-required-any');
		const inputElements = (Array.from(element.getElementsByTagName('INPUT')) as Array<HTMLInputElement>).filter(element => element.type !== 'hidden');
		for (const element of inputElements) {
			switch (element.type) {
				case 'checkbox':
				case 'radio':
					element.addEventListener('input', () => {
						this.touch();
						this.inputted()
					});
					element.addEventListener('change', () => {
						requiredAny ? this.validateCheckboxSelectMultiple() : this.validate()
					});
					break;
				case 'file':
					this.initFileControlPanel(element);
					break;
				default:
					element.addEventListener('focus', () => this.touch());
					element.addEventListener('input', () => this.inputted());
					element.addEventListener('blur', () => this.validate());
					break;
			}
		}
		const selectElements = Array.from(element.getElementsByTagName('SELECT')) as Array<HTMLSelectElement>;
		for (const element of selectElements) {
			element.addEventListener('focus', () => this.touch());
			element.addEventListener('change', () => {
				this.setDirty();
				this.resetCustomError();
				this.validate()
			});
		}
		const textAreaElements = Array.from(element.getElementsByTagName('TEXTAREA')) as Array<HTMLTextAreaElement>;
		for (const element of textAreaElements) {
			element.addEventListener('focus', () => this.touch());
			element.addEventListener('input', () => this.inputted());
			element.addEventListener('blur', () => this.validate());
		}
		this.inputElements = Array<FieldElement>(0).concat(inputElements, selectElements, textAreaElements);
		for (const element of this.inputElements) {
			if (typeof this.name === 'undefined') {
				this.name = element.name;
			} else {
				if (this.name !== element.name)
					throw new Error(`Name mismatch on multiple input fields on ${element.name}`);
			}
		}
		if (requiredAny) {
			this.validateCheckboxSelectMultiple();
		} else {
			this.validateBoundField();
		}
		this.pristineValue = new BoundValue(this.aggregateValue());
		this.updateVisibility = this.parseIfAttribute('show-if', true) || this.parseIfAttribute('hide-if', false) || function() {};
		this.untouch();
		this.setPristine();
	}

	private swallowEvent = (event: Event) => {
		event.stopPropagation();
		event.preventDefault();
	}

	aggregateValue(): string | Array<string | Object> {
		if (this.inputElements.length === 1) {
			const element = this.inputElements[0];
			if (element.type === 'checkbox') {
				return (element as HTMLInputElement).checked ? element.value : '';
			}
			if (element.type === 'select-multiple') {
				const value = [];
				const select = element as HTMLSelectElement;
				for (const key in select.options) {
					if (select.options[key].selected) {
						value.push(select.options[key].value);
					}
				}
				return value;
			}
			if (element.type === 'file') {
				return this.uploadedFiles;
			}
			// all other input types just return their value
			return element.value;
		} else {
			const value = [];
			for (let element of this.inputElements) {
				if (element.type === 'checkbox') {
					if ((element as HTMLInputElement).checked) {
						value.push(element.value);
					}
				} else if (element.type === 'radio') {
					if ((element as HTMLInputElement).checked)
						return element.value;
				}
			}
			return value;
		}
	}

	private parseIfAttribute(attribute: string, visible: boolean): Function {
		if (this.inputElements.length !== 1)
			return;  // groups with multiple input elements are ignored
		const attrValue = this.inputElements[0].getAttribute(attribute);
		if (typeof attrValue !== 'string')
			return;
		const path = attrValue.includes('.') ? attrValue : `${this.form.name}.${attrValue}`;
		if (visible) {
			return () => this.form.formset.getDataValue(path)
				? this.element.removeAttribute('hidden')
				: this.element.setAttribute('hidden', 'hidden');
		} else {
			return () => this.form.formset.getDataValue(path)
				? this.element.setAttribute('hidden', 'hidden')
				: this.element.removeAttribute('hidden');
		}
	}

	private inputted() {
		if (this.pristineValue.equals(this.aggregateValue())) {
			this.setPristine();
		} else {
			this.setDirty();
		}
		this.resetCustomError();
	}

	private initFileControlPanel(inputElement: HTMLInputElement) {
		const dropboxes = this.element.getElementsByClassName('dj-dropbox');
		if (dropboxes.length !== 1)
			throw new Error('Element <input type="file"> requires sibling element <ul class="dj-dropbox"></ul>');
		this.dropbox = dropboxes[0] as HTMLUListElement;

		const buttons = this.element.getElementsByClassName('dj-choose-file');
		if (buttons.length !== 1)
			throw new Error('Element <input type="file"> requires sibling element <button class="dj-choose-file"></button>');
		this.chooseFileButton = buttons[0] as HTMLButtonElement;

		const progressBars = this.element.getElementsByClassName('dj-progress-bar');
		if (progressBars.length === 1) {
			this.progressBar = progressBars[0] as HTMLDivElement;
			this.progressBar.style.visibility = 'hidden';
		}

		const templates = this.element.getElementsByClassName('dj-dropbox-items');
		if (templates.length !== 1)
			throw new Error('Element <input type="file"> requires sibling element <template class="dj-dropbox-items"></template>');
		this.dropboxItemTemplate = template(templates[0].innerHTML);

		this.uploadedFiles = [];
		this.dropbox.addEventListener('dragenter', this.swallowEvent);
		this.dropbox.addEventListener('dragover', this.swallowEvent);
		this.dropbox.addEventListener('drop', this.fileDrop);
		// this.dropbox.addEventListener('click', this.fileRemove);  // TODO: move towards explicit delete button
		this.chooseFileButton.addEventListener('click', () => inputElement.click());
		this.defaultDropboxItem = this.dropbox.getElementsByTagName('li')[0];
		inputElement.addEventListener('change', () => {
			const files = (this.inputElements[0] as HTMLInputElement).files;
			this.uploadFiles(files).then(() => this.validate());
		});
	}

	private fileDrop = (event: DragEvent) => {
		this.swallowEvent(event);
		const files = event.dataTransfer.files;
		(this.inputElements[0] as HTMLInputElement).files = files;
		this.uploadFiles(files).then(() => this.validate());
	}

	private fileRemove = () => {
		this.inputElements[0].value = '';
		this.uploadedFiles = [];
		while (this.dropbox.firstChild) {
			this.dropbox.removeChild(this.dropbox.firstChild);
		}
		this.dropbox.appendChild(this.defaultDropboxItem);
	}

	private uploadFiles(files: FileList): Promise<void> {
		if (files.length === 0)
			return Promise.reject();
		return new Promise<void>(resolve => {
			// Django currently can't handle multiple file uploads, restrict to first file
			this.uploadFile(files.item(0), this.dropbox.clientHeight).then(response => {
				this.uploadedFiles = [response];
				this.renderDropbox();
				this.inputted();
				resolve();
			});
		});
	}

	public async uploadFile(file: File, imageHeight: number): Promise<Object> {
		let self = this;

		function updateProgress(event: ProgressEvent) {
			const complete = event.lengthComputable ? event.loaded / event.total : 0;
			self.progressBar.style.visibility = 'visible';
			self.progressBar.getElementsByTagName('div')[0].style.width = `${complete * 100}%`;
		}

		const body = new FormData();
		body.append('temp_file', file);
		body.append('image_height', imageHeight.toString());

		return new Promise<Response>((resolve, reject) => {
			function transferComplete() {
				if (self.progressBar) {
					self.progressBar.style.visibility = 'hidden';
				}
				if (request.status === 200) {
					resolve(request.response);
				} else {
					reject(request.response);
				}
			}

			const request = new XMLHttpRequest();
			if (self.progressBar) {
				request.addEventListener('loadstart', updateProgress);
				request.addEventListener('progress', updateProgress);
			}
			request.addEventListener('loadend', transferComplete);
			request.open('POST', this.form.formset.endpoint, true);
			request.setRequestHeader('X-CSRFToken', this.form.formset.getCSRFToken());
			request.responseType = 'json';
			request.send(body);
		});
	}

	private renderDropbox() {
		let list = [];
		for (const fileHandle of this.uploadedFiles) {
			const listItem = this.dropboxItemTemplate(fileHandle);
			list.push(listItem);
		}
		this.dropbox.innerHTML = list.join('');
		const buttons = this.dropbox.getElementsByClassName('dj-delete-file');
		if (buttons.length > 0) {
			buttons[0].addEventListener('click', this.fileRemove, {once: true});
		}
	}

	private resetCustomError() {
		this.errorPlaceholder.innerHTML = '';
		for (const element of this.inputElements) {
			if (element.validity.customError)
				element.setCustomValidity('');
		}
	}

	private touch() {
		this.element.classList.remove('dj-submitted');
		this.element.classList.remove('dj-untouched');
		this.element.classList.remove('dj-validated');
		this.element.classList.add('dj-touched');
	}

	private untouch() {
		this.element.classList.remove('dj-touched');
		this.element.classList.add('dj-untouched');
	}

	private setDirty() {
		this.element.classList.remove('dj-pristine');
		this.element.classList.add('dj-dirty');
	}

	private setPristine() {
		this.element.classList.remove('dj-dirty');
		this.element.classList.add('dj-pristine');
	}

	setSubmitted() {
		this.element.classList.add('dj-submitted');
	}

	private validate() {
		let element: FieldElement;
		for (element of this.inputElements) {
			if (!element.validity.valid)
				break;
		}
		if (!element.validity.valid) {
			for (const key in this.errorMessages) {
				if (element.validity[key]) {
					if (!this.form.formset.withholdMessages) {
						this.errorPlaceholder.innerHTML = this.errorMessages[key];
					}
					element = null;
					break;
				}
			}
			if (!this.form.formset.withholdMessages && element instanceof HTMLInputElement) {
				this.validateInputLength(element);
			}
		}
		this.form.validate();
	}

	private validateCheckboxSelectMultiple() {
		let validity = false;
		for (const inputElement of this.inputElements) {
			if (inputElement.type !== 'checkbox')
				throw new Error("Expected input element of type 'checkbox'.");
			if ((inputElement as HTMLInputElement).checked) {
				validity = true;
			} else {
				inputElement.setCustomValidity(this.errorMessages['customError']);
			}
		}
		if (validity) {
			for (const inputElement of this.inputElements) {
				inputElement.setCustomValidity('');
			}
		} else if (this.pristineValue !== undefined && !this.form.formset.withholdMessages) {
			this.errorPlaceholder.innerHTML = this.errorMessages['customError'];
		}
		this.form.validate();
		return validity;
	}

	private validateInputLength(inputElement: HTMLInputElement) {
		// By default, HTML input fields do not validate their bound value regarding their
		// min- and max-length. Therefore this validation must be performed by the client.
		if (inputElement.type === 'text' && inputElement.value) {
			if (inputElement.minLength > 0 && inputElement.value.length < inputElement.minLength) {
				this.errorPlaceholder.innerHTML = this.errorMessages['tooShort'];
				return false;
			}
			if (inputElement.maxLength > 0 && inputElement.value.length > inputElement.maxLength) {
				this.errorPlaceholder.innerHTML = this.errorMessages['tooLong'];
				return false;
			}
		}
		if (inputElement.type === 'file' && inputElement.files) {
			// seems that file upload is still in progress => field shall not be valid
			if (this.uploadedFiles.length === 0) {
				this.errorPlaceholder.innerHTML = this.errorMessages['typeMismatch'];
				return false;
			}
		}
		return true;
	}

	private validateBoundField() {
		// By default, HTML input fields do not validate their bound value regarding their min-
		// and max-length. Therefore this validation must be performed separately.
		if (this.inputElements.length !== 1 || !(this.inputElements[0] instanceof HTMLInputElement))
			return;
		const inputElement = this.inputElements[0];
		if (!inputElement.value)
			return;
		if (inputElement.type === 'text') {
			if (inputElement.minLength > 0 && inputElement.value.length < inputElement.minLength)
				return inputElement.setCustomValidity(this.errorMessages['tooShort']);
			if (inputElement.maxLength > 0 && inputElement.value.length > inputElement.maxLength)
				return inputElement.setCustomValidity(this.errorMessages['tooLong']);
		}
	}

	private findErrorPlaceholder() {
		const errorlist = this.element.getElementsByClassName('dj-errorlist');
		if (errorlist.length > 0) {
			const placeholder = errorlist[0].getElementsByClassName('dj-placeholder');
			if (placeholder.length > 0) {
				this.errorPlaceholder = placeholder[0];
			}
		}
	}

	private parseErrorMessages() {
		const element = Array.from(this.element.getElementsByTagName('django-error-messages')) as Array<HTMLElement>;
		if (element.length !== 1)
			throw new Error(`<django-field-group> for '${this.name}' requires excatly one <django-error-messages> tag.`);
		for (const key of element[0].getAttributeNames()) {
			const clientKey = key.replace(/([_][a-z])/g,(group) => group.toUpperCase().replace('_', ''));
			this.errorMessages[clientKey] = element[0].getAttribute(key);
		}
	}

	setValidationError(): boolean {
		let element: FieldElement;
		for (element of this.inputElements) {
			if (!element.validity.valid)
				break;
		}
		for (const key in this.errorMessages) {
			if (element.validity[key]) {
				const message = this.errorMessages[key];
				this.errorPlaceholder.innerHTML = message;
				element.setCustomValidity(message);
				return false;
			}
		}
		if (element instanceof HTMLInputElement)
			return this.validateInputLength(element);
		return true;
	}

	reportCustomError(message: string) {
		this.errorPlaceholder.innerHTML = message;
		this.inputElements[0].setCustomValidity(message);
	}
}

class ButtonAction {
	constructor(func: Function, args: Array<any>) {
		this.func = func;
		this.args = args;
	}

	public readonly func: Function;
	public readonly args: Array<any>;
}

class DjangoButton {
	private readonly formset: DjangoFormset;
	private readonly element: HTMLButtonElement;
	private readonly initialClass: string;
	private readonly isAutoDisabled: boolean;
	private readonly successActions = Array<ButtonAction>(0);
	private readonly rejectActions = Array<ButtonAction>(0);
	private timeoutHandler: number;

	constructor(formset: DjangoFormset, element: HTMLButtonElement) {
		this.formset = formset;
		this.element = element;
		this.initialClass = element.getAttribute('class');
		this.isAutoDisabled = !!JSON.parse((element.getAttribute('auto-disable') || 'false').toLowerCase());
		this.parseActionsQueue(element.getAttribute('click'));
		element.addEventListener('click', () => this.clicked());
	}

	/**
	 * Event handler to be called when someone clicks on the button.
	 */
	// @ts-ignore
	private clicked() {
		let promise: Promise<any>;
		for (const [index, action] of this.successActions.entries()) {
			if (index === 0) {
				promise = action.func.apply(this, action.args)();
			} else {
				promise = promise.then(action.func.apply(this, action.args));
			}
		}
		for (const [index, action] of this.rejectActions.entries()) {
			if (index === 0) {
				promise = promise.catch(action.func.apply(this, action.args));
			} else {
				promise = promise.then(action.func.apply(this, action.args));
			}
		}
		promise.finally(this.restore.apply(this));
	}

	autoDisable(formValidity: Boolean) {
		if (this.isAutoDisabled) {
			this.element.disabled = !formValidity;
		}
	}

	/**
	 * Disable the button for further submission.
	 */
	// @ts-ignore
	private disable() {
		return response => {
			this.element.disabled = true;
			return Promise.resolve(response);
		};
	}

	/**
	 * Re-enable the button for further submission.
	 */
	// @ts-ignore
	enable() {
		return response => {
			this.element.disabled = false;
			return Promise.resolve(response);
		};
	}

	/**
	 * Validate form content and submit to the endpoint given in element `<django-formset>`.
	 */
	// @ts-ignore
	submit() {
		return () => {
			return new Promise((resolve, reject) => {
				this.formset.submit().then(response =>
					response instanceof Response && response.status === 200 ? resolve(response) : reject(response)
				);
			});
		}
	}

	/**
	 * Proceed to a given URL, if the response object returs status code 200.
	 * If the response object contains an element `success_url`, proceed to that URL,
	 * otherwise proceed to the given fallback URL.
	 *
	 * @param fallbackUrl: The URL to proceed to, for valid response objects without
	 * given success URL.
	 */
	// @ts-ignore
	private proceed(fallbackUrl: string | undefined) {
		return response => {
			if (response instanceof Response && response.status === 200) {
				response.json().then(body => {
					if ('success_url' in body) {
						window.location.href = body.success_url;
					}
				});
				if (typeof fallbackUrl === 'string') {
					window.location.href = fallbackUrl;
				}
			}
			return Promise.resolve(response);
		}
	}

	/**
	 * Delay execution of the next task.
	 *
	 * @param ms: Time to wait in milliseconds.
	 */
	// @ts-ignore
	private delay(ms: number) {
		return response => new Promise(resolve => this.timeoutHandler = setTimeout(() => {
			this.timeoutHandler = null;
			resolve(response);
		}, ms));
	}

	public abortAction() {
		if (this.timeoutHandler) {
			clearTimeout(this.timeoutHandler);
			this.timeoutHandler = null;
		}
	}

	/**
	 * Add a CSS class to the button element.
	 *
	 * @param cssClass: The CSS class.
	 */
	// @ts-ignore
	private addClass(cssClass: string) {
		return response => {
			this.element.classList.add(cssClass);
			return Promise.resolve(response);
		};
	}

	/**
	 * Remove a CSS class from the button element.
	 *
	 * @param cssClass: The CSS class.
	 */
	// @ts-ignore
	private removeClass(cssClass: string) {
		return response => {
			this.element.classList.remove(cssClass);
			return Promise.resolve(response);
		};
	}

	/**
	 * Add a CSS class to the button element or remove it if it is already set.
	 *
	 * @param cssClass: The CSS class.
	 */
	// @ts-ignore
	private toggleClass(cssClass: string) {
		return response => {
			this.element.classList.toggle(cssClass);
			return Promise.resolve(response);
		};
	}

	/**
	 * Emit an event to the DOM.
	 *
	 * @param event: The named event.
	 */
	// @ts-ignore
	private emit(namedEvent: string, data: any) {
		return response => {
			const event = data instanceof Object ? new CustomEvent(namedEvent, data) : new Event(namedEvent);
			this.element.dispatchEvent(event);
			return Promise.resolve(response);
		};
	}

	/**
	 * For debugging purpose only: Intercept, log and forward the response to the next handler.
 	 */
	// @ts-ignore
	private intercept() {
		return response => {
			console.info(response);
			return Promise.resolve(response);
		}
	}

	private restore() {
		return () => {
			this.element.setAttribute('class', this.initialClass);
			this.element.disabled = false;
		}
	}

	private parseActionsQueue(actionsQueue: string) {
		function createActions(actions, chain) {
			for (let action of chain) {
				const func = self[action.funcname];
				if (typeof func !== 'function')
					throw new Error(`Unknown function '${action.funcname}'.`);
				actions.push(new ButtonAction(func, action.args));
			}
		}

		let self = this;
		try {
			const ast = parse(actionsQueue);
			createActions(this.successActions, ast.successChain);
			createActions(this.rejectActions, ast.rejectChain);
		} catch (error) {
			throw new Error(`Error while parsing <button click="...">: ${error}.`);
		}
	}
}


class DjangoForm {
	public readonly name: string;
	public readonly formset: DjangoFormset;
	private readonly element: HTMLFormElement;
	private readonly fieldGroups = Array<FieldGroup>(0);

	constructor(formset: DjangoFormset, element: HTMLFormElement) {
		this.name = element.getAttribute('name') || '__default__';
		this.formset = formset;
		this.element = element;
		for (const element of Array.from(this.element.getElementsByTagName('django-field-group')) as Array<HTMLElement>) {
			this.fieldGroups.push(new FieldGroup(this, element));
		}
	}

	aggregateValues() {
		const data = {};
		for (const fieldGroup of this.fieldGroups) {
			data[fieldGroup.name] = fieldGroup.aggregateValue();
		}
		// hidden fields are not handled by a django-field-group
		for (const element of Array.from(this.element.getElementsByTagName('INPUT')) as Array<HTMLInputElement>) {
			if (element.type === 'hidden') {
				data[element.name] = element.value;
			}
		}
		return data;
	}

	updateVisibility() {
		for (const fieldGroup of this.fieldGroups) {
			fieldGroup.updateVisibility();
		}
	}

	setSubmitted() {
		for (const fieldGroup of this.fieldGroups) {
			fieldGroup.setSubmitted();
		}
	}

	validate() {
		this.formset.validate();
	}

	isValid() {
		let isValid = true;
		for (const fieldGroup of this.fieldGroups) {
			isValid = fieldGroup.setValidationError() && isValid;
		}
		return isValid;
	}

	checkValidity() {
		return this.element.checkValidity();
	}

	reportValidity() {
		this.element.reportValidity();
	}

	reportCustomErrors(errors) {
		for (const fieldGroup of this.fieldGroups) {
			if (errors[fieldGroup.name] instanceof Array && errors[fieldGroup.name].length > 0) {
				fieldGroup.reportCustomError(errors[fieldGroup.name][0]);
			}
		}
	}
}


@Component({
	tag: 'django-formset',
	styleUrl: 'django-formset.scss',
	shadow: false,
})
// valid: This property returns true if the element’s contents are valid and false otherwise.
// invalid: This property returns true if the element’s contents are invalid and false otherwise.
//
// pristine: This property returns true if the element’s contents have not been changed.
// dirty: This property returns true if the element’s contents have been changed.
//
// untouched: This property returns true if the user has not visited the element.
// touched: This property returns true if the user has visited the element.

// valueMissing: if the element has no value but is a required field.
// typeMismatch: if the element's value is not in the correct syntax.
// patternMismatch: if the element's value doesn't match the provided pattern.
// tooLong: if the element's value is longer than the provided maximum length.
// tooShort: if the element's value, if it is not the empty string, is shorter than the provided minimum length.
// rangeUnderflow: if the element's value is lower than the provided minimum.
// rangeOverflow: if the element's value is higher than the provided maximum.
// stepMismatch: if the element's value doesn't fit the rules given by the step attribute.
// badInput: if the user has provided input in the user interface that the user agent is unable to convert to a value.
// customError: if the element has a custom error.
export class DjangoFormset {
	@Element() private element: HTMLElement;
	@Prop() endpoint: string;
	@Prop({attribute: 'withhold-messages'}) withholdMessages = false;
	@Prop({attribute: 'force-submission'}) forceSubmission = false;
	private data = {};
	private buttons = Array<DjangoButton>(0);
	private forms = Array<DjangoForm>(0);
	private abortController: AbortController;

	connectedCallback() {
		for (const element of Array.from(this.element.getElementsByTagName('BUTTON')) as Array<HTMLButtonElement>) {
			if (element.hasAttribute('click')) {
				this.buttons.push(new DjangoButton(this, element));
			}
		}
		for (const element of Array.from(this.element.getElementsByTagName('FORM')) as Array<HTMLFormElement>) {
			this.forms.push(new DjangoForm(this, element));
		}
		this.abortController = new AbortController();
	}

	componentWillLoad() {
		const formNames = Array<string>(0);
		for (const form of this.forms) {
			if (form.name in formNames)
				throw new Error(`Detected more than one <form name="${form.name}"> in <django-formset>`);
			formNames.push(form.name);
		}
	}

	componentDidLoad() {
		this.validate();
	}

	getCSRFToken() {
		const value = `; ${document.cookie}`;
		const parts = value.split('; csrftoken=');

		if (parts.length === 2) {
			return  parts.pop().split(';').shift();
		}
	}

	private aggregateValues() {
		this.data = {};
		for (const form of this.forms) {
			this.data[form.name] = form.aggregateValues();
		}
		for (const form of this.forms) {
			form.updateVisibility();
		}
	}

	public validate() {
		let isValid = true;
		for (const form of this.forms) {
			isValid = form.checkValidity() && isValid;
		}
		for (const button of this.buttons) {
			button.autoDisable(isValid);
		}
		this.aggregateValues();
		return isValid;
	}

	@Method()
	public async submit(): Promise<Response | undefined> {
		let formsAreValid = true;
		if (!this.forceSubmission) {
			for (const form of this.forms) {
				formsAreValid = form.isValid() && formsAreValid;
			}
		}
		this.setSubmitted();
		if (formsAreValid) {
			if (!this.endpoint)
				throw new Error("<django-formset> requires attribute 'endpoint=\"server endpoint\"' for submission");
			const response = await fetch(this.endpoint, {
				method: 'POST',
				headers: {
					'Accept': 'application/json',
					'Content-Type': 'application/json',
					'X-CSRFToken': this.getCSRFToken(),
				},
				body: JSON.stringify(this.data),
				signal: this.abortController.signal,
			});
			if (response.status === 422) {
				response.json().then(body => {
					for (const form of this.forms) {
						if (form.name in body) {
							form.reportCustomErrors(body[form.name]);
							form.reportValidity();
						}
					}
				});
			}
			return response;
		} else {
			for (const form of this.forms) {
				form.reportValidity();
			}
		}
	}

	/**
	 * Abort the current actions.
	 *
	 */
	@Method()
	public async abort() {
		for (const button of this.buttons) {
			button.abortAction();
		}
		this.abortController.abort();
	}

	private setSubmitted() {
		for (const form of this.forms) {
			form.setSubmitted();
		}
	}

	public getDataValue(path) {
		return getDataValue(this.data, path);
	}
}
