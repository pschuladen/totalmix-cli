#dependencies oscpy

from functools import partial
import argparse
import threading
import os
import datetime

import ps_tmcli_osccom as tmcom
from ps_tmcli_data import TmDataClass as tmdata
import ps_tmcli_parseArgs as tmargs


parser = argparse.ArgumentParser(description='Command line tool for controlling totalmix from RME')
actionParser = parser.add_subparsers(title='actions')#TODO: add_mutually_exclusive_group(required=False)

parser.add_argument('-i', '--interactive', action='count', help='run in interactive mode')
parser.set_defaults(selectedAction=None)
parser.add_argument('-f', '--fetch', action='count', default=0, help='fetch device layout and properties, use -ff for also fetching gain matrix (may take a while depending on channel count')
parser.add_argument('-ft', '--fetchforget', action='store_true', default=0, help='fetch device layout and properties, dont store fetch-file')
parser.add_argument('-F', '--file', default='tm-fetched.json', help='use prefetched values from file or fetch and write to file if -f')
parser.add_argument('-o', '--port',  default=2, help='either 1,2,3 or 4, default is 2 for second default osc-control (9002:localhost:7002). More than one controller can be set with "," seperated')
parser.add_argument('-r', '--remote', default=None,  help='<tmOutPort>:<tm-ip>:<tmReceivePort>, e.g. 9002:192.168.178.27:7002 for remote control and default osc-control 2'
                                           ' overwrites -o')
parser.add_argument('-d', '--default', type=int, default=0, help='remember configs (remote, port, channellayout), and stores them in "~/library/Application Support/totalmix-cli". Different defaults can be stored/loaded with index')
parser.add_argument('-v', '--verbose', action='count', help='verbosity level, no function yet')


setParser = actionParser.add_parser('set', help='set parameter, "set -h" for help')
setParser.set_defaults(selectedAction='set')
setParser.add_argument('layer', metavar='LAYER', action='store', help='layer to work on to set parameter. Choose on of ["output", "input", "playback"]', choices=['output', 'input', 'playback'])
setParser.add_argument('channel', action='store',  help='channel to process starting with index 1, "all" or ":" for all channels. Legit are channelrange ":",  channellists ","e.g. "1:3,6,13:16", "1,2,3,4,5", "5:10".')
setParser.add_argument('parameter', action='store', help='parameter to set')
setParser.add_argument('value', action='store', type=float, help='value to set to')
setParser.add_argument('-f', '--fast', action='store_true', default=False, help='"fast-mode":set values fast using the prefetchted data. Might not set correctly if parameters did change since fetch. NOT IMPLEMENTED YET')

routeParser = actionParser.add_parser('route', help='set routing for a bunch of channels. either diagonal (many to many), 1 to many or many to 1, NOT IMPLEMENTED YET')
routeParser.set_defaults(selectedAction='route')
routeParser.add_argument('layer', metavar='LAYER', action='store', help='layer to route channels. Choose on of ["input", "playback"]', choices=['input', 'playback'])
routeParser.add_argument('sending_channels', help='channels or channelrange to route')
routeParser.add_argument('output_channels', help='channels to route on')
routeParser.add_argument('-v', '--volume', metavar='vol', default=0.817204, help='volumes to set channels to, with 0 = -oo, 0.61 = -12dB, 1 = 0dB, 1.23 = +6dB.')
routeParser.add_argument('-d', '--diagonal', default=False, action='store_true', help='If set the script tries to process all channel for diagonal routing. E.g. choose a range of output channels and just the first input channel for the diagonal routing.')
routeParser.add_argument('-e', '--exclusive', default=False, action='store_true', help='Set routing exclusiveley, set all other channel to 0.')
routeParser.add_argument('-n', '--numberchannels', default=0, action='store', help='number of channels to route diagonal')


# routeParser.add_argument('-m', '--mode', default=False, choices=['diag', 'fdiag', '1toMany', 'manyTo1'], help='mode for setting volume. To a certain degree the will be automatically set depending on the input/output channel configuration. Default is attempting normal diagonal routing and stop if one of the channellist is completely processed. If set to "fdiag" the highest channel count on columns/rows is used. E.g. this can be used to select a number of outputs and just the channel to start with or vice versa.')

copyParser = actionParser.add_parser('copy', help='copy a parameter from a channel, "copy -h" for help, NOT IMPLEMENTED YET')
copyParser.set_defaults(selectedAction='copy')

