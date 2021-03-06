function resetContent(lis) {
    lis[0].textContent = 'Click here and select the file';
    lis[1].textContent = 'or drag and drop directly.';
}


async function upload(uploader, lis, form, span, img) {
    lis[0].textContent = 'Please wait,';
    lis[1].textContent = 'preparing upload...';

    let action;
    let method;
    let body = new FormData();
    let date;
    let inputs = [];

    for (let input of form.querySelectorAll('input')) {
        if (input.type === 'file') {
            body.append('name', input.files[0].name);
            date = input.files[0].lastModified;
        } else {
            if (input.name === 'action') {
                action = input.value;
            } else {
                if (input.name === 'method') {
                    method = input.value;
                }
                body.append(input.name, input.value);
            }
            inputs.push(input);
        }
    }

    let response = await fetch(action, {
        method: 'post',
        body: body,
    });

    if (response.status == 200) {
        body = await response.json();

        lis[1].textContent = 'uploading...';

        if (method === 'code') {
            body.date = date;
        }

        for (let input of inputs) {
            form.removeChild(input);
        }

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
    } else {
        lis[1].textContent = await response.text();
        lis[0].textContent = 'Error:';

        img.classList.add('hidden');
        span.classList.remove('hidden');

        uploader.disabled = false;
    }
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
        let lis = uploader.querySelectorAll('li');
        let form = uploader.querySelector('form');
        let input = uploader.querySelector('input[type="file"]');

        uploader.addEventListener('click', function (event) {
            event.preventDefault();
            input.dispatchEvent(new MouseEvent('click'));
        });

        if (form === null) {
            input.addEventListener('change', function () {
                if (input.files.length > 0) {
                    lis[0].textContent = 'File:';
                    lis[1].textContent = input.files[0].name;
                } else {
                    resetContent(lis);
                }
            });
        } else {
            let span = uploader.querySelector('span');
            let img = uploader.querySelector('img');

            input.addEventListener('change', function () {
                uploader.disabled = true;

                span.classList.add('hidden');
                img.classList.remove('hidden');

                upload(uploader, lis, form, span, img);
            });

            img.classList.add('hidden');
        }

        resetContent(lis);
    }
});
