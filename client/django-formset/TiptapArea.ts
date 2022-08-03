import { Editor } from '@tiptap/core';
import StarterKit from '@tiptap/starter-kit';
import Document from '@tiptap/extension-document'
import Paragraph from '@tiptap/extension-paragraph'
import Text from '@tiptap/extension-text'

export class TiptapArea {
	private readonly field: FieldGroup;
	private readonly textAreaElement: HTMLTextAreaElement;
	private readonly editor: Editor;

	constructor(fieldGroup: FieldGroup, textAreaElement: HTMLTextAreaElement) {
		this.field = fieldGroup;
		const divElement = document.createElement('DIV');
		textAreaElement.insertAdjacentElement('afterend', divElement);
		this.textAreaElement = textAreaElement;
		this.editor = new Editor({
			element: divElement,
			extensions: [
				StarterKit,
				Document,
				Paragraph,
				Text,
			],
			content: '',
			autofocus: true,
			editable: true,
			injectCSS: false,
		});
		// TODO: Pilfer styles from textAreaElement
		// textAreaElement.hidden = true;
	}
}
