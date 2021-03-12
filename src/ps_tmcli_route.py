



class tmOscCommunicator(object):

    channelPropertiesFetched = False
    channelNamesByIndex = []

    def __init__(self, ipaddress, port, rcv_port, database:dict=None):

        self.taskStack = set()
        self.tmpChannelData = {}
        self.currentLayer = ''



    def oscR_receivedTmData(self, address, *args):
        sOsc = address.decode()
        if sOsc[0:2] == '/2':
            try:
                self.tmpChannelData[sOsc[3:]] = args[0].decode()
            except:
                self.tmpChannelData[sOsc[3:]] = args[0]

            if settingTargetValue:
                checkValue()
        else:
            return


    def oscR_setLayer(self, layer: str, mode: int, *args):

        if args[0] == 1.0:
            self.currentLayer = layer


    def oscR_selectedSubmix(mode: int, *args):

        global selectedSubmixName, selectedSubmixIndex, changingChannel
        selectedSubmixName = args[0].decode()

        if channelPropertiesFetched:
            selectedSubmixIndex = channelNamesByIndex[output].index(selectedSubmixName)

        if mode == 2:
            checkTaskStack()
        elif mode == 1:
            global countFader
            if countFader:
                countFader = False


chLimitReached = False
checkChannelLimit = False
def oscR_setChannelName(*args):
    chName = args[0].decode()
    if checkChannelLimit:
        global chLimitReached, tmpChannelName
        chLimitReached = tmpChannelName == chName
    tmpChannelName = chName

numberFader = 0
countFader = True

def oscR_countRemoteFader(nFader, *args):
    global numberFader
    if countFader:
        numberFader = nFader
        if nFader > 1:
            sOSc = '/1/labelS{}'.format(nFader-1)
            oscServer.unbind(sOSc.encode(), partial(oscR_countRemoteFader, nFader-1))
    else:
        sOSc = '/1/labelS{}'.format(numberFader)
        oscServer.unbind(sOSc.encode(), partial(oscR_countRemoteFader, numberFader))


def oscR_tmpChannelDataMode1(fader:int, key:str, *args):

    try:
        value = args[0].decode()
    except:
        value = args[0]

    tmpChannelDataMode1[key][fader] = value

    if fader == 1 and key == 'name':
        global tmpChannelName
        tmpChannelName = value
        global currentChIndex
        if value in channelNamesByIndex:
            currentChIndex = channelNamesByIndex[currentLayer].index(value)


def oscR_dataMode1complete(*args):
    checkTaskStack()


def createChanVolDic(vol=0.0, pan=0.5) -> dict:
    return {
        'vol': vol,
        'pan': pan
    }


def checkTaskStack(*args):
    global timeout
    timeout.cancel()

    if taskStack:
        timeout = scheduleTimeOut(taskStack[0])
        timeout.start()
        taskStack.pop(0)()
    else:
        print('no tasks on stack')
        timeout = scheduleTimeOut()
        timeout.start()


def oscS_goToLayer(layer: str, mode: int = 2):
    initTmpData()
    sOsc = '/{}/{}'.format(mode, layer)
    toTM.send_message(sOsc.encode(), [1.0])


def oscS_goToChannelIndex(index: int):
    global currentChIndex
    currentChIndex = index
    toTM.send_message(b'/setBankStart', [float(index)])


def oscS_goToNextChannel():
    global currentChIndex
    if getDataOfSelectedChannel()['stereo'] == 1.0:
        currentChIndex = currentChIndex + 2
    else:
        currentChIndex = currentChIndex + 1

    toTM.send_message(b'/2/track+', [1.0])

def oscS_previousChannel(mode:int=2):
    if mode == 2:
        toTM.send_message(b'/2/track-', [1.0])
    else:
        toTM.send_message(b'/1/track+', [1.0])

def oscS_goToNextBank():
    toTM.send_message(b'/1/bank+', [1.0])

def oscS_previousBank():
    toTM.send_message(b'/1/bank-', [1.0])


def oscS_selectSubmix(outChannel:int):
    if not selectedSubmixIndex == outChannel:
        toTM.send_message(b'/setSubmix', [float(outChannel)])
        global timeout
        if timeout.is_alive():
            timeout.cancel()
        timeout = threading.Timer(0.5, checkTaskStack)
        timeout.start()
    else:
        checkTaskStack()


lastChName = None
def goToFirstChannel(mode:int=1):
    if tmpChannelName == lastChName:
        checkTaskStack()
    else:
        taskStack.insert(0, partial(goToFirstChannel, mode))
        oscS_previousBank()

def getDataOfSelectedChannel() -> dict:
    return channelDataByName[currentLayer][channelNamesByIndex[currentLayer][currentChIndex]]

def getChannelDataByIndex(layer:str, idx:int, key:str=''):
    if key:
        return channelDataByName[layer][channelNamesByIndex[layer][idx]][key]
    else:
        return channelDataByName[layer][channelNamesByIndex[idx]]


settingTargetValue = False
def checkValue():
    global settingTargetValue
    if tmpChannelData[targetParameter] == targetValue:
        settingTargetValue = False
        setValuesForTargetChannels()
    else:
        settingTargetValue = True
        if parameterIsToggle:
            oscS_toggleValue(targetOsc)
        else:
            oscS_doSetValue(targetOsc, float(targetValue))


def oscS_doSetValue(oscAd, value):
    toTM.send_message(oscAd, [value])

def oscS_toggleValue(oscAd):
    toTM.send_message(oscAd, [1.0])
