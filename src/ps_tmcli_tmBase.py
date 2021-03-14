busOutput = 'busOutput'
busInput = 'busInput'
busPlayback = 'busPlayback'

class TotalmixBaseClass():
    busOutput = 'busOutput'
    busInput = 'busInput'
    busPlayback = 'busPlayback'

    channelLayoutFetched = False
    channelPropertiesFetched = False
    channelVolumesFetched =False

    channelDataByName = {
        busOutput: {},
        busInput: {},
        busPlayback: {}
    }
    channelNamesByIndex = {
        busOutput: [],
        busInput: [],
        busPlayback: []
    }

    outputVolumes = {}
    channelSends = {
        busInput: {},
        busPlayback: {}
    }
    outputReceives = {
        busInput: {},
        busPlayback: {}
    }

    numberTmChannel = -1
    numberChannelInLayer = {
        busOutput: -1,
        busInput: -1,
        busPlayback: -1
    }



    valuesThatAreToggles = ['mute', 'phase', 'phaserRight', 'phantom', 'instrument', 'pad', "msProc", "autoset",
                            "loopback",
                            "stereo", "talkbackSel", "noTrim", "cue", "recordEnable", "playChannel", "lowcutEnable",
                            "eqEnable", "compexpEnable", "alevEnable"]

    def parameterIsToggle(self, parameter: str) -> bool:
        return parameter in self.valuesThatAreToggles

    volume = 'volume'
    pan = 'pan'
    mute = 'mute'
    solo = 'solo'
    trackname = 'trackname'
    select = 'select'

    m1_parameters = {
        volume: volume,
        pan: pan,
        trackname: trackname,
        mute: 'mute/1/',
        solo: 'solo/1/',
        select: 'select/1/'
    }

    parameterInMode1 = [volume, pan, mute, solo, trackname, select]

    def evalBestModeForParam(self, parameter:str) -> int:
        return 2
        #TODO:implement mode 1
        # if parameter in self.parameterInMode1:
        #     return 1
        # else:
        #     return 2


    def getChannelDataByIndex(self, layer: str, idx: int, key: str = ''):
        if key:
            return self.channelDataByName[layer][self.channelNamesByIndex[layer][idx]][key]
        else:
            return self.channelDataByName[layer][self.channelNamesByIndex[layer][idx]]

    def getNumberChannelOfLayer(self, layer:str=busOutput, respectStereo:bool=True) -> int:

        if respectStereo:
            _chSet = set()
            for _ch in self.channelNamesByIndex[layer]:
                _chSet.add(_ch)
            return len(_chSet)
        else:
            return len(self.channelNamesByIndex[layer])