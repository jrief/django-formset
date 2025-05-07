type JSONValue = string|number|boolean|null|Array<JSONValue>|{[key: string]: JSONValue};
type Path = Array<string>;
type FieldElement = HTMLInputElement|HTMLSelectElement|HTMLTextAreaElement;
type FieldValue = string|Array<string|Object>;

interface DjangoButton {
	element: HTMLButtonElement;
	path: Path;
}

interface DjangoFormset {
	endpoint: string;
	CSRFToken: string | undefined;
	buttons: Array<DjangoButton>;
	currentActiveButton: DjangoButton | null;
	registerInducer(inducer: Inducible, func: Function): void;
}

interface DjangoForm {
	formset: DjangoFormset;
	path: Path;
	setPristine(): void;
	untouch(): void;
	isValid(): boolean;
	resetToInitial(): void;
	getDataValue(path: Path) : string|null;
}

interface FieldErrorPlaceholder {
	showsError: boolean;
	reportCustomError(message: string): void;
	clearError(): void;
}

interface FieldGroup {
	form: DjangoForm;
	element: HTMLElement;
	errorPlaceholder: FieldErrorPlaceholder;
	touch(): void;
	validate(): void;
	reportFailedUpload(): void;
	inputted(): void;
}

interface OptionData {
	id: string,
	label: string,
	optgroup?: string,
}

interface Inducible {
	updateOperability(...args: any[]): void;
}
