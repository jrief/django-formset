import 'altcha';

export function amendAltchaComponent(fragmentRoot: Document|DocumentFragment, resolve: Function) {
	window.customElements.whenDefined('altcha-widget').then(() => {
		for (const inputElement of fragmentRoot.querySelectorAll('altcha-widget input[form]')) {
			if (inputElement instanceof HTMLInputElement && inputElement.type !== 'hidden') {
				inputElement.removeAttribute('form');
			}
		}
		resolve();
	});
}
