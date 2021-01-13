document.addEventListener('DOMContentLoaded', function () {
    let as = document.querySelectorAll('.submit');

    for (let a of as) {
        let form = a.querySelector('form');

        a.addEventListener('click', function (event) {
            event.preventDefault();
            form.submit();
        });
    }
});
