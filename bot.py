#!/usr/bin/env python3

import json
import socket
import sys
import time
import urllib.request
import urllib.error
from decimal import Decimal


API_URL = 'https://api.telegram.org/bot{bot_key}/test/{method}'
BOT_KEY = ...
# PHOTO_ID = 'https://i.ibb.co/qC9JRtY/640x360-ramp.png'
PHOTO_ID = 'AgACAgIAAxkBAAMHYxJ12ZlK9nZoKO_eiPQgAWZDKQUAAqmnMRsk75FIGZf-VgNAQx0BAAMCAANtAAMpBA'

RAMP_API = 'https://api-instant.hackaton.ramp-network.org/api'
RAMP_WIDGET = 'https://widget.hackaton.ramp-network.org/'

ASSETS = []


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


def get_assets():
    addr = RAMP_API + '/host-api/assets'
    try:
        with urllib.request.urlopen(addr, timeout=60) as response:
            if response.status != 200:
                return {}
            html = response.read()
            data = json.loads(html)
            return data
    except urllib.error.URLError as err:
        print('URLError:', addr, 'err:', err, file=sys.stderr)
        return {}
    except socket.timeout:
        return {}


def search_crypto(query):
    result = []
    lower = query.lower()
    for ass in ASSETS:
        satisfied = False
        for k in {'symbol', 'name'}:
            val = ass[k].lower()
            if query in val:
                satisfied = True
                break
        if satisfied:
            result += [ass]
    return result


def get_results(wallet, amount, assets):
    results = []
    for ass in assets:
        ass_amount = Decimal(amount) * (10 ** ass['decimals'])
        ass_code = ass['symbol']
        results += [
            {
                'type': 'article',
                'id': ass_code,
                'title': ass['name'],
                'input_message_content': {
                    'message_text': f'Push the button below to pay for crypto with a credit card',
                    'parse_mode': 'Markdown'
                },
                'reply_markup': {
                    'inline_keyboard': [
                        [
                            {
                                'text': 'Buy Crypto💰',
                                'url': f'https://widget.hackaton.ramp-network.org?userAddress={wallet}&swapAmount={ass_amount}&swapAsset={ass_code}'
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
                'thumb_url': ass['logoUrl']
            }
        ]
    return results


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
    fields = inline_query['query'].split()
    if len(fields) < 3:
        request('answerInlineQuery', {
            'inline_query_id': query_id,
            'results': []
        })
        return
    wallet, amount, currency = fields
    assets = search_crypto(currency)
    results = get_results(wallet, amount, assets)
    request('answerInlineQuery', {
        'inline_query_id': query_id,
        'results': results
    })


def update(obj):
    message = obj.get('message', None)
    if message:
        new_message(message)
    inline_query = obj.get('inline_query', None)
    if inline_query:
        new_inline_query(inline_query)


def main():
    global ASSETS
    ASSETS = get_assets()['assets']
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
