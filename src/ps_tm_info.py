output = 'busOutput'
input = 'busInput'
playback = 'busPlayback'


valuesThatAreToggles = ['mute', 'phase', 'phaserRight', 'phantom', 'instrument', 'pad', "msProc", "autoset", "loopback",
                        "stereo", "talkbackSel", "noTrim","cue", "recordEnable", "playChannel", "lowcutEnable",
                        "eqEnable","compexpEnable", "alevEnable"]


def parameterIsToggle(parameter:str) -> bool:
    return parameter in valuesThatAreToggles


def getChannelDataByIndex(self, layer: str, idx: int, key: str = ''):
    if key:
        return self.channelDataByName[layer][self.channelNamesByIndex[layer][idx]][key]
    else:
        return self.channelDataByName[layer][self.channelNamesByIndex[layer][idx]]