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
import sys


parser = argparse.ArgumentParser(description='Command line tool for controlling totalmix from RME')
actionParser = parser.add_subparsers(title='actions')#add_mutually_exclusive_group(required=False)
# subParser = parser.add_subparsers(help='actions')

parser.add_argument('-i', '--interactive', action='count', help='run in interactive mode')
parser.add_argument('-f', '--fetch', action='count', default=0, help='fetch device layout and properties, use -ff for also fetching gain matrix (may take a while depending on channel count')
parser.add_argument('-ft', '--fetchforget', action='store_true', default=0, help='fetch device layout and properties, dont store fetch-file')
parser.add_argument('-F', '--file', default='tm-fetched.json', help='use prefetched values from file or fetch and write to file if -f')
parser.add_argument('-o', '--port', type=int,  default=2, help='either 1,2,3 or 4, default is 2 for second default osc-control (9002:localhost:7002')
parser.add_argument('-r', '--remote', help='<tmOutPort>:<tm-ip>:<tmReceivePort>, e.g. 9002:192.168.178.27:7002 for remote control and default osc-control 2'
                                           ' overwrites -o')
parser.add_argument('-d', '--default', type=int, default=0, help='remember configs (remote, port, channellayout), and stores them in "~/library/Application Support/totalmix-cli". Different defaults can be stored/loaded with index')
parser.add_argument('-v', '--verbose', action='count', help='verbosity level, no function yet')

# setParser = subParser.add_parser('--set', help='setvalues')
setParser = actionParser.add_parser('set', help='set parameter, "set -h" for help')
setParser.set_defaults(selectedAction='set')
setParser.add_argument('layer', metavar='LAYER', action='store', help='layer to work on to set parameter. Choose on of ["output", "input", "playback"]', choices=['output', 'input', 'playback'])
setParser.add_argument('channel', action='store',  help='channel to process starting with index 1, "all" or ":" for all channels. Legit are channelrange ":",  channellists ","e.g. "1:3,6,13:16", "1,2,3,4,5", "5:10".')
setParser.add_argument('parameter', action='store', help='parameter to set')
setParser.add_argument('value', action='store', type=float, help='value to set to')
setParser.add_argument('-f', '--fast', action='store_true', default=False, help='"fast-mode":set values fast using the prefetchted data. Might not set correctly if parameters did change since fetch. NOT IMPLEMENTED YET')

routeParser = actionParser.add_parser('route', help='set routing for a bunch of channels. either diagonal (many to many), 1 to many or many to 2')
routeParser.set_defaults(selectedAction='route')
routeParser.add_argument('layer', metavar='LAYER', action='store', help='layer to route channels. Choose on of ["output", "input", "playback"]', choices=['output', 'input', 'playback'])
routeParser.add_argument('sending_channels', help='channels or channelrange to route')
routeParser.add_argument('output_channels', help='channels to route on')
routeParser.add_argument('-v', '--volume', metavar='vol', default=0.817204, help='volumes to set channels to, with 0 = -oo, 0.61 = -12dB, 1 = 0dB, 1.23 = +6dB.')
routeParser.add_argument('-d', '--diagonal', default=False, action='store_true', help='If set the script tries to process all channel for diagonal routing. E.g. choose a range of output channels and just the first input channel for the diagonal routing.')
routeParser.add_argument('-e', '--exclusive', default=False, action='store_true', help='Set routing exclusiveley, set all other channel to 0.')

# routeParser.add_argument('-m', '--mode', default=False, choices=['diag', 'fdiag', '1toMany', 'manyTo1'], help='mode for setting volume. To a certain degree the will be automatically set depending on the input/output channel configuration. Default is attempting normal diagonal routing and stop if one of the channellist is completely processed. If set to "fdiag" the highest channel count on columns/rows is used. E.g. this can be used to select a number of outputs and just the channel to start with or vice versa.')

copyParser = actionParser.add_parser('copy', help='copy a parameter from a channel, "copy -h" for help, NOT IMPLEMENTED YET')
copyParser.set_defaults(selectedAction='copy')

daemonParser = actionParser.add_parser('daemon', help='run as daemon, e.g. watch a channel for synchronising Eqs, NOT IMPLEMENTED YET')
copyParser.set_defaults(selectedAction='daemon')

args = parser.parse_args()

globalTaskStack = list()


def setPropertiesFetched(val:bool=True):
    global channelPropertiesFetched
    channelPropertiesFetched = val
    global numberTmChannels
    numberTmChannels = len(channelNamesByIndex[input])
    checkTaskStack()