daemonParser = actionParser.add_parser('daemon', help='run as daemon, e.g. watch a channel for synchronising Eqs, NOT IMPLEMENTED YET')
copyParser.set_defaults(selectedAction='daemon')



shutdown = False
def exitProgram(immediately:bool=False):

    print('open tasks:', globalTaskStack)

    global shutdown
    if not shutdown:
        shutdown = True
        if timeout.is_alive():
            timeout.cancel()
        if immediately:
            sshhhuh()
        else:
            print('shutting down')
            threading.Timer(0.678, sshhhuh).start()


def sshhhuh():
    print('ssshshhhuuuu', os.getpid())
    timeout.cancel()
    for control in tmController:
        control.oscServer.close()

    os.kill(os.getpid(), signal.SIGQUIT)


def scheduleTimeOut(lastFunction=None, t=5):
    return threading.Timer(t, timeoutCalled, args=[lastFunction])


def timeoutCalled(lastFunctionCall=None, caller: tmcom=None):
    print(caller)
    print('process timeout.\nTotalmix is not responding, configuration has failures or there is a bug.'
          '\nLast function called is', lastFunctionCall, '\nTasks on stack are', globalTaskStack)
    exitProgram()


def dumdumdummyfunc():
    return False
    # print('I am a dumdumdummy funcion and should normally not be called.')

def checkGlobalTasks():
    if globalTaskStack:
        globalTaskStack.pop(0)()
    else:
        exitProgram()


def didFinishFetchLayout(caller: tmcom):

    if caller.timeout.is_alive():
        print('canceling timeout')
        caller.timeout.cancel()


    if tmDataManager.setNumberTmChannel() and tmDataManager.setLayoutFetched():
        if not args.fetchforget and args.file:
            tmDataManager.writeFetchFiles(fname=args.file)


        print('MAIN: number of channels are', tmDataManager.getNumberTmChannel())
        checkGlobalTasks()
    else:
        print('error in layout fetch. shutting down...')
        exitProgram(True)


def didFinishSetParameter(timerObject:threading.Timer=None, caller:tmcom=None):
    if timerObject and timerObject.is_alive():
        timerObject.cancel()

    if globalTaskStack:
        checkGlobalTasks()
    else:
        exitProgram()


def createActions():
    print(args.selectedAction)

    if args.selectedAction == 'set':
        setaction = tmargs.TmAction_Set(args)
        setaction.createTasksList(tmController, didFinishSetParameter)

    elif args.selectedAction == 'None':
        print('no action defined. Just fetching... maybe')
        checkGlobalTasks()

    for control in tmController:
        control.checkTaskStack()



def executeActions():
    pass


args = parser.parse_args()
globalTaskStack = list()
timeout = scheduleTimeOut()

tmDataManager = tmdata()

# shouldFetchLayout:bool = args.fetch > 0
shouldFetchVolumes:bool = args.fetch > 1


if args.file and args.fetch < 1:
    if not tmDataManager.readPrefetchFile(args.file):
        print('Fetch-File could not be read or there is something wrong with that file')
        tmDataManager.fetchState['layout'] = False
        # shouldFetchLayout = True
    else:
        print('using prefetched file from', datetime.datetime.fromtimestamp(tmDataManager.fetchtime))


tmController = []
if args.port and not args.remote:
    if type(args.port) == int:
        tmControlStandardports = [args.port]
    else:
        tmControlStandardports = args.port.split(',')

    for port in tmControlStandardports:
        _address = 'localhost'
        try:
            _sPort = 7000 + int(port)
            _rPort = 9000 + int(port)

            tmController.append(tmcom.TmOscCommunicator(_address, _sPort, _rPort, timeoutFunction=timeoutCalled))

        except:
            print('something wrong with control ports', tmControlStandardports, port)
            exitProgram(True)
            break



if not tmDataManager.fetchState['layout'] or args.fetch > 0:
    globalTaskStack.append(partial(tmController[0].initiateLayoutFetch, finishFunction=didFinishFetchLayout))


if args.fetch > 1:
    globalTaskStack.append(tmController[0].initiateVolumeFetch)


if args.selectedAction:
    print('prepare action', args.selectedAction)

    globalTaskStack.append(createActions)


globalTaskStack.append(exitProgram)
checkGlobalTasks()


import signal
signal.pause()
