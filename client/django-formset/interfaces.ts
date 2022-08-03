interface DjangoFormset {
	endpoint: string;
	CSRFToken: string | undefined;
}

interface DjangoForm {
	formset: DjangoFormset;
}

interface FieldGroup {
	form: DjangoForm;
	element: HTMLElement;
	touch(): void;
	validate(): void;
	reportFailedUpload(): void;
	inputted(): void;
}
