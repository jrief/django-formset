import { createPopper, Instance } from '@popperjs/core';
import { Editor, Extension, Mark, Node } from '@tiptap/core';
import Document from '@tiptap/extension-document';
import History from '@tiptap/extension-history';
import Paragraph from '@tiptap/extension-paragraph';
import Text from '@tiptap/extension-text';
import { Heading, Level } from '@tiptap/extension-heading';
import Bold from '@tiptap/extension-bold';
import Italic from '@tiptap/extension-italic';
import Underline from '@tiptap/extension-underline';
import BulletList from '@tiptap/extension-bullet-list';
import OrderedList from '@tiptap/extension-ordered-list';
import HorizontalRule from '@tiptap/extension-horizontal-rule';
import ListItem from '@tiptap/extension-list-item';
import Link from '@tiptap/extension-link';
import Image from '@tiptap/extension-image';
import styles from './RichtextArea.scss';
import { StyleHelpers } from './helpers';


abstract class Action {
	public readonly button: HTMLButtonElement;
	public readonly extensions: Array<Extension|Mark|Node> = [];

	constructor(wrapperElement: HTMLElement, button: HTMLButtonElement) {
		this.button = button;
	}

	installEventHandler(editor: Editor) {
		this.button.addEventListener('click', () => this.toggle(editor));
	}

	abstract toggle(editor: Editor): void;
}


namespace controls {
	export class boldAction extends Action {
		public readonly extensions = [Bold];

		toggle(editor: Editor) {
			editor.chain().focus().toggleBold().run();
		}
	}

	export class italicAction extends Action {
		public readonly extensions = [Italic];

		toggle(editor: Editor) {
			editor.chain().focus().toggleItalic().run();
		}
	}

	export class underlineAction extends Action {
		public readonly extensions = [Underline];

		toggle(editor: Editor) {
			editor.chain().focus().toggleUnderline().run();
		}
	}

	export class bulletListAction extends Action {
		public readonly extensions = [BulletList, ListItem];

		toggle(editor: Editor) {
			editor.chain().focus().toggleBulletList().run();
		}
	}

	export class orderedListAction extends Action {
		public readonly extensions = [OrderedList, ListItem];

		toggle(editor: Editor) {
			editor.chain().focus().toggleOrderedList().run();
		}
	}

	export class horizontalRuleAction extends Action {
		public readonly extensions = [HorizontalRule];

		toggle(editor: Editor) {
			editor.chain().focus().setHorizontalRule().run();
		}
	}

	export class clearFormatAction extends Action {
		toggle(editor: Editor) {
			editor.chain().focus().clearNodes().unsetAllMarks().run();
		}
	}

	export class undoAction extends Action {
		public readonly extensions = [History];

		toggle(editor: Editor) {
			editor.commands.undo();
		}
	}

	export class redoAction extends Action {
		public readonly extensions = [History];

		toggle(editor: Editor) {
			editor.commands.redo();
		}
	}

	export class headingAction extends Action {
		private readonly dropdownInstance?: Instance;
		private readonly dropdownMenu: HTMLElement | null;

		constructor(wrapperElement: HTMLElement, button: HTMLButtonElement) {
			super(wrapperElement, button);
			const levels: Array<Level> = [];
			this.dropdownMenu = wrapperElement.querySelector('button[richtext-toggle="heading"] + [role="menu"]');
			if (this.dropdownMenu) {
				this.dropdownInstance = createPopper(this.button, this.dropdownMenu, {
					placement: 'bottom-start',
				});
				this.dropdownMenu.querySelectorAll('[richtext-toggle^="heading:"]').forEach(element => {
					levels.push(this.extractLevel(element));
				});
			} else {
				levels.push(this.extractLevel(this.button));
			}
			this.extensions.push(Heading.configure({
				levels: levels,
			}));
		}

		private extractLevel(element: Element) : Level {
			const parts = element.getAttribute('richtext-toggle')?.split(':') ?? [];
			if (parts.length !== 2)
				throw new Error(`Element ${element} requires attribute 'richtext-toggle'.`);
			const level = parseInt(parts[1]) as Level;
			return level;
		}

