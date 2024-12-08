import os
import sys
from datetime import datetime

import pandas as pd  # type: ignore
import plotly  # type: ignore
import plotly.graph_objects as go  # type: ignore
import pytz  # type: ignore


def load_and_prepare_data(file_path: str) -> pd.DataFrame:
    """ CSVファイルを読み込み、必要なデータを抽出して変換する """
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"ファイル '{file_path}' が見つかりません。")
        exit()

    jst = pytz.timezone('Asia/Tokyo')
    df['StartedAt'] = pd.to_datetime(df['StartedAt'], utc=True)
    df['StartedAt_JST'] = df['StartedAt'].dt.tz_convert(jst)

    weekday_map = {0: '月', 1: '火', 2: '水', 3: '木', 4: '金', 5: '土', 6: '日'}
    df['曜日番号'] = df['StartedAt_JST'].dt.dayofweek
    df['曜日'] = df['StartedAt_JST'].dt.dayofweek.map(weekday_map)
    df['時間'] = df['StartedAt_JST'].dt.hour

    df['DownloadedMbps'] = df['DownloadedSpeed'] / 1000 / 1000
    df['UploadedMbps'] = df['UploadedSpeed'] / 1000 / 1000

    selected_columns = ['StartedAt_JST', '曜日', '曜日番号', '時間', 'DownloadedMbps', 'UploadedMbps']
    new_df = df[selected_columns].copy()
    new_df = new_df.sort_values(by=['曜日番号', '時間'])
    return new_df


def calculate_medians(new_df: pd.DataFrame) -> pd.DataFrame:
    """ データフレームから中央値を計算 """
    median_df = (
        new_df.assign(箱ひげキー=lambda x: x['曜日'] + '-' + x['時間'].astype(str))
        .groupby(['曜日', '時間', '曜日番号'])
        .agg({
            'DownloadedMbps': 'median',
            'UploadedMbps': 'median',
            '箱ひげキー': 'first'
        })
        .reset_index()
        .sort_values(by=['曜日番号', '時間'])
    )
    return median_df


def plot_graph(new_df: pd.DataFrame, median_df: pd.DataFrame) -> go.Figure:
    """ グラフを作成し表示する """
    jst = pytz.timezone('Asia/Tokyo')
    # 現在のUTC時間を取得し、JSTに変換
    now_utc = datetime.now(pytz.utc)
    now_jst = now_utc.astimezone(jst)
    formatted_time = now_jst.strftime('%Y-%m-%d %H:%M:%S')

    fig = go.Figure()

    fig.add_trace(
        go.Box(
            y=new_df['DownloadedMbps'],
            x=new_df['曜日'].astype(str) + '-' + new_df['時間'].astype(str),
            boxmean='sd',
            marker=dict(color='skyblue'),
            name='Download'
        )
    )

    fig.add_trace(
        go.Box(
            y=new_df['UploadedMbps'],
            x=new_df['曜日'].astype(str) + '-' + new_df['時間'].astype(str),
            boxmean='sd',
            marker=dict(color='orange'),
            name='Upload'
        )
    )

    fig.add_trace(go.Scatter(
        x=median_df['箱ひげキー'],
        y=median_df['DownloadedMbps'],
        mode='lines+markers',
        marker=dict(color='blue'),
        name='Download Median'
    ))

    fig.add_trace(go.Scatter(
        x=median_df['箱ひげキー'],
        y=median_df['UploadedMbps'],
        mode='lines+markers',
        marker=dict(color='red'),
        name='Upload Median'
    ))

    fig.update_layout(
        title=f"Downloaded Mbps & Uploaded Mbps by Time (with Medians) - {formatted_time} JST",
        xaxis_title="Day - Hour",
        yaxis_title="Speed (Mbps)",
        boxmode='group',
        showlegend=True,
    )

    return fig

def save_as_html(fig: go.Figure, file_path: str) -> None:
    """ グラフをHTMLファイルとして保存 """
    # ディレクトリを作成
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    fig.write_html(file_path)

def save_as_offline_html(fig: go.Figure, file_path: str) -> None:
    """ グラフをHTMLファイルとして保存 """
    # ディレクトリを作成
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    plotly.offline.plot(fig, filename=file_path)


def add_japanese_metadata(html_file_path: str) -> None:
    """ HTMLファイルに日本語メタデータを追加 """
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # メタタグを <head> に追加
    new_meta_tags = '''
<meta name="language" content="ja" />
<meta http-equiv="Content-Language" content="ja" />
'''

    # </head> の直前にメタタグを挿入
    html_content = html_content.replace('</head>', new_meta_tags + '</head>', 1)

    with open(html_file_path, 'w', encoding='utf-8') as file:
        file.write(html_content)


def main():
    print(sys.version)
    print(sys.executable)

    file_path = 'data/sampling.csv'
    new_df = load_and_prepare_data(file_path)
    median_df = calculate_medians(new_df)
    fig = plot_graph(new_df, median_df)

    # HTMLとして保存
    html_file_path = "dist/index.html"
    save_as_offline_html(fig, html_file_path)
    add_japanese_metadata(html_file_path)

    # フィギュアを表示する場合
    fig.show()


if __name__ == "__main__":
    main()
