document.addEventListener('DOMContentLoaded', function () {
    let form = document.querySelector('form');
    let submit = document.querySelector('input[type="submit"]');

    form.addEventListener('submit', function () {
        submit.disabled = true;
    });
});
