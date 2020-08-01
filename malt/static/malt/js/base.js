function resetContent(ps) {
    ps[0].textContent = 'Click here and select the file';
    ps[1].textContent = 'or drag and drop directly.';
}


async function upload(ps, form) {
    ps[0].textContent = 'Please wait,';
    ps[1].textContent = 'preparing upload...';

    let action;
    let body = new FormData();

    for (let input of form.querySelectorAll('input')) {
        if (input.type === 'file') {
            body.append('name', input.files[0].name);
        } else {
            if (input.name === 'action') {
                action = input.value;
            } else {
                body.append(input.name, input.value);
            }
            form.removeChild(input);
        }
    }

    let response = await fetch(action, {
        method: 'post',
        body: body,
    });

    body = await response.json();

    ps[1].textContent = 'uploading...';

    for (let [name, value] of Object.entries(body)) {
        if (name === 'action') {
            form.action = value;
        } else {
            let input = document.createElement('input');
            input.type = 'hidden';
            input.name = name;
            input.value = value;
            form.prepend(input);
        }
    }

    form.submit();
}


function connectDragSignals(source, target) {
    let counter = 0;

    source.addEventListener('dragenter', function () {
        if (counter === 0) {
            target.classList.add('drag');
        }
        counter++;
    });

    source.addEventListener('dragleave', function () {
        counter--;
        if (counter === 0) {
            target.classList.remove('drag');
        }
    });

    source.addEventListener('dragover', function (event) {
        event.preventDefault();
    });

    source.addEventListener('drop', function (event) {
        event.preventDefault();

        let input = target.querySelector('input[type="file"]');

        if (event.dataTransfer.files.length > 0) {
            input.files = event.dataTransfer.files;
            input.dispatchEvent(new Event('change'));
        }

        counter = 0;
        target.classList.remove('drag');
    });
}


document.addEventListener('DOMContentLoaded', function () {
    let body = document.querySelector('body');
    let uploaders = document.querySelectorAll('.uploader');

    if (uploaders.length > 0) {
        if (uploaders.length > 1) {
            for (let uploader of uploaders) {
                connectDragSignals(uploader, uploader);
            }
        } else {
            connectDragSignals(body, uploaders[0]);
        }
    }

    for (let uploader of uploaders) {
        let ps = uploader.querySelectorAll('p');
        let form = uploader.querySelector('form');
        let input = uploader.querySelector('input[type="file"]');

        uploader.addEventListener('click', function (event) {
            event.preventDefault();
            input.dispatchEvent(new MouseEvent('click'));
        });

        if (form === null) {
            input.addEventListener('change', function () {
                if (input.files.length > 0) {
                    ps[0].textContent = 'File:';
                    ps[1].textContent = input.files[0].name;
                } else {
                    resetContent(ps);
                }
            });
        } else {
            let span = uploader.querySelector('span');
            let img = uploader.querySelector('img');

            input.addEventListener('change', function () {
                uploader.disabled = true;

                span.classList.add('hidden');
                img.classList.remove('hidden');

                upload(ps, form);
            });

            img.classList.add('hidden');
        }

        resetContent(ps);
    }
});
