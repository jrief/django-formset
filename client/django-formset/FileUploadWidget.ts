import template from 'lodash.template';

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


export class FileUploadWidget {
	private readonly field: FieldGroup;
	private readonly inputElement: HTMLInputElement;
	private readonly dropbox: HTMLUListElement;
	private readonly chooseFileButton: HTMLButtonElement;
	private readonly progressBar: HTMLProgressElement | null = null;
	private readonly dropboxItemTemplate: Function;
	private readonly emptyDropboxItem: HTMLLIElement;
	private readonly observer: MutationObserver;
	private readonly initialData: Array<Object>;
	public uploadedFiles: Array<Object>;

	constructor(fieldGroup: FieldGroup, inputElement: HTMLInputElement) {
		this.field = fieldGroup;
		this.inputElement = inputElement;

		this.dropbox = this.field.element.querySelector('ul.dj-dropbox') as HTMLUListElement;
		if (!this.dropbox)
			throw new Error('Element <input type="file"> requires sibling element <ul class="dj-dropbox"></ul>');

		this.chooseFileButton = this.field.element.querySelector('button.dj-choose-file') as HTMLButtonElement;
		if (!this.chooseFileButton)
			throw new Error('Element <input type="file"> requires sibling element <button class="dj-choose-file"></button>');

		this.progressBar = this.field.element.querySelector('progress') as HTMLProgressElement;
		if (this.progressBar) {
			this.progressBar.style.visibility = 'hidden';
		}

		this.emptyDropboxItem = this.dropbox.querySelector('li') as HTMLLIElement;
		const dropboxItemTemplate = this.field.element.querySelector('.dj-dropbox-items');
		if (!dropboxItemTemplate)
			throw new Error('Element <input type="file"> requires sibling element <template class="dj-dropbox-items"></template>');
		this.dropboxItemTemplate = template(dropboxItemTemplate.innerHTML);

		this.observer = new MutationObserver(mutationsList => this.attributesChanged(mutationsList));
		this.observer.observe(this.inputElement, {attributes: true});
		this.chooseFileButton.disabled = inputElement.disabled;

		const initialData = document.getElementById(`initial_${inputElement.id}`);
		if (initialData?.textContent) {
			this.uploadedFiles = this.initialData = [JSON.parse(initialData.textContent)];
			this.renderDropbox();
		} else {
			this.uploadedFiles = this.initialData = [];
		}
		this.dropbox.addEventListener('dragenter', this.swallowEvent);
		this.dropbox.addEventListener('dragover', this.swallowEvent);
		this.dropbox.addEventListener('drop', this.fileDrop);
		this.chooseFileButton.addEventListener('click', () => inputElement.click());
		inputElement.addEventListener('change', () => this.uploadFiles(this.inputElement.files).then(() => {
			this.field.inputted();
			this.field.validate();
		}).catch(() => {
			this.field.reportFailedUpload();
		}).finally(() => this.field.touch()));
	}

	private fileDrop = (event: DragEvent) => {
		this.swallowEvent(event);
		if (event.dataTransfer) {
			this.field.touch();
			this.inputElement.files = event.dataTransfer.files;
			this.uploadFiles(this.inputElement.files).then(() => {
				this.field.inputted();
				this.field.validate();
			});
		}
	}

	private fileRemove = () => {
		this.inputElement.value = '';  // used to clear readonly `this.inputElement.files`
		this.uploadedFiles = this.initialData.length > 0 ? [{}] : [];
		while (this.dropbox.firstChild) {
			this.dropbox.removeChild(this.dropbox.firstChild);
		}
		this.dropbox.appendChild(this.emptyDropboxItem);
		this.field.touch();
		this.field.inputted();
		this.field.validate();
	}

	private swallowEvent = (event: Event) => {
		event.stopPropagation();
		event.preventDefault();
	}

	private async uploadFiles(files: FileList | null) : Promise<void> {
		if (!files || files.length === 0)
			return Promise.reject();
		return new Promise<void>((resolve, reject) => {
			// Django currently can't handle multiple file uploads, restrict to first file
			const file = files.item(0);
			if (file) {
				this.uploadFile(file, this.dropbox.clientHeight).then(response => {
					this.uploadedFiles = [response];
					this.renderDropbox();
					this.field.inputted();
					resolve();
				}).catch(() => {
					reject();
				});
			} else {
				reject();
			}
		});
	}

	private async uploadFile(file: File, imageHeight: number): Promise<Object> {
		let self = this;

		function updateProgress(event: ProgressEvent) {
			const complete = event.lengthComputable ? event.loaded / event.total : 0;
			if (self.progressBar) {
				self.progressBar.style.visibility = 'visible';
				self.progressBar.value = complete;
			}
		}

		const body = new FormData();
		body.append('temp_file', file);
		body.append('image_height', imageHeight.toString());

		return new Promise<Response>((resolve, reject) => {
			function transferComplete() {
				if (self.progressBar) {
					self.progressBar.style.visibility = 'hidden';
				}
				if (request.status === 200) {
					resolve(request.response);
				} else {
					reject(request.response);
				}
			}

			const request = new XMLHttpRequest();
			if (self.progressBar) {
				request.addEventListener('loadstart', updateProgress);
				request.upload.addEventListener('progress', updateProgress, false);
			}
			request.addEventListener('loadend', transferComplete);
			request.open('POST', this.field.form.formset.endpoint, true);
			const csrfToken = this.field.form.formset.CSRFToken;
			if (csrfToken) {
				request.setRequestHeader('X-CSRFToken', csrfToken);
			}
			request.responseType = 'json';
			request.send(body);
		});
	}

	private renderDropbox() {
		let list = [];
		for (const fileHandle of this.uploadedFiles) {
			list.push(this.dropboxItemTemplate(fileHandle));
		}
		if (list.length > 0) {
			this.dropbox.innerHTML = list.join('');
		} else {
			this.dropbox.replaceChildren(this.emptyDropboxItem);
		}
		const button = this.dropbox.querySelector('.dj-delete-file');
		if (button) {
			button.addEventListener('click', this.fileRemove, {once: true});
		}
	}

	private attributesChanged(mutationsList: Array<MutationRecord>) {
		for (const mutation of mutationsList) {
			if (mutation.type === 'attributes' && mutation.attributeName === 'disabled'
			&& this.chooseFileButton.disabled != this.inputElement.disabled) {
				this.chooseFileButton.disabled = this.inputElement.disabled;
			}
		}
	}

	public inProgress(): boolean {
		return !!this.inputElement.files && this.inputElement.files.length > this.uploadedFiles.length;
	}

	public resetToInitial() {
		this.uploadedFiles = this.initialData;
		this.renderDropbox();
	}
}
