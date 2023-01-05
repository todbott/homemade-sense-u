def page(AcX, AcY, AcZ, GyX, GyY, GyZ, monitoring):

    p = open("calibrate.html", "r").read()
    doubled = p.replace(" {", "{{").replace(" }", "}}")

    page = """<!DOCTYPE html>
                <html>""" + doubled.format(AcX = str(AcX),
                    AcY = str(AcY),
                    AcZ = str(AcZ),
                    GyX = str(GyX),
                    GyY = str(GyY),
                    GyZ = str(GyZ),
                    monitoring = monitoring) + """
                </html>
            """
    return page