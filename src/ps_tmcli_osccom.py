from oscpy.server import OSCThreadServer
from oscpy.client import OSCClient
from functools import partial
from threading import Timer
# import ps_tm_info as tmi
import ps_tmcli_tmBase as tmbase



# output = 'busOutput'
# input = 'busInput'
# playback = 'busPlayback'

def dumdumdummyfunc(*args):
    return False

class TmOscCommunicator(tmbase.TotalmixBaseClass):

    channelPropertiesFetched = False
    # channelNamesByIndex = {}
    channelDataByName = {}

    chLimitReached = False
    checkChannelLimit = False
    lastChName = None

    numberFader = 0
    countFader = True

    timeoutFunction = dumdumdummyfunc
    timeoutT = 0.5

    finishedJobFunction = dumdumdummyfunc

    def __init__(self, ipaddress, port, answer_port, database:dict=None, timeoutFunction=dumdumdummyfunc):

        self.taskStack = list()
        self.currentLayer = ''
        self.currentChIndex = -1
        self.selectedSubmixIndex = -1

        self.currentChannelName = ''

        self.tmpChannelData = {}
        self.tmpChannelDataMode1 = {'vol': [], 'pan': [], 'name': []}

        self.timeout = Timer(10, dumdumdummyfunc)

        self.settingTargetValue = False
        self.targetParameter = ''
        self.targetValue = -1.
        self.targetOsc = ''
        self.targetChannels = set()

        self.timeoutFunction = timeoutFunction

        self.toTM = OSCClient(address=ipaddress, port=port)
        self.oscServer = OSCThreadServer(default_handler=self.oscR_receivedTmData)
        self.oscServer.listen(address='0.0.0.0', port=answer_port, default=True)

        self.setupOscBindings()



    def setupOscBindings(self):

        for i in [1, 2]:
            for bus in ['busInput', 'busPlayback', 'busOutput']:
                oscAddr = ('/' + str(i) + '/' + bus).encode()
                self.oscServer.bind(oscAddr, partial(self.oscR_setLayer, bus, i))

            sOsc = '/{}/labelSubmix'.format(i)
            self.oscServer.bind(sOsc.encode(), partial(self.oscR_selectedSubmix, i))

        self.oscServer.bind(b'/2/trackname', partial(self.oscR_setChannelName))

        for i in range(64):
            sOSc = '/1/labelS{}'.format(i + 1)
            self.oscServer.bind(sOSc.encode(), partial(self.oscR_countRemoteFader, i + 1))
            for _key, _par in self.m1_parameters.items():
                #     if _key, _par in self.m1_parameters.items():
                sOsc = '/1/{}{}'.format(_par, i+1)
                self.oscServer.bind(sOsc.encode(), partial(self.oscR_tmpChannelDataMode1, i, _par))

            # sOSc = '/1/volume{}'.format(i + 1)
            # self.oscServer.bind(sOSc.encode(), partial(self.oscR_tmpChannelDataMode1, i, 'vol'))
            # sOsc = '/1/pan{}'.format(i + 1)
            # self.oscServer.bind(sOsc.encode(), partial(self.oscR_tmpChannelDataMode1, i, 'pan'))
            # sOsc = '/1/trackname{}'.format(i + 1)
            # self.oscServer.bind(sOsc.encode(), partial(self.oscR_tmpChannelDataMode1, i, 'name'))

        for x in range(64):
            sOsc = '/1/micgain{}Val'.format(x+1)
            self.oscServer.bind(sOsc.encode(), self.oscR_checkTmOutMode1complete, x + 1)

        # if database:
        #     self.channelNamesByIndex = database['channel indices']
        #     self.channelDataByName = database['channel properties']



    def oscR_receivedTmData(self, address, *args):
        sOsc = address.decode()
        if sOsc[0:2] == '/2':
            _param = sOsc[3:]
            value = args[0] if type(args[0])==float else args[0].decode()
            self.tmpChannelData[_param] = value
            # try:
            #     self.tmpChannelData[_param] = args[0].decode()
            # except:
            #     self.tmpChannelData[_param] = args[0]

            if self.settingTargetValue:
                # self.checkValue(_param)
                self.checkTaskStack()
        else:
            return


    def oscR_setLayer(self, layer: str, _mode: int, *args):

        if args[0] == 1.0:
            self.currentLayer = layer


    def oscR_selectedSubmix(self, mode: int, *args):

        global selectedSubmixName, selectedSubmixIndex, changingChannel
        selectedSubmixName = args[0].decode()

        if self.channelPropertiesFetched:
            selectedSubmixIndex = self.channelNamesByIndex[self.busOutput].index(selectedSubmixName)

        if mode == 2:
            #TM output finished
            self.checkTaskStack()
        elif mode == 1:
            return
            # if self.countFader:
            #     self.countFader = False


    def oscR_setChannelName(self, *args):
        chName = args[0].decode()
        if self.checkChannelLimit:
            self.chLimitReached = self.currentChannelName == chName
        self.currentChannelName = chName


    def oscR_countRemoteFader(self, nFader, *args):
        # Evaluate number of remote fader

        if nFader == 1:
            self.tmpChannelDataMode1.clear()

        while len(self.tmpChannelDataMode1) < nFader:
            for _, _layer in self.tmpChannelDataMode1.items():
                _layer.append(dict())


    def oscR_tmpChannelDataMode1(self, fader:int, key:str, *args):

        try:
            value = args[0].decode()
        except:
            value = args[0]

        self.tmpChannelDataMode1[fader][key] = value

        if fader == 1 and key == 'name':
            self.currentChannelName = value
            if value in self.channelNamesByIndex[self.currentLayer]:
                self.currentChIndex = self.channelNamesByIndex[self.currentLayer].index(value)


    def oscR_checkTmOutMode1complete(self, chN:int):
        if chN == self.numberFader:
            self.checkTaskStack()

    def scheduleTimeOut(self, lastFunction=None, t=5):
        return Timer(t, self.timeoutFunction, args=[lastFunction])

    def checkTaskStack(self, *args):
        self.timeout.cancel()

        if self.taskStack:
            self.timeout = self.scheduleTimeOut(self.taskStack[0])
            self.timeout.start()
            self.taskStack.pop(0)()
        else:
            print('no tasks on stack')
            timeout = self.scheduleTimeOut()
            timeout.start()

    def initTmpData(self):
        self.tmpChannelData.clear()
        self.currentChannelName = ''
        for _, _list in self.tmpChannelDataMode1.items():
            _list.clear()


    def oscS_goToLayer(self, layer: str, mode: int = 2):
        self.initTmpData()
        sOsc = '/{}/{}'.format(mode, layer)
        self.toTM.send_message(sOsc.encode(), [1.0])


    def oscS_goToChannelIndex(self, index: int):
        # self.currentChIndex = index
        self.toTM.send_message(b'/setBankStart', [float(index)])


    def oscS_goToNextChannel(self):
        if self.getDataOfSelectedChannel()['stereo'] == 1.0:
            self.currentChIndex = self.currentChIndex + 2
        else:
            self.currentChIndex = self.currentChIndex + 1

        self.toTM.send_message(b'/2/track+', [1.0])


    def oscS_previousChannel(self, mode:int=2):
        if mode == 2:
            self.toTM.send_message(b'/2/track-', [1.0])
        else:
            self.toTM.send_message(b'/1/track+', [1.0])


    def oscS_goToNextBank(self):
        self.toTM.send_message(b'/1/bank+', [1.0])


    def oscS_previousBank(self):
        self.toTM.send_message(b'/1/bank-', [1.0])


    def oscS_selectSubmix(self, outChannelIdx:int):

        if not self.selectedSubmixIndex == outChannelIdx:
            self.toTM.send_message(b'/setSubmix', [float(outChannelIdx)])
            # global timeout
            if self.timeout.is_alive():
                self.timeout.cancel()
            self.timeout = Timer(self.timeoutT, self.timeoutFunction)
            self.timeout.start()
        else:
            self.checkTaskStack()


    def getChannelDataByIndex(self, layer: str, idx: int, key: str = ''):
        if key:
            return self.channelDataByName[layer][self.channelNamesByIndex[layer][idx]][key]
        else:
            return self.channelDataByName[layer][self.channelNamesByIndex[layer][idx]]


    def goToFirstChannel_wBanks(self, mode:int=1):
        if self.currentChannelName == self.lastChName:
            self.checkTaskStack()
        else:
            self.taskStack.insert(0, partial(self.goToFirstChannel_wBanks, mode))
            self.oscS_previousBank()


    def getDataOfSelectedChannel(self) -> dict:
        return self.channelDataByName[self.currentLayer][self.currentChannelName]


    def checkValue(self, parameter, value):
        if parameter:
            if self.tmpChannelData[parameter] == value:
                self.settingTargetValue = False
                self.checkTaskStack()
                # self.setValuesForTargetChannels()
            else:
                self.settingTargetValue = True
                self.taskStack.insert(0, partial(self.checkValue, parameter, value))
                if self.parameterIsToggle(self.targetParameter):
                    self.oscS_toggleValue(self.targetOsc)
                else:
                    self.oscS_doSetValue(self.targetOsc, float(self.targetValue))
        else:
            print('no target parameter specified')

    def checkMultipleValues(self):
        #TODO:implement
        pass

    def oscS_doSetValue(self, oscAd, value):
        self.toTM.send_message(oscAd, [value])


    def oscS_toggleValue(self, oscAd):
        self.toTM.send_message(oscAd, [1.0])


    # def setValuesForTargetChannels(self):
    #     if self.targetChannels:
    #         c = self.targetChannels.pop()
    #         self.taskStack.append(self.checkValue)
    #         self.oscS_goToChannelIndex(c)
    #
    #     else:
    #         print('finished setting values')
    #         self.finishedJobFunction()


    def fetchChannelProperties(self):

        if self.chLimitReached:
            self.chLimitReached = False
            self.checkTaskStack()
        else:
            self.channelNamesByIndex[self.currentLayer].append(self.currentChannelName)
            if self.tmpChannelData['stereo'] == 1.0:
                self.channelNamesByIndex[self.currentLayer].append(self.currentChannelName)
            self.channelDataByName[self.currentLayer][self.currentChannelName] = self.tmpChannelData.copy()
            # self.tmpChannelData.clear()
            self.initTmpData()
            self.checkChannelLimit = True
            self.taskStack.insert(0, self.fetchChannelProperties)

            self.oscS_goToNextChannel()

    #TODO: Reimplement fetch Channel Volume
    def initiateVolumeFetch(self):
        print('caution volume fetching not implemented yet')
    #     global tmpChannelDataMode1, channelSends, outputReceives, outputVolumes
    #     countedFader = numberFader
    #     for idx in range(len(tmpChannelDataMode1['name'].keys())):
    #         chName = tmpChannelDataMode1['name'][idx]
    #         if chName == 'n.a.':
    #             countedFader = idx
    #             break
    #
    #         chIdx = channelNamesByIndex[currentLayer].index(chName)
    #         chDic = createChanVolDic(tmpChannelDataMode1['vol'][idx],
    #                                  tmpChannelDataMode1['pan'][idx])
    #         if currentLayer == output:
    #             chDic['name'] = chName
    #             chDic['index'] = chIdx
    #             outputVolumes[chIdx] = chDic
    #             outputVolumes[chName] = chDic
    #         else:
    #             outputIndex = selectedSubmixIndex
    #             if not chIdx in channelSends[currentLayer].keys():
    #                 channelSends[currentLayer][chIdx] = {}
    #             if not outputIndex in outputReceives[currentLayer].keys():
    #                 outputReceives[currentLayer][outputIndex] = {}
    #             channelSends[currentLayer][chIdx][selectedSubmixIndex] = chDic
    #             outputReceives[currentLayer][outputIndex][chIdx] = chDic
    #
    #     lastChannelReached = bool(
    #         tmpChannelDataMode1['name'][countedFader - 1] == channelNamesByIndex[currentLayer][-1])
    #     tmpChannelDataMode1 = initTmpChannelDataMode1()
    #     if lastChannelReached:
    #         # if currentLayer == output:
    #         #     checkTaskStack()
    #         #     return
    #
    #         if channelNamesByIndex[output][selectedSubmixIndex + 1] == channelNamesByIndex[output][selectedSubmixIndex]:
    #             nextSubmixIdx = selectedSubmixIndex + 2
    #         else:
    #             nextSubmixIdx = selectedSubmixIndex + 1
    #
    #         if nextSubmixIdx < numberTmChannels:
    #             taskStack.insert(0, fetchChannelVolume)
    #             taskStack.insert(0, partial(oscS_goToChannelIndex, 0))
    #             oscS_selectSubmix(nextSubmixIdx)
    #         else:
    #             checkTaskStack()
    #
    #     else:
    #         taskStack.insert(0, fetchChannelVolume)
    #         oscS_goToNextBank()

    def initiateLayoutFetch(self, fastFetch:bool=False, finishFunction=dumdumdummyfunc):
        self.scheduleLayoutFetch(fastFetch)
        self.taskStack.append(finishFunction)

        self.checkTaskStack()

    #TODO: implement "Fast Fetch" without Properties, layermode=1
    def scheduleLayoutFetch(self, fastFetch:bool=False):
        if fastFetch:
            print('ERROR: fast fetch not implemented yet')
            return False
        else:
            for _layer in [self.busOutput, self.busInput, self.busPlayback]:
                self.taskStack.append(self.oscS_goToLayer(_layer))
                self.taskStack.append(self.oscS_goToChannelIndex(0))
                self.taskStack.append(self.fetchChannelProperties)



    def scheduleJob(self):
        pass
    # def createChanVolDic(vol=0.0, pan=0.5) -> dict:
    #     return {
    #         'vol': vol,
    #         'pan': pan
    #     }

