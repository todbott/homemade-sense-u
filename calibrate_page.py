def page(AcX, AcY, AcZ, GyX, GyY, GyZ, monitoring):

    return open("calibrate.html", "r").read().replace(" {", "{{").replace(" }", "}}").format(AcX = str(AcX),
                    AcY = str(AcY),
                    AcZ = str(AcZ),
                    GyX = str(GyX),
                    GyY = str(GyY),
                    GyZ = str(GyZ),
                    monitoring = monitoring)