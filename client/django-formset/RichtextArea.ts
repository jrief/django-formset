import styles from './RichtextArea.scss';
import { createPopper, Instance } from '@popperjs/core';
import { Editor, Extension, Mark, Node } from '@tiptap/core';
import Blockquote from '@tiptap/extension-blockquote';
import Bold from '@tiptap/extension-bold';
import BulletList from '@tiptap/extension-bullet-list';
import CharacterCount from '@tiptap/extension-character-count';
import CodeBlock from '@tiptap/extension-code-block';
import Document from '@tiptap/extension-document';
import HardBreak from '@tiptap/extension-hard-break';
import { Heading, Level } from '@tiptap/extension-heading';
import History from '@tiptap/extension-history';
import HorizontalRule from '@tiptap/extension-horizontal-rule';
import Image from '@tiptap/extension-image';
import Italic from '@tiptap/extension-italic';
import Link from '@tiptap/extension-link';
import ListItem from '@tiptap/extension-list-item';
import OrderedList from '@tiptap/extension-ordered-list';
import Paragraph from '@tiptap/extension-paragraph';
import Placeholder from '@tiptap/extension-placeholder';
import Text from '@tiptap/extension-text';
import { TextAlign, TextAlignOptions } from '@tiptap/extension-text-align';
import { TextIndent, TextIndentOptions } from './RichtextIndent';
import { TextMargin, TextMarginOptions } from './RichtextMargin';
import { Color, ColorOptions } from '@tiptap/extension-color';
import Underline from '@tiptap/extension-underline';
import { StyleHelpers } from './helpers';
import template from 'lodash.template';


abstract class Action {
	public readonly name: string;
	protected readonly button: HTMLButtonElement;
	protected readonly extensions: Array<Extension|Mark|Node> = [];

	constructor(wrapperElement: HTMLElement, name: string, button: HTMLButtonElement) {
		this.name = name;
		this.button = button;
	}

	installEventHandler(editor: Editor) {
		this.button.addEventListener('click', () => this.clicked(editor));
	}

	abstract clicked(editor: Editor): void;

	activate(editor: Editor) {
		this.button.classList.toggle('active', editor.isActive(this.name));
	}

	deactivate() {
		this.button.classList.remove('active');
	}

	extendExtensions(extensions: Array<Extension|Mark|Node>) {
		this.extensions.forEach(e => {
			if (!extensions.includes(e)) {
				extensions.push(e)
			}
		});
	}
}


namespace controls {
	export class BoldAction extends Action {
		protected readonly extensions = [Bold];

		clicked(editor: Editor) {
			editor.chain().focus().toggleBold().run();
			this.activate(editor);
		}
	}

	export class ItalicAction extends Action {
		protected readonly extensions = [Italic];

		clicked(editor: Editor) {
			editor.chain().focus().toggleItalic().run();
			this.activate(editor);
		}
	}

	export class UnderlineAction extends Action {
		protected readonly extensions = [Underline];

		clicked(editor: Editor) {
			editor.chain().focus().toggleUnderline().run();
			this.activate(editor);
		}
	}

	export class BulletListAction extends Action {
		protected readonly extensions = [BulletList, ListItem];

		clicked(editor: Editor) {
			editor.chain().focus().toggleBulletList().run();
			this.activate(editor);
		}
	}

	export class BlockquoteAction extends Action {
		protected readonly extensions = [Blockquote];

		clicked(editor: Editor) {
			editor.chain().focus().toggleBlockquote().run();
			this.activate(editor);
		}
	}

	export class CodeBlockAction extends Action {
		protected readonly extensions = [CodeBlock];

		clicked(editor: Editor) {
			editor.chain().focus().toggleCodeBlock().run();
			this.activate(editor);
		}
	}

	export class HardBreakAction extends Action {
		clicked(editor: Editor) {
			editor.chain().focus().setHardBreak().run();
			this.activate(editor);
		}
	}

	export class TextColorAction extends Action {
		protected extensions = [Color];

		clicked(editor: Editor) {
			editor.chain().focus().setColor('#a00000').run();
			this.activate(editor);
		}
	}

	export class TextIndentAction extends Action {
		private readonly options: TextIndentOptions = {
			types: ['heading', 'paragraph'],
		};
		private readonly indent: string;

		constructor(wrapperElement: HTMLElement, name: string, button: HTMLButtonElement) {
			super(wrapperElement, name, button);
			const parts = name.split(':');
			this.indent = parts[1] ?? '';
		}

