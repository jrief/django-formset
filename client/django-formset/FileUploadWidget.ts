import template from 'lodash.template';


interface FileUploadResponse {
	content_type: string;
	content_type_extra: Object;
	download_url: string;
	name: string;
	size: number;
	thumbnail_url: string;
	upload_temp_name: string;
}


export class FileUploadWidget {
	private readonly fieldGroup: FieldGroup;
	private readonly inputElement: HTMLInputElement;
	private readonly dropbox: HTMLElement;
	private readonly chooseFileButton: HTMLButtonElement;
	private readonly progressBar: HTMLProgressElement | null = null;
	private readonly dropboxItemTemplate: Function;
	private readonly emptyDropboxItem: HTMLDivElement;
	private readonly observer: MutationObserver;
	private readonly initialData: Array<Object>;
	private readonly maxUploadSize: number;
	public uploadedFiles: Array<Object>;

	constructor(fieldGroup: FieldGroup, inputElement: HTMLInputElement) {
		this.fieldGroup = fieldGroup;
		this.inputElement = inputElement;
		this.maxUploadSize = parseInt(this.inputElement.getAttribute('max-size') ?? '0');
		this.dropbox = this.fieldGroup.element.querySelector('figure.dj-dropbox') as HTMLElement;
		if (!this.dropbox)
			throw new Error('Element <input type="file"> requires sibling element <figure class="dj-dropbox"></figure>');

		this.chooseFileButton = this.fieldGroup.element.querySelector('button.dj-choose-file') as HTMLButtonElement;
		if (!this.chooseFileButton)
			throw new Error('Element <input type="file"> requires sibling element <button class="dj-choose-file"></button>');

		this.progressBar = this.fieldGroup.element.querySelector('progress') as HTMLProgressElement;
		if (this.progressBar) {
			this.progressBar.style.visibility = 'hidden';
		}

		this.emptyDropboxItem = this.dropbox.querySelector('div.dj-empty-item') as HTMLDivElement;
		if (!this.emptyDropboxItem)
			throw new Error('Element <input type="file"> requires sibling element <figure><div class="dj-empty-item"></div></figure>');

		const dropboxItemTemplate = this.fieldGroup.element.querySelector('.dj-dropbox-items');
		if (!dropboxItemTemplate)
			throw new Error('Element <input type="file"> requires sibling element <template class="dj-dropbox-items"></template>');
		this.dropboxItemTemplate = template(dropboxItemTemplate.innerHTML) as Function;

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
		this.chooseFileButton.addEventListener('click', () => {
			inputElement.click();
		});
		inputElement.addEventListener('change', () => this.uploadFiles(this.inputElement.files).then(() => {
			this.fieldGroup.inputted();
			this.fieldGroup.validate();
		}).catch(() => {
			this.fieldGroup.reportFailedUpload();
		}).finally(() => {
			this.chooseFileButton.blur();
			this.fieldGroup.touch();
		}));
	}

	private fileDrop = (event: DragEvent) => {
		this.swallowEvent(event);
		if (event.dataTransfer) {
			this.fieldGroup.touch();
			this.inputElement.files = event.dataTransfer.files;
			this.uploadFiles(this.inputElement.files).then(() => {
				this.fieldGroup.inputted();
				this.fieldGroup.validate();
			});
		}
	};

	private fileRemove = () => {
		this.inputElement.value = '';  // used to clear readonly `this.inputElement.files`
		this.uploadedFiles = this.initialData.length > 0 ? [{}] : [];
		while (this.dropbox.firstChild) {
			this.dropbox.removeChild(this.dropbox.firstChild);
		}
		this.dropbox.appendChild(this.emptyDropboxItem);
		this.fieldGroup.touch();
		this.fieldGroup.inputted();
		this.fieldGroup.validate();
	};

	private swallowEvent = (event: Event) => {
		event.stopPropagation();
		event.preventDefault();
	};

	private async uploadFiles(files: FileList | null) : Promise<void> {
		if (!files || files.length === 0)
			return Promise.reject();
		return new Promise<void>((resolve, reject) => {
			// Django currently can't handle multiple file uploads, restrict to first file
			const file = files.item(0);
			if (file && (!this.maxUploadSize || file.size <= this.maxUploadSize)) {
				this.uploadFile(file, this.dropbox.clientHeight).then(response => {
					this.uploadedFiles = [response];
					this.renderDropbox();
					this.fieldGroup.inputted();
					this.inputElement.dataset.fileupload = JSON.stringify(response);
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
				// the remaining 3% of the progress bar are reserved for image transformation
				self.progressBar.value = 0.97 * complete;
			}
		}

		const body = new FormData();
		body.append('temp_file', file);
		body.append('image_height', imageHeight.toString());

		return new Promise<Response>((resolve, reject) => {
			function transferComplete() {
				if (self.progressBar) {
					self.progressBar.value = 1;
					window.setTimeout(() => self.progressBar!.style.visibility = 'hidden', 333);
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
			request.open('POST', this.fieldGroup.form.formset.endpoint, true);
			const csrfToken = this.fieldGroup.form.formset.CSRFToken;
			if (csrfToken) {
				request.setRequestHeader('X-CSRFToken', csrfToken);
			}
			request.responseType = 'json';
			request.send(body as XMLHttpRequestBodyInit);
		});
	}

	private renderDropbox() {
		const list = this.uploadedFiles.map(this.dropboxItemTemplate);
		if (list.length > 0) {
			this.dropbox.innerHTML = list.join('');
			this.inputElement.dataset.fileupload = JSON.stringify(this.uploadedFiles[0]);
		} else {
			this.dropbox.replaceChildren(this.emptyDropboxItem);
		}
	}

	private attributesChanged(mutationsList: Array<MutationRecord>) {
		for (const mutation of mutationsList) {
			if (mutation.type === 'attributes') {
				if (mutation.attributeName === 'disabled' && this.chooseFileButton.disabled != this.inputElement.disabled) {
					this.chooseFileButton.disabled = this.inputElement.disabled;
				}
				if (mutation.attributeName === 'data-fileupload') {
					const fileUpload = this.inputElement.dataset.fileupload;
					if (fileUpload) {
						this.dropbox.innerHTML = this.dropboxItemTemplate(JSON.parse(fileUpload));
						const button = this.dropbox.querySelector('.dj-delete-file');
						if (button) {
							button.addEventListener('click', this.fileRemove, {once: true});
						}
					}
				}
			}
		}
	}

	public inProgress(): boolean {
		return !!this.inputElement.files && this.inputElement.files.length > 0 && !this.uploadedFiles.length;
	}

	public resetToInitial() {
		this.uploadedFiles = this.initialData;
		this.renderDropbox();
	}
}