def setVolumesFetched(val:bool=True):
    global channelVolumeFetched
    channelVolumeFetched = val
    checkTaskStack()

def startInit():

    if not shutdown:
        thingsToFetch = []
        if shallFetchProperties:
            print('fetch properties')
            thingsToFetch.append((fetchChannelProperties, 2))
        if shallFetchVolumes:
            print('fetch gains')
            thingsToFetch.append((fetchChannelVolume, 1))
        global currentLayer
        currentLayer = ''

        for fetch, mode in thingsToFetch:
            for layer in [output,input,playback]:
                print('setting up tasks', fetch, mode, layer)
                taskStack.append(partial(oscS_goToLayer, layer, mode))
                if mode == 1:
                    taskStack.append(partial(oscS_selectSubmix, 0))
                taskStack.append(partial(oscS_goToChannelIndex, 0))
                taskStack.append(fetch)
            if mode == 2:
                taskStack.append(setPropertiesFetched)
            elif mode == 1:
                taskStack.append(setVolumesFetched)

        # if not (shallFetchProperties and shallFetchVolumes)


        taskStack.append(finishInit)
        checkTaskStack()


shutdown = False
def finishInit():

    print('finished init')

    if (shallFetchVolumes or shallFetchProperties) and args.file:
        # print('filename', args.file)
        fname = args.file
        writeFetchFiles(fname)

    _boolDoProcessing = actionSpecificInit()

    # global channelSet_1
    # channelSet_1, _chToVerify = parseTargetChannels(targetChannels)
    # for c in verifyTargetChannels(_chToVerify):
    #     channelSet_1.add(c)
    # if targetParameter:
    #     print(' start setting parameter', targetParameter, targetValue, 'for channels', indicesWithOffset(channelSet_1, 1), 'on layer', layerToSet)
    # else:
    #     print('no parameter to set')

    # print('channelsss', channelsToSet)

    if _boolDoProcessing:
        prepareProcessing(mainAction)
    else:
        exitProgram()



def indexListWithOffset(indices, offset) -> list:
    ll = []
    for i in indices:
        ll.append(i+offset)
    return ll


def getTargetChannelSetFromString(channelString:str) -> set:
    targetChs_, _chToVerify = parseTargetChannels(targetChannels)
    for c in verifyTargetChannels(_chToVerify):
        targetChs_.add(c)
    return targetChs_


def parseTargetChannels(inputChannelString:str) -> (set, set):
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


def verifyTargetChannels(channelStrToVerify) -> set:

    outputSet = set()
    while (channelStrToVerify):
        chRange = channelStrToVerify.pop()
        if chRange == 'all':
            print('all',  numberTmChannels, 'channels')
            for c in range(numberTmChannels):
                outputSet.add(c)
        else:
            try:
                lowIdx = channelNamesByIndex[layerToSet].index(chRange[0])
                highIdx = channelNamesByIndex[layerToSet].index(chRange[1])

                for c in range(lowIdx, highIdx + 1):
                    outputSet.add(c)
            except:
                print('Channels', chRange, 'not found in TM Data and will not be set')

    _limitReached = False
    _channelsToRemove = set()
    _channelsToAdd = set()
    for c in outputSet:
        if c > 0 and c % 2:
            chIsStereo = bool(getChannelDataByIndex(layerToSet, c, 'stereo'))
            if chIsStereo:
                _channelsToRemove.add(c)
                _channelsToAdd.add(c - 1)

        if c >= numberTmChannels:
            _channelsToRemove.add(c)
            _limitReached = True
    for c in _channelsToRemove:
        outputSet.remove(c)
    for c in _channelsToAdd:
        outputSet.add(c)

    if _limitReached:
        print('channel limit is', numberTmChannels, 'higher channels will not be set')

    return outputSet


def prepareProcessing(actionFunction):
#TODO: rather not clearing taskStack?
    taskStack.clear()
    taskStack.append(actionFunction)
    oscS_goToLayer(layerToSet)


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


def setValuesForTargetChannels():
    if channelSet_1:
        c = channelSet_1.pop()
        taskStack.append(checkValue)
        oscS_goToChannelIndex(c)

    else:
        print('finished setting values')
        exitProgram()


def exitProgram():

    print('open tasks:', taskStack)

    global shutdown
    if not shutdown:
        shutdown = True
        if timeout.is_alive():
            timeout.cancel()
        print('shutting down')
        threading.Timer(0.678, sshhhuh).start()