		clicked(editor: Editor) {
			if (editor.isActive({textIndent: this.indent})) {
				editor.chain().focus().unsetTextIndent().run();
			} else {
				editor.chain().focus().setTextIndent(this.indent).run();
			}
			this.activate(editor);
		}

		activate(editor: Editor) {
			this.button.classList.toggle('active', editor.isActive({textIndent: this.indent}));
		}

		extendExtensions(extensions: Array<Extension|Mark|Node>) {
			if (!extensions.filter(e => e.name === 'textIndent').length) {
				extensions.push(TextIndent.configure(this.options));
			}
		}
	}

	export class TextMarginAction extends Action {
		private readonly options: TextMarginOptions = {
			types: ['heading', 'paragraph'],
		};
		private readonly indent: string;

		constructor(wrapperElement: HTMLElement, name: string, button: HTMLButtonElement) {
			super(wrapperElement, name, button);
			const parts = name.split(':');
			this.indent = parts[1] ?? '';
		}

		clicked(editor: Editor) {
			if (this.indent === 'increase') {
				editor.chain().focus().increaseTextMargin().run();
			} else if (this.indent === 'decrease') {
				editor.chain().focus().decreaseTextMargin().run();
			} else {
				editor.chain().focus().unsetTextMargin().run();
			}
			this.activate(editor);
		}

		activate(editor: Editor) {
			this.button.classList.toggle('active', editor.isActive({textMargin: this.indent}));
		}

		extendExtensions(extensions: Array<Extension|Mark|Node>) {
			if (!extensions.filter(e => e.name === 'textMargin').length) {
				extensions.push(TextMargin.configure(this.options));
			}
		}
	}

	export class OrderedListAction extends Action {
		protected readonly extensions = [OrderedList, ListItem];

		clicked(editor: Editor) {
			editor.chain().focus().toggleOrderedList().run();
			this.activate(editor);
		}
	}

	export class HorizontalRuleAction extends Action {
		protected readonly extensions = [HorizontalRule];

		clicked(editor: Editor) {
			editor.chain().focus().setHorizontalRule().run();
		}
	}

	export class ClearFormatAction extends Action {
		clicked(editor: Editor) {
			editor.chain().focus().clearNodes().unsetAllMarks().run();
			this.activate(editor);
		}
	}

	export class UndoAction extends Action {
		protected readonly extensions = [History];

		clicked(editor: Editor) {
			editor.commands.undo();
		}
	}

	export class RedoAction extends Action {
		protected readonly extensions = [History];

		clicked(editor: Editor) {
			editor.commands.redo();
		}
	}

	export class HeadingAction extends Action {
		private readonly dropdownInstance?: Instance;
		private readonly dropdownMenu: HTMLElement | null;
		private readonly dropdownItems: NodeListOf<Element> | [] = [];
		private readonly defaultIcon: Element;
		private readonly levels: Array<Level> = [];

		constructor(wrapperElement: HTMLElement, name: string, button: HTMLButtonElement) {
			super(wrapperElement, name, button);
			this.dropdownMenu = button.nextElementSibling instanceof HTMLUListElement && button.nextElementSibling.role === 'menu' ? button.nextElementSibling : null;
			if (this.dropdownMenu) {
				this.dropdownInstance = createPopper(this.button, this.dropdownMenu, {
					placement: 'bottom-start',
				});
				this.dropdownItems = this.dropdownMenu.querySelectorAll('[richtext-click^="heading:"]');
				this.dropdownItems.forEach(element => this.levels.push(this.extractLevel(element)));
			} else {
				this.levels.push(this.extractLevel(this.button));
			}
			this.defaultIcon = this.button.querySelector('svg')?.cloneNode(true) as Element;
		}

		private extractLevel(element: Element) : Level {
			const parts = element.getAttribute('richtext-click')?.split(':') ?? [];
			if (parts.length !== 2)
				throw new Error(`Element ${element} requires attribute 'richtext-click'.`);
			const level = parseInt(parts[1]) as Level;
			return level;
		}

		installEventHandler(editor: Editor) {
			if (this.dropdownMenu) {
				this.button.addEventListener('click', () => this.toggleMenu(editor));
				this.dropdownMenu.addEventListener('click', event => this.toggleItem(event, editor));
				document.addEventListener('click', event => {
					let element = event.target instanceof Element ? event.target : null;
					while (element) {
						if (element.isSameNode(this.button) || element.isSameNode(this.dropdownMenu))
							return;
						element = element.parentElement;
					}
					this.toggleMenu(editor, false);
				});
			} else {
				this.button.addEventListener('click', event => this.toggleItem(event, editor));
			}
		}

