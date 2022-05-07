export namespace Styling {
	export function extractStyles(element: Element, properties: Array<string>): string {
		let styles = Array<string>();
		const style = window.getComputedStyle(element);
		for (let property of properties) {
			styles.push(`${property}:${style.getPropertyValue(property)}`);
		}
		return styles.join('; ').concat('; ');
	}

	export function convertPseudoClasses() : HTMLStyleElement {
		// Iterate over all style sheets, find most pseudo classes and add CSSRules with a
		// CSS selector where the pseudo class has been replaced by a real counterpart.
		// This is required, because browsers can not invoke `window.getComputedStyle(element)`
		// using pseudo classes.
		// With function `removeConvertedClasses()` the added CSSRules are removed again.
		const numStyleSheets = document.styleSheets.length;
		const styleElement = document.createElement('style');
		document.head.appendChild(styleElement);
		for (let index = 0; index < numStyleSheets; index++) {
			const sheet = document.styleSheets[index];
			for (let k = 0; k < sheet.cssRules.length; k++) {
				const cssRule = sheet.cssRules.item(k);
				if (cssRule) {
					traverseStyles(cssRule, styleElement.sheet as CSSStyleSheet);
				}
			}
		}
		return styleElement;
	}

	function traverseStyles(cssRule: CSSRule, extraCSSStyleSheet: CSSStyleSheet) {
		if (cssRule instanceof CSSImportRule) {
			if (!cssRule.styleSheet)
				return;
			for (let subRule of cssRule.styleSheet.cssRules) {
				traverseStyles(subRule, extraCSSStyleSheet);
			}
		} else if (cssRule instanceof CSSStyleRule) {
			if (!cssRule.selectorText)
				return;
			const newSelectorText = cssRule.selectorText.
				replaceAll(':focus', '.-focus-').
				replaceAll(':focus-visible', '.-focus-visible-').
				replaceAll(':hover', '.-hover-').
				replaceAll(':disabled', '.-disabled-').
				replaceAll(':invalid', '.-invalid-').
				replaceAll(':valid', '.-valid-').
				replaceAll('::placeholder-shown', '.-placeholder-shown').
				replaceAll(':placeholder-shown', '.-placeholder-shown').
				replaceAll('::placeholder', '.-placeholder-').
				replaceAll(':placeholder', '.-placeholder-');
			if (newSelectorText !== cssRule.selectorText) {
				extraCSSStyleSheet.insertRule(`${newSelectorText}{${cssRule.style.cssText}}`);
			}
		} // else handle other CSSRule types
	}
}