def sshhhuh():
    print('ssshshhhuuuu', os.getpid())
    timeout.cancel()
    # del timeout
    oscServer.close()
    # del oscServer
    os.kill(os.getpid(), signal.SIGQUIT)


def scheduleTimeOut(lastFunction=None, t=5):
    return threading.Timer(t, timeoutCalled, args=[lastFunction])


def timeoutCalled(lastFunctionCall=None):
    print('process timeout.\nTotalmix is not responding, configuration has failures or there is a bug.'
          '\nLast function called is', lastFunctionCall, '\nTasks on stack are', taskStack)
    exitProgram()


def dumdumdummyfunc():
    return False
    # print('I am a dumdumdummy funcion and should normally not be called.')

timeout = scheduleTimeOut()

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

def initTmpData():
    global tmpChannelDataMode1, tmpChannelData, tmpChannelName
    tmpChannelData = {}
    tmpChannelName = ''
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

taskStack = []


# parsing input

if args.interactive:
    print('I\'m so sorry. Interactive mode is not implemented yet. \nBe patient...')


fetchtime = 'fetchtime'
if args.fetch and args.fetch > 0:
    # shallFetchVolumes = True
    # shallFetchProperties = True
    shallFetchProperties = args.fetch > 0
    shallFetchVolumes = args.fetch > 1
else:
    print('dont fetch channel layout')
    shallFetchVolumes = False
    shallFetchProperties = False

    if args.file:
        readPrefetchFile(args.file)


if args.remote:
    remoteParams = args.remote.split(':')
    rcvPort = int(remoteParams[0])
    sendAddress = remoteParams[1]
    sendPort = remoteParams[2]
else:
    sendPort = 7000 + int(args.port)
    rcvPort = 9000 + int(args.port)


#INTIALISE
# startInit()
# print('arguments are __', args)

selectedAction = ''
try:
    selectedAction = args.selectedAction
except:
    pass

# if selectedAction == 'set':
#     targetParameter = args.parameter
#     targetValue = args.value
#     targetChannels = args.channel
# else:
#     targetParameter = ''
#     targetValue = None
#     targetChannels = ''

channelSet_1 = set()
channelStrToVerify_1 = set()
channelSet_2 = set()
channelStrToVerify_2 = set()
layerToSet = ''
targetOsc = ''

actionSpecificInit = dumdumdummyfunc
mainAction = dumdumdummyfunc


def initSetParameter():
    global channelSet_1, layerToSet
    layerToSet = args.layer
    channelSet_1 = getTargetChannelSetFromString(targetChannels)
    # channelSet_1, _chToVerify = parseTargetChannels(targetChannels)
    # for c in verifyTargetChannels(_chToVerify):
    #     channelSet_1.add(c)
    if targetParameter:
        print(' start setting parameter', targetParameter, targetValue, 'for channels',
              indexListWithOffset(channelSet_1, 1), 'on layer', layerToSet)
    else:
        print('no parameter to set')

    return len(channelSet_1) > 0

def initRouteChannels():
    global channelSet_1, channelSet_2, layerToSet
    layerToSet = args.layer
    targetSendChannels = args.sending_channels
    targetOutputs = args.outout_channels

    channelSet_1 = getTargetChannelSetFromString(targetSendChannels)
    channelSet_2 = getTargetChannelSetFromString(targetOutputs)



    channelSet_1 = set()
    channelStrToVerify_1 = set()
    layerToSet = ''



if selectedAction == 'set':
    targetParameter = args.parameter
    targetValue = args.value
    targetChannels = args.channel
    targetLayer = args.layer

    actionSpecificInit = initSetParameter
    mainAction = setValuesForTargetChannels

    targetOsc = '/2/{}'.format(targetParameter).encode()

    valuesThatAreToggles = ['mute', 'phase', 'phaserRight', 'phantom', 'instrument', 'pad', "msProc", "autoset", "loopback",
                          "stereo",
                          "talkbackSel",
                          "noTrim",
                          "cue",
                          "recordEnable",
                          "playChannel",
                          "lowcutEnable",
                          "eqEnable",
                          "compexpEnable",
                          "alevEnable"
                            ]
    parameterIsToggle = targetParameter in valuesThatAreToggles



if selectedAction == 'route':

    targetLayer = args.layer
    targetSendChannels = args.sending_channels
    targetOutputs = args.outout_channels

    channelSet_1 = set()
    channelStrToVerify_1 = set()
    layerToSet = ''





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