		clicked() {}

		activate(editor: Editor) {
			if (this.dropdownMenu) {
				let isActive = false;
				this.dropdownItems.forEach(element => {
					const level = this.extractLevel(element);
					const icon = element.querySelector('svg')?.cloneNode(true);
					if (editor.isActive('heading', {level}) && icon) {
						this.button.replaceChildren(icon);
						isActive = true;
					}
				});
				this.button.classList.toggle('active', isActive);
				if (!isActive) {
					this.button.replaceChildren(this.defaultIcon);
				}
			} else {
				const level = this.extractLevel(this.button);
				this.button.classList.toggle('active', editor.isActive('heading', {level}));
			}
		}

		extendExtensions(extensions: Array<Extension|Mark|Node>) {
			let unmergedOptions = true;
			extensions.forEach(e => {
				if (e.name === 'heading') {
					e.options.levels.push(...this.levels);
					unmergedOptions = false;
				}
			});
			if (unmergedOptions) {
				extensions.push(Heading.configure({
					levels: this.levels,
				}));
			}
		}

		private toggleMenu(editor: Editor, force?: boolean) {
			const expanded = (force !== false && this.button.ariaExpanded === 'false');
			this.button.ariaExpanded = expanded ? 'true' : 'false';
			this.dropdownItems.forEach(element => {
				const level = this.extractLevel(element);
				element.parentElement?.classList.toggle('active', editor.isActive('heading', {level}));
			});
			this.dropdownInstance?.update();
		}

		toggleItem(event: MouseEvent, editor: Editor) {
			let element = event.target instanceof Element ? event.target : null;
			while (element) {
				if (element instanceof HTMLButtonElement || element instanceof HTMLAnchorElement) {
					const level = this.extractLevel(element);
					editor.chain().focus().setHeading({level: level}).run();
					this.activate(editor);
					this.toggleMenu(editor, false);
					const icon = element.querySelector('svg')?.cloneNode(true);
					if (icon) {
						this.button.replaceChildren(icon);
					}
					break;
				}
				element = element.parentElement;
			}
		}
	}

	export class AlignmentAction extends Action {
		private readonly dropdownInstance?: Instance;
		private readonly dropdownMenu: HTMLElement | null;
		private readonly dropdownItems: NodeListOf<Element> | [] = [];
		private readonly defaultIcon: Element;
		private readonly options: TextAlignOptions = {
			types: ['heading', 'paragraph'],
			alignments: [],
			defaultAlignment: '',
		};

		constructor(wrapperElement: HTMLElement, name: string, button: HTMLButtonElement) {
			super(wrapperElement, name, button);
			this.dropdownMenu = button.nextElementSibling instanceof HTMLUListElement && button.nextElementSibling.role === 'menu' ? button.nextElementSibling : null;
			if (this.dropdownMenu) {
				this.dropdownInstance = createPopper(this.button, this.dropdownMenu, {
					placement: 'bottom-start',
				});
				this.dropdownItems = this.dropdownMenu.querySelectorAll('[richtext-click^="alignment:"]');
				this.dropdownItems.forEach(element => {
					this.options.alignments.push(this.extractAlignment(element));
				});
			} else {
				this.options.alignments.push(this.extractAlignment(this.button));
			}
			this.defaultIcon = this.button.querySelector('svg')?.cloneNode(true) as Element;
		}

		private extractAlignment(element: Element) : string {
			const parts = element.getAttribute('richtext-click')?.split(':') ?? [];
			if (parts.length !== 2)
				throw new Error(`Element ${element} requires attribute 'richtext-click'.`);
			return parts[1];
		}

		installEventHandler(editor: Editor) {
			if (this.dropdownMenu) {
				this.button.addEventListener('click', () => this.toggleMenu(editor));
				this.dropdownMenu.addEventListener('click', event => this.toggleItem(event, editor));
				document.addEventListener('click', event => {
					let element = event.target instanceof Element ? event.target : null;
					while (element) {
						if (element.isSameNode(this.button) || element.isSameNode(this.dropdownMenu))
							return;
						element = element.parentElement;
					}
					this.toggleMenu(editor, false);
				});
			} else {
				this.button.addEventListener('click', event => this.toggleItem(event, editor));
			}
		}

		clicked() {}

