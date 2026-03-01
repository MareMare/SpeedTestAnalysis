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
    prepared_df = df[selected_columns].copy()
    return prepared_df


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
        )
    )

    # アップロード速度のボックスプロット
    fig.add_trace(
        go.Box(
            y=sorted_df['UploadedMbps'],
            x=sorted_df['曜日'].astype(str) + '-' + sorted_df['時間'].astype(str),
            boxmean='sd',
            marker=dict(color='orange'),
            name='Upload'
        )
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
        )
    )

    # アップロード速度の中央値線
    fig.add_trace(
        go.Scatter(
            x=median_df['箱ひげキー'],
            y=median_df['UploadedMbps'],
            mode='lines+markers',
            marker=dict(color='red'),
            name='Upload Median'
        )
    )


def update_figure_layout(fig: go.Figure, title: str):
    """グラフレイアウトを更新する"""
    fig.update_layout(
        title=title,
        xaxis_title="Day - Hour",
        yaxis_title="Speed (Mbps)",
        boxmode='group',
        showlegend=True,
    )

def plot_graph(prepared_df: pd.DataFrame, title: str) -> go.Figure:
    """ グラフを作成し表示する """
    fig = go.Figure()

    add_box_plot_traces(fig, prepared_df)
    add_line_plot_traces(fig, prepared_df)

    # レイアウトの更新
    update_figure_layout(fig, title)

    return fig


def save_as_html(fig: go.Figure, file_path: str) -> None:
    """ グラフをHTMLファイルとして保存 """
    # ディレクトリを作成
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    fig.write_html(
        file_path,
        include_plotlyjs='cdn',
        full_html=True,
        )


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


def generate_index_html(html_file_path: str, past_html_path: str, latest_html_path: str, past_title: str = 'Past Graphs', latest_title: str = 'Latest Graphs'):
    """
    2つのHTMLファイルへのリンクを含むindex.htmlを生成。
    """
    # html_file_pathを基準にした相対パスを計算
    past_relative_path = os.path.relpath(past_html_path, start=os.path.dirname(html_file_path))
    current_relative_path = os.path.relpath(latest_html_path, start=os.path.dirname(html_file_path))

    index_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body>
        <nav>
            <h1>SpeedTest Analysis Graphs</h1>
            <ul>
                <li><a href="{past_relative_path}" target="_blank">{past_title}</a></li>
                <li><a href="{current_relative_path}" target="_blank">{latest_title}</a></li>
            </ul>
        </nav>
    </body>
    </html>
    """
    with open(html_file_path, "w", encoding="utf-8") as file:
        file.write(index_content)
    print("index.html を生成しました。")


def generate_graph_html(csv_file_path: str, html_file_path: str, title: str):
    """
    グラフを生成しHTMLファイルに保存、
    日本語メタデータを追加する共通処理
    """
    # グラフの生成
    prepared_df = load_and_prepare_data(csv_file_path)
    fig = plot_graph(prepared_df, title)
    # HTMLとして保存
    save_as_html(fig, html_file_path)
    add_japanese_metadata(html_file_path)
    print(f"'{html_file_path}' の生成が完了しました。")


def get_date_range_in_jst(csv_file_path: str, datetime_column: str = 'timestamp') -> tuple[str, str]:
    """
    指定されたCSVから最古と最新の日時をJSTで取得します。

    Parameters:
        csv_file_path (str): 読み込むCSVファイルのパス
        datetime_column (str): 日時情報を含むカラム名（デフォルトは'timestamp'）

    Returns:
        (str, str): JSTの最古と最新の日時文字列
    """
    # CSVファイルをDataFrameとして読み込む
    df = pd.read_csv(csv_file_path)

    # 指定された日時列をDatetime型に変換
    df[datetime_column] = pd.to_datetime(df[datetime_column], utc=True)

    # 最古と最新の日時を取得
    min_timestamp_utc = df[datetime_column].min()
    max_timestamp_utc = df[datetime_column].max()

    # JSTに変換
    jst = pytz.timezone('Asia/Tokyo')
    min_timestamp_jst = min_timestamp_utc.astimezone(jst)
    max_timestamp_jst = max_timestamp_utc.astimezone(jst)

    # フォーマット整形
    min_timestamp_str = min_timestamp_jst.strftime('%Y-%m-%d %H:%M')
    max_timestamp_str = max_timestamp_jst.strftime('%Y-%m-%d %H:%M')

    return min_timestamp_str, max_timestamp_str


def get_current_jst_time() -> str:
    """
    現在のUTC時間をJSTに変換して文字列返却
    """
    jst = pytz.timezone('Asia/Tokyo')
    now_utc = datetime.now(pytz.utc)
    now_jst = now_utc.astimezone(jst)
    return now_jst.strftime('%Y-%m-%d %H:%M')


def main():
    print(sys.version)
    print(sys.executable)

    # 現在時間JSTを取得
    formatted_time = get_current_jst_time()

    past_csv_file_path = 'data/sampling_20250319_1229.csv'
    past_html_file_path = 'dist/past_graph.html'
    past_min_date, past_max_date = get_date_range_in_jst(past_csv_file_path, datetime_column='StartedAt')
    past_graph_title = f"Downloaded Mbps & Uploaded Mbps by Time (with Medians) - {past_min_date} → {past_max_date}"
    # 過去データのグラフ生成
    generate_graph_html(
        csv_file_path=past_csv_file_path,
        html_file_path=past_html_file_path,
        title=past_graph_title
    )

    latest_csv_file_path = 'data/sampling.csv'
    latest_html_file_path = 'dist/latest_graph.html'
    latest_min_date, latest_max_date = get_date_range_in_jst(latest_csv_file_path, datetime_column='StartedAt')
    latest_graph_title = f"Downloaded Mbps & Uploaded Mbps by Time (with Medians) Updated: {formatted_time}"
    # 現在データのグラフ生成
    generate_graph_html(
        csv_file_path=latest_csv_file_path,
        html_file_path=latest_html_file_path,
        title=latest_graph_title
    )

    # index.html の生成
    index_html_file_path = "dist/index.html"
    generate_index_html(
        index_html_file_path,
        past_html_file_path,
        latest_html_file_path,
        past_title=f'{past_min_date} → {past_max_date}: Past',
        latest_title=f'{latest_min_date} → {latest_max_date}: Latest')

if __name__ == "__main__":
    main()
