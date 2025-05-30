import argparse
import asyncio
import contextlib
import logging
import random

import aiovoip

sip_config = {
    'srv_host': '127.0.0.1',
    'srv_port': 6000,
    'realm': 'example.net',
    'user': 'subscriber',
    'pwd': 'hunter2',
    'local_host': '127.0.0.1',
    'local_port': random.randint(6001, 6100)
}


async def run_subscription(peer, duration):
    subscription = await peer.subscribe(
        from_details=aiovoip.Contact.from_header('sip:{}@{}:{}'.format(
            sip_config['user'], sip_config['local_host'],
            sip_config['local_port'])),
        to_details=aiovoip.Contact.from_header('sip:666@{}:{}'.format(
            sip_config['srv_host'], sip_config['srv_port'])),
        password=sip_config['pwd'])

    async def reader():
        async for request in subscription:
            print('NOTIFY:', request.payload)
            await subscription.reply(request, status_code=200)

    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(reader(), timeout=duration)

    await subscription.close()


async def start(app, protocol, duration):
    if protocol is aiovoip.WS:
        peer = await app.connect(
            'ws://{}:{}'.format(sip_config['srv_host'], sip_config['srv_port']),
            protocol=protocol,
            local_addr=(sip_config['local_host'], sip_config['local_port']))
    else:
        peer = await app.connect(
            (sip_config['srv_host'], sip_config['srv_port']),
            protocol=protocol,
            local_addr=(sip_config['local_host'], sip_config['local_port']))

    await run_subscription(peer, duration)
    await app.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--protocol', default='udp')
    parser.add_argument('-d', '--duration', type=int, default=5)
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    app = aiovoip.Application(loop=loop)

    if args.protocol == 'udp':
        loop.run_until_complete(start(app, aiovoip.UDP, args.duration))
    elif args.protocol == 'tcp':
        loop.run_until_complete(start(app, aiovoip.TCP, args.duration))
    elif args.protocol == 'ws':
        loop.run_until_complete(start(app, aiovoip.WS, args.duration))
    else:
        raise RuntimeError("Unsupported protocol: {}".format(args.protocol))

    loop.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