		activate(editor: Editor) {
			if (this.dropdownMenu) {
				let isActive = false;
				this.dropdownItems.forEach(element => {
					const alignment = this.extractAlignment(element);
					const icon = element.querySelector('svg')?.cloneNode(true);
					if (editor.isActive({textAlign: alignment}) && icon) {
						this.button.replaceChildren(icon);
						isActive = true;
					}
				});
				// do not toggle dropdown button's class "active", because text is somehow always aligned
				if (!isActive) {
					this.button.replaceChildren(this.defaultIcon);
				}
			} else {
				const alignment = this.extractAlignment(this.button);
				this.button.classList.toggle('active', editor.isActive({textAlign: alignment}));
			}
		}

		extendExtensions(extensions: Array<Extension|Mark|Node>) {
			let unmergedOptions = true;
			extensions.forEach(e => {
				if (e.name === 'textAlign') {
					e.options.alignments.push(...this.options.alignments);
					unmergedOptions = false;
				}
			});
			if (unmergedOptions) {
				extensions.push(TextAlign.configure(this.options));
			}
		}

		private toggleMenu(editor: Editor, force?: boolean) {
			const expanded = (force !== false && this.button.ariaExpanded === 'false');
			this.button.ariaExpanded = expanded ? 'true' : 'false';
			this.dropdownItems.forEach(element => {
				const alignment = this.extractAlignment(element);
				element.parentElement?.classList.toggle('active', editor.isActive({textAlign: alignment}));
			});
			this.dropdownInstance?.update();
		}

