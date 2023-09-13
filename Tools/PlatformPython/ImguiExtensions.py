# -*- coding: utf-8 -*-

# Classes and functions useful as an addition to imgui base functions

# I recommend importing this module "as imgui_ex"

import imgui

class ImguiFontSet:
    """Holds a list of loaded fonts"""
    # def __init__(self, imguiIO):
    def __init__(self):
        # self.io = imguiIO
        io = imgui.get_io()

        # Cascadia
        self.cascadiaCodePL_16 = io.fonts.add_font_from_file_ttf("toolAssets/Fonts/Cascadia/ttf/CascadiaCodePL.ttf", 16)
        self.cascadiaCodePL_20 = io.fonts.add_font_from_file_ttf("toolAssets/Fonts/Cascadia/ttf/CascadiaCodePL.ttf", 20)
        self.cascadiaCodePL_24 = io.fonts.add_font_from_file_ttf("toolAssets/Fonts/Cascadia/ttf/CascadiaCodePL.ttf", 24)

        self.cascadiaCodePL_SemiLight_16 = io.fonts.add_font_from_file_ttf("toolAssets/Fonts/Cascadia/ttf/static/CascadiaCodePL-SemiLight.ttf", 16)

        self.cascadiaMonoPL_18 = io.fonts.add_font_from_file_ttf("toolAssets/Fonts/Cascadia/ttf/CascadiaMonoPL.ttf", 18)
        self.cascadiaMonoPL_20 = io.fonts.add_font_from_file_ttf("toolAssets/Fonts/Cascadia/ttf/CascadiaMonoPL.ttf", 20)

        # Futura
        self.futura_medium_bt_18 = io.fonts.add_font_from_file_ttf("toolAssets/Fonts/Futura/futura medium bt.ttf", 18)
        self.futura_medium_bt_20 = io.fonts.add_font_from_file_ttf("toolAssets/Fonts/Futura/futura medium bt.ttf", 20)
        self.futura_heavy_bt_20 = io.fonts.add_font_from_file_ttf("toolAssets/Fonts/Futura/futura Heavy font.ttf", 20)
        self.futura_heavy_bt_24 = io.fonts.add_font_from_file_ttf("toolAssets/Fonts/Futura/futura Heavy font.ttf", 24)

        # What you should actually use
        # self.title =    self.cascadiaCodePL_24
        self.title =    self.futura_heavy_bt_24

        # self.heading =  self.cascadiaCodePL_20
        self.heading =  self.futura_heavy_bt_20
        
        # self.body =     self.cascadiaCodePL_SemiLight_16
        self.body =     self.futura_medium_bt_18

        self.mono =     self.cascadiaMonoPL_18

    def pushTitleFont(self):
        imgui.push_font(self.title)
    def pushHeadingFont(self):
        imgui.push_font(self.heading)
    def pushBodyFont(self):
        imgui.push_font(self.body)
    def pushMonoFont(self):
        imgui.push_font(self.mono)
    def popFont(self):
        imgui.pop_font()

class rgba_color():
    """0.0->1.0 Red/Green/Blue/Alpha color"""
    r = 1.0
    g = 1.0
    b = 1.0
    a = 1.0
    def __init__(self,r,g,b,a=1.0):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

"""A set of colors that have good contrast and colorblind-safeness"""
contrast_colors = {
    "White"   :     rgba_color( 255.0/255.0, 255.0/255.0, 255.0/255.0 ),
    "Yellow"  :     rgba_color( 255.0/255.0, 225.0/255.0, 25.0/255.0 ), 
    "Blue"    :     rgba_color(0.0/255.0, 130.0/255.0, 200.0/255.0),    
    "Orange"  :     rgba_color(245.0/255.0, 130.0/255.0, 48.0/255.0),   
    "Pink"    :     rgba_color(250.0/255.0, 190.0/255.0, 190.0/255.0),  
    "Purple"  :     rgba_color(230.0/255.0, 190.0/255.0, 255.0/255.0),  
    "Grey"    :     rgba_color(128.0/255.0, 128.0/255.0, 128.0/255.0)   
}