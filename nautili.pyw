#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil

from nautili.menus import MainMenu
from nautili import settings

if __name__ == "__main__":
    if os.path.exists(settings.TMP_DIR):
        shutil.rmtree(settings.TMP_DIR)
    m = MainMenu()
    m.run()
