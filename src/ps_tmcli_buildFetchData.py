
class tmDataClass():

    def __init__(self, filename=None):
        pass


    def writeFetchFiles(fname):
        with open(fname, 'w') as fp:
            completeDict = {
                fetchtime: time.time(),
                'channel properties': channelDataByName,
                'channel list': channelNamesByIndex,
                'output volumes': outputVolumes,
                'channel sends': channelSends,
                'output receives': outputReceives
            }
            json.dump(completeDict, fp, indent=5)

        fp.close()
        print('results written to', fname)

    def setValueWithSubDicts(targetDict: dict, keylist: [], value):
        if len(keylist) > 1:
            key = keylist.pop(0)
            subDict: dict
            if key in targetDict.keys():
                subDict = targetDict[key]
            else:
                subDict = {}
                targetDict[key] = subDict
            setValueWithSubDicts(subDict, keylist, value)

        else:
            # print('setVlaue tree', targetDict, keylist, value)
            targetDict[keylist.pop()] = value

    def indexListWithOffset(indices, offset) -> list:
        ll = []
        for i in indices:
            ll.append(i + offset)
        return ll

    def readPrefetchFile(fname: str) -> bool:
        everythingsFine = True
        global channelDataByName, channelNamesByIndex, outputVolumes, outputReceives, channelSends
        try:
            with open(fname) as dicF:
                data = json.load(dicF)
                print('using layout fetched at', datetime.datetime.fromtimestamp(data[fetchtime]))
                channelDataByName = data['channel properties']
                channelNamesByIndex = data['channel indices']
                _tmpOutputReceives = data['output receives']
                _tmpOutputVolumes = data['output volumes']
                # _tmpChannelSends = data['channel sends']

                for chName in channelDataByName[output].keys():

                    idx = channelNamesByIndex[output].index(chName)
                    if str(idx) in data['output volumes'].keys() and chName in data['output volumes'].keys():
                        outDic = data['output volumes'][chName]
                        outputVolumes[idx] = outDic
                        outputVolumes[chName] = outDic

                for _layer, _outChannels in _tmpOutputReceives.items():
                    for _outCh, _sendChannels in _outChannels.items():
                        for _sendCh, _data in _sendChannels.items():
                            setValueWithSubDicts(outputReceives, [_layer, _outCh, _sendCh], _data)
                            setValueWithSubDicts(channelSends, [_layer, _sendCh, _outCh], _data)

            dicF.close()

        except:
            print("Unexpected error:", sys.exc_info()[0])
            print('CAUTION no data file found, or data corrupted')
            everythingsFine = False

        if everythingsFine:
            global numberTmChannels
            numberTmChannels = len(channelNamesByIndex[input])

        return everythingsFine
