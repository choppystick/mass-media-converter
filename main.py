import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from heic2png import HEIC2PNG
import multiprocessing
from multiprocessing import Pool, Manager
import threading
from queue import Queue, Empty
import time


def get_file_counts(input_dir):
    """Get counts of images and videos in the input directory"""
    image_ext = ('.HEIC', '.HEIF')
    heic_files = [f for f in os.listdir(input_dir) if f.endswith(image_ext)]
    mov_files = [f for f in os.listdir(input_dir) if f.endswith('.MOV')]
    other_files = [f for f in os.listdir(input_dir) if
                   not (f.endswith(image_ext) or f.endswith('.MOV') or f.endswith('.AAE'))]
    return len(heic_files), len(mov_files), len(other_files), heic_files, mov_files, other_files


def convert_directory(input_dir, output_dir, progress_dict, dir_index):
    """Enhanced function for directory conversion with file management"""
    results = []

    # Get file counts
    image_ext = ('.HEIC', '.HEIF')
    heic_files = [f for f in os.listdir(input_dir) if f.endswith(image_ext)]
    mov_files = [f for f in os.listdir(input_dir) if f.endswith('.MOV')]
    other_files = [f for f in os.listdir(input_dir) if
                   not (f.endswith(image_ext) or f.endswith('.MOV') or f.endswith('.AAE'))]

    total_files = len(heic_files) + len(mov_files) + len(other_files)
    if total_files == 0:
        return results

    files_processed = 0

    # Convert HEIC/HEIF files
    for file in heic_files:
        try:
            img = HEIC2PNG(os.path.join(input_dir, file), quality=100)
            output_file = os.path.join(output_dir, f"{file[:-5]}.png")
            img.save(output_file)
            files_processed += 1
            progress_dict[dir_index] = files_processed
            results.append(("success", f"Converted image: {file}"))
        except Exception as e:
            files_processed += 1
            progress_dict[dir_index] = files_processed
            results.append(("error", f"Error converting {file}: {str(e)}"))

    # Convert MOV files
    for file in mov_files:
        try:
            input_path = os.path.join(input_dir, file)

            # Ensure output path has .mp4 extension and handle spaces in path
            base_name = os.path.splitext(file)[0]
            output_path = os.path.join(output_dir, f"{base_name}.mp4")

            # Fixed ffmpeg command with proper quotation and parameters
            ffmpeg_command = (
                f'ffmpeg -y -i "{input_path}" -vf '
                'zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,'
                'tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,'
                f'format=yuv420p -x264-params colormatrix=bt709 -crf 21 -c:a copy "{output_path}" '
                '-hide_banner -loglevel error -stats'
            )

            os.system(ffmpeg_command)
            files_processed += 1
            progress_dict[dir_index] = files_processed
            results.append(("success", f"Converted video: {file}"))
        except Exception as e:
            files_processed += 1
            progress_dict[dir_index] = files_processed
            results.append(("error", f"Error converting {file}: {str(e)}"))

    # Copy other files
    for file in other_files:
        try:
            input_path = os.path.join(input_dir, file)
            output_path = os.path.join(output_dir, file)
            import shutil
            shutil.copy2(input_path, output_path)  # copy2 preserves metadata
            files_processed += 1
            progress_dict[dir_index] = files_processed
            results.append(("success", f"Copied file: {file}"))
        except Exception as e:
            files_processed += 1
            progress_dict[dir_index] = files_processed
            results.append(("error", f"Error copying {file}: {str(e)}"))

    return results


def cleanup_output_directory(output_dir):
    """Clean up output directory by removing AAE files and handling duplicates"""
    results = []

    # Initialize counters
    aae_count = 0
    duplicate_count = 0

    print("\n=== Cleanup Summary ===")
    print(f"Cleaning directory: {output_dir}")

    # Remove AAE files
    print("\nRemoving AAE files:")
    aae_files = [f for f in os.listdir(output_dir) if f.endswith('.AAE')]
    if not aae_files:
        print("No AAE files found")
    else:
        print(f"Found {len(aae_files)} AAE files:")
        for file in aae_files:
            try:
                os.remove(os.path.join(output_dir, file))
                print(f"- Removed: {file}")
                results.append(("cleanup", f"Removed AAE file: {file}"))
                aae_count += 1
            except Exception as e:
                print(f"- Error removing {file}: {str(e)}")
                results.append(("error", f"Error removing AAE file {file}: {str(e)}"))

    # Handle duplicates
    print("\nChecking for duplicates:")
    files = os.listdir(output_dir)
    seen_files = {}  # Changed to store full filename as key
    duplicates = []

    for file in files:
        # Skip AAE files as they're already handled
        if file.endswith('.AAE'):
            continue

        if file in seen_files:
            duplicates.append((file, seen_files[file]))  # Store both duplicate and original
        else:
            seen_files[file] = file

    if not duplicates:
        print("No duplicate files found")
    else:
        print(f"Found {len(duplicates)} duplicate files:")
        for duplicate, original in duplicates:
            try:
                os.remove(os.path.join(output_dir, duplicate))
                print(f"- Removed: {duplicate} (duplicate of {original})")
                results.append(("cleanup", f"Removed duplicate file: {duplicate} (duplicate of {original})"))
                duplicate_count += 1
            except Exception as e:
                print(f"- Error removing {duplicate}: {str(e)}")
                results.append(("error", f"Error removing duplicate file {duplicate}: {str(e)}"))

    # Print final summary
    print("\nCleanup Summary:")
    print(f"- AAE files removed: {aae_count}")
    print(f"- Duplicate files removed: {duplicate_count}")
    print(f"- Total files removed: {aae_count + duplicate_count}")
    print("=== End Cleanup Summary ===\n")

    return results


def cleanup_all_directories(directory_data):
    """Clean up all output directories and provide a total summary"""
    total_aae_removed = 0
    total_duplicates_removed = 0

    for _, output_dir in directory_data:
        cleanup_output_directory(output_dir)

    print("\n=== Final Cleanup Statistics ===")
    print(f"Total AAE files removed: {total_aae_removed}")
    print(f"Total duplicate files removed: {total_duplicates_removed}")
    print(f"Total files removed: {total_aae_removed + total_duplicates_removed}")
    print("=== End Final Statistics ===\n")


def browse_directory(entry):
    directory = filedialog.askdirectory()
    if directory:
        entry.delete(0, tk.END)
        entry.insert(0, directory)


class MediaConverterGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Multi-Folder Media Converter")
        self.window.geometry("800x600")

        # List of input/output directory pairs
        self.directory_pairs = []

        # Create main container
        self.main_container = ttk.Frame(self.window)
        self.main_container.pack(fill='both', expand=True, padx=10, pady=10)

        # Directory list frame
        self.dir_list_frame = ttk.LabelFrame(self.main_container, text="Directory Pairs")
        self.dir_list_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Total progress frame
        self.total_progress_frame = ttk.Frame(self.main_container)
        self.total_progress_frame.pack(fill='x', padx=5, pady=5)

        self.total_progress_label = ttk.Label(self.total_progress_frame, text="Total Progress: ")
        self.total_progress_label.pack(side='left')

        self.total_progress = ttk.Progressbar(self.total_progress_frame, mode='determinate')
        self.total_progress.pack(side='left', fill='x', expand=True, padx=5)

        self.progress_text = ttk.Label(self.total_progress_frame, text="0/0 files")
        self.progress_text.pack(side='left')

        # Scrollable frame for directory pairs
        self.canvas = tk.Canvas(self.dir_list_frame)
        self.scrollbar = ttk.Scrollbar(self.dir_list_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Buttons frame
        self.button_frame = ttk.Frame(self.main_container)
        self.button_frame.pack(fill='x', pady=10)

        self.add_pair_button = ttk.Button(self.button_frame, text="Add Directory Pair", command=self.add_directory_pair)
        self.add_pair_button.pack(side='left', padx=5)

        self.remove_pair_button = ttk.Button(self.button_frame, text="Remove Selected",
                                             command=self.remove_selected_pair)
        self.remove_pair_button.pack(side='left', padx=5)

        self.convert_button = ttk.Button(self.button_frame, text="Convert All", command=self.start_conversion)
        self.convert_button.pack(side='right', padx=5)

        # Status text
        self.status_frame = ttk.LabelFrame(self.main_container, text="Status")
        self.status_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.status_text = tk.Text(self.status_frame, height=10, width=50)
        self.status_text.pack(fill='both', expand=True)

        # Message queue for status updates
        self.status_queue = Queue()
        self.progress_queue = Queue()
        self.window.after(100, self.check_queues)

        # Store all directory buttons
        self.directory_buttons = []

    def remove_selected_pair(self):
        to_remove = []
        buttons_to_remove = []  # New list to track buttons to remove

        for pair in self.directory_pairs:
            if pair['check'].get():
                # Find the input and output buttons associated with this pair
                frame = pair['frame']
                frame_buttons = [btn for btn in self.directory_buttons
                                 if str(btn.master) == str(frame)]
                buttons_to_remove.extend(frame_buttons)

                # Destroy the frame
                pair['frame'].destroy()
                to_remove.append(pair)

        # Remove the pairs
        for pair in to_remove:
            self.directory_pairs.remove(pair)

        # Remove the buttons from directory_buttons list
        for btn in buttons_to_remove:
            if btn in self.directory_buttons:
                self.directory_buttons.remove(btn)

    def add_directory_pair(self):
        pair_frame = ttk.Frame(self.scrollable_frame)
        pair_frame.pack(fill='x', padx=5, pady=5)

        # Checkbox for selection
        var = tk.BooleanVar()
        check = ttk.Checkbutton(pair_frame, variable=var)
        check.pack(side='left')

        # Input directory
        input_entry = ttk.Entry(pair_frame)
        input_entry.pack(side='left', fill='x', expand=True, padx=5)

        input_button = ttk.Button(
            pair_frame,
            text="Input",
            command=lambda: browse_directory(input_entry)
        )
        input_button.pack(side='left')
        self.directory_buttons.append(input_button)

        # Output directory
        output_entry = ttk.Entry(pair_frame)
        output_entry.pack(side='left', fill='x', expand=True, padx=5)

        output_button = ttk.Button(
            pair_frame,
            text="Output",
            command=lambda: browse_directory(output_entry)
        )
        output_button.pack(side='left')
        self.directory_buttons.append(output_button)

        # Progress bar
        progress_bar = ttk.Progressbar(pair_frame, mode='determinate')
        progress_bar.pack(side='left', padx=5, fill='x', expand=True)

        self.directory_pairs.append({
            'frame': pair_frame,
            'check': var,
            'input': input_entry,
            'output': output_entry,
            'progress': progress_bar,
            'input_button': input_button,  # Store references to buttons
            'output_button': output_button  # Store references to buttons
        })

    def update_status(self, message):
        self.status_queue.put(message)

    def process_directories(self, directory_data, total_files):
        with Manager() as manager:
            # Create a shared dictionary to track progress
            progress_dict = manager.dict()

            # Initialize progress for each directory
            for i in range(len(directory_data)):
                progress_dict[i] = 0

            # Create a progress update function
            def update_progress():
                while True:
                    try:
                        current_total = sum(progress_dict.values())
                        self.progress_queue.put((current_total, total_files))
                        time.sleep(0.1)  # Update every 100ms

                    except:
                        break

            # Start progress update thread
            progress_thread = threading.Thread(target=update_progress, daemon=True)
            progress_thread.start()

            # Create pool and process directories
            try:
                with Pool() as pool:
                    # Create tasks with progress tracking
                    tasks = [(input_dir, output_dir, progress_dict, i)
                             for i, (input_dir, output_dir) in enumerate(directory_data)]

                    # Start processing
                    results = []
                    for result in pool.starmap(convert_directory, tasks):
                        results.append(result)

                    return results
            finally:
                # Ensure final progress is updated
                current_total = sum(progress_dict.values())
                self.progress_queue.put((current_total, total_files))

    def check_queues(self):
        try:
            # Check status queue
            while not self.status_queue.empty():
                message = self.status_queue.get_nowait()
                self.status_text.insert(tk.END, message + "\n")
                self.status_text.see(tk.END)

            # Check progress queue
            while not self.progress_queue.empty():
                try:
                    current, total = self.progress_queue.get_nowait()
                    if total > 0:  # Prevent division by zero
                        percentage = (current / total) * 100
                        self.total_progress['value'] = percentage
                        self.progress_text['text'] = f"{current}/{total} files ({percentage:.1f}%)"
                        self.window.update_idletasks()

                except Empty:
                    pass

        except Exception as e:
            print(f"Error in check_queues: {str(e)}")

        finally:
            self.window.after(50, self.check_queues)  # Check more frequently (50ms)

    def start_conversion(self):
        # Collect directory pairs and count files
        directory_data = []
        total_images = 0
        total_videos = 0
        total_other = 0
        conversion_summary = []

        print("\n=== Conversion Summary ===")
        print("Processing the following directories:\n")

        for pair in self.directory_pairs:
            input_dir = pair['input'].get()
            output_dir = pair['output'].get()

            if input_dir and output_dir:
                # Count files in this directory
                num_images, num_videos, num_other, image_files, video_files, other_files = get_file_counts(input_dir)
                total_images += num_images
                total_videos += num_videos
                total_other += num_other

                # Print directory information
                print(f"\nInput Directory:  {input_dir}")
                print(f"Output Directory: {output_dir}")
                print(f"Files to process:")
                print(
                    f"- Images: {num_images} ({', '.join(image_files) if num_images < 6 else ', '.join(image_files[:5]) + '...'})")
                print(
                    f"- Videos: {num_videos} ({', '.join(video_files) if num_videos < 6 else ', '.join(video_files[:5]) + '...'})")
                print(
                    f"- Other Files: {num_other} ({', '.join(other_files) if num_other < 6 else ', '.join(other_files[:5]) + '...'})")
                print("-" * 50)

                directory_data.append((input_dir, output_dir))
                conversion_summary.append({
                    'input': input_dir,
                    'output': output_dir,
                    'images': num_images,
                    'videos': num_videos,
                    'other': num_other
                })

        if not directory_data:
            messagebox.showerror("Error", "No valid directory pairs found")
            return

        # Fix the total_files calculation to include other files
        total_files = total_images + total_videos + total_other

        # Print total summary
        print(f"\nTotal files to convert:")
        print(f"- Total Images: {total_images}")
        print(f"- Total Videos: {total_videos}")
        print(f"- Other Files: {total_other}")
        print(f"- Grand Total:  {total_files}")
        print("\n=== End Summary ===\n")

        # Create detailed confirmation message
        confirm_msg = f"Ready to convert:\n\n"
        confirm_msg += f"Total Images: {total_images}\n"
        confirm_msg += f"Total Videos: {total_videos}\n"
        confirm_msg += f"Other Files: {total_other}\n"
        confirm_msg += f"Total Files: {total_files}\n\n"
        confirm_msg += "Start conversion?"

        # Confirm conversion
        response = messagebox.askyesno("Confirm Conversion", confirm_msg)
        if not response:
            print("Conversion cancelled by user")
            return

        # Disable all buttons during conversion
        self.convert_button['state'] = 'disabled'
        self.add_pair_button['state'] = 'disabled'
        self.remove_pair_button['state'] = 'disabled'
        for button in self.directory_buttons:
            button['state'] = 'disabled'

        # Reset and initialize progress bar
        self.total_progress['value'] = 0
        self.progress_text['text'] = f"0/{total_files} files"

        print("\nStarting conversion process...")

        def conversion_thread():
            try:
                # Process directories concurrently
                results = self.process_directories(directory_data, total_files)

                # Update GUI with conversion results
                for pair_results in results:
                    for status, message in pair_results:
                        self.status_queue.put(message)
                        print(message)

                # Clean up output directories
                print("\nStarting cleanup process...")
                self.status_queue.put("\nStarting cleanup process...")

                cleanup_all_directories(directory_data)

                # Print completion message
                print("\nConversion and cleanup completed!")
                self.status_queue.put("\nConversion and cleanup completed!")

                # Re-enable buttons
                self.window.after(0, lambda: self.convert_button.configure(state='normal'))
                self.window.after(0, lambda: self.add_pair_button.configure(state='normal'))
                self.window.after(0, lambda: self.remove_pair_button.configure(state='normal'))
                for button in self.directory_buttons:
                    self.window.after(0, lambda b=button: b.configure(state='normal'))
                self.window.after(0, lambda: messagebox.showinfo("Complete", "All conversions and cleanup completed!"))

            except Exception as e:
                error_msg = f"Error during conversion: {str(e)}"
                self.status_queue.put(error_msg)
                print(error_msg)

                # Re-enable buttons on error
                self.window.after(0, lambda: self.convert_button.configure(state='normal'))
                self.window.after(0, lambda: self.add_pair_button.configure(state='normal'))
                self.window.after(0, lambda: self.remove_pair_button.configure(state='normal'))
                for button in self.directory_buttons:
                    self.window.after(0, lambda b=button: b.configure(state='normal'))

        # Start the conversion thread (fixed indentation)
        threading.Thread(target=conversion_thread, daemon=True).start()

    def run(self):
        self.window.mainloop()


if __name__ == '__main__':
    multiprocessing.freeze_support()  # Required for Windows executable
    app = MediaConverterGUI()
    app.run()
