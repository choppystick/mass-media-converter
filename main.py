import subprocess
import os
import tempfile
import shutil


def extract_video_portions(input_file, timestamps, output_file):
    print(f"Starting video extraction process...")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Create a temporary directory for intermediate files
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Created temporary directory: {temp_dir}")

        # Create a list to store the names of intermediate files
        intermediate_files = []

        # Process each timestamp pair
        for i, (start, end) in enumerate(timestamps):
            output = os.path.join(temp_dir, f"part_{i}.mp4")
            intermediate_files.append(output)

            if end.lower() == "end":
                cmd = [
                    "ffmpeg",
                    "-i", input_file,
                    "-ss", start,
                    "-c", "copy",
                    output
                ]
            else:
                cmd = [
                    "ffmpeg",
                    "-i", input_file,
                    "-ss", start,
                    "-to", end,
                    "-c", "copy",
                    output
                ]

            print(f"Extracting portion {i + 1}: {start} to {end}")
            subprocess.run(cmd, check=True, capture_output=True, text=True)

            if not os.path.exists(output):
                raise FileNotFoundError(f"Failed to create intermediate file: {output}")
            print(f"Created intermediate file: {output}")

        # Create a concat demuxer file
        concat_file = os.path.join(temp_dir, "concat.txt")
        with open(concat_file, "w") as f:
            for file in intermediate_files:
                f.write(f"file '{os.path.basename(file)}'\n")
        print(f"Created concat file: {concat_file}")

        # Use the concat demuxer to join the files
        concat_cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            output_file
        ]
        print("Running final concatenation command...")
        result = subprocess.run(concat_cmd, check=True, capture_output=True, text=True, cwd=temp_dir)
        print("FFmpeg concat output:")
        print(result.stdout)
        print(result.stderr)

    if not os.path.exists(output_file):
        raise FileNotFoundError(f"Failed to create output file: {output_file}")

    print(f"Video portions extracted and combined into {output_file}")
    print(f"Output file size: {os.path.getsize(output_file)} bytes")


input_file = "I LOVE YOU ZUTOMAYO.mp4"
output_file = "D:\\output.mp4"
timestamps = [
    ("00:16:10", "00:37:17"),
    ("00:40:41", "01:23:09"),
    ("01:29:08", "01:58:55"),
    ("01:59:55", "end")
]

extract_video_portions(input_file, timestamps, output_file)
