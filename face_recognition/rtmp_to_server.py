import subprocess

def start_stream(camera_name, rtmp_server, stream_key):
    # Define FFmpeg command
    ffmpeg_command = [
        'ffmpeg',
        '-f', 'dshow',
        '-i', f'video={camera_name}',
        '-s', '640x360',  # Set resolution to 640x360
        '-r', '10',  # Set frame rate to 15 fps
        '-c:v', 'libx264',
        '-b:v', '300k',  # Set video bitrate to 500 kbps
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-f', 'flv',
        f'rtmp://{rtmp_server}/live/{stream_key}'
    ]
     
    # Run FFmpeg command in a subprocess
    process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait for process to finish (which should be never in this case, as it's streaming indefinitely)
    process.communicate()

    # Check if process exited with an error
    if process.returncode != 0:
        print("Error occurred while streaming.")
    else:
        print("Streaming finished.")

# Example usage
if __name__ == "__main__":
    camera_name = "Lenovo EasyCamera"
    rtmp_server = "13.214.171.73"
    stream_key = "stream_1"
    
    start_stream(camera_name, rtmp_server, stream_key)
