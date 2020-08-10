import display

def text_centred(tft, text, vpos):
    tft.text(120 - int(tft.textWidth(text)/2), vpos - int(tft.fontSize()[1]/2), text)