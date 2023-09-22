import cv2
from time import sleep
from manim import Scene, Text, Circle, Arrow, config
from manim.animation.creation import Create
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip


RED = "#FF0000"
GREEN = "#00FF00"
BLUE = "#0000FF"
YELLOW = "#FFFF00"
PURPLE = "#800080"


def detect_objects(image_path):
    img = cv2.imread(image_path)
    detected_items = []

    for item, attributes in color_dictionary.items():
        mask = cv2.inRange(img, attributes["color"], attributes["color"])
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            center = (int((2 * x + w) / 2), int((2 * y + h) / 2))
            detected_items.append({
                "type": item,
                "center": center,
                "size": (w, h),
                "scene_name": attributes["scene_name"]
            })

    return detected_items


class ProcessedImageScene(Scene):
    def __init__(self, detected_items, image_path, total_length_minutes, total_length_seconds, *args, **kwargs):
        self.detected_items = detected_items
        self.image_path = image_path
        self.total_length_minutes = total_length_minutes
        self.total_length_seconds = total_length_seconds
        super().__init__(*args, **kwargs)

    def construct(self):
        for item in self.detected_items:
            obj = None
            attributes = color_dictionary.get(item["type"], {})

            if "scene_name" in attributes:
                scene = attributes["scene_name"]
                if scene != self.name and scene != 'all':
                    continue

            start_time = attributes.get("start_time", 0)
            end_time = attributes.get("end_time", self.total_length_minutes * 60 + self.total_length_seconds)

            if item["type"] == "text":
                obj = Text("Your Text Here", font=attributes["font"], size=attributes["size"]).set_color(
                    attributes["output_color"]).move_to(item["center"])
                self.play(Create(obj), rate_func=lambda t: smooth(1 if start_time <= t <= end_time else 0))

            elif item["type"] == "circle":
                obj = Circle(radius=item["size"][0] / 2).set_color(attributes["output_color"]).move_to(item["center"])
                self.play(Create(obj), rate_func=lambda t: smooth(1 if start_time <= t <= end_time else 0))

            elif item["type"] == "arrow":
                obj = Arrow(start=item["center"],
                            end=(item["center"][0], item["center"][1] + item["size"][1])).set_color(
                    attributes["output_color"])
                self.play(Create(obj), rate_func=lambda t: smooth(1 if start_time <= t <= end_time else 0))

            elif item["type"] == "question_mark":
                obj = Text("?").set_color(attributes["output_color"]).scale(3).move_to(item["center"])
                self.play(obj.animate.rotate(PI / 2).set_color(attributes["output_color"]),
                          rate_func=lambda t: smooth(1 if start_time <= t <= end_time else 0))

        self.wait(self.total_length_minutes * 60 + self.total_length_seconds)


def process_scene(scene_name, image_pairs, output_filename, total_length_minutes, total_length_seconds):
    detected_items = detect_objects(image_pairs[0])
    config.output_file = output_filename
    scene = ProcessedImageScene(detected_items, image_pairs[1], total_length_minutes, total_length_seconds)
    scene.render()


def concatenate_scenes(scene_filenames, audio_file, output_filename):
    clips = [VideoFileClip(scene_filename) for scene_filename in scene_filenames]
    final_clip = concatenate_videoclips(clips)
    audio = AudioFileClip(audio_file)
    final_clip = final_clip.set_audio(audio)
    final_clip.write_videofile(output_filename)


color_dictionary = {
    "text": {
        "color": (255, 0, 0),
        "font": "Times New Roman",
        "size": 1,
        "output_color": RED,
        "start_time": 5,
        "end_time": 15,
        "scene_name": "all"
    },
    "circle": {
        "color": (22,154,185),
        "output_color": GREEN,
        "start_time": 10,
        "end_time": 20,
        "scene_name": "scene1"
    },
    "arrow": {
        "color": (0, 0, 255),
        "output_color": BLUE,
        "start_time": 15,
        "end_time": 25,
        "scene_name": "scene2"
    },
    "question_mark": {
        "color": (255, 255, 0),
        "output_color": YELLOW,
        "start_time": 20,
        "end_time": 30,
        "scene_name": "scene1"
    }
}

scenes_to_process = {
    "scene1": {
        "image_pairs": ("image1_drawing.png", "image1_raw.png"),
        "output_filename": "scene1_output.mp4",
        "total_length_minutes": 0,
        "total_length_seconds": 30
    }
}

if __name__ == "__main__":
    scene_outputs = []
    for scene_name, scene_data in scenes_to_process.items():
        process_scene(scene_name, scene_data["image_pairs"], scene_data["output_filename"],
                      scene_data["total_length_minutes"], scene_data["total_length_seconds"])
        scene_outputs.append(scene_data["output_filename"])

    print("Sleeping")
    sleep(10)

    concatenate_scenes(scene_outputs, "audio.mp3", "final_output.mp4")
