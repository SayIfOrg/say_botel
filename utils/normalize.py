from typing import Counter
from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag


def childs(element: Tag) -> bool:
    for child in element.children:
        if type(child) == Tag:
            yield child


def newline_after():
    def wrapper(elements: ResultSet):
        for element in elements:
            element.insert_after("\n")

    return wrapper


newline_after = newline_after()


def replace_tag(tag: str):
    def wrapper(elements: ResultSet):
        for element in elements:
            element.name = tag

    return wrapper


def remove_tag():
    def wrapper(elements: ResultSet):
        for element in elements:
            element.unwrap()

    return wrapper


remove_tag = remove_tag()


def list_tag():
    def wrapper(elements: ResultSet):
        for element in elements:
            count = 0
            for child in childs(element):
                if child.name == "li":
                    count += 1
                    child.insert_before(
                        "\N{bullet}" if element.name == "ul" else f"{count}) "
                    )
                    child.insert_after("\n")
                    child.unwrap()
            element.insert_after("\n")
            element.unwrap()

    return wrapper


list_tag = list_tag()

tags = (
    ("h1", [newline_after, replace_tag("strong")]),
    ("h2", [newline_after, replace_tag("strong")]),
    ("h3", [newline_after, replace_tag("strong")]),
    ("p", [newline_after, remove_tag]),
    ("ol", [list_tag]),
    ("ul", [list_tag]),
)


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag, actions in tags:
        elements = soup.find_all(tag)
        for action in actions:
            action(elements)
    return str(soup)
