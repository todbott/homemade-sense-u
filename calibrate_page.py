def page():

    return open("calibrate.html", "r").read().replace(" {", "{{").replace(" }", "}}")