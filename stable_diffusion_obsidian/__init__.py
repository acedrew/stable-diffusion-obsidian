import os
import re
from datetime import datetime
from collections import defaultdict
from glob import glob
from pathlib import Path
from typing import Dict, List
import png
import yaml


prompt_images = defaultdict(list)
negative_prompt_images = defaultdict(list)
date_images = defaultdict(list)


def find_images(root_path: str, output_type: str):
    return Path(root_path).glob(f"/{output_type}/**/*.png")

def get_prompt_components(img: png.Reader) -> tuple:
    for chunk in img.chunks():
        if chunk[0] == b"tEXt":
            data = chunk[1].decode("utf8", "replace")
            break
    for line in data.splitlines():
        if line.startswith("parameters"):
            prompt = line[11:]
            positive_words = re.split(", | |,", prompt)
        if line.startswith("Negative prompt:"):
            negative_prompt = line[17:]
            negative_words = re.split(", | |,", negative_prompt)
        if line.startswith("Steps:"):
            parameters = {
                k: v for k, v in [pair.split(": ") for pair in line.split(", ")]
            }
    return prompt, positive_words, negative_prompt, negative_words, parameters

def link_prompt(prompt: str, words: List[str], prompt_type: str) -> str:
    linked_prompt = prompt
    for word in set(words):
        linked_prompt = re.sub(
            f"(\s|^)({re.escape(word)})(,|, | |$)",
            f"\g<1>[\g<2>]({prompt_type}/\g<2>.md)\g<3>",
            linked_prompt,
        )
    return linked_prompt
    
def create_image_page(img_fp: Path, prompt: str, positive_words: List[str], negative_prompt: str, negative_words: List[str], parameters: dict):
    md_fp = img_fp.parents[5].joinpath(
        "obsidian",
        "oustcat",
        *img_fp.parts[-3:-1],
        img_fp.parts[-1].replace("png", "md"),
    )
    md_fp.parents[0].mkdir(parents=True, exist_ok=True)
    with open(md_fp, "w+") as md_file:
        md_file.write("---\n")
        md_file.write(
            yaml.dump(
                dict(
                    **{"tags": [img_fp.parts[-2], file_time.isoformat()]},
                    **parameters,
                )
            )
        )
        md_file.write("\n---\n")
        md_file.write(f'![[{Path("/outputs").joinpath(*img_fp.parts[-3:])}]]')
        linked_prompt = link_prompt(prompt, positive_words, "positive")
        negative_linked_prompt = link_prompt(negative_prompt, negative_words, "negative")
        md_file.write(f"\n## Prompt:\n{linked_prompt}\n")
        if negative_prompt is not None:
            md_file.write(
                f"\n## Negative Prompt:\n{negative_linked_prompt}\n"
            )
        md_file.write(
            f"\n## Parameters:\n```{yaml.dump(parameters)}```"
        )
    

def create_tag_files(tag_images: Dict[str, List[str]], tag_category: str):
    for word, images in prompt_images.items():
        if word:
            word_fp = img_fp.parents[5].joinpath(
                "obsidian", "oustcat", "words", tag_category, f"{word}.md"
            )
            word_fp.parents[0].mkdir(parents=True, exist_ok=True)
            with open(word_fp, "w+") as word_file:
                word_file.write(f'---\n{yaml.dump({"tags": [word]})}\n---\n')
                for image in set(images):
                    img_fp = Path(image)
                    word_file.write(
                        f'![[{Path("/outputs").joinpath(*img_fp.parts[-3:])}]]\n'
                    )
                    word_file.write(f'## [[{img_fp.parts[-1].replace("png", "md")}]]\n\n')


for img_fp in find_images(
    "/Users/shelli/Documents/stable-diffusion/stable-diffusion-webui/outputs/", "txt2img-images"
):
    negative_prompt = None
    prompt, positive_words, negative_prompt, negative_words, parameters = get_prompt_components(png.Reader(img_fp))
    file_time = datetime.fromtimestamp(os.path.getmtime(img_fp))
    file_time = file_time.replace(microsecond=0)
    file_date = file_time.date()
    for word in positive_words:
        images = prompt_images[word]
        images.append(img_fp)
        prompt_images[word] = images
    for word in negative_words:
        images = negative_prompt_images[word]
        images.append(img_fp)
        negative_prompt_images[word] = images
    date_images[file_date].append(img_fp)
    

    create_image_page(img_fp, prompt, positive_words, negative_prompt, negative_words, parameters)


create_tag_files(prompt_images, "positive")
create_tag_files(negative_prompt_images, "negative")
create_tag_files(date_images, "date")