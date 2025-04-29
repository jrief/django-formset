export namespace StyleHelpers {
	let pseudoStyleSheet: CSSStyleSheet|null = null;
	const styleElement = document.createElement('style');
	const mediaQueryStyles = Array<Function>();
	const observer = new MutationObserver(themeHasChanged);
	observer.observe(document.documentElement, {attributes: true});
	observer.observe(document.body, {attributes: true});
	window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', stylesHaveChanged);

	export function extractStyles(element: Element, properties: Array<string>|{[key: string]: string}): string {
		let styles = Array<string>();
		const style = window.getComputedStyle(element);
		if (Array.isArray(properties)) {
			for (let property of properties) {
				styles.push(`${property}:${style.getPropertyValue(property)}`);
			}
		} else {
			for (let [property, key] of Object.entries(properties)) {
				styles.push(`${property}:${style.getPropertyValue(key)}`);
			}
		}
		return styles.join(';').concat(';');
	}

	export function mutableStyles(sheet: CSSStyleSheet, selector: string, properties: {[key: string]: string}, element: HTMLElement, extraCssClass?: string) : Function {
		const setStyles = () => {
			const transition = window.getComputedStyle(element).getPropertyValue('transition');
			const hidden = element.hidden;
			element.style.transition = 'none';  // temporarily disable transitions
			element.hidden = false;  // temporarily make element visible to pilfer styles
			if (extraCssClass) {
				element.classList.add(extraCssClass);
			}
			const style = Object.entries(properties).map(([property, value]) => {
				return `${property}:${window.getComputedStyle(element).getPropertyValue(value)};`;
			}).join('');
			if (extraCssClass) {
				element.classList.remove(extraCssClass);
			}
			element.hidden = hidden;  // restore visibility
			element.style.transition = transition;  // restore transitions
			return style;
		};
		const ruleIndex = sheet.insertRule(`${selector}{${setStyles()}}`, sheet.cssRules.length);
		return () => {
			sheet.deleteRule(ruleIndex);
			sheet.insertRule(`${selector}{${setStyles()}}`, ruleIndex);
		};
	}

	export function pushMediaQueryStyles(sheet: CSSStyleSheet, selector: string, properties: {[key: string]: string}, element: HTMLElement, extraCssClass?: string) {
		mediaQueryStyles.push(
			mutableStyles(sheet, selector, properties, element, extraCssClass)
		);
	}

	function stylesHaveChanged() {
		mediaQueryStyles.forEach(styleModifiers => styleModifiers());
	}

	function themeHasChanged(mutationList: MutationRecord[], observer: MutationObserver) {
		// this observer is triggered whenever the attribute containing substring "theme" is changed on the body element
		mutationList.forEach((mutation) => {
			if (mutation.type === 'attributes' && mutation.attributeName?.includes('theme')) {
				stylesHaveChanged();
			}
		});
	}

	function convertPseudoClasses() {
		// Iterate over all style sheets, find most pseudo classes and add CSSRules with a
		// CSS selector where the pseudo class has been replaced by a real counterpart.
		// This is required, because browsers can not invoke `window.getComputedStyle(element)`
		// using pseudo classes.
		if (!pseudoStyleSheet)
			throw new Error('Style Sheet is not initialized');

		const numStyleSheets = document.styleSheets.length;
		for (let index = 0; index < numStyleSheets; index++) {
			const sheet = document.styleSheets[index];
			try {
				for (let k = 0; k < sheet.cssRules.length; k++) {
					const cssRule = sheet.cssRules.item(k);
					if (cssRule) {
						traverseStyles(cssRule, pseudoStyleSheet);
					}
				}
			} catch (e) {
				if (e instanceof DOMException) {
					console.warn('Could not read stylesheet, try adding crossorigin="anonymous"', sheet, e)
				} else {
					throw e;
				}
			}
		}
	}

	export function attachPseudoStyles() {
		if (document.head.contains(styleElement)) {
			document.head.removeChild(styleElement);
		}
		document.head.appendChild(styleElement);
		if (pseudoStyleSheet === null) {
			pseudoStyleSheet = styleElement.sheet as CSSStyleSheet;
			convertPseudoClasses();
		} else {
			while (styleElement.sheet?.cssRules.length) {
				styleElement.sheet?.deleteRule(0);
			}
			for (let index = 0; index < pseudoStyleSheet.cssRules.length; index++) {
				const cssText = pseudoStyleSheet.cssRules.item(index)?.cssText;
				if (cssText) {
					styleElement.sheet?.insertRule(cssText);
				}
			}
		}
	}

	export function stylesAreInstalled(baseSelector: string) : CSSStyleSheet|null {
		// check if styles have been loaded for this widget and return the CSSStyleSheet
		for (let k = document.styleSheets.length - 1; k >= 0; --k) {
			const cssRule = document?.styleSheets?.item(k)?.cssRules?.item(0);
			if (cssRule instanceof CSSStyleRule && cssRule.selectorText.trim() === baseSelector) {
				return document.styleSheets.item(k);
			}
		}
		return null;
	}

	function traverseStyles(cssRule: CSSRule, extraCSSStyleSheet: CSSStyleSheet) {
		if (cssRule instanceof CSSImportRule) {
			try {
				if (!cssRule.styleSheet)
					return;
				for (let subRule of cssRule.styleSheet.cssRules) {
					traverseStyles(subRule, extraCSSStyleSheet);
				}
			} catch (e) {
				if (e instanceof DOMException) {
					console.warn('Could not traverse CSS import', cssRule, e)
				} else {
					throw e;
				}
			}
		} else if (cssRule instanceof CSSStyleRule) {
			if (!cssRule.selectorText)
				return;
			// `getComputedStyle()` has no support for querying pseudo classes such as :focus, :hover, :disabled, etc.,
			// so we need to convert them to a real CSS class. In order to handle this the `⁝` character is used as a
			// prefix to the class name. This is a special character that is very unlikely to conflict with any existing
			// CSS class name.
			const newSelectorText = cssRule.selectorText.
				replaceAll(':focus', '.⁝focus').
				replaceAll(':focus-visible', '.⁝focus-visible').
				replaceAll(':hover', '.⁝hover').
				replaceAll(':disabled', '.⁝disabled').
				replaceAll(':invalid', '.⁝invalid').
				replaceAll(':valid', '.⁝valid').
				replaceAll('::placeholder-shown', '.⁝placeholder-shown').
				replaceAll(':placeholder-shown', '.⁝placeholder-shown').
				replaceAll('::placeholder', '.⁝placeholder').
				replaceAll(':placeholder', '.⁝placeholder');
			if (newSelectorText !== cssRule.selectorText) {
				extraCSSStyleSheet.insertRule(`${newSelectorText}{${cssRule.style.cssText}}`);
			}
		} // else handle other CSSRule types
	}
}

export function assert(condition: any, message?: string) {
	if (!condition) {
		message = message ? `Assertion failed: ${message}` : "Assertion failed";
		throw new Error(message);
	}
}
