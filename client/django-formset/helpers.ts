export namespace StyleHelpers {
	let pseudoStyleSheet: CSSStyleSheet|null = null;
	const styleElement = document.createElement('style');
	const mediaQueryStyles = Array<Function>();
	const observer = new MutationObserver(themeHasChanged);
	observer.observe(document.documentElement, {attributes: true});
	observer.observe(document.body, {attributes: true});
	window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', stylesHaveChanged);

	export function extractStyles(element: Element, properties: Array<string>|Record<string, string>): string {
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

	function mutableStyles(sheet: CSSStyleSheet, selector: string, properties: Record<string, string>, element: HTMLElement, attributes: Record<string, string|null>, extraCssClass?: string) : Function {
		const setStyles = () => {
			const transition = window.getComputedStyle(element).getPropertyValue('transition');
			element.style.transition = 'none';  // temporarily disable transitions
			attributes['hidden'] = null;  // make element temporarily visible to pilfer styles

			// remember element attributes and CSS classes and overwrite them
			const currentValues: [string, string|null][] = Object.entries(attributes).map(([qualifiedName]) =>
				[qualifiedName, element.getAttribute(qualifiedName)]
			);
			Object.entries(attributes).forEach(([qualifiedName, value]) => {
				value === null ? element.removeAttribute(qualifiedName) : element.setAttribute(qualifiedName, value);
			});
			if (extraCssClass) {
				element.classList.add(extraCssClass);
			}

			// pilfer styles for given properties
			const style = Object.entries(properties).map(([property, value]) => {
				return `${property}:${window.getComputedStyle(element).getPropertyValue(value)};`;
			}).join('');

			// restore element attributes and CSS classes
			if (extraCssClass) {
				element.classList.remove(extraCssClass);
			}
			currentValues.forEach(([qualifiedName, value]) => {
				value === null ? element.removeAttribute(qualifiedName) : element.setAttribute(qualifiedName, value);
			});

			element.style.transition = transition;  // restore transitions
			return style;
		};
		const ruleIndex = sheet.insertRule(`${selector}{${setStyles()}}`, sheet.cssRules.length);
		return () => {
			sheet.deleteRule(ruleIndex);
			sheet.insertRule(`${selector}{${setStyles()}}`, ruleIndex);
		};
	}

	export function replaceMediaQueryStyles(index: number, sheet: CSSStyleSheet, selector: string, properties: Record<string, string>, element: HTMLElement, attributes: Record<string, string|null> = {}, extraCssClass?: string) {
		if (index < 0 || index >= mediaQueryStyles.length) {
			return mediaQueryStyles.push(mutableStyles(sheet, selector, properties, element, attributes, extraCssClass)) - 1;
		} else {
			mediaQueryStyles.splice(index, 1, mutableStyles(sheet, selector, properties, element, attributes, extraCssClass));
			return index;
		}
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

	export function addSpriteFlags(rootNode: HTMLHeadElement|ShadowRoot) {
		const currentURL = new URL(import.meta.url);
		const parts = currentURL.pathname.split('/');
		currentURL.pathname = `${parts.slice(0, -2).join('/')}/css/sprite-flags.css`;
		const href = currentURL.toString();
		if (!rootNode.querySelector(`link[href="${href}"]`)) {
			const link = document.createElement('link');
			link.rel = 'stylesheet';
			link.href = href;
			link.type = 'text/css';
			link.media = 'screen';
			rootNode.insertBefore(link, rootNode.firstChild);
		}
	}
}

export function asUTCDate(date: Date) : Date {
	return new Date(date.getTime() - date.getTimezoneOffset() * 60000);
}

export function compareArrays(needle: Array<string>, haystack: Array<string>): boolean {
	for (let k = 0; k < needle.length; k++) {
		if (haystack.length <= k || needle[k] !== haystack[k]) {
			return false;
		}
	}
	return true;
}

export function toAbsPath(basePath: Path, path: Array<string>) : Path {
	if (path.at(0) !== '')
		return path;
	// path is relative, so concatenate it to the form's path
	const absPath = [...basePath];
	const relPath = path.filter(part => part !== '');
	const delta = path.length - relPath.length;
	absPath.splice(absPath.length - delta + 1);
	absPath.push(...relPath);
	return absPath;
}

export function assert(condition: any, message?: string) {
	if (!condition) {
		message = message ? `Assertion failed: ${message}` : "Assertion failed";
		throw new Error(message);
	}
}
