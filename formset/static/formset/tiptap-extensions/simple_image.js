{
	name: 'simple_image',
	inline: true,
	group: 'inline',
	draggable: true,

	addAttributes() {
		return {
			src: {
				default: null,
			},
			alt: {
				default: null,
			},
			title: {
				default: null,
			},
			dataset: {
				default: {},
			},
		};
	},

	parseHTML() {
		return [{tag: 'img[src]'}];
	},

	renderHTML({HTMLAttributes}) {
		return ['img', HTMLAttributes];
	},

	image_to_document(elements) {
		// richtext-map-to: SimpleImageDialogForm.image
		console.log('image_to_document', elements);
		const fileupload = JSON.parse(elements.image.dataset.fileupload);
		return {
			src: fileupload.download_url,
			dataset: fileupload,
		};
	},

	document_to_image(inputElement, attributes) {
		// richtext-map-from: SimpleImageDialogForm.image
		console.log('document_to_image', attributes, inputElement);
		return {
			dataset: {fileupload: JSON.stringify(attributes.dataset)},
		};
	},

}
