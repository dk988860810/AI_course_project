import subprocess

def start_stream(camera_name, rtmp_server, stream_key):
    # Define FFmpeg command
    ffmpeg_command = [
        'ffmpeg',
        '-f', 'dshow',
        '-i', f'video={camera_name}',
        '-c:v', 'libx264',
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
    rtmp_server = "54.162.189.102"
    stream_key = "aws"
    
    start_stream(camera_name, rtmp_server, stream_key)
