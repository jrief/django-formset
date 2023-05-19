import { Extension } from '@tiptap/core'

export interface TextMarginOptions {
	types: string[],
	maxIndentLevel: number;
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

	addOptions() {
		return {
			types: [],
			maxIndentLevel: 8,
		}
	},

	addGlobalAttributes() {
		return [{
			types: this.options.types,
			attributes: {
				textMargin: {
					default: null,
					parseHTML: element => Number(element.getAttribute('data-text-indent')) ?? null,
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
			increaseTextMargin: () => ({commands}) => {
				const indentLevel = (this.editor.getAttributes('paragraph').textMargin ?? 0) + 1;
				if (indentLevel < this.options.maxIndentLevel)
					return this.options.types.every(type => commands.updateAttributes(type, {textMargin: indentLevel}));
				return true;
			},
			decreaseTextMargin: () => ({commands}) => {
				const indentLevel = (this.editor.getAttributes('paragraph').textMargin ?? 0) - 1;
				if (indentLevel > 0)
					return this.options.types.every(type => commands.updateAttributes(type, {textMargin: indentLevel}));
				return this.options.types.every(type => commands.resetAttributes(type, ['textMargin']));
			},
			unsetTextMargin: () => ({commands}) => {
				return this.options.types.every(type => commands.resetAttributes(type, ['textMargin']));
			},
		}
	},
});
