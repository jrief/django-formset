import isString from 'lodash.isstring';
import {parse} from '../build/tag-attributes';
import isEqual from 'lodash.isequal';
import isFunction from 'lodash.isfunction';
import {toAbsPath} from './helpers';


export abstract class FormDialogBase {
	protected readonly element: HTMLDialogElement;
	protected readonly formElement: HTMLFormElement;
	private readonly dialogHeaderElement: HTMLElement|null;
	protected readonly isModal: boolean;
	protected readonly induceOpen: Function;
	protected readonly induceClose: Function;
	private dialogOffsetX: number = 0;
	private dialogOffsetY: number = 0;

	constructor(element: HTMLDialogElement) {
		this.element = element;
		this.formElement = this.element.querySelector('form[method="dialog"]')! as HTMLFormElement;
		if (!this.formElement)
			throw new Error(`${this} requires child <form method="dialog">`);
		this.dialogHeaderElement = this.element.querySelector('.dialog-header');
		this.isModal = this.element.hasAttribute('df-modal');
		this.induceOpen = this.evalInducer('df-induce-open', (...args: any[]) => this.openDialog(...args));
		this.induceClose = this.evalInducer('df-induce-close', (...args: any[]) => this.closeDialog(...args));
	}

	protected evalInducer(attr: string, inducer: Function) : Function {
		const attrValue = this.element?.getAttribute(attr);
		if (!isString(attrValue))
			return () => {};
		try {
			const evalExpression = new Function('...args', `return ${parse(attrValue, {startRule: 'InduceExpression'})}`);
			return (...args: any[]) => {
				if (evalExpression.call(this, ...args)) {
					inducer(...args);
				}
			};
		} catch (error) {
			throw new Error(`Error while parsing <dialog ${attr}="${attrValue}">: ${error}.`);
		}
	}

	public openDialog(button?: DjangoButton, ...args: any[]) {
		if (this.element.open)
			return;
		if (this.isModal) {
			this.element.showModal();
		} else {
			this.element.show();
			this.positionDialogBox();
		}
		this.element.addEventListener('close', () => this.closeDialog(), {once: true});
	}

	public closeDialog(button?: DjangoButton, returnValue?: string) {
		if (this.dialogHeaderElement) {
			this.dialogHeaderElement.removeEventListener('pointerdown', this.handlePointerDown);
			this.dialogHeaderElement.removeEventListener('touchstart', this.handlePointerDown);
		}
		this.element.close(returnValue);
	}

	private positionDialogBox() {
		const parentDialog = this.element.parentElement?.closest('dialog');
		const parentRect = parentDialog instanceof HTMLDialogElement
			? parentDialog.getBoundingClientRect()
			: new DOMRect(0, 0, window.visualViewport?.width ?? 0, window.visualViewport?.height ?? 0);
		const dialogRect = this.element.getBoundingClientRect();
		this.dialogOffsetX = Math.max((parentRect.width - dialogRect.width) / 2, 0);
		this.dialogOffsetY = Math.max((parentRect.height - dialogRect.height) / 2, 0);
		if (this.dialogHeaderElement) {
			// Freeze dialog in viewport coordinates.
			Object.assign(this.element.style, {
				position: 'fixed',
				top: 0,
				margin: '0',
				overflow: 'visible',
				transform: `translate(${this.dialogOffsetX}px, ${this.dialogOffsetY}px)`,
			});
			this.dialogHeaderElement.addEventListener('pointerdown', this.handlePointerDown);
			this.dialogHeaderElement.addEventListener('touchstart', this.handlePointerDown);
		}
	}

	private handlePointerDown = (event: PointerEvent|TouchEvent) => {
		const viewport = window.visualViewport!;
		const header = this.dialogHeaderElement!;
		const dialogRect = this.element.getBoundingClientRect();
		const parentDialog = this.element.parentElement?.closest('dialog');
		const parentRect = parentDialog instanceof HTMLDialogElement
			? parentDialog.getBoundingClientRect()
			: new DOMRect(0, 0, 0, 0);
		const [maxX, maxY] = [viewport.width - dialogRect.width - parentRect.x, viewport.height - dialogRect.height - parentRect.y];
		const moveDialog = (clientX: number, clientY: number) => {
			let [x, y] = [clientX - this.dialogOffsetX, clientY - this.dialogOffsetY];
			x = Math.max(-parentRect.x, Math.min(x, maxX));
			y = Math.max(-parentRect.y, Math.min(y, maxY));
			this.element.style.transform = `translate(${x}px, ${y}px)`;
		};

		if (event instanceof PointerEvent) {
			const handlePointerMove = (e: PointerEvent) => {
				moveDialog(e.clientX, e.clientY);
			};
			this.dialogOffsetX = event.clientX - dialogRect.x + parentRect.x;
			this.dialogOffsetY = event.clientY - dialogRect.y + parentRect.y;
			moveDialog(event.clientX, event.clientY);
			header.setPointerCapture(event.pointerId);
			header.addEventListener('pointermove', handlePointerMove);
			header.addEventListener('pointerup', (up) => {
				header.releasePointerCapture(up.pointerId);
				header.removeEventListener('pointermove', handlePointerMove);
			}, {once: true});
		} else {
			const handleTouchMove = (e: TouchEvent) => {
				e.preventDefault();
				moveDialog(e.touches[0].clientX, e.touches[0].clientY);
			};
			this.dialogOffsetX = event.touches[0].clientX - dialogRect.x + parentRect.x;
			this.dialogOffsetY = event.touches[0].clientY - dialogRect.y + parentRect.y;
			moveDialog(event.touches[0].clientX, event.touches[0].clientY);
			header.addEventListener('touchmove', handleTouchMove, {passive: false});
			header.addEventListener('touchend', () => {
				header.removeEventListener('touchmove', handleTouchMove);
			}, {once: true});
		}
	};

