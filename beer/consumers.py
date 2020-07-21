from channels.generic.websocket import AsyncJsonWebsocketConsumer


class Consumer(AsyncJsonWebsocketConsumer):
    public = []

    async def before_accept(self):
        pass

    async def after_accept(self):
        pass

    async def connect(self):
        await self.before_accept()
        await self.accept()
        await self.after_accept()

    async def group_add(self, group):
        await self.channel_layer.group_add(group, self.channel_name)

    async def group_discard(self, group):
        await self.channel_layer.group_discard(group, self.channel_name)

    async def send_client(self, method, *args):
        event = {
            'method': method,
            'args': args,
        }
        await self.send_json(event)

    async def send_group(self, group, method, *args):
        event = {
            'type': 'receive_group',
            'method': method,
            'args': args,
        }
        await self.channel_layer.group_send(group, event)

    async def call(self, prefix, event):
        method = getattr(self, '{}_{}'.format(prefix, event['method']))
        await method(*event['args'])

    async def receive_json(self, event):
        if event['method'] not in self.public:
            raise ValueError('Method {} is not public'.format(event['method']))
        await self.call('client', event)

    async def receive_group(self, event):
        await self.call('group', event)


class UploadConsumer(Consumer):
    async def after_accept(self):
        await self.send_client('accept', self.channel_name)

    async def handler_report(self, event):
        await self.send_client('report', *event['args'])

    async def handler_complete(self, event):
        await self.close()
