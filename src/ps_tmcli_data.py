import json
import time, datetime
import ps_tm_info as ti
import ps_tmcli_tmBase as tmbase


channel_properties = 'channel properties'
channel_list = 'channel list'
output_receives = 'output receives'
output_volumes = 'output volumes'



class TmDataClass(tmbase.TotalmixBaseClass):

    filename = ''
    # channelDataByName = {
    #     ti.output: {},
    #     ti.input: {},
    #     ti.playback: {}
    # }
    # channelNamesByIndex = {
    #     ti.output: [],
    #     ti.input: [],
    #     ti.playback: []
    # }
    #
    # outputVolumes = {}
    # channelSends = {
    #     ti.input: {},
    #     ti.playback: {}
    # }
    # outputReceives = {
    #     ti.input: {},
    #     ti.playback: {}
    # }


    # def dictionariesForAllLayers(cls):
    #     return {
    #         ti.output: {},
    #         ti.input: {},
    #         ti.playback: {}
    #     }


    def writeFetchFiles(cls, data:dict=None,  fname=None) -> bool:
        if fname:
            cls.filename = fname
        if not data:
            data = {
                channel_properties: cls.channelDataByName,
                channel_list: cls.channelNamesByIndex,
                output_volumes: cls.outputVolumes,
                output_receives: cls.outputReceives
            }

        if fname:
            with open(cls.filename, 'w') as fp:
                completeDict = {
                    'fetchtime': time.time()
                }
                for key, _data in data:
                    completeDict[key] = _data

                json.dump(completeDict, fp, indent=5)

            fp.close()
            print('results written to', fname)
            return True
        else:
            print('no file was written')
            return False


    def setValueWithSubDicts(cls, targetDict: dict, keylist: [], value):
        if len(keylist) > 1:
            key = keylist.pop(0)
            subDict: dict
            if key in targetDict.keys():
                subDict = targetDict[key]
            else:
                subDict = {}
                targetDict[key] = subDict
            cls.setValueWithSubDicts(subDict, keylist, value)

        else:
            # print('setVlaue tree', targetDict, keylist, value)
            targetDict[keylist.pop()] = value


    def readPrefetchFile(cls, fname: str) -> bool:
        everythingsFine = True
        cls.filename = fname
        # global channelDataByName, channelNamesByIndex, outputVolumes, outputReceives, channelSends
        try:
            with open(fname) as dicF:
                data = json.load(dicF)
                print('using layout fetched at', datetime.datetime.fromtimestamp(data['fetchtime']))
                channelDataByName = data[channel_properties]
                channelNamesByIndex = data[channel_list]
                _tmpOutputReceives = data[output_receives ]
                _tmpOutputVolumes = data[output_volumes]
                # _tmpChannelSends = data['channel sends']

                for chName in channelDataByName[ti.output].keys():

                    idx = channelNamesByIndex[ti.output].index(chName)
                    if str(idx) in data['output volumes'].keys() and chName in data['output volumes'].keys():
                        outDic = data['output volumes'][chName]
                        cls.outputVolumes[idx] = outDic
                        cls.outputVolumes[chName] = outDic

                for _layer, _outChannels in _tmpOutputReceives.items():
                    for _outCh, _sendChannels in _outChannels.items():
                        for _sendCh, _data in _sendChannels.items():
                            cls.setValueWithSubDicts(cls.outputReceives, [_layer, _outCh, _sendCh], _data)
                            cls.setValueWithSubDicts(cls.channelSends, [_layer, _sendCh, _outCh], _data)

            dicF.close()

        except:
            print("Unexpected error:")
            print('CAUTION no data file found, or data corrupted')
            everythingsFine = False

        numberChannelInLayer = [0,0,0]
        _i = 0
        for _lay in cls.channelDataByName:
            if not len(_lay.keys()) == cls.getNumberChannelOfLayer(_lay):
                everythingsFine = False
            else:
                numberChannelInLayer[_i] = cls.getNumberChannelOfLayer(_lay, False)

        for _i in range(2):
            if not numberChannelInLayer[_i] == numberChannelInLayer[_i+1]:
                everythingsFine = False

        if everythingsFine:

            cls.numberTmChannel = len(cls.channelNamesByIndex[tmbase.busOutput])
            cls.channelLayoutFetched = len(cls.channelNamesByIndex[tmbase.busInput]) > 0
            cls.channelPropertiesFetched = len(cls.getChannelDataByIndex(tmbase.busInput, 0).keys()) > 80
            cls.channelVolumesFetched = len(cls.channelSends[tmbase.busInput].keys()) > 0

        return everythingsFine


    def setNumberTmChannel(cls) -> bool:

        _tmpNumber= 0
        i = 0
        for _lay in cls.channelDataByName:
            cls.numberChannelInLayer[_lay] = cls.getNumberChannelOfLayer(_lay)
            if not len(_lay.keys()) == cls.numberChannelInLayer(_lay):
                return False

            _nChInLayer = cls.getNumberChannelOfLayer(_lay, respectStereo=False)
            if i > 0 and not _tmpNumber == _nChInLayer:
                return False
            _tmpNumber = _nChInLayer
            i = i+1

        cls.numberTmChannel = cls.getNumberChannelOfLayer()
        if cls.numberTmChannel > 0:
            return True
        else:
            return False


    def setLayoutFetched(cls) -> bool:
        cls.numberTmChannel = cls.getNumberChannelOfLayer(respectStereo=False)
        cls.channelLayoutFetched = cls.numberTmChannel > 0
        return cls.channelLayoutFetched


    # def channelPropertiesFetched


    # def getChannelList(cls) -> dict:
    #     return {}
    #
    # def getChannelProperties(cls) -> dict:
    #     return {}
    #
    # # def getChannelVolumes(cls) -> dict:
    # #     return {}
    #
    # def getOutputVolumes(cls) -> dict:
    #     return {}
    #
    # def getOutputReceives(cls) -> dict:
    #     return {}
    #
    # def getChannelSends(cls) -> dict:
    #     return {}
