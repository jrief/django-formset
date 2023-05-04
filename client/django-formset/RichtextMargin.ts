import { Extension } from '@tiptap/core'

export interface TextMarginOptions {
	types: string[],
}

declare module '@tiptap/core' {
	interface Commands<ReturnType> {
		textMargin: {
			increaseTextMargin: () => ReturnType,
			decreaseTextMargin: () => ReturnType,
			unsetTextMargin: () => ReturnType,
		}
	}
}

export const TextMargin = Extension.create<TextMarginOptions>({
	name: 'textMargin',
	indentLevel: 0,

	addOptions() {
		return {
			types: [],
		}
	},

	addStorage() {
		return {
			indentLevel: 0,
		}
	},

	addGlobalAttributes() {
		return [{
			types: this.options.types,
			attributes: {
				textMargin: {
					default: null,
					parseHTML: element => element.style.margin,
					renderHTML: attributes => {
						if (!attributes.textMargin)
							return {}
						return {
							'data-text-indent': attributes.textMargin,
						}
					},
				},
			},
		}]
	},

	addCommands() {
		return {
			increaseTextMargin: () => ({editor, commands}) => {
				editor.storage.textMargin.indentLevel = Math.min(editor.storage.textMargin.indentLevel + 1, 7);
				return this.options.types.every(type => commands.updateAttributes(type, {textMargin: editor.storage.textMargin.indentLevel}));
			},
			decreaseTextMargin: () => ({editor, commands}) => {
				editor.storage.textMargin.indentLevel = Math.max(editor.storage.textMargin.indentLevel - 1, 0);
				if (editor.storage.textMargin.indentLevel === 0)
					return this.options.types.every(type => commands.resetAttributes(type, ['textMargin']));
				return this.options.types.every(type => commands.updateAttributes(type, {textMargin: editor.storage.textMargin.indentLevel}));
			},
			unsetTextMargin: () => ({commands}) => {
				return this.options.types.every(type => commands.resetAttributes(type, ['textMargin']));
			},
		}
	},
});
