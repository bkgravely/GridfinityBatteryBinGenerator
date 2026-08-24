from .commandCreateBatteryBin import entry as commandCreateBatteryBin

commands = [
    commandCreateBatteryBin,
]


def start():
    for command in commands:
        command.start()


def stop():
    for command in commands:
        command.stop()
