import display

class TTGO(display.TFT):

    __init__(self):
        super().__init__(display.TFT.ST7789,
                         bgr = False,                                      # Normal (not BGR) colour mode
                         rot = display.TFT.LANDSCAPE,                      # Display rotation
                         backl_pin = 4, backl_on = 1,                      # Backlight on
                         miso = 17, mosi = 19, clk = 18, cs = 5, dc = 16)  # SPI interface pins
        super().setwin(40, 52, 320, 240)
        super().font(display.TFT.FONT_Comic) # Yeah - comic sans - but it's big, bold and readable

    text_centred(self, text, vpos):
        super().text(120 - int(super().textWidth(text)/2), 
                     vpos - int(super().fontSize()[1]/2), 
                     text))