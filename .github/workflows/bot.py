from telegram import Update, InputMediaVideo
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests
import os
import re
import time
from tqdm import tqdm
from moviepy.editor import VideoFileClip

TOKEN = '7122805926:AAHHice8Ja2wxqUz1r6ggxZfi5jrpd1KbyM'
DOWNLOAD_PATH = './downloads/'

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def start(update: Update, context: CallbackContext):
    update.message.reply_text('Send me a direct link to download the file.')

def download_file(update: Update, context: CallbackContext):
    url = update.message.text
    file_name = sanitize_filename(url.split('/')[-1])
    file_path = os.path.join(DOWNLOAD_PATH, file_name)

    os.makedirs(DOWNLOAD_PATH, exist_ok=True)

    try:
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024

        progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True, unit_divisor=1024, desc='Downloading')

        start_time = time.time()
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(block_size):
                if chunk:
                    file.write(chunk)
                    progress_bar.update(len(chunk))
                    elapsed_time = time.time() - start_time
                    speed = (progress_bar.n / elapsed_time) / 1024  # Speed in KB/s
                    update.message.reply_text(f"Download Progress: {progress_bar.n / total_size * 100:.2f}%\nSpeed: {speed:.2f} KB/s", parse_mode='Markdown')

        progress_bar.close()

        # Check if the file is a video and convert it if necessary
        if file_name.lower().endswith(('.mp4', '.mov', '.avi')):
            video_clip = VideoFileClip(file_path)
            converted_file_path = file_path.rsplit('.', 1)[0] + '.mp4'
            video_clip.write_videofile(converted_file_path, codec='libx264')

            os.remove(file_path)  # Remove the original file
            file_path = converted_file_path

        # Send the file back to the user
        if file_name.lower().endswith(('.mp4', '.mov', '.avi')):
            with open(file_path, 'rb') as video_file:
                update.message.reply_video(video=video_file)
        else:
            with open(file_path, 'rb') as file:
                update.message.reply_document(document=file)

        # Clean up the file after sending
        os.remove(file_path)

    except Exception as e:
        update.message.reply_text(f"An error occurred: {e}")

def main():
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, download_file))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
