import matplotlib.pyplot as plt
import pandas as pd
import mplfinance as mpf
import datetime
import os
import glob
import random
from moviepy.editor import *
from PIL import Image, ImageDraw
import gc
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from moviepy.video.fx import fadeout
from moviepy.audio.fx import audio_fadeout as afx

from variables import get_most_recent_close, get_stock_data_to_plot, log


def save_intro_images(symbol=None, second_image_text=None):
    if not os.path.exists('temp_images'):
        os.makedirs('temp_images')

    if not symbol:
        raise ValueError("Symbol needs to be specified in save_intro_images()")

    fig, ax = plt.subplots(figsize=(6, 10.67))
    ax.axis('off')

    # Increased the y-coordinate for more top margin
    ax.text(0.5, 0.75, "Stock Replay", ha='center', va='center',
            fontdict={'family': 'sans', 'color': 'darkblue', 'weight': 'bold', 'size': 40})
    ax.text(0.5, 0.65, "in seconds", ha='center', va='center',
            fontdict={'family': 'sans', 'color': 'darkblue', 'weight': 'normal', 'size': 30})

    plt.tight_layout()
    filename1 = "temp_images/temp_intro_image1.png"
    plt.savefig(filename1, dpi=180)

    ax.text(0.5, 0.55, symbol, ha='center', va='center',
            fontdict={'family': 'sans', 'color': 'darkblue', 'weight': 'bold', 'size': 30})

    plt.tight_layout()
    filename2 = "temp_images/temp_intro_image2.png"
    plt.savefig(filename2, dpi=180)

    ax.text(0.5, 0.45, f"{'INTRADAY' if not second_image_text else second_image_text}", ha='center', va='center',
            fontdict={'family': 'sans', 'color': 'red', 'weight': 'bold', 'size': 30})

    filename3 = "temp_images/temp_intro_image3.png"
    plt.savefig(filename3, dpi=180)

    gc.collect()

    return filename1, filename2, filename3


def save_candlestick_image(df, index, is_last_image=False, prev_close=None, chart_title=None):
    if not os.path.exists('temp_images'):
        os.makedirs('temp_images')

    if not chart_title:
        raise ValueError("Symbol needs to be specified in save_candlestick_image()")

    if prev_close:
        # Ensure gain_loss_color is either 'green' or 'red'
        percentage_change = round(
            ((df['close'].iloc[-1] - prev_close) / prev_close) * 100, 2
        )

        value_change = round(
            df['close'].iloc[-1] - prev_close, 2
        )
    else:
        # Ensure gain_loss_color is either 'green' or 'red'
        percentage_change = round(
            ((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]) * 100, 2
        )

        value_change = round(
            df['close'].iloc[-1] - df['close'].iloc[0], 2
        )

    gain_loss_color = 'green' if percentage_change > 0 else 'red'

    if gain_loss_color not in ['green', 'red']:
        raise ValueError("gain_loss_color must be either 'green' or 'red'")

    # Convert 'Datetime' from string to datetime object
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)

    # Style and plot settings
    style = mpf.make_mpf_style(base_mpf_style='yahoo', y_on_right=True)

    if prev_close:
        # Adjust ylim
        y_min = min(df['low'].min(), prev_close) - 0.5
        y_max = max(df['high'].max(), prev_close) + 0.5

        # Create horizontal line data for prev_close without the label argument
        hline_data = [prev_close] * len(df)
        ap = [mpf.make_addplot(hline_data, color='navy')]  # Updated color to navy

    else:
        # Adjust ylim
        y_min = df['low'].min() - 4
        y_max = df['high'].max() + 4

        # Create horizontal line data for prev_close without the label argument
        hline_data = [df['close'].iloc[0]] * len(df)
        ap = [mpf.make_addplot(hline_data, color='navy')]  # Updated color to navy

    fig, axes = mpf.plot(df, type='candle', style=style, addplot=ap, returnfig=True,
                         ylabel='Price',
                         ylim=(y_min, y_max),
                         figsize=(6, 10.67),
                         tight_layout=True)

    # Set the main title and the subtitle for the chart
    axes[0].set_title(chart_title, fontsize=16, horizontalalignment='center', pad=20)

    last_date = df.index[-1]
    formatted_date = last_date.strftime('%A %B %d, %Y') if prev_close else last_date.strftime('%B %d, %Y')
    axes[0].set_xlabel(formatted_date, fontsize=12, horizontalalignment='center', labelpad=10)

    # Manually add a legend for the Previous Day Close
    current_close_patch = plt.Line2D([0], [0], marker='o', color='#aaaaaa', markerfacecolor='#aaaaaa', markersize=10,
                                       label=f"Close: {df['close'].iloc[-1]}")
    prev_close_patch = plt.Line2D([0], [0], marker='o', color='navy', markerfacecolor='navy', markersize=10,
                                  label=f'Previous Day Close: {prev_close}' if prev_close else f"Start Day: {df['close'].iloc[0]}")
    gain_loss_difference_patch = plt.Line2D([0], [0], marker='o', color=gain_loss_color, markerfacecolor=gain_loss_color, markersize=10,
                                       label=f'Change: {value_change}')
    daily_gain_loss_patch = plt.Line2D([0], [0], marker='o', color=gain_loss_color, markerfacecolor=gain_loss_color, markersize=10,
                                       label=f'Daily Gain/Loss: {percentage_change}%')

    legend = axes[0].legend(handles=[current_close_patch, prev_close_patch, gain_loss_difference_patch, daily_gain_loss_patch], loc='upper left')  # Changed order and added daily_gain_loss_patch
    legend.get_texts()[2].set_color(gain_loss_color)
    legend.get_texts()[3].set_color(gain_loss_color)
    legend.get_texts()[2].set_weight('bold')
    legend.get_texts()[3].set_weight('bold')

    # Save the modified figure with unique filename
    filename = f"temp_images/temp_candlestick_image_{index}.png"
    fig.savefig(filename, dpi=180, bbox_inches='tight')

    if is_last_image:
        # Load the saved image using PIL
        img = Image.open(filename)
        draw = ImageDraw.Draw(img)

        # Determine the location for the vertical line. Here, we draw the line near the right edge.
        # Adjust the values if needed.
        width, height = img.size
        line_x = width - 115  # 115 pixels from the right edge
        line_start = 0
        line_end = height

        # Draw the vertical line on the image
        draw.line([(line_x, line_start), (line_x, line_end)], fill='black', width=2)

        # Save the modified image
        img.save(filename)

    plt.close()
    gc.collect()

    return filename


def resize_image(img_path, target_size=(1088, 1920)):
    with Image.open(img_path) as img:
        img = img.resize(target_size, Image.ANTIALIAS)
        img.save(img_path)


def get_audio_filename():
    folder_path = "./audio/"
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    if not files:
        return None  # or handle empty folder differently if you prefer
    selected_file = random.choice(files)
    return f"{folder_path + selected_file}"


def create_video(image_list, audio_file=get_audio_filename(), output_filename_marker=None):
    if output_filename_marker == 'intraday':
        duration_of_candlestick_charts = 0.13
    elif output_filename_marker == 'quarterly':
        duration_of_candlestick_charts = 0.16
    elif output_filename_marker == 'six_months':
        duration_of_candlestick_charts = 0.15
    elif output_filename_marker == 'yearly':
        duration_of_candlestick_charts = 0.09
    else:
        raise ValueError("create_video() needs an output_filename input")

    log("Starting process to create video")
    # Resize images to ensure they have the same size
    for img_path in image_list:
        resize_image(img_path)

    intro_duration1 = 0.5  # Duration for the first intro image
    intro_duration2 = 1  # Duration for the second intro image
    intro_duration3 = 1.6  # Duration for the third intro image (with fade-out)
    final_image_duration = 2
    clips = []

    # First intro image without fade-out
    clips.append(ImageClip(image_list[0]).set_duration(intro_duration1))

    # Second intro image without fade-out
    clips.append(ImageClip(image_list[1]).set_duration(intro_duration2))

    # Third intro image with fade-out
    clips.append(
        ImageClip(image_list[2]).set_duration(intro_duration3).fx(fadeout.fadeout, 0.5))

    for filename in image_list[3:-1]:  # All images except the intro images and the last image
        clip = ImageClip(filename, duration=duration_of_candlestick_charts)
        clips.append(clip)
        clip.close()

    clips.append(ImageClip(image_list[-1], duration=final_image_duration))
    clips[-1].close()

    video = concatenate_videoclips(clips, method="compose")

    log("Adding audio to the file")
    audio = AudioFileClip(audio_file).subclip(0, video.duration)
    audio_with_fadeout = audio.fx(afx.audio_fadeout, duration=1.5)  # Fading out last 3 seconds
    final_audio = audio_with_fadeout.subclip(0, video.duration)
    video = video.set_audio(final_audio)

    log("Exporting final video")
    video.write_videofile(f"stock_replay_{output_filename_marker}_{datetime.datetime.now().date()}.mp4", fps=24)