	// Hook to be overridden by subclasses.
	// It shall return the aggregated data of the form dialog.
	protected getDataValue(path: Array<string>) : string|null {
		return null;
	}

	// Hook to be overridden by subclasses.
	// `path` – against which path shall the button be compared.
	// `activator` – function to determine whether the button is active.
	// `button` – the button to be checked.
	// It shall return true if the activation button is considered to be pressed.
	protected isButtonActive(path: string[], activator: Function, button?: DjangoButton, ...args: any[]): boolean {
		return false;
	}

	public isOpen() {
		return this.element.open;
	}

	updateOperability(...args: any[]) {
		this.induceOpen(...args);
		this.induceClose(...args);
	}

	// force to open this dialog if it contains the given formElement.
	forceVisibility(formElement: HTMLFormElement) {
		if (this.formElement === formElement) {
			this.openDialog();
		}
	}
}


class FormDialog extends FormDialogBase implements Inducible {
	private form?: DjangoForm;
	private formIsValid: Function = () => false;

	constructor(element: HTMLDialogElement) {
		super(element);
		const formElement = element.querySelector('form[method="dialog"]');
		if (!formElement)
			throw new Error(`${element} requires child <form method="dialog">`);
		formElement.addEventListener('django-formset-connected', this.registerInducer, {once: true});
	}

	private registerInducer = (event: Event) => {
		if (!(event instanceof CustomEvent))
			return;
		this.form = event.detail.form as DjangoForm;
		this.formIsValid = this.form.isValid;
		this.form.isValid = this.isDialogValid.bind(this);  // override DjangoForm's isValid() method
		this.form.formset.registerInducer(this);
	};

	private isDialogValid() {
		if (!this.element.open)
			return true;  // closed dialogs are considered as valid because they are unable to report errors
		return this.formIsValid();
	}

	public openDialog(button?: DjangoButton, ...args: any[]) {
		if (this.element.open)
			return;
		if (!this.form)
			throw new Error(`${this}.form has never been registered`);
		this.form.setPristine();
		this.form.untouch();
		if (button?.element instanceof HTMLButtonElement && isFunction(args[0])) {
			args[0].call(button, this.form.path);
		}
		super.openDialog(button, ...args);
 	}

	public closeDialog(button?: DjangoButton, returnValue?: string) {
		if (!(button?.element instanceof HTMLButtonElement) || !isString(returnValue))
			return;
		switch (returnValue) {
			case 'apply':
				if (this.formIsValid()) {
					this.element.close('apply');
				}
				break;
			case 'close':
				this.element.blur();
				this.element.close('close');
				break;
			case 'reset':
				this.form?.resetToInitial();
				break;
			case 'clear':
				this.form?.resetToInitial();
				this.element.blur();
				this.element.close('clear');
				break;
			default:
				break;
		}
	}

	protected getDataValue(path: Path) : string|null {
		return this.form!.getDataValue(path);
	}

	protected isButtonActive(path: string[], activator: Function, button?: DjangoButton, ...args: any[]): boolean {
		return button && isEqual(toAbsPath(this.form!.path, path), button.path) && activator(...args);
	}
}


export class FormDialogElement extends HTMLDialogElement {
	readonly #formdialog: FormDialog;

	constructor() {
		super();
		this.#formdialog = new FormDialog(this);
	}
}


export class TransientFormDialog extends FormDialogBase {
	private readonly basePath: Path;
	protected readonly applyButton: HTMLButtonElement|null = null;
	public readonly extension: string;

	constructor(element: HTMLDialogElement, path: Path) {
		super(element);
		this.basePath = path;
		this.applyButton = Array.from(this.formElement.elements).find(elm => elm instanceof HTMLButtonElement && elm.value === 'apply') as HTMLButtonElement;
		const extension = this.formElement.getAttribute('df-extension');
		if (!extension)
			throw new Error(`${this} requires a <form df-extension="…">`);
		this.extension = extension;
	}

	public get path(): Path {
		return toAbsPath(this.basePath, this.formElement.getAttribute('name')!.split('.'));
	}

	protected isButtonActive(path: Path, activator: Function, button?: DjangoButton, ...args: any[]): boolean {
		return button && isEqual(toAbsPath(this.basePath, path), button.path) && activator(...args);
	}

	public updateOperability(...args: any[]) {
		super.updateOperability(...args);
		if (this.applyButton?.hasAttribute('auto-disable')) {
			this.applyButton.disabled = !this.formElement.checkValidity();
		}
	}
}
