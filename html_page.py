def web_page(AcX, AcY, AcZ, GyX, GyY, GyZ):

    p = open("html_page.html", "r").read()
    doubled = p.replace(" {", "{{").replace(" }", "}}")

    page = """<!DOCTYPE html>
                <html>""" + doubled.format(AcX = str(AcX),
                    AcY = str(AcY),
                    AcZ = str(AcZ),
                    GyX = str(GyX),
                    GyY = str(GyY),
                    GyZ = str(GyZ)) + """
                </html>
            """
    return page