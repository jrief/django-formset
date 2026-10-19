import 'altcha/i18n';
import {StyleHelpers} from './helpers';


export function amendAltchaComponent(fragmentRoot: Document|DocumentFragment, resolve: Function) {
	window.customElements.whenDefined('altcha-widget').then((x) => {
		const altchaWidget = fragmentRoot.querySelector('altcha-widget');
		if (!(altchaWidget instanceof HTMLElement))
			throw new Error('altcha-widget not found');

		const findIndexOfSelector = (sheet: CSSStyleSheet, selector: string) => Array.from(sheet.cssRules ?? []).findIndex(rule => rule instanceof CSSStyleRule && rule.selectorText === selector);
		const origClassName = altchaWidget.className;
		altchaWidget.className = '';
		for (const inputElement of altchaWidget.querySelectorAll('input[form]')) {
			if (inputElement instanceof HTMLInputElement && inputElement.type === 'hidden') {
				inputElement.type = 'text'; // enforce this field to become member of a field group
				const altchaStyles = document?.getElementById('altcha-css');
				if (altchaStyles instanceof HTMLStyleElement && !StyleHelpers.stylesAreInstalled('altcha-widget')) {
					altchaStyles.sheet?.deleteRule(findIndexOfSelector(altchaStyles.sheet!, '.altcha *'));
					const declaredStyles = document.createElement('style');
					if (origClassName) {
						inputElement.classList.add(origClassName);
					}
					const extraStyles = StyleHelpers.extractStyles(inputElement, {
						'--altcha-border-style': 'border-style',
						'--altcha-border-width': 'border-width',
						'--altcha-border-radius': 'border-radius',
						'--altcha-padding': 'padding',
					}).concat('--altcha-max-width: 100%;');
					declaredStyles.innerText = `altcha-widget{${extraStyles}}`;
					document.head.appendChild(declaredStyles);
					StyleHelpers.replaceMediaQueryStyles(
						-1,
						declaredStyles.sheet!,
						'altcha-widget',
						{
							'--altcha-border-color': 'border-color',
							'--altcha-color-base': 'background-color',
							'--altcha-color-base-content': 'color',
						},
						inputElement,
						{},
						origClassName,
					);
					if (origClassName) {
						inputElement.classList.remove(origClassName);
					}
				}
				inputElement.classList.add('dj-concealed');
			} else {
				// other input elements must not be associated with the form
				inputElement.removeAttribute('form');
			}
		}
		resolve();
	});
}
