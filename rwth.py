#!/usr/bin/env pyhton3

from distutils.log import error
from io import BytesIO
from json import JSONDecoder
import threading
import http
from time import sleep
import requests
from PIL import Image
import os
from loguru import logger

class RoamingConfigUpdater():
    _default_thread_interval = 3 * 60 # 3 mins
    _target_json_url = "https://georgar.de/api/place/getConfig"
    _ran_once = False
    _img_updater = None

    roamingConfig = None

    def __init__(self):
        self._scriptdir = os.path.dirname(os.path.realpath(__file__))
        self._img_updater = ImageUpdater()
        self._img_updater._default_thread_interval = self._default_thread_interval

    def getConfig(self) -> None:
        resp = requests.get(self._target_json_url, verify="certificates.pem")
        
        if resp.status_code != http.HTTPStatus.OK:
            if not self._ran_once:
                raise Exception(f"{self._target_json_url}:: konnte nicht geladen werden. HTTP: {resp.status_code}")
            else:
                logger.error(f"{self._target_json_url}:: konnte nicht geladen werden. HTTP: {resp.status_code}")

        cfg = None
        try:
            cfg = resp.json()
        except:
            if not self._ran_once:
                raise Exception(f"{self._target_json_url}:: konnte nicht als JSON geladen werden: {resp.content}")
            else:
                logger.error(f"{self._target_json_url}:: konnte nicht als JSON geladen werden: {resp.content}")

        if cfg["image_start_coords"] != None and cfg["internal_start_coords"] != None:
            self.roamingConfig = cfg
            self._ran_once = True
            logger.info(f"Roaming config geladen")
        else:
            if not self._ran_once:
                raise Exception(f"{self._target_json_url}::[\"image_start_coords\"] existiert nicht")
            else:
                logger.error(f"{self._target_json_url}::[\"image_start_coords\"] existiert nicht")

    def run(self):
        self.getConfig()
        self._img_updater.updateImage()
    
    def BuildThread(self, interval_seconds=_default_thread_interval) -> threading.Timer:
        return threading.Timer(interval_seconds, self.run)


class ImageUpdater():
    _default_thread_interval = 6 * 60 # 6 mins
    _target_image_url = "https://georgar.de/api/place/getImage"
    _rgb_transparent_new = (69, 42, 0, 255)
    _image_file = "image.png"
    _image_lock = ".image.png.lock"

    def __init__(self):
        self._scriptdir = os.path.dirname(os.path.realpath(__file__))

    def updateImage(self) -> None:
        resp = requests.get(self._target_image_url, verify="certificates.pem")
        if resp.status_code != http.HTTPStatus.OK:
            raise Exception(f"{ImageUpdater._target_image_url} konnte nicht geladen werden. HTTP: {resp.status_code}")
        img = Image.open(BytesIO(resp.content))
        img.convert("RGBA")

        data = img.load()
        for x in range(img.size[0]):
            for y in range(img.size[1]):
                if data[x,y][0] == self._rgb_transparent_new[0] and data[x,y][1] == self._rgb_transparent_new[1] and data[x,y][2] == self._rgb_transparent_new[2]:
                    raise Exception("Bild hat schon Pixel mit Farbe RGB(69, 42, 0)")
                if data[x, y][3] == 0:
                    data[x, y] = ImageUpdater._rgb_transparent_new

        ImageUpdater.WaitForImgUnlock()
        ImageUpdater.LockImage()

        try:
            img.save(os.path.join(self._scriptdir, self._image_file), bitmap_format='png')
        except:
            ImageUpdater.UnlockImage()
            raise Exception("Bild konnte nicht gespeichert werden")
        else:
            logger.info(f"{self._image_file} gespeichert")



        ImageUpdater.UnlockImage()


    def WaitForImgUnlock():
        scriptdir = os.path.dirname(os.path.realpath(__file__))
        while os.path.isfile(os.path.join(scriptdir, ImageUpdater._image_lock)):
            sleep(1)

    def LockImage():
        scriptdir = os.path.dirname(os.path.realpath(__file__))

        ImageUpdater.WaitForImgUnlock()
        img_file_lock = os.open(os.path.join(scriptdir, ImageUpdater._image_lock), os.O_CREAT | os.O_RDWR)
        os.close(img_file_lock)

    def UnlockImage():
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), ImageUpdater._image_lock)
        if os.path.isfile(path):
            os.remove(path)
        

if __name__ == "__main__":
    thread = ImageUpdater().BuildThread(1)
    thread.start()
    thread.join()
    