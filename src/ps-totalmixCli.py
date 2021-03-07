#dependencies oscpy


from oscpy.server import OSCThreadServer
from oscpy.client import OSCClient
from functools import partial
import json
import signal
import argparse
import threading
import os
import time, datetime


parser = argparse.ArgumentParser()
parser.add_argument('-i', '--interactive', action='count', help='run in interactive mode')
parser.add_argument('-f', '--fetch', action='store_true', help='fetch all device properties')
parser.add_argument('-F', '--file', default='tmChProps.json', help='use prefetched values from file or fetch and write to file if -f')
parser.add_argument('-o', '--port', default=2, help='either 1,2,3 or 4, default is 2 for second default osc-control (9002:localhost:7002')
parser.add_argument('-r', '--remote', help='<portTmOut>:<tm-ip>:<tmReceive>, e.g. 9002:192.168.178.27:7002 for local control for default osc-control 2'
                                           ' overwrites -c')
parser.add_argument('-v', '--verbose', action='count', help='verbosity mode')

parser.add_argument('-a', '--action', default='set', help='action to perform. set/copy default:set')
parser.add_argument('-p', '--parameter', default='', help='parameter to set.')
parser.add_argument('-vf', '--value', type=float, default=0, help='number-value to set to from 0 to 1')
parser.add_argument('-val' '--realvalue', default='', help='real vlaue e.g. "300hz" or "-6db"')
parser.add_argument('-ch', '--channel', default='', help='channel to process starting with 1, e.g. "output:[1:3],6,[13:16]", "playback:1,2,3,4,5", "input:[5:10]"')



args = parser.parse_args()


def oscR_receivedTmData(address, *args):
    sOsc = address.decode()
    if sOsc[0:2] == '/2':
        try:
            tmpChannelData[sOsc[3:]] = args[0].decode()
        except:
            tmpChannelData[sOsc[3:]] = args[0]

        if settingTargetValue:
            checkValue()
    # elif sOsc[0:2] == '/1':
    #     pass
    else:
        return


def oscR_setLayer(layer: str, mode: int, *args):

    if args[0] == 1.0:
        global currentLayer
        currentLayer = layer


def oscR_selectedSubmix(mode: int, *args):

    global selectedSubmixName, selectedSubmixIndex, changingChannel
    selectedSubmixName = args[0].decode()

    if channelPropertiesFetched:
        # print('eindeutiger identifier', len(channelNamesByIndex[output]))
        selectedSubmixIndex = channelNamesByIndex[output].index(selectedSubmixName)

    if mode == 2:
        tmOutputComplete()
    elif mode == 1:
        global countFader
        if countFader:
            # sOsc = '/1/MicGainVal{}'.format(numberFader)
            # oscServer.bind(sOSc.encode(), tmOutputComplete)

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
    # if type(args[0]) == type(bytes):
    #     value = args[0].decode()
    # else:
    #     value = args[0]
    try:
        value = args[0].decode()
    except:
        value = args[0]

    # if not key in tmpChannelDataMode1.keys():
    #     tmpChannelDataMode1[key] = {}
    tmpChannelDataMode1[key][fader] = value
    if fader == 1 and key == 'name':
        global currentChIndex
        currentChIndex = channelNamesByIndex[currentLayer].index(value)


def oscR_dataMode1complete(*args):
    tmOutputComplete()


def createChanVolDic(vol=0.0, pan=0.5) -> dict:
    return {
        'vol': vol,
        'pan': pan
    }


def tmOutputComplete(*args):
    try:
        doWhatYouMustDo.pop(0)()
    except:
        print('no tasks on stack')



def oscS_goToLayer(layer: str, mode: int = 2):
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

def oscS_goToNextBank():
    toTM.send_message(b'/1/bank+', [1.0])

def oscS_selectSubmix(outChannel:int):
    toTM.send_message(b'/setSubmix', [float(outChannel)])


# def goToChannelName(name: str):
#     pass


def getDataOfSelectedChannel() -> dict:
    return channelDataByName[currentLayer][channelNamesByIndex[currentLayer][currentChIndex]]

def getChannelDataByIndex(layer:str, idx:int, key:str=''):
    # print('getting channel data ', layer, idx, key)
    if key:
        return channelDataByName[layer][channelNamesByIndex[layer][idx]][key]
    else:
        return channelDataByName[layer][channelNamesByIndex[idx]]

def fetchDeviceState(fetchtask):

    doWhatYouMustDo.append(fetchtask)

    mode = 2 if fetchtask == fetchLayerPorperties else 1

    if currentLayer == '':
        oscS_goToLayer(output, mode)
    elif currentLayer == output:
        oscS_goToLayer(input, mode)
    elif currentLayer == input:
        oscS_goToLayer(playback, mode)
    elif currentLayer == playback:
        global channelVolumeFetched

        if fetchtask == fetchLayerPorperties:
            global channelPropertiesFetched, numberTmChannels
            numberTmChannels = len(channelNamesByIndex[input])
            doWhatYouMustDo.pop()
            channelPropertiesFetched = True

        elif fetchtask == fetchLayerVolume:
            global channelVolumeFetched

            doWhatYouMustDo.pop()
            channelVolumeFetched = True



        startInit()
    else:
        finishInit()


def fetchLayerPorperties():

    global currentChIndex, checkChannelLimit, chLimitReached
    currentChIndex = 0
    channelNamesByIndex[currentLayer] = []
    channelDataByName[currentLayer] = {}
    doWhatYouMustDo.append(fetchChannelProperties)
    checkChannelLimit = False
    chLimitReached = False
    oscS_goToChannelIndex(0)


def fetchChannelProperties():

    global chLimitReached
    if chLimitReached:
        fetchDeviceState(fetchLayerPorperties)
    else:
        global tmpChannelData, checkChannelLimit

        channelNamesByIndex[currentLayer].append(tmpChannelName)
        if tmpChannelData['stereo'] == 1.0:
            channelNamesByIndex[currentLayer].append(tmpChannelName)
        channelDataByName[currentLayer][tmpChannelName] = tmpChannelData.copy()
        tmpChannelData = {}
        checkChannelLimit = True
        doWhatYouMustDo.append(fetchChannelProperties)

        oscS_goToNextChannel()


# def fetchDeviceVolume():
#     pass

def fetchLayerVolume():
    if selectedSubmixIndex > 0:
        doWhatYouMustDo.append(fetchLayerVolume)
        oscS_selectSubmix(0)

    else:
        doWhatYouMustDo.append(fetchChannelVolume)
        oscS_goToChannelIndex(0)


def fetchChannelVolume():
    global tmpChannelDataMode1
    for idx in range(len(tmpChannelDataMode1['name'])):
        chName = tmpChannelDataMode1['name'][idx]
        chIdx = channelNamesByIndex[currentLayer].index(chName)

        chDic = createChanVolDic(tmpChannelDataMode1['vol'][idx],
                                 tmpChannelDataMode1['pan'][idx])
        if currentLayer == output:
            chDic['name'] = chName
            chDic['index'] = chIdx
            outputVolumes[chIdx] = chDic
            outputVolumes[chName] = chDic
        else:
            outputIndex = selectedSubmixIndex
            if not chIdx in channelSends[currentLayer].keys():
                channelSends[currentLayer][chIdx] = {}
            if not outputIndex in outputReceives[currentLayer].keys():
                outputReceives[currentLayer][outputIndex] = {}
            channelSends[currentLayer][chIdx][selectedSubmixIndex] = chDic
            outputReceives[currentLayer][outputIndex][chIdx] = chDic

    lastChannelReached = bool(tmpChannelDataMode1['name'][numberFader-1] == channelNamesByIndex[currentLayer][-1])
    tmpChannelDataMode1 = initTmpChannelDataMode1()

    if lastChannelReached:
        if channelNamesByIndex[output][selectedSubmixIndex + 1] == channelNamesByIndex[output][selectedSubmixIndex]:
            nextSubmixIdx = selectedSubmixIndex + 2
        else:
            nextSubmixIdx = selectedSubmixIndex + 1


        if nextSubmixIdx < numberTmChannels:
            doWhatYouMustDo.append(partial(oscS_goToChannelIndex, 0))
            doWhatYouMustDo.append(fetchChannelVolume)
            oscS_selectSubmix(nextSubmixIdx)
        else:
            fetchDeviceState(fetchLayerVolume)

    else:
        doWhatYouMustDo.append(fetchChannelVolume)
        oscS_goToNextBank()


def startInit():

    if not shutdown:

        global currentLayer
        if shallFetchProperties and not channelPropertiesFetched:
            currentLayer = ''
            print('fetching channel properties')
            fetchDeviceState(fetchLayerPorperties)
            return
        elif shallFetchVolumes and not channelVolumeFetched:
            currentLayer = ''
            print('fetching channel gains')
            fetchDeviceState(fetchLayerVolume)
            return

        finishInit()


shutdown = False
def finishInit():

    print('finished init')

    global numberTmChannels
    numberTmChannels = len(channelNamesByIndex[input])

    if args.fetch and args.file:
        fname = args.file
        with open(fname, 'w') as fp:
            completeDict = {
                fetchtime: time.time(),
                'channel properties': channelDataByName,
                'channel indices': channelNamesByIndex,
                'output volumes': outputVolumes,
                'channel sends': channelSends,
                'output receives': outputReceives
            }
            json.dump(completeDict, fp, indent=5)

        fp.close()
        print('results written to', fname)


    verifyTargetChannels()

    print(' start setting parameter', targetParameter, targetValue, 'for channels', channelsToSet, 'on layer', layerToSet)

    if channelsToSet:
        prepareSettingValues()
    else:
        exitProgram()


def verifyTargetChannels():
    # print('verify target channels', channelNameRanges, numberTmChannels)

    while (channelNameRanges):
        chRange = channelNameRanges.pop()
        if chRange == 'all':
            for c in range(numberTmChannels):
                channelsToSet.add(c)
        else:
            try:
                lowIdx = channelNamesByIndex[layerToSet].index(chRange[0])
                highIdx = channelNamesByIndex[layerToSet].index(chRange[1])
                # if lowIdx > 0 and lowIdx % 2:
                #     lowIdx = lowIdx - 1 if channelDataByName[layerToSet]
                for c in range(lowIdx, highIdx + 1):
                    channelsToSet.add(c)
            except:
                print('Channels', chRange, 'not found in TM Data and will not be set')

    _limitReached = False
    _channelsToRemove = set()
    _channelsToAdd = set()
    for c in channelsToSet:
        if c > 0 and c % 2:
            chSt = bool(getChannelDataByIndex(layerToSet, c, 'stereo'))
            if chSt:
                _channelsToRemove.add(c)
                # channelsToSet.remove(c)
                _channelsToAdd.add(c - 1)
                # channelsToSet.add(c - 1)

        if c >= numberTmChannels:
            _channelsToRemove.add(c)
            # channelsToSet.remove(c)
            _limitReached = True
    for c in _channelsToRemove:
        channelsToSet.remove(c)
    for c in _channelsToAdd:
        channelsToSet.add(c)

    if _limitReached:
        print('channel limit is', numberTmChannels, 'higher channels will not be set')


def prepareSettingValues():


    doWhatYouMustDo.clear()
    doWhatYouMustDo.append(setValuesForTargetChannels)

    oscS_goToLayer(layerToSet)

# def startWorking():
#     doWhatYouMustDo.clear()
#     doWhatYouMustDo.append(doIt)
#     oscS_goToLayer()

settingTargetValue = False
def checkValue():
    global settingTargetValue
    # print('checkingvalue', currentLayer, currentChIndex, tmpChannelData[targetParameter], targetValue)
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
    # print('setting value')
    toTM.send_message(oscAd, [value])

def oscS_toggleValue(oscAd):
    toTM.send_message(oscAd, [1.0])


def setValuesForTargetChannels():
    if channelsToSet:
        c = channelsToSet.pop()
        doWhatYouMustDo.append(checkValue)
        oscS_goToChannelIndex(c)

    else:
        print('finished setting values')
        exitProgram()



    # exitProgram()


def exitProgram():
    global shutdown
    if not shutdown:
        shutdown = True
        print('shutting down')
        threading.Timer(0.678, sshhhuh).start()


def sshhhuh():
    print('ssshshhhuuuu', os.getpid())
    os.kill(os.getpid(), signal.SIGQUIT)


def dumdumdummyfunc():
    pass


shallFetchProperties = True
channelPropertiesFetched = False
shallFetchVolumes = True
channelVolumeFetched = False

rcvPort = 9002
sendPort = 7002
sendAddress = 'localhost'

input = 'busInput'
playback = 'busPlayback'
output = 'busOutput'

changingLayer = False
changingChannel = False

currentLayer = ''
controlLayer = 0

currentChIndex = -1

selectedSubmixName = ''
selectedSubmixIndex = -1

tmpChannelData = {}
tmpChannelName = ''

def initTmpChannelDataMode1() -> dict:
    return {
    'vol': {},
    'pan': {},
    'name': {}
}

tmpChannelDataMode1 = initTmpChannelDataMode1()

channelNamesByIndex = {
    input: [],
    playback: [],
    output: []
}

channelDataByName = {
    input: {},
    playback: {},
    output: {}
}
numberTmChannels = 0

channelSends = {
    input: {},
    playback: {}
}
outputReceives = {
    input: {},
    playback: {}
}
outputVolumes = {}

doWhatYouMustDo = []




# parsing input

