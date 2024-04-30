{
	name: 'procurator',  // renamed extension from "placeholder" to avoid naming conflict
	keepOnSplit: false,

	addAttributes() {
		return {
			variable_name: {
				default: null,
			},
			sample_value: {
				default: null,
			},
			role: {
				default: 'placeholder',
			},
		}
	},

	parseHTML() {
		return [{
			tag: 'output',
			role: 'placeholder',
		}];
	},

	renderHTML({HTMLAttributes}) {
		return ['output', HTMLAttributes, 0];
	},

}
