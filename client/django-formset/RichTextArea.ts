import { Editor } from '@tiptap/core';
import Document from '@tiptap/extension-document';
<<<<<<< HEAD
import History from '@tiptap/extension-history';
=======
>>>>>>> origin/tiptap
import Paragraph from '@tiptap/extension-paragraph';
import Text from '@tiptap/extension-text';
import Bold from '@tiptap/extension-bold';
import Italic from '@tiptap/extension-italic';
import Underline from '@tiptap/extension-underline';
import BulletList from '@tiptap/extension-bullet-list';
import ListItem from '@tiptap/extension-list-item';
import Link from '@tiptap/extension-link';
import styles from 'sass:./RichTextArea.scss';
import { StyleHelpers } from "./helpers";


class RichTextArea {
	private readonly textAreaElement: HTMLTextAreaElement;
	private readonly wrapperElement: HTMLElement;
<<<<<<< HEAD
	private readonly modalDialogElement: HTMLDialogElement | null;
	private readonly buttonGroupElement: HTMLElement | null;
	private readonly registeredCommands = new Map<string, HTMLButtonElement>();
=======
	private readonly buttonGroupElement: HTMLElement | null;
>>>>>>> origin/tiptap
	private readonly declaredStyles: HTMLStyleElement;
	private readonly editor: Editor;
	private readonly initialValue: string | object;
	private readonly required: Boolean;

	constructor(wrapperElement: HTMLElement, textAreaElement: HTMLTextAreaElement) {
		this.wrapperElement = wrapperElement;
		this.textAreaElement = textAreaElement;
<<<<<<< HEAD
		this.modalDialogElement = wrapperElement.querySelector('dialog');
=======
>>>>>>> origin/tiptap
		this.buttonGroupElement = wrapperElement.querySelector('[role="group"]');
		this.declaredStyles = document.createElement('style');
		this.declaredStyles.innerText = styles;
		document.head.appendChild(this.declaredStyles);
		this.editor = this.createEditor(wrapperElement);
<<<<<<< HEAD
		this.initialValue = this.getValue();
		this.transferStyles();
		this.required = textAreaElement.required;
		this.concealTextArea(wrapperElement);
		this.registerCommands();
		// innerHTML must reflect the content, otherwise field validation complains about a missing value
		this.textAreaElement.innerHTML = this.editor.getHTML();
=======
		this.transferStyles();
		//wrapperElement.style.width = 'fit-content';
		this.initialValue = textAreaElement.value;
		this.required = textAreaElement.required;
		this.concealTextArea(wrapperElement);
>>>>>>> origin/tiptap
		this.installEventHandlers();
	}

	private createEditor(wrapperElement: HTMLElement) : Editor {
<<<<<<< HEAD
		const scriptElement = wrapperElement.querySelector('textarea + script');
=======
		const scriptContent = wrapperElement.querySelector('textarea + script')?.textContent ?? '';
>>>>>>> origin/tiptap
		const editor = new Editor({
			element: wrapperElement,
			extensions: [
				Document,
<<<<<<< HEAD
				History,
				Paragraph,
				Text,
				BulletList,
				ListItem,
				Bold,
				Italic,
				Underline,
				Link.configure({
					openOnClick: false
				})
			],
			content: scriptElement?.textContent ? JSON.parse(scriptElement.textContent) : '',
=======
				Paragraph,
				Text,
				Bold,
				Italic,
				Underline,
				BulletList,
				ListItem.extend({
					content: 'text*',
				}),
				Link,
			],
			content: JSON.parse(scriptContent),
>>>>>>> origin/tiptap
			autofocus: false,
			editable: !this.textAreaElement.disabled,
			injectCSS: false,
		});
<<<<<<< HEAD
		scriptElement?.remove();
		return editor;
	}

	private registerCommands() {
		this.buttonGroupElement?.querySelectorAll('button[aria-label]').forEach(button => {
			if (!button.ariaLabel)
				return;
			const parts = button.ariaLabel.split('-');
			const funcname = parts.map((p, k) => k > 0 ? p.charAt(0).toUpperCase() + p.slice(1) : p).join('');
			const func = this[funcname as keyof RichTextArea];
			if (typeof func !== 'function')
				throw new Error(`Unknown command function '${funcname}' in RichTextArea.`);
			this.registeredCommands.set(funcname, button as HTMLButtonElement);
		});
	}

=======
		return editor;
	}