if args.interactive:
    print('I\'m so sorry. Interactive mode is not implemented yet. \nBe patient...')


fetchtime = 'fetchtime'
if args.fetch:
    shallFetchVolumes = True
    shallFetchProperties = True
else:
    print('dont fetch channel layout')
    shallFetchVolumes = False
    shallFetchProperties = False

    if args.file:
        try:
            with open(args.file) as dicF:
                data = json.load(dicF)
                print('using layout fetched at', datetime.datetime.fromtimestamp(data[fetchtime]))
                channelDataByName = data['channel properties']
                channelNamesByIndex = data['channel indices']
                outputVolumes = data['output volumes']
                outputReceives = data['output receives']
                channelSends = data['channel sends']
            dicF.close()

        except:
            print('CAUTION no data file found')


if args.remote:
    remoteParams = args.remote.split(':')
    rcvPort = int(remoteParams[0])
    sendAddress = remoteParams[1]
    sendPort = remoteParams[2]
else:
    sendPort = 7000 + args.port
    rcvPort = 9000 + args.port


#INTIALISE
# startInit()

targetParameter = args.parameter
targetOsc = '/2/{}'.format(targetParameter).encode()
targetValue = args.value
parameterIsToggle = True


channelsToSet = set()
channelNameRanges = set()
layerToSet = ''
if args.channel:
    _layer = ''
    splitIdx = 0
    # print(args.channel)
    try:
        splitIdx = args.channel.index(':')
        # print(splitIdx)
        _layer = args.channel[:splitIdx]
    except:
        print('ERROR something wrong with layer selection')
    if _layer in ['input', 'output', 'playback']:
        #TODO: dummes Konstrukt
        _layerNames = {
            'input': input,
            'output': output,
            'playback': playback
        }
        layerToSet =  _layerNames[_layer]

        _channelsRaw = args.channel[splitIdx+1:]


        if _channelsRaw in ['', 'all', ':']:
            channelNameRanges.add('all')
            # print('target are all channels of layer', _layer)
        else:
            try:
                _channelsRaw = _channelsRaw.split(',')
            except:
                _channelsRaw = [_channelsRaw]

            _channelStrings = set()
            for _ch in _channelsRaw:

                try:
                    channelsToSet.add(int(_ch)-1)
                except:
                    _channelStrings.add(_ch)

            for _chStr in _channelStrings:


                _chR = _chStr[1:-1]
                # print('channel is ', _chR)
                try:
                    _chR = _chR.split(':')
                    # print('splitted', _chR)
                    try:
                        for c in range(int(_chR[0])-1, int(_chR[1])):
                            channelsToSet.add(c)
                    except:
                        if len(_chR) == 2:
                            channelNameRanges.add((_chR[0], _chR[1]))
                        else:
                            print('something wrong with channel range', _chStr)
                except:
                    channelsToSet.add(_chStr)


    else:
        print('layer is missing in -ch', args.channel)


if args.action == 'set':
    pass


toTM = OSCClient(address=sendAddress, port=sendPort)

oscServer = OSCThreadServer(default_handler=oscR_receivedTmData)
oscServer.listen(address='0.0.0.0', port=rcvPort, default=True)

for i in [1, 2]:
    for bus in ['busInput', 'busPlayback', 'busOutput']:
        oscAddr = ('/'+str(i)+'/'+bus).encode()
        oscServer.bind(oscAddr, partial(oscR_setLayer, bus, i))

    sOsc = '/{}/labelSubmix'.format(i)
    oscServer.bind(sOsc.encode(), partial(oscR_selectedSubmix, i))
    del sOsc

oscServer.bind(b'/2/trackname', partial(oscR_setChannelName))


for i in range(64):
    sOSc = '/1/labelS{}'.format(i+1)
    oscServer.bind(sOSc.encode(), partial(oscR_countRemoteFader, i+1))
    sOSc = '/1/volume{}'.format(i+1)
    oscServer.bind(sOSc.encode(), partial(oscR_tmpChannelDataMode1, i, 'vol'))
    sOsc = '/1/pan{}'.format(i+1)
    oscServer.bind(sOsc.encode(), partial(oscR_tmpChannelDataMode1, i, 'pan'))
    sOsc = '/1/trackname{}'.format(i+1)
    oscServer.bind(sOsc.encode(), partial(oscR_tmpChannelDataMode1, i, 'name'))
    del sOsc

oscServer.bind(b'/1/micgain8', oscR_dataMode1complete)


if shutdown:
    print('shutting down... cause I got nothing to do.. or something went wrong')
    exitProgram()
else:
    startInit()
    signal.pause()
# signal.pause()
