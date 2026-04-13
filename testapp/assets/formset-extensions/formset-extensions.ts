window.djangoFormsetComponents = window.djangoFormsetComponents || [];
window.djangoFormsetComponents.push({
	selector: 'input[is="simpsons-selector"]',
	loader: (fragmentRoot) => new Promise((resolve, reject) => {
		import('./SimpsonsSelector').then(({SimpsonsInputElement}) => {
			if (!window.customElements.get('simpsons-selector')) {
				window.customElements.define('simpsons-selector', SimpsonsInputElement, {extends: 'input'});
			}
			window.customElements.whenDefined('simpsons-selector').then(() => resolve());
		}).catch(err => reject(err));
	}),
});