>>>>>>> origin/tiptap
	private installEventHandlers() {
		this.editor.on('focus', this.focused);
		this.editor.on('update', this.updated);
		this.editor.on('blur', this.blurred);
<<<<<<< HEAD
		this.editor.on('selectionUpdate', this.selectionUpdate);
		const form = this.wrapperElement.closest('form');
		form?.addEventListener('reset', this.formResetted);
		form?.addEventListener('submitted', this.formSubmitted);
		this.registeredCommands.forEach((button, action) => {
			const func = this[action as keyof RichTextArea];
			button.addEventListener('click', () => func.apply(this));
=======
		this.buttonGroupElement?.querySelectorAll('button[aria-label]').forEach(button => {
			button.addEventListener('click', this.controlButtonClicked);
>>>>>>> origin/tiptap
		});
	}

	private concealTextArea(wrapperElement: HTMLElement) {
		wrapperElement.insertAdjacentElement('afterend', this.textAreaElement);
		this.textAreaElement.classList.add('dj-concealed');
	}

	private focused = () => {
<<<<<<< HEAD
=======
		console.log('focus');
>>>>>>> origin/tiptap
		this.wrapperElement.classList.add('focused');
		this.textAreaElement.dispatchEvent(new Event('focus'));
	}

	private updated = () => {
<<<<<<< HEAD
		this.textAreaElement.innerHTML = this.editor.getHTML();
=======
		console.log('update');
		this.textAreaElement.innerText = this.editor.getText();
>>>>>>> origin/tiptap
		this.textAreaElement.dispatchEvent(new Event('input'));
	}

	private blurred = () => {
<<<<<<< HEAD
		this.registeredCommands.forEach((button) => {
			button.classList.remove('active');
		});
		this.wrapperElement.classList.remove('focused');
		if (this.required && this.editor.getText().length === 0) {
=======
		console.log('blurred');
		this.wrapperElement.classList.remove('focused');
		if (this.required && !this.editor.getText()) {
>>>>>>> origin/tiptap
			this.wrapperElement.classList.remove('valid');
			this.wrapperElement.classList.add('invalid');
		} else {
			this.wrapperElement.classList.add('valid');
			this.wrapperElement.classList.remove('invalid');
		}
		this.textAreaElement.dispatchEvent(new Event('blur'));
	}

<<<<<<< HEAD
	private selectionUpdate = () => {
		this.registeredCommands.forEach((button, action) => {
			button.classList.toggle('active', this.editor.isActive(action));
		});
	}

	private formResetted = () => {
		this.editor.chain().clearContent().insertContent(this.initialValue).run();
	}

	private formSubmitted = () => {}

=======
	private controlButtonClicked = (event: Event) => {
		if (event.currentTarget instanceof HTMLButtonElement && typeof event.currentTarget.ariaLabel === 'string') {
			const parts = event.currentTarget.ariaLabel.split('-');
			const funcname = parts.map((p, k) => k > 0 ? p.charAt(0).toUpperCase() + p.slice(1) : p).join('');
			const func = this[funcname as keyof RichTextArea] as (() => void);
			if (typeof func !== 'function')
				throw new Error(`Unknown editor function '${funcname}'.`);
			func.apply(this);
		}
	}

>>>>>>> origin/tiptap
	private bold() {
		this.editor.chain().focus().toggleBold().run();
	}

	private italic() {
		this.editor.chain().focus().toggleItalic().run();
	}

	private underline() {
		this.editor.chain().focus().toggleUnderline().run();
	}

	private link() {
<<<<<<< HEAD
		const modalDialogElement = this.modalDialogElement;
		const textField = modalDialogElement?.querySelector('INPUT[name="text"]');
		const urlField = modalDialogElement?.querySelector('INPUT[name="url"]');
		if (!(modalDialogElement && textField instanceof HTMLInputElement && urlField instanceof HTMLInputElement))
			return;

		const { selection, doc } = this.editor.view.state;
		textField.value = doc.textBetween(selection.from, selection.to, '');
		urlField.value = this.editor.getAttributes('link').href ?? '';
		if (!urlField.value) {
			modalDialogElement.querySelector('button[value="remove"]')
				?.setAttribute('hidden', 'hidden');
		}
		modalDialogElement.showModal();
		modalDialogElement.addEventListener('close', () => {
			const returnValue = this.modalDialogElement?.returnValue;
			if (returnValue === 'save' && textField.value && urlField.value) {
				this.editor.chain().focus()
					.extendMarkRange('link')
					.setLink({href: urlField.value})
					.insertContentAt({from: selection.from, to: selection.to}, textField.value)
					.run();
			} else if (returnValue === 'remove' || !urlField.value) {
				this.editor.chain().focus().extendMarkRange('link').unsetLink().run();
			}
		}, {once: true});
=======
		const previousUrl = this.editor.getAttributes('link').href;
		const url = window.prompt('URL', previousUrl);

		// cancelled
		if (url === null)
			return;

		// empty
		if (url === '') {
			this.editor.chain().focus().extendMarkRange('link').unsetLink().run();
			return
		}

		// update link
		this.editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
>>>>>>> origin/tiptap
	}

	private bulletList() {
		this.editor.chain().focus().toggleBulletList().run();
	}

	private clearFormat() {
<<<<<<< HEAD
		this.editor.chain().focus().unsetBold().unsetUnderline().unsetItalic().setParagraph().run();
	}

	private undo() {
		this.editor.commands.undo();
	}

	private redo() {
		this.editor.commands.redo();
=======
		this.editor.chain().focus().unsetBold().unsetUnderline().unsetItalic().run();
>>>>>>> origin/tiptap
	}

	private transferStyles() {
		const buttonGroupHeight = this.buttonGroupElement ? this.buttonGroupElement.getBoundingClientRect().height : 0;
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
				case '.dj-richtext-wrapper [role="group"]':
					extraStyles = StyleHelpers.extractStyles(this.textAreaElement, [
						'border-bottom'
					])
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					break;
				default:
					break;
			}
		}
	}

	public getValue() : any {
<<<<<<< HEAD
=======
		//return this.textAreaElement.innerText;
>>>>>>> origin/tiptap
		return this.editor.getJSON();
	}
}


const RTA = Symbol('RichTextArea');

export class RichTextAreaElement extends HTMLTextAreaElement {
	private [RTA]?: RichTextArea;  // hides internal implementation

	private connectedCallback() {
		const wrapperElement = this.closest('.dj-richtext-wrapper');
		if (wrapperElement instanceof HTMLElement) {
			this[RTA] = new RichTextArea(wrapperElement, this);
		}
	}

	public get value() : any {
		return this[RTA]?.getValue();
	}

	public async getValue() {
		return this[RTA]?.getValue();
	}
}
