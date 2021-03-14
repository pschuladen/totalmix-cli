import json
import time, datetime
import ps_tm_info as ti
import ps_tmcli_tmBase as tmbase


channel_properties = 'channel properties'
channel_indices = 'channel indices'
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


    def writeFetchFiles(cls, fname, data:dict):
        with open(cls.filename, 'w') as fp:
            completeDict = {
                'fetchtime': time.time()
            }
            for key, _data in data:
                completeDict[key] = _data
            #     'fetchtime': time.time(),
            #     'channel properties': channelDataByName,
            #     'channel list': channelNamesByIndex,
            #     'output volumes': outputVolumes,
            #     'channel sends': channelSends,
            #     'output receives': outputReceives
            # }
            json.dump(completeDict, fp, indent=5)

        fp.close()
        print('results written to', fname)


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
        # global channelDataByName, channelNamesByIndex, outputVolumes, outputReceives, channelSends
        try:
            with open(fname) as dicF:
                data = json.load(dicF)
                print('using layout fetched at', datetime.datetime.fromtimestamp(data['fetchtime']))
                channelDataByName = data[channel_properties]
                channelNamesByIndex = data[channel_indices]
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

        if everythingsFine:
            cls.numberTmChannels = len(channelNamesByIndex[input])

        return everythingsFine


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
