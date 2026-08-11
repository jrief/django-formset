{
	name: 'simple_geomap',
	inline: true,
	group: 'inline',
	draggable: true,

	addAttributes() {
		return {
			dataset: {
				default: {},
			},
		};
	},

	parseHTML() {
		return [{tag: 'geojson-renderer'}];
	},

	renderHTML({HTMLAttributes}) {
		return ['geojson-renderer', HTMLAttributes];
	},
}
