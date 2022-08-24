from posixpath import split
from bs4 import BeautifulSoup

tags = (
    ("h1", "tag-strong"),
    ("h2", "tag-strong"),
    ("h3", "tag-strong"),
    ("p", "val-\n"),
    ("ol", "val-\n"),
    ("ul", "val-\n"),
)


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag, replacement in tags:
        elements = soup.find_all(tag)
        action, val = replacement.split("-")[0], replacement.split("-")[1]
        if action == "tag":
            if not val:
                [element.replaceWith(element.text + "\n") for element in elements]
            else:
                for element in elements:
                    element.name = val
                    element.string = element.string + "\n"
        elif action == "val":
            [element.replaceWith(element.text + val) for element in elements]
    return soup
