
#Json
from re import U
from urllib.parse import uses_relative
import requests, json

#OS
import os

#log
import logging

#chatGPT
import openai

#Google spreadsheet
import gspread
from oauth2client.service_account import ServiceAccountCredentials

#10進数
from decimal import Decimal

#:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:
# main
#:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:
def lambda_handler(event, context):
    
    #イベント開始のログ出力
    print('##### EVENT #####')
    print(event)
    
    #SlackからのPOSTデータを取得
    #eventデータのboy部分のみを抽出する
    slack_event = json.loads(event['body'])

    #enventからユーザIDを取得する
    userID = slack_event.get('event')
    userID = userID.get('user')

    #取得したユーザIDを出力する
    print('##### USER #####')
    print(userID)
    
    #【終了条件】既存のイベントのとき処理を終了する
    #eventのevent_idとスプレッドのeventIDシートの値を比較して、既に記載があれば既存イベントとする
    table = spreadsheet_get_all_record('slackEventID') #spreadのデータを取得
    for row in range(0, len(table)):
        if slack_event.get('event_id') == table[row][0]:
            #終了した際のログを出力する
            print('## END: ', slack_event.get('event_id'), ", ", table[row][0])
            return 0

    #【終了条件】
    #入館システム用のbotのユーザIDのとき
    if userID == 'botのID':
        #終了した際のログを出力する
        print('## END: ', userID)
        return 0

    #slackAPIのトークンを環境変数から定義する
    slackToken = os.environ['SlackToken']
    
    #slackに投稿(slackからの重複リクエストを防ぐために一旦ユーザへ通知)
    #slack_webhook関数の呼び出し
    slack_webhook('考え中。。。', userID, slackToken)
    print('考え中。。。')
    
    #イベントID記録
    #spreadsheet_write_recordの呼び出し
    spreadsheet_write_record('slackEventID', slack_event.get('event_id'), '')
    
    #bodyの中テキストからメンションを除いた部分を抽出する
    slackInputText = slack_event.get('event').get('text')
    slackInputText = slackInputText.replace('<@U05J6JU5H0S>\n', '') #メンション削除
    slackInputText = slackInputText.replace('<@U05J6JU5H0S>', '') #メンション削除
    
    #spreadのデータを取得
    #spreadsheet_get_all_recordの呼び出し
    table = spreadsheet_get_all_record('record')

    #発行番号/その行数の取得(配列)
    getData = get_id(table)
    #発行番号
    gateNum = getData[0]
    #発行した番号の行
    row = getData[1]

    #slackに投稿
    slack_webhook(gateNum, userID, slackToken)
    print(gateNum)

    #テーブルの更新
    spreadsheet_write_record('record', row,userID)
    
    print('#################終了#################')
    
    #slack_challenge用
    #return {
    #    "statusCode": 200,
    #    "body": slack_event.get('challenge'),
    #    "headers": {
    #        "Content-Type": "application/json"
    #    }
    #}

#:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:
# 変換関数
#:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:
def decimal_to_int(obj):
    if isinstance(obj, Decimal):
        return int(obj)

#:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:
# スプレッドシートのデータ取得
#引数(シート名)
#:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:
def spreadsheet_get_all_record(shtName):
    
    #スプレッドシート(認証)
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        os.environ['Auth_File'],
        os.environ['Scope'].split(', ')
    )
    gc = gspread.authorize(credentials)
    
    #スプレッドシートファイル取得
    sh = gc.open(os.environ['Spread_FileName'])
    
    #スプレッドシートのworksheet取得
    wks = sh.worksheet(shtName)
    
    #すべてのデータを取得
    data = wks.get_all_values()
    
    #戻り値
    return data


#:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:
#slackに返信
#引数(送信メッセージ、ユーザID、slackAPIトークン)
#:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:
def slack_webhook(text, userID, slackToken):

    # Slack APIのメッセージ送信エンドポイント
    url = 'https://slack.com/api/chat.postMessage'

    # メッセージを送信するパラメータを設定
    data = {
        'channel': userID,  # ユーザIDをチャンネルとして指定
        'text': text,
        'link_names': 1,  # 名前をリンク化
    }

    # ヘッダーにAPIトークンを設定
    headers = {
        'Authorization': f'Bearer {slackToken}'
    }
    
    #webhookにてメッセージ送信
    response = requests.post(url, data=data, headers=headers)
    
    #戻り値なし

#:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:
# slackに返信
#:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:
def slack_webhook_apiChannel(slackInputText, response_message):

    text = 'actiasGPTより新規質問がありました。\n'
    text = text + slackInputText + '\n' + response_message
    
    #URL
    url = os.environ['Slack_URL']
    
    #slack送信
    requests.post(url, data = json.dumps(
        {
            'text': text,
            'username': u'actias GPT', #ユーザー名
            'link_names': 1,           #名前をリンク化
        }
    ))
    
    #戻り値なし

#:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:
# スプレッドシートに書き込み
#引数(シート名、[eventID/userID]、[""/gateNum])
#eventIDの出力/質問回答の蓄積かで引数が変わり、異なるシートへ出力される
#:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:
def spreadsheet_write_record(shtName, columnA, columnB):
    
    #スプレッドシート(認証)
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        os.environ['Auth_File'],
        os.environ['Scope'].split(', ')
    )
    gc = gspread.authorize(credentials)
    
    #スプレッドシート名を環境変数から定義
    sh = gc.open(os.environ['Spread_FileName'])
    
    #スプレッドシートのworksheet取得
    wks = sh.worksheet(shtName)
    
    #終端行
    lastRow = len(wks.col_values(1))
    lastRow = lastRow + 1
    
    #シートデータクリア
    if lastRow > 1000:
        wks.clear()
    
    #シートへの出力
    #columBがないとき(eventIDの出力)は
    if columnB == '':
        wks.update_cell(lastRow, 1, columnA)
    #colimBがあるとき(シートの対象列に済を入れる)
    else:
        wks.update_cell(columnA, 4, "済")
    
    #戻り値なし

#:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:
#発行IDの取得
#引数(スプレッドのデータ)
#:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:=:
def get_id(table):
    
    #要素[3]に済が入っていなかったら、要素[0](発行番号)を返す
    #処理が行われた時点で処理を終了する
    for row in range(0, len(table)):
        if table[row][3] == "":
            gateNum = table[row][0]
            gateNumRow = row
            break

    return gateNum,gateNumRow
