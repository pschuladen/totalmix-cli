valuesThatAreToggles = ['mute', 'phase', 'phaserRight', 'phantom', 'instrument', 'pad', "msProc", "autoset", "loopback",
                        "stereo", "talkbackSel", "noTrim","cue", "recordEnable", "playChannel", "lowcutEnable",
                        "eqEnable","compexpEnable", "alevEnable"]


def parameterIsToggle(parameter:str) -> bool:
    return parameter in valuesThatAreToggles

