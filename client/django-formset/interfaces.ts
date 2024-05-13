type JSONValue = string|number|boolean|null|Array<JSONValue>|{[key: string]: JSONValue};
type Path = Array<string>;

interface DjangoButton {
	element: HTMLButtonElement;
	path: Path;
}

interface DjangoFormset {
	endpoint: string;
	CSRFToken: string | undefined;
	buttons: Array<DjangoButton>;
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

interface FieldGroup {
	form: DjangoForm;
	element: HTMLElement;
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
