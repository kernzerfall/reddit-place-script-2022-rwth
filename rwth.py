#!/usr/bin/env pyhton3

from io import BytesIO
import threading
import http
from time import sleep
import requests
from PIL import Image
import os
from loguru import logger


class RwthTumCollab():
    default_thread_interval = 5 * 60 # 5 mins
    _target_image_url = "https://github.com/etonaly/pixel/raw/main/output.png"
    _rgb_transparent_new = (69, 42, 0, 255)
    _image_file = "image.png"
    _image_lock = ".image.png.lock"

    def __init__(self):
        self._scriptdir = os.path.dirname(os.path.realpath(__file__))

    def updateImage(self) -> None:
        resp = requests.get(url=RwthTumCollab._target_image_url)
        if resp.status_code != http.HTTPStatus.OK:
            raise Exception(f"{RwthTumCollab._target_image_url} konnte nicht geladen werden. HTTP: {resp.status_code}")
        img = Image.open(BytesIO(resp.content))
        img.convert("RGBA")

        data = img.load()
        for x in range(img.size[0]):
            for y in range(img.size[1]):
                if data[x,y][0] == self._rgb_transparent_new[0] and data[x,y][1] == self._rgb_transparent_new[1] and data[x,y][2] == self._rgb_transparent_new[2]:
                    raise Exception("Bild hat schon Pixel mit Farbe RGB(69, 420, 0)")
                if data[x, y][3] == 0:
                    data[x, y] = RwthTumCollab._rgb_transparent_new

        RwthTumCollab.WaitForImgUnlock()
        RwthTumCollab.LockImage()

        try:
            img.save(os.path.join(self._scriptdir, self._image_file), bitmap_format='png')
        except:
            RwthTumCollab.UnlockImage()
            raise Exception("Bild konnte nicht gespeichert werden")
        else:
            logger.info(f"{self._image_file} gespeichert")



        RwthTumCollab.UnlockImage()


    def WaitForImgUnlock():
        scriptdir = os.path.dirname(os.path.realpath(__file__))
        while os.path.isfile(os.path.join(scriptdir, RwthTumCollab._image_lock)):
            sleep(1)

    def LockImage():
        scriptdir = os.path.dirname(os.path.realpath(__file__))

        RwthTumCollab.WaitForImgUnlock()
        img_file_lock = os.open(os.path.join(scriptdir, RwthTumCollab._image_lock), os.O_CREAT | os.O_RDWR)
        os.close(img_file_lock)

    def UnlockImage():
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), RwthTumCollab._image_lock)
        if os.path.isfile(path):
            os.remove(path)

    def BuildThread(self, interval_seconds = default_thread_interval) -> threading.Timer:
        return threading.Timer(interval_seconds, self.updateImage)
        

if __name__ == "__main__":
    thread = RwthTumCollab().BuildThread(1)
    thread.start()
    thread.join()
    