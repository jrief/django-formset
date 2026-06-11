import styles from './SimpsonsSelector.css';


class SimpsonsSelector {
	private readonly element: HTMLInputElement;
	private readonly listElement: HTMLUListElement;

	constructor(element: HTMLInputElement) {
		this.element = element;
		this.element.classList.add('dj-concealed');
		const declaredStyles = document.createElement('style');
		declaredStyles.textContent = styles;
		document.head.appendChild(declaredStyles);
		if (!(element.nextElementSibling instanceof HTMLUListElement))
			throw ("Missing next sibling UListElement");
		this.listElement = element.nextElementSibling;
	}

	public connectedCallback() {
		this.listElement.querySelectorAll('li').forEach(item => {
			item.addEventListener('click', this.handleSelectMember);
		});
		this.element.addEventListener('change', this.handleMemberChanged);
		this.setMember(this.element.value);
	}

	public disconnectedCallback() {
		this.listElement.querySelectorAll('li').forEach(item => {
			item.removeEventListener('click', this.handleSelectMember);
		});
		this.element.removeEventListener('change', this.handleMemberChanged);
	}

	private setMember(memberValue: string) {
		this.listElement.querySelectorAll('li').forEach(item => item.ariaSelected = null);
		const preselected = this.listElement.querySelector(`li[data-member="${memberValue}"]`);
		if (preselected instanceof HTMLLIElement) {
			preselected.ariaSelected = 'true';
		}
	}

	private handleMemberChanged = (event: Event) => {
		if (event.target !== this.element)
			return;
		this.setMember(this.element.value);
	};

	private handleSelectMember = (event: Event) => {
		const target = event.target as HTMLElement;
		const liElement = target.tagName === 'LI' ? target : target.closest('li');
		if (liElement instanceof HTMLLIElement) {
			const memberValue = liElement.dataset.member ?? '';
			this.setMember(memberValue);
			this.element.value = memberValue;
			this.element.dispatchEvent(new Event('change', {bubbles: true}));
		}
	};
}

export class SimpsonsInputElement extends HTMLInputElement {
	#selector?: SimpsonsSelector;

	connectedCallback() {
		this.#selector = new SimpsonsSelector(this);
		this.#selector.connectedCallback();
	}

	disconnectedCallback() {
		this.#selector?.disconnectedCallback();
	}
}
