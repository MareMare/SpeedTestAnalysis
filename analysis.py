import os
import sys
from datetime import datetime

import pandas as pd  # type: ignore
import plotly  # type: ignore
import plotly.graph_objects as go  # type: ignore
import pytz  # type: ignore
from plotly.subplots import make_subplots  # type: ignore


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
    return new_df


def calculate_medians(prepared_df: pd.DataFrame) -> pd.DataFrame:
    """ データフレームから中央値を計算 """
    median_df = (
        prepared_df.assign(箱ひげキー=lambda x: x['曜日'] + '-' + x['時間'].astype(str))
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


def add_box_plot_traces(fig: go.Figure, prepared_df: pd.DataFrame) -> None:
    """グラフにボックスプロットのトレースを追加する"""
    sorted_df = prepared_df.sort_values(by=['曜日番号', '時間'])

    # ダウンロード速度のボックスプロット
    fig.add_trace(
        go.Box(
            y=sorted_df['DownloadedMbps'],
            x=sorted_df['曜日'].astype(str) + '-' + sorted_df['時間'].astype(str),
            boxmean='sd',
            marker=dict(color='skyblue'),
            name='Download'
        ),
        row=1, col=1
    )

    # アップロード速度のボックスプロット
    fig.add_trace(
        go.Box(
            y=sorted_df['UploadedMbps'],
            x=sorted_df['曜日'].astype(str) + '-' + sorted_df['時間'].astype(str),
            boxmean='sd',
            marker=dict(color='orange'),
            name='Upload'
        ),
        row=1, col=1
    )


def add_line_plot_traces(fig: go.Figure, prepared_df: pd.DataFrame) -> None:
    """グラフに折れ線グラフのトレースを追加する"""
    median_df = calculate_medians(prepared_df)

    # ダウンロード速度の中央値線
    fig.add_trace(
        go.Scatter(
            x=median_df['箱ひげキー'],
            y=median_df['DownloadedMbps'],
            mode='lines+markers',
            marker=dict(color='blue'),
            name='Download Median'
        ),
        row=1, col=1
    )

    # アップロード速度の中央値線
    fig.add_trace(
        go.Scatter(
            x=median_df['箱ひげキー'],
            y=median_df['UploadedMbps'],
            mode='lines+markers',
            marker=dict(color='red'),
            name='Upload Median'
        ),
        row=1, col=1
    )


def add_table(fig: go.Figure, prepared_df: pd.DataFrame) -> None:
    """グラフにテーブルを追加する"""
    sorted_df = prepared_df.sort_values(by='StartedAt_JST', ascending=False)

    fig.add_trace(
        go.Table(
            header=dict(
                values=["StartedAt JST", "曜日", "曜日番号", "時間", "DownloadedMbps", "UploadedMbps"],
                fill_color='paleturquoise',
                align='left'
            ),
            cells=dict(
                values=[sorted_df[col] for col in sorted_df.columns],
                fill_color='lavender',
                align='left'
            )
        ),
        row=2, col=1
    )


def update_figure_layout(fig: go.Figure):
    """グラフレイアウトを更新する"""
    jst = pytz.timezone('Asia/Tokyo')
    # 現在のUTC時間を取得し、JSTに変換
    now_utc = datetime.now(pytz.utc)
    now_jst = now_utc.astimezone(jst)
    formatted_time = now_jst.strftime('%Y-%m-%d %H:%M:%S')

    fig.update_layout(
        title=f"Downloaded Mbps & Uploaded Mbps by Time (with Medians) - {formatted_time} JST",
        #xaxis_title="Day - Hour",
        yaxis_title="Speed (Mbps)",
        boxmode='group',
        showlegend=True,
    )


def plot_graph_with_table(prepared_df: pd.DataFrame) -> go.Figure:
    """ グラフを作成し表示する """

    # fig = go.Figure()
    # グラフとテーブルを配置するためのサブプロットを生成
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.7, 0.3],
        specs=[
            [{"type": "xy"}],
            [{"type": "table"}]
        ],
        subplot_titles=("Box and Line Plots", "Data Table"),
        vertical_spacing=0.1
    )

    # 各プロットやテーブルを追加
    add_box_plot_traces(fig, prepared_df)
    add_line_plot_traces(fig, prepared_df)
    add_table(fig, prepared_df)

    # レイアウトの更新
    update_figure_layout(fig)

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
    prepared_df = load_and_prepare_data(file_path)
    fig = plot_graph_with_table(prepared_df)

    # HTMLとして保存
    html_file_path = "dist/index.html"
    save_as_offline_html(fig, html_file_path)
    add_japanese_metadata(html_file_path)

    # フィギュアを表示する場合
    fig.show()


if __name__ == "__main__":
    main()
