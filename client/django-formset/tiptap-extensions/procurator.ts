import { Mark } from '@tiptap/core';

export interface ProcuratorOptions {
	HTMLAttributes: Record<string, any>,
}

declare module '@tiptap/core' {
	interface Commands<ReturnType> {
		procurator: {
			setPlaceholder: (attributes: {variable: string}) => ReturnType,
			unsetPlaceholder: () => ReturnType,
		}
	}
}

export const Procurator = Mark.create<ProcuratorOptions>({
	name: 'procurator',
	keepOnSplit: false,

	addOptions() {
		return {
			HTMLAttributes: {role: 'placeholder'},
		}
	},

	addAttributes() {
		return {
			variable: {
				default: null,
			},
			role: {
				default: this.options.HTMLAttributes.role,
			},
		}
	},

	parseHTML() {
		return [{
			tag: 'output',
			role: this.options.HTMLAttributes.role,
		}];
	},

	renderHTML({HTMLAttributes}) {
		return ['output', HTMLAttributes, 0];
	},

	addCommands() {
		return {
			setPlaceholder: attributes => ({ chain }) => {
				return chain().setMark(this.name, attributes).run();
			},
			unsetPlaceholder: () => ({ chain }) => {
				return chain().unsetMark(this.name, { extendEmptyMarkRange: true }).run();
			},
		}
	},
});