def clean_temp_files():
    # Remove all files in /temp folder
    temp_files = glob.glob('./temp_images/*')
    for f in temp_files:
        try:
            os.remove(f)
        except Exception as e:
            print(f"Error deleting {f}: {e}")

    # Remove temp video files that are not stock output videos
    video_files = glob.glob('temp_video*.mp4')
    stock_output_files = glob.glob('stock*.mp4')
    for video in video_files:
        if video not in stock_output_files:
            try:
                os.remove(video)
            except Exception as e:
                print(f"Error deleting {video}: {e}")


def run_intraday_charts(symbols):
    for symbol in symbols:
        df = get_stock_data_to_plot(symbol, use_yfinance_data=True, period_to_chart='1m')
        prev_close = get_most_recent_close(symbol, days_back=1)
        intro_images = save_intro_images(symbol=symbol)
        images = list(intro_images)

        for i in range(len(df)):
            log(f"Making image {i} of {len(df)}")
            subset_df = df.iloc[:i + 1].copy()
            is_last_image = i == len(df) - 1
            img = save_candlestick_image(subset_df, i, is_last_image, prev_close=prev_close, chart_title=f"{symbol} Intraday Action")
            images.append(img)

        create_video(images, output_filename_marker='intraday')
        log(f"Finished {symbol} INTRADAY")


def run_quarterly_charts(symbols):
    for symbol in symbols:
        df = get_stock_data_to_plot(symbol, only_get_most_recent_day=False, period_to_chart='quarter')
        intro_images = save_intro_images(symbol=symbol, second_image_text='LAST 3 MONTHS')
        images = list(intro_images)

        for i in range(len(df)):
            log(f"Making image {i} of {len(df)}")
            subset_df = df.iloc[:i + 1].copy()
            is_last_image = i == len(df) - 1
            img = save_candlestick_image(subset_df, i, is_last_image, chart_title=f"{symbol} Last 3 Months")
            images.append(img)

        create_video(images, output_filename_marker='quarterly')
        log(f"Finished {symbol} QUARTERLY")


def run_six_months_charts(symbols):
    for symbol in symbols:
        df = get_stock_data_to_plot(symbol, only_get_most_recent_day=False, period_to_chart='six_months')
        intro_images = save_intro_images(symbol=symbol, second_image_text='LAST 6 MONTHS')
        images = list(intro_images)

        for i in range(len(df)):
            log(f"Making image {i} of {len(df)}")
            subset_df = df.iloc[:i + 1].copy()
            is_last_image = i == len(df) - 1
            img = save_candlestick_image(subset_df, i, is_last_image, chart_title=f"{symbol} Last 6 Months")
            images.append(img)

        create_video(images, output_filename_marker='six_months')
        log(f"Finished {symbol} SIX MONTHS")


def run_yearly_charts(symbols):
    for symbol in symbols:
        df = get_stock_data_to_plot(symbol, only_get_most_recent_day=False, period_to_chart='year')
        intro_images = save_intro_images(symbol=symbol, second_image_text='LAST 12 MONTHS')
        images = list(intro_images)

        for i in range(len(df)):
            log(f"Making image {i} of {len(df)}")
            subset_df = df.iloc[:i + 1].copy()
            is_last_image = i == len(df) - 1
            img = save_candlestick_image(subset_df, i, is_last_image, chart_title=f"{symbol} Last 12 Months")
            images.append(img)

        create_video(images, output_filename_marker='yearly')
        log(f"Finished {symbol} YEARLY")


def main():
    symbols = ['SPY']

    run_intraday_charts(symbols)
    gc.collect()

    run_quarterly_charts(symbols)
    gc.collect()

    run_six_months_charts(symbols)
    gc.collect()

    run_yearly_charts(symbols)
    gc.collect()

    clean_temp_files()

if __name__ == "__main__":
    main()