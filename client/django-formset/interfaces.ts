interface DjangoButton {
	element: HTMLButtonElement;
	path: Array<string>;
}

interface DjangoFormset {
	endpoint: string;
	CSRFToken: string | undefined;
	buttons: Array<DjangoButton>;
}

interface DjangoForm {
	formset: DjangoFormset;
	path: Array<string>;
	setPristine(): void;
	untouch(): void;
	isValid(): boolean;
	resetToInitial(): void;
	getDataValue(path: Array<string>) : string | null;
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
