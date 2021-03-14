import ps_tm_info as ti

class TotalmixBaseClass():

    channelDataByName = {
        ti.output: {},
        ti.input: {},
        ti.playback: {}
    }
    channelNamesByIndex = {
        ti.output: [],
        ti.input: [],
        ti.playback: []
    }

    outputVolumes = {}
    channelSends = {
        ti.input: {},
        ti.playback: {}
    }
    outputReceives = {
        ti.input: {},
        ti.playback: {}
    }

    numberTmChannel = -1

    output = 'busOutput'
    input = 'busInput'
    playback = 'busPlayback'

    valuesThatAreToggles = ['mute', 'phase', 'phaserRight', 'phantom', 'instrument', 'pad', "msProc", "autoset",
                            "loopback",
                            "stereo", "talkbackSel", "noTrim", "cue", "recordEnable", "playChannel", "lowcutEnable",
                            "eqEnable", "compexpEnable", "alevEnable"]

    def parameterIsToggle(cls, parameter: str) -> bool:
        return parameter in cls.valuesThatAreToggles

    def getChannelDataByIndex(self, layer: str, idx: int, key: str = ''):
        if key:
            return self.channelDataByName[layer][self.channelNamesByIndex[layer][idx]][key]
        else:
            return self.channelDataByName[layer][self.channelNamesByIndex[layer][idx]]