		installEventHandler(editor: Editor) {
			if (this.dropdownMenu) {
				this.button.addEventListener('click', () => this.toggleMenu());
				this.dropdownMenu.addEventListener('click', event => this.toggleItem(event, editor));
				document.addEventListener('click', event => {
					let element = event.target instanceof Element ? event.target : null;
					while (element) {
						if (element.isSameNode(this.button) || element.isSameNode(this.dropdownMenu))
							return;
						element = element.parentElement;
					}
					this.toggleMenu(false);
				});
			} else {
				this.button.addEventListener('click', event => this.toggleItem(event, editor));
			}
		}

		toggle() {}

		toggleMenu(force?: boolean) {
			this.button.classList.toggle('active', force);
			this.dropdownMenu?.classList.toggle('show', force);
			this.button.ariaExpanded = this.dropdownMenu?.classList.contains('show') ? 'true' : 'false';
			this.dropdownInstance?.update();
		}

		toggleItem(event: MouseEvent, editor: Editor) {
			let element = event.target instanceof Element ? event.target : null;
			while (element) {
				if (element instanceof HTMLButtonElement || element instanceof HTMLAnchorElement) {
					const level = this.extractLevel(element);
					editor.chain().focus().setHeading({'level': level}).run();
					this.toggleMenu(false);
					break;
				}
				element = element.parentElement;
			}
		}
	}
}


namespace controls {
	abstract class FormDialogAction extends Action {
		protected readonly modalDialogElement: HTMLDialogElement;
		protected readonly formElement: HTMLFormElement;

		constructor(wrapperElement: HTMLElement, button: HTMLButtonElement) {
			super(wrapperElement, button);
			const label = button.getAttribute('richtext-toggle') ?? '';
			this.modalDialogElement = wrapperElement.querySelector(`dialog[richtext-opener="${label}"]`)! as HTMLDialogElement;
			this.formElement = this.modalDialogElement.querySelector('form[method="dialog"]')! as HTMLFormElement;
		}

		toggle = (editor: Editor) => this.openDialog(editor);
		protected abstract openDialog(editor: Editor): void;
	}

	export class linkAction extends FormDialogAction {
		private readonly textInputElement: HTMLInputElement;
		private readonly urlInputElement: HTMLInputElement;
		public extensions = [Link.configure({
			openOnClick: false
		})];

		constructor(wrapperElement: HTMLElement, button: HTMLButtonElement) {
			super(wrapperElement, button);
			this.textInputElement = this.formElement.elements.namedItem('text') as HTMLInputElement;
			this.urlInputElement = this.formElement.elements.namedItem('url') as HTMLInputElement;
			this.initialize();
		}

		private initialize() {
			if (!this.formElement)
				throw new Error('LinkDialog requires a <form method="dialog">');
			if (!(this.textInputElement instanceof HTMLInputElement))
				throw new Error('<form method="dialog"> requires field <input name="text">');
			if (!(this.urlInputElement instanceof HTMLInputElement))
				throw new Error('<form method="dialog"> requires field <input name="url">');
		}

		private toggleRemoveButton(condidtion: boolean) {
			const removeButton = this.formElement.elements.namedItem('remove');
			if (!(removeButton instanceof HTMLButtonElement))
				return;
			if (condidtion) {
				removeButton.removeAttribute('hidden');
				removeButton.addEventListener('click', () => {
					this.modalDialogElement.close('remove');
				});
			} else {
				removeButton.setAttribute('hidden', 'hidden');
			}
		}

		private handleCloseButton() {
			const closeButton = this.formElement.elements.namedItem('close');
			if (!(closeButton instanceof HTMLButtonElement))
				return;
			closeButton.addEventListener('click', () => {
				this.modalDialogElement.close('close')
			}, {once: true});
		}

		private closeDialog(editor: Editor) {
			const returnValue = this.modalDialogElement.returnValue;
			if (returnValue === 'save') {
				const selection = editor.view.state.selection;
				editor.chain().focus()
					.extendMarkRange('link')
					.setLink({href: this.urlInputElement.value})
					.insertContentAt({from: selection.from, to: selection.to}, this.textInputElement.value)
					.run();
			} else if (returnValue === 'remove') {
				editor.chain().focus().extendMarkRange('link').unsetLink().run();
			}
			// reset form to be pristine for the next invocation
			this.formElement.reset();
		}

		protected openDialog(editor: Editor) {
			const {selection, doc} = editor.view.state;
			if (selection.from === selection.to)
				return;  // nothing selected
			this.textInputElement.value = doc.textBetween(selection.from, selection.to, '');
			this.urlInputElement.value = editor.getAttributes('link').href ?? '';
			this.toggleRemoveButton(!!this.urlInputElement.value.length);
			this.handleCloseButton();
			this.modalDialogElement.showModal();
			this.modalDialogElement.addEventListener('close', () => this.closeDialog(editor), {once: true});
		}
	}


	export class ImageAction extends FormDialogAction {
		// unfinished
		private readonly fileInputElement: HTMLInputElement;
		public extensions = [Image.configure({
			inline: false
		})];

		constructor(wrapperElement: HTMLElement, button: HTMLButtonElement) {
			super(wrapperElement, button);
			this.fileInputElement = this.formElement.elements.namedItem('image') as HTMLInputElement;
		}

		private closeDialog(editor: Editor) {
			const returnValue = this.modalDialogElement.returnValue;
			if (returnValue === 'save') {
				const imgElement = this.modalDialogElement.querySelector('.dj-dropbox img') as HTMLImageElement;
				editor.chain().focus().setImage({src: imgElement.src}).run();
			} else if (returnValue === 'remove') {
				editor.chain().focus().extendMarkRange('link').unsetLink().run();
			}
		}

		protected openDialog(editor: Editor) {
			//this.toggleRemoveButton(!!this.urlInputElement.value.length);
			//this.handleCloseButton();
			this.modalDialogElement.showModal();
			this.modalDialogElement.addEventListener('close', () => this.closeDialog(editor), {once: true});
		}
	}

}


class RichtextArea {
	private readonly textAreaElement: HTMLTextAreaElement;
	public readonly wrapperElement: HTMLElement;
	private readonly menubarElement: HTMLElement | null;
	private readonly registeredCommands = new Map<string, Action>();
	private readonly declaredStyles: HTMLStyleElement;
	private readonly useJson: boolean = false;
	private readonly editor: Editor;
	private readonly initialValue: string | object;

	constructor(wrapperElement: HTMLElement, textAreaElement: HTMLTextAreaElement) {
		this.wrapperElement = wrapperElement;
		this.textAreaElement = textAreaElement;
		this.menubarElement = wrapperElement.querySelector('[role="menubar"]');
		this.declaredStyles = document.createElement('style');
		this.declaredStyles.innerText = styles;
		document.head.appendChild(this.declaredStyles);
		const scriptElement = wrapperElement.querySelector('textarea + script');
		if (scriptElement instanceof HTMLScriptElement && scriptElement.type === 'application/json') {
			this.useJson = true;
			const content = scriptElement.textContent ? JSON.parse(scriptElement.textContent) : '';
			this.editor = this.createEditor(wrapperElement, content);
			scriptElement.remove();
		} else {
			this.useJson = false;
			this.editor = this.createEditor(wrapperElement, textAreaElement.textContent);
		}
		this.initialValue = this.getValue();
		this.transferStyles();
		this.concealTextArea(wrapperElement);
		// innerHTML must reflect the content, otherwise field validation complains about a missing value
		this.textAreaElement.innerHTML = this.editor.getHTML();
		this.installEventHandlers();
	}

	private createEditor(wrapperElement: HTMLElement, content: any) : Editor {
		const editor = new Editor({
			element: wrapperElement,
			extensions: [
				Document,
				Paragraph,
				Text,
				...this.registerCommands(),
			],
			content: content,
			autofocus: false,
			editable: !this.textAreaElement.disabled,
			injectCSS: false,
		});
		return editor;
	}

	private registerCommands() : Array<Extension|Mark|Node> {
		const extensions = new Set<Extension|Mark|Node>();
		this.menubarElement?.querySelectorAll('button[richtext-toggle]').forEach(button => {
			if (!(button instanceof HTMLButtonElement))
				return;
			const parts = button.getAttribute('richtext-toggle')?.split(':') ?? [];
			parts[1] = 'Action';
			const actionName = parts.join('');
			const ActionClass = (<any>controls)[actionName];
			if (!(ActionClass?.prototype instanceof Action))
				throw new Error(`Unknown action class '${actionName}'.`);
			const actionInstance = new ActionClass(this.wrapperElement, button);
			this.registeredCommands.set(parts[0], actionInstance);
			(actionInstance as Action).extensions.forEach(e => extensions.add(e));
		});
		return Array.from(extensions);
	}

