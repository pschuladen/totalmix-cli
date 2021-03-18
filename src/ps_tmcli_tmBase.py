busOutput = 'busOutput'
busInput = 'busInput'
busPlayback = 'busPlayback'
total = 'total'



tmLayer = {
    'input': busInput,
    'playback': busPlayback,
    'output': busOutput
}


class TotalmixBaseClass():

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

    numberOfChannel = {
        'total': -1,
        busOutput: -1,
        busInput: -1,
        busPlayback: -1
    }

    fetchState = {
        'layout': False,
        'properties': False,
        'volumes': False
    }

    def setInitiateData(self):
        for _lay in self.channelNamesByIndex.keys():
            self.channelNamesByIndex[_lay] = list()
            self.channelDataByName[_lay] = dict()
            self.numberOfChannel[_lay] = -1

            if not _lay == busOutput:
                self.channelSends = dict()
                self.outputReceives = dict()

        self.numberOfChannel[total] = -1

        for _attri in self.fetchState:
            self.fetchState[_attri] = False


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


    def getNumberTmChannel(self, layer:str=total) -> int:
        return self.numberOfChannel[layer]


