import ujson

def load_settings(settings_file):
    """ Load a JSON encoded settings file

    Args:
        settings_file (string): Filename to load

    Returns:
        ujson-object: The loaded settings
    """    
    try:
        fd = open(settings_file)
        encoded = fd.read()
        fd.close()
        settings = ujson.loads(encoded)
        return settings
    except Exception as e:
        print(settings_file + ": read error: " + str(e))