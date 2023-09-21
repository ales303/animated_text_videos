from manim import *
from manim.utils.rate_functions import linear
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip

def process_scene(scene_name, image_pairs, output_filename, total_length_minutes, total_length_seconds):
    detected_items = []
    image1 = cv2.imread(image_pairs[0])
    
    for color, (scene, item_type, appear_time, disappear_time, custom_text, font_name, font_size, output_color) in color_dictionary.items():
        if scene != scene_name and scene != 'all':
            continue
        lower_bound = np.array(color, dtype=np.uint8)
        upper_bound = np.array(color, dtype=np.uint8)
        mask = cv2.inRange(image1, lower_bound, upper_bound)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            detected_items.append((item_type, appear_time, disappear_time, custom_text, font_name, font_size, output_color, x, y, w, h))
            
    class AnimateDetectedItems(Scene):
        def construct(self):
            current_time = 0
            aspect_ratio = 800 / 600
            second_image = ImageMobject(image_pairs[1]).scale(0.5)
            self.add(second_image)
            
            for item_type, appear_time, disappear_time, custom_text, font_name, font_size, output_color, x, y, w, h in detected_items:
                manim_x = (x - 400) / 400 * aspect_ratio
                manim_y = (300 - y) / 300
                appear_minutes, appear_seconds = map(int, appear_time.split(":"))
                appear_time_seconds = appear_minutes * 60 + appear_seconds
                disappear_minutes, disappear_seconds = map(int, disappear_time.split(":"))
                disappear_time_seconds = disappear_minutes * 60 + disappear_seconds
                self.wait(appear_time_seconds - current_time)
                
                if item_type == "text":
                    obj = Text(custom_text, font=font_name).move_to([manim_x, manim_y, 0]).scale(font_size).set_color(output_color)
                    self.play(Create(obj, rate_func=linear))
                elif item_type == "arrow":
                    obj = Arrow(start=[manim_x, manim_y, 0], end=[manim_x + w / 800, manim_y - h / 600], color=output_color)
                elif item_type == "circle":
                    obj = Circle().move_to([manim_x, manim_y, 0]).set_width(w / 800).set_height(h / 600).set_color(output_color)
                elif item_type == "oval":
                    obj = Ellipse(width=w / 800, height=h / 600).move_to([manim_x, manim_y, 0]).set_color(output_color)
                elif item_type == "question_mark":
                    obj = Text("?", font=font_name).move_to([manim_x, manim_y, 0]).scale(font_size).set_color(output_color)
                    self.play(Create(obj, rate_func=linear), Rotate(obj, angle=2*PI))
                
                self.play(ShowCreation(obj))
                self.wait(disappear_time_seconds - appear_time_seconds)
                self.play(FadeOut(obj))
                current_time = disappear_time_seconds
    
    config.file_writer_config["output_file"] = output_filename
    scene = AnimateDetectedItems()
    scene.render()

# Manim Configuration
config.pixel_height = 1080
config.pixel_width = 1920
config.frame_height = 8.0
config.frame_width = 14.22

# Color Dictionary
color_dictionary = {
    (255, 0, 0): ('all', 'text', "0:05", "0:07", "Hello", "Arial", 0.5, RED),
    (0, 255, 0): ('scene1', 'arrow', "0:10", "0:12", "", "", 0, GREEN),
    (0, 0, 255): ('scene2', 'circle', "0:15", "0:17", "", "", 0, BLUE),
    (255, 255, 0): ('scene2', 'oval', "0:20", "0:22", "", "", 0, YELLOW),
    (0, 255, 255): ('all', 'question_mark', "0:25", "0:27", "", "Arial", 0.5, CYAN)
}

# Scenes to Process
scenes_to_process = {
    "scene1": {
        "image_pairs": ("image1_for_detection.png", "image1_for_annotation.png"),
        "output_filename": "output_scene1",
        "total_length": ("0", "30")
    },
    "scene2": {
        "image_pairs": ("image2_for_detection.png", "image2_for_annotation.png"),
        "output_filename": "output_scene2",
        "total_length": ("0", "30")
    }
}

# Process Each Scene
video_files = []
for scene_name, scene_details in scenes_to_process.items():
    image_pairs = scene_details["image_pairs"]
    output_filename = scene_details["output_filename"]
    total_length_minutes, total_length_seconds = scene_details["total_length"]
    process_scene(scene_name, image_pairs, output_filename, total_length_minutes, total_length_seconds)
    video_files.append(f"{output_filename}.mp4")

# Merge Videos and Add Audio
final_audio = "your_audio.mp3"
final_clip = concatenate_videoclips([VideoFileClip(f) for f in video_files])
final_clip.audio = AudioFileClip(final_audio).subclip(0, final_clip.end)
final_clip.write_videofile("final_output.mp4")
