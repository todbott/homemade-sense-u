import Operator

# Warning seconds of 60 and 120 caused too many alerts, so I'm trying 90 and 150 now
Operator.SensorController("remote", 10, 80, 100).main()