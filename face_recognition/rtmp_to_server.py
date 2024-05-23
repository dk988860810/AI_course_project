import subprocess


def start_stream(camera_name, rtmp_server, stream_key):
    # Define FFmpeg command with reduced quality for faster streaming
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
        f'rtmp://{rtmp_server}/face/{stream_key}'
    ]

    try:
        # Run FFmpeg command in a subprocess
        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Continuously read from stderr to get error messages in real-time
        while True:
            output = process.stderr.readline()
            if output == b'' and process.poll() is not None:
                break
            if output:
                print(output.strip().decode('utf-8'))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Check if process exited with an error
        if process.returncode != 0:
            print("Error occurred while streaming.")
        else:
            print("Streaming finished.")


# Example usage
if __name__ == "__main__":
    camera_name = "HD Webcam"
    rtmp_server = "13.214.171.73"
    stream_key = "aws"

    start_stream(camera_name, rtmp_server, stream_key)