		toggleItem(event: MouseEvent, editor: Editor) {
			let element = event.target instanceof Element ? event.target : null;
			while (element) {
				if (element instanceof HTMLButtonElement || element instanceof HTMLAnchorElement) {
					const alignment = this.extractAlignment(element);
					editor.chain().focus().setTextAlign(alignment).run();
					this.activate(editor);
					this.toggleMenu(editor, false);
					const icon = element.querySelector('svg')?.cloneNode(true);
					if (icon) {
						this.button.replaceChildren(icon);
					}
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

		constructor(wrapperElement: HTMLElement, name: string, button: HTMLButtonElement) {
			super(wrapperElement, name, button);
			const label = button.getAttribute('richtext-click') ?? '';
			this.modalDialogElement = wrapperElement.querySelector(`dialog[richtext-opener="${label}"]`)! as HTMLDialogElement;
			this.formElement = this.modalDialogElement.querySelector('form[method="dialog"]')! as HTMLFormElement;
		}

		clicked = (editor: Editor) => this.openDialog(editor);
		protected abstract openDialog(editor: Editor): void;
	}


	export class LinkAction extends FormDialogAction {
		private readonly textInputElement: HTMLInputElement;
		private readonly urlInputElement: HTMLInputElement;
		public extensions = [Link.configure({
			openOnClick: false
		})];

		constructor(wrapperElement: HTMLElement, name: string, button: HTMLButtonElement) {
			super(wrapperElement, name, button);
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

		private handleSaveButton() {
			const saveButton = this.formElement.elements.namedItem('save');
			if (!(saveButton instanceof HTMLButtonElement))
				return;
			saveButton.addEventListener('click', () => {
				if (this.formElement.checkValidity()) {
					this.modalDialogElement.close('save');
				}
			});
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
			this.handleSaveButton();
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

		constructor(wrapperElement: HTMLElement, name: string, button: HTMLButtonElement) {
			super(wrapperElement, name, button);
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
			this.modalDialogElement.showModal();
			this.modalDialogElement.addEventListener('close', () => this.closeDialog(editor), {once: true});
		}
	}

}


class RichtextArea {
	private readonly textAreaElement: HTMLTextAreaElement;
	public readonly wrapperElement: HTMLElement;
	private readonly menubarElement: HTMLElement | null;
	private readonly registeredActions = new Array<Action>();
	private readonly declaredStyles: HTMLStyleElement;
	private readonly useJson: boolean = false;
	private readonly editor: Editor;
	private readonly initialValue: string | object;
	private charaterCountTemplate?: Function;
	private charaterCountDiv: HTMLElement | null = null;

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
		this.contentUpdate();
		this.installEventHandlers();
	}

	private createEditor(wrapperElement: HTMLElement, content: any) : Editor {
		const extensions = new Array<Extension|Mark|Node>(
			Document,
			Paragraph,
			Text,
			HardBreak,  // always add hard breaks via keyboard entry
		);
		this.registerControlActions(extensions);
		this.registerPlaceholder(extensions);
		this.registerCharaterCount(extensions);
		const editor = new Editor({
			element: wrapperElement,
			extensions: extensions,
			content: content,
			autofocus: false,
			editable: !this.textAreaElement.disabled,
			injectCSS: false,
		});
		return editor;
	}

	private registerControlActions(extensions: Array<Extension|Mark|Node>) {
		this.menubarElement?.querySelectorAll('button[richtext-click]').forEach(button => {
			if (!(button instanceof HTMLButtonElement))
				return;
			const richtextClick = button.getAttribute('richtext-click');
			if (!richtextClick)
				throw new Error("Missing attribute 'richtext-click' on action button");
			const parts = richtextClick.split(':');
			const actionName = `${parts[0].charAt(0).toUpperCase()}${parts[0].slice(1)}Action`;
			const ActionClass = (<any>controls)[actionName];
			if (!(ActionClass?.prototype instanceof Action))
				throw new Error(`Unknown action class '${actionName}'.`);
			const actionInstance = new ActionClass(this.wrapperElement, richtextClick, button) as Action;
			this.registeredActions.push(actionInstance);
			actionInstance.extendExtensions(extensions);
		});
		return extensions;
	}

	private registerPlaceholder(extensions: Array<Extension|Mark|Node>) {
		const placeholderText = this.textAreaElement.getAttribute('placeholder');
		if (!placeholderText)
			return;
		extensions.push(Placeholder.configure({placeholder: placeholderText}));
	}

	private registerCharaterCount(extensions: Array<Extension|Mark|Node>) {
		const limit = parseInt(this.textAreaElement.getAttribute('maxlength') ?? '');
		if (limit > 0) {
			extensions.push(CharacterCount.configure({limit}));
			this.charaterCountTemplate = template(`\${count}/${limit}`);
			this.charaterCountDiv = document.createElement('div');
			this.charaterCountDiv.classList.add('character-count');
			this.wrapperElement.insertAdjacentElement('beforeend', this.charaterCountDiv);
		}
	}

	private installEventHandlers() {
		this.editor.on('focus', this.focused);
		this.editor.on('update', this.updated);
		this.editor.on('blur', this.blurred);
		this.editor.on('update', this.contentUpdate);
		this.editor.on('selectionUpdate', this.selectionUpdate);
		const form = this.textAreaElement.form;
		form!.addEventListener('reset', this.formResetted);
		form!.addEventListener('submitted', this.formSubmitted);
		this.registeredActions.forEach(action => action.installEventHandler(this.editor));
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
		this.registeredActions.forEach(action => action.deactivate());
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

	private contentUpdate = () => {
		if (this.charaterCountDiv && this.charaterCountTemplate) {
			const context = {count: this.editor.storage.characterCount.characters()};
			this.charaterCountDiv.innerHTML = this.charaterCountTemplate(context);
		}
	}

	private selectionUpdate = () => {
		this.registeredActions.forEach(action => action.activate(this.editor));
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
				case '.dj-submitted .dj-richtext-wrapper.focused.invalid':
					this.textAreaElement.style.transition = 'none';
					this.textAreaElement.classList.add('-focus-', '-invalid-', 'is-invalid');  // is-invalid is a Bootstrap hack
					extraStyles = StyleHelpers.extractStyles(this.textAreaElement, [
						'border', 'box-shadow', 'outline']);
					this.textAreaElement.classList.remove('-focus-', '-invalid-', 'is-invalid');
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
				case '.dj-richtext-wrapper [role="menubar"] button[aria-haspopup="true"] + ul[role="menu"]':
					extraStyles = StyleHelpers.extractStyles(this.textAreaElement, [
						'border', 'z-index']);
					const re = new RegExp('z-index:(\\d+);');
					const matches = extraStyles.match(re);
					if (matches) {
						extraStyles = extraStyles.replace(re, `z-index:${parseInt(matches[1]) + 1}`);
					} else {
						extraStyles = extraStyles.replace('z-index:auto;', 'z-index:1;');
					}
					sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					if (this.menubarElement) {
						extraStyles = StyleHelpers.extractStyles(document.documentElement, ['background-color']);
						if (extraStyles === 'background-color:rgba(0, 0, 0, 0); ') {
							extraStyles = 'background-color:rgb(255, 255, 255);'
						}
						sheet.insertRule(`${cssRule.selectorText}{${extraStyles}}`, ++index);
					}
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
		if (this.editor.isEmpty)
			return '';  // otherwise empty field is not detected by calling function
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
}