	private installEventHandlers() {
		this.editor.on('focus', this.focused);
		this.editor.on('update', this.updated);
		this.editor.on('blur', this.blurred);
		this.editor.on('selectionUpdate', this.selectionUpdate);
		const form = this.textAreaElement.form;
		form!.addEventListener('reset', this.formResetted);
		form!.addEventListener('submitted', this.formSubmitted);
		this.registeredCommands.forEach(command => command.installEventHandler(this.editor));
	}

	private concealTextArea(wrapperElement: HTMLElement) {
		wrapperElement.insertAdjacentElement('afterend', this.textAreaElement);
		this.textAreaElement.classList.add('dj-concealed');
	}

	private focused = () => {
		this.wrapperElement.classList.add('focused');
		this.textAreaElement.dispatchEvent(new Event('focus'));
	}

	private updated = () => {
		this.textAreaElement.innerHTML = this.editor.getHTML();
		this.textAreaElement.dispatchEvent(new Event('input'));
	}

	private blurred = () => {
		this.registeredCommands.forEach((action) => {
			action.button.classList.remove('active');
		});
		this.wrapperElement.classList.remove('focused');
		if (this.textAreaElement.required && this.editor.getText().length === 0) {
			this.wrapperElement.classList.remove('valid');
			this.wrapperElement.classList.add('invalid');
		} else {
			this.wrapperElement.classList.add('valid');
			this.wrapperElement.classList.remove('invalid');
		}
		this.textAreaElement.dispatchEvent(new Event('blur'));
	}

	private selectionUpdate = () => {
		this.registeredCommands.forEach((action, name) => {
			action.button.classList.toggle('active', this.editor.isActive(name));
		});
	}

	private formResetted = () => {
		this.editor.chain().clearContent().insertContent(this.initialValue).run();
	}

	private formSubmitted = () => {}

	private transferStyles() {
		const buttonGroupHeight = this.menubarElement?.getBoundingClientRect().height ?? 0;
		const sheet = this.declaredStyles.sheet;
		for (let index = 0; sheet && index < sheet.cssRules.length; index++) {
			const cssRule = sheet.cssRules.item(index) as CSSStyleRule;
			let extraStyles: string;
			switch (cssRule.selectorText) {
				case '.dj-richtext-wrapper':
					extraStyles = StyleHelpers.extractStyles(this.textAreaElement, [
						'height', 'background-image', 'border', 'border-radius', 'box-shadow', 'outline',
						'resize',
					]);
					extraStyles = extraStyles.concat(`min-height:${buttonGroupHeight * 2}px;`);
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.dj-richtext-wrapper.focused':
					this.textAreaElement.style.transition = 'none';
					this.textAreaElement.focus();
					extraStyles = StyleHelpers.extractStyles(this.textAreaElement, [
						'border', 'box-shadow', 'outline']);
					this.textAreaElement.blur();
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					this.textAreaElement.style.transition = '';
					break;
				case '.dj-richtext-wrapper .ProseMirror':
					extraStyles = StyleHelpers.extractStyles(this.textAreaElement, [
						'font-family', 'font-size', 'font-strech', 'font-style', 'font-weight', 'letter-spacing',
						'white-space', 'line-height', 'overflow', 'padding']);
					extraStyles = extraStyles.concat(`top:${buttonGroupHeight + 1}px;`);
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				case '.dj-richtext-wrapper [role="menubar"]':
					extraStyles = StyleHelpers.extractStyles(this.textAreaElement, [
						'border-bottom'
					]);
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				default:
					break;
			}
		}
	}

	public disconnect() {
		// TODO: remove event handlers
	}

	public getValue() : any {
		return this.useJson ? this.editor.getJSON() : this.editor.getHTML();
	}
}


const RA = Symbol('RichtextArea');

export class RichTextAreaElement extends HTMLTextAreaElement {
	private [RA]?: RichtextArea;  // hides internal implementation

	private connectedCallback() {
		const wrapperElement = this.closest('.dj-richtext-wrapper');
		if (wrapperElement instanceof HTMLElement) {
			this[RA] = new RichtextArea(wrapperElement, this);
		}
	}

	private disconnectCallback() {
		this[RA]?.disconnect();
	}

	public get value() : any {
		return this[RA]?.getValue();
	}

	public async getValue() {
		return this[RA]?.getValue();
	}
}
