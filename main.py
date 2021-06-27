import json
import logging
import urllib.request

import PySimpleGUI as sg
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException


# Setup for AnkiConnect


def request(action, **params):
    return {"action": action, "params": params, "version": 6}


def invoke(action, **params):
    request_json = json.dumps(request(action, **params)).encode("utf-8")
    response = json.load(
        urllib.request.urlopen(
            urllib.request.Request("http://localhost:8765", request_json)
        )
    )
    if len(response) != 2:
        raise Exception("response has an unexpected number of fields")
    if "error" not in response:
        raise Exception("response is missing required error field")
    if "result" not in response:
        raise Exception("response is missing required result field")
    if response["error"] is not None:
        raise Exception(response["error"])
    return response["result"]


try:
    decks = invoke("deckNames")
    models = invoke("modelNames")
except Exception as e:
    sg.popup_error(
        "Please Run Anki before and make sure AnkiConnect is Running properly."
    )
    raise Exception("AnkiConnect is not running properly")

layout = [
    [sg.Text("Auto Auto Note Adder")],
    [sg.Text("Choose your deck"), sg.Combo(decks, key="_DECK_COMBO_")],
    [sg.Text("Choose your deck type"), sg.Combo(models, key="_DECK_TYPE_COMBO_")],
    [sg.Text("Type word"), sg.InputText(key="_WORD_INPUT_TEXT_")],
    [sg.OK(), sg.Button("Quit")],
]

# sg.theme("DarkAmber")
window = sg.Window("Anki Auto Note Adder", layout)
while True:
    event, values = window.read()
    if event in (sg.WINDOW_CLOSED, "Quit"):
        break
    if event == "OK":
        try:
            for value in values.values():
                if value == "":
                    sg.popup_error("Make sure to fill every field")
                    raise Exception("one or more fields are not filled")
        except Exception:
            continue
        firefox_options = Options()
        firefox_options.headless = True
        driver = webdriver.Firefox(
            executable_path="./geckodriver.exe", options=firefox_options
        )

        driver.get(
            "https://www.oxfordlearnersdictionaries.com/definition/english/"
            + values["_WORD_INPUT_TEXT_"]
        )
        print(driver.current_url)
        try:
            word = driver.find_element_by_xpath("//h1[@hclass='headword']").text
            pronunciation = driver.find_element_by_xpath(
                "//div[@class='phons_n_am']/span[@class='phon']"
            ).text
            definition = "<br>".join(
                [
                    f"{i + 1}.{x.text}"
                    for i, x in enumerate(
                        driver.find_elements_by_xpath("//span[@class='def']")
                    )
                ]
            )
            example = "<br><br>".join(
                list(
                    map(
                        lambda x: x.text,
                        driver.find_elements_by_xpath("//span[@class='x']"),
                    )
                )
            )
        except NoSuchElementException:
            sg.popup_error("Could not find the word on Oxford Dictionary")
            break
        print(f"{word=} {pronunciation=} {definition=} {example=}")

        if values["_DECK_TYPE_COMBO_"] == "Basic (and reversed card)":
            invoke(
                "addNote",
                note={
                    "deckName": values["_DECK_COMBO_"],
                    "modelName": values["_DECK_TYPE_COMBO_"],
                    "fields": {
                        "Word": word,
                        "Pronunciation": pronunciation,
                        "Meaning": definition,
                        "Ex": example,
                    },
                    "options": {"allowDuplicate": True},
                    "tags": ["AnkiAutoNoteAdder"],
                },
            )
        sg.popup("Note successfully added")

window.close()

logging.debug(f"{decks=} {models=}")

# invoke("addNote", {"deckName": "English",})
