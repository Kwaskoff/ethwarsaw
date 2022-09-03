#!/usr/bin/env python3

import json
import socket
import sys
import time
import urllib.request
import urllib.error


API_URL = 'https://api.telegram.org/bot{bot_key}/test/{method}'
BOT_KEY = ...
PHOTO_ID = 'AgACAgIAAxkBAAMHYxJ12ZlK9nZoKO_eiPQgAWZDKQUAAqmnMRsk75FIGZf-VgNAQx0BAAMCAANtAAMpBA'
LOGO_URL = 'https://i.ibb.co/R7VgfNN/photo-2022-09-03-16-47-31.jpg'


def get_deep(obj_dic, *keys):
    if not keys:
        return obj_dic
    if obj_dic is None:
        return None
    if isinstance(obj_dic, dict):
        return get_deep(obj_dic.get(keys[0], None), *keys[1:])
    elif isinstance(obj_dic, (list, tuple)) and isinstance(keys[0], int) and keys[0] < len(obj_dic):
        return get_deep(obj_dic[keys[0]], *keys[1:])
    else:
        return get_deep(getattr(obj_dic, keys[0], None), *keys[1:])


def request(method, params):
    addr = API_URL.format(bot_key=BOT_KEY, method=method)
    req = urllib.request.Request(addr)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    jsondata = json.dumps(params).encode('utf-8')
    req.add_header('Content-Length', len(jsondata))
    try:
        with urllib.request.urlopen(req, jsondata, timeout=60) as response:
            if response.status != 200:
                return {}
            html = response.read()
            data = json.loads(html)
            return data
    except urllib.error.URLError as err:
        print('URLError:', addr, 'err:', err, file=sys.stderr)
        # print('URLError:', addr, 'data:', jsondata, file=sys.stderr)
        time.sleep(1)
        return {}
    except socket.timeout:
        return {}


def new_message(message):
    from_id = get_deep(message, 'chat', 'id') or get_deep(message, 'from', 'id')
    request('sendPhoto', {
        'chat_id': from_id,
        'photo': PHOTO_ID,
        'caption': 'Hello! This Ramp bot will help you buy cryptocurrency.',
        'reply_markup': {
            'inline_keyboard': [
                [
                    {
                        'text': 'Buy cryptocurrency',
                        'web_app': {
                            'url': 'https://widget.hackaton.ramp-network.org'
                        }
                    }
                ],
                [
                    {
                        'text': 'Add to menu 📎',
                        'url': 'https://t.me/ramp_bot?startattach'
                    }
                ]
            ]
        }
    })


def new_inline_query(inline_query):
    query_id = inline_query['id']
    wallet = inline_query['query'].split(' ')[0]
    request('answerInlineQuery', {
        'inline_query_id': query_id,
        'results': [
            {
                'type': 'article',
                'id': 'pay',
                'title': 'Pay via Ramp',
                'input_message_content': {
                    'message_text': f'Push the button below to pay for crypto with a credit card.\n\nUse my address below to pay 🔻\n\n`{wallet}`\n\n(Tap on address to copy it)',
                    'parse_mode': 'Markdown'
                },
                'reply_markup': {
                    'inline_keyboard': [
                        [
                            {
                                'text': 'Buy Crypto💰',
                                'url': 'https://widget.hackaton.ramp-network.org'
                                # 'web_app': {
                                #     'url': 'https://widget.hackaton.ramp-network.org'
                                # }
                            }
                        ],
                        [
                            {
                                'text': 'Go to Ramp Bot 🤖',
                                'url': 'https://t.me/ramp_bot'
                            }
                        ]
                    ]
                },
                'thumb_url': LOGO_URL
            }
        ]
    })


def update(obj):
    message = obj.get('message', None)
    if message:
        new_message(message)
    inline_query = obj.get('inline_query', None)
    if inline_query:
        new_inline_query(inline_query)


def main():
    offset = None
    try:
        while True:
            params = {}
            if offset:
                params['offset'] = offset
            data = request('getUpdates', params)
            updates = data.get('result', [])
            for upd in updates:
                update(upd)
                if 'update_id' in upd:
                    offset = upd['update_id'] + 1
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
