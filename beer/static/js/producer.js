const SOCKET_SCHEME = (typeof DEBUG !== 'undefined' && DEBUG) ? 'ws' : 'wss';

const COOKIE_KEY = 'djangochannel'


class Producer extends WebSocket {
    constructor(suffix) {
        super(SOCKET_SCHEME + '://' + window.location.host + '/' + suffix + '/');
        this.addEventListener('open', this.open);
        this.addEventListener('close', this.close);
        this.addEventListener('error', this.error);
        this.addEventListener('message', this.message);
    }

    open() {
    }

    close() {
    }

    error() {
    }

    message(event) {
        let data = JSON.parse(event.data);
        let method = data.method.charAt(0).toUpperCase() + data.method.substring(1);
        this['server' + method](...data.args);
    }

    sendServer(method, ...args) {
        let event = {
            'method': method,
            'args': args,
        };
        this.send(JSON.stringify(event));
    }
}


class UploadProducer extends Producer {
    static bind(suffix, form) {
        let Class = this;
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            new Class(suffix, form);
        });
    }

    constructor(suffix, form) {
        super(suffix);
        this.form = form;
    }

    serverAccept(channel) {
        let date = new Date();
        date.setTime(date.getTime() + 60000);
        document.cookie = COOKIE_KEY + '=' + channel + ';expires=' + date.toUTCString();
        this.form.submit();
    }

    serverReport(progress) {
    }
}
