import ps_tmcli_tmBase as tmbase
# import ps_tmcli_osccom as tmosc
from ps_tmcli_osccom import TmOscCommunicator as Tmosc
from functools import partial

def dumdumdummyfunc(*args):
    return False

class TmAction_Base(tmbase.TotalmixBaseClass):

    def __init__(self):
        self.tasks = []


class TmAction_Set(TmAction_Base):

    def __init__(self, cliArgs):
        super(TmAction_Set, self).__init__()

        # self.targetChannelString = cliArgs.channel
        self.layerToSet = cliArgs.layer
        self.parameter = cliArgs.parameter
        self.value = cliArgs.value
        self.targetChannel = set()

        self.getTargetChannelSetFromString(cliArgs.channel)



    def createTasksList(self, osccom:[Tmosc], whenFinished=dumdumdummyfunc):
        mode = self.evalBestModeForParam(self.parameter)

        if len(osccom) > 0:
            _tmosc: Tmosc = osccom[0]
            _tmosc.taskStack = self.tasks
            self.tasks.append(partial(_tmosc.oscS_goToLayer, self.layerToSet, mode))

            for _ch in self.targetChannel:
                self.tasks.append(partial(_tmosc.oscS_goToChannelIndex, _ch))
                self.tasks.append(partial(_tmosc.checkValue, self.parameter, self.value))

            self.tasks.append(whenFinished)

        else:
            print('error setting parameter. No controller set')


    def getTargetChannelSetFromString(self, channelString: str) -> set:
        targetChs_, _chToVerify = self.parseTargetChannels(channelString)
        for c in self.verifyTargetChannels(_chToVerify):
            targetChs_.add(c)
        return targetChs_


    def parseTargetChannels(self, inputChannelString: str) -> (set, set):
        channelsToSet_ = set()
        verifyThisChannels_ = set()

        if inputChannelString in ['', 'all', ':']:
            verifyThisChannels_.add('all')
        else:
            _channelsRaw = inputChannelString.split(',')

            _channelStrings = set()

            for _ch in _channelsRaw:
                try:
                    channelsToSet_.add(int(_ch) - 1)
                except:
                    _channelStrings.add(_ch)

            for _chStr in _channelStrings:
                try:
                    _chStr = _chStr.split(':')
                    # print('splitted', _chR)
                    try:
                        for c in range(int(_chStr[0]) - 1, int(_chStr[1])):
                            channelsToSet_.add(c)
                    except:
                        if len(_chStr) == 2:
                            verifyThisChannels_.add((_chStr[0], _chStr[1]))
                        else:
                            print('something wrong with channel range', _chStr)
                except:
                    channelsToSet_.add(_chStr)

        return (channelsToSet_, verifyThisChannels_)


    def verifyTargetChannels(self, channelStrToVerify) -> set:

        outputSet = set()
        while (channelStrToVerify):
            chRange = channelStrToVerify.pop()
            if chRange == 'all':
                print('all', self.numberTmChannel, 'channels')
                for c in range(self.numberTmChannel):
                    outputSet.add(c)
            else:
                try:
                    lowIdx = self.channelNamesByIndex[self.layerToSet].index(chRange[0])
                    highIdx = self.channelNamesByIndex[self.layerToSet].index(chRange[1])

                    for c in range(lowIdx, highIdx + 1):
                        outputSet.add(c)
                except:
                    print('Channels', chRange, 'not found in TM Data and will not be set')

        _limitReached = False
        _channelsToRemove = set()
        _channelsToAdd = set()
        for c in outputSet:
            if c > 0 and c % 2:
                chIsStereo = bool(self.getChannelDataByIndex(self.layerToSet, c, 'stereo'))
                if chIsStereo:
                    _channelsToRemove.add(c)
                    _channelsToAdd.add(c - 1)

            if c >= self.numberTmChannel:
                _channelsToRemove.add(c)
                _limitReached = True
        for c in _channelsToRemove:
            outputSet.remove(c)
        for c in _channelsToAdd:
            outputSet.add(c)

        if _limitReached:
            print('channel limit is', self.numberTmChannel, 'higher channels will not be set')

        return outputSet


class TmAction_Route(TmAction_Base):
    pass
#TODO: implement route



