import { Extension } from '@tiptap/core'

export interface TextIndentOptions {
	types: string[],
}

declare module '@tiptap/core' {
	interface Commands<ReturnType> {
		textIndent: {
			setTextIndent: (indent: string) => ReturnType,
			unsetTextIndent: () => ReturnType,
		}
	}
}

export const TextIndent = Extension.create<TextIndentOptions>({
	name: 'textIndent',

	addOptions() {
		return {
			types: [],
		}
	},

	addGlobalAttributes() {
		return [{
			types: this.options.types,
			attributes: {
				textIndent: {
					default: null,
					parseHTML: element => element.style.textIndent,
					renderHTML: attributes => {
						if (!attributes.textIndent)
							return {}
						return {
							'data-text': attributes.textIndent,
						}
					},
				},
			},
		}]
	},

	addCommands() {
		return {
			setTextIndent: (indent: string) => ({commands}) => {
				return this.options.types.every(type => commands.updateAttributes(type, {textIndent: indent}));
			},
			unsetTextIndent: () => ({commands}) => {
				return this.options.types.every(type => commands.resetAttributes(type, ['textIndent']));
			},
		}
	},
});
