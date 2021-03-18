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
    fetchtime = None


    def writeFetchFiles(self, data:dict=None,  fname=None) -> bool:
        if fname:
            self.filename = fname
        if not data:
            data = {
                channel_properties: self.channelDataByName.copy(),
                channel_list: self.channelNamesByIndex.copy(),
                output_volumes: self.outputVolumes.copy(),
                output_receives: self.outputReceives.copy()
            }

        if self.filename:
            with open(self.filename, 'w') as fp:
                completeDict = {
                    'fetchtime': time.time()
                }
                for key, _data in data.items():
                    completeDict[key] = _data

                json.dump(completeDict, fp, indent=5)

            fp.close()
            print('results written to', fname)
            return True
        else:
            print('no file was written')
            return False


    def setValueWithSubDicts(self, targetDict: dict, keylist: [], value):
        if len(keylist) > 1:
            key = keylist.pop(0)
            subDict: dict
            if key in targetDict.keys():
                subDict = targetDict[key]
            else:
                subDict = {}
                targetDict[key] = subDict
            self.setValueWithSubDicts(subDict, keylist, value)

        else:
            # print('setVlaue tree', targetDict, keylist, value)
            targetDict[keylist.pop()] = value


    def readPrefetchFile(self, fname: str) -> bool:
        everythingsFine = True
        self.filename = fname
        # global channelDataByName, channelNamesByIndex, outputVolumes, outputReceives, channelSends
        try:
            with open(fname) as dicF:
                data = json.load(dicF)
                print('using layout fetched at', datetime.datetime.fromtimestamp(data['fetchtime']))
                _channelDataByName = data[channel_properties]
                _channelNamesByIndex = data[channel_list]
                _tmpOutputReceives = data[output_receives ]
                _tmpOutputVolumes = data[output_volumes]
                # _tmpChannelSends = data['channel sends']

                # getting Properties and Names
                for _lay in self.channelNamesByIndex:
                    self.channelNamesByIndex[_lay] = _channelNamesByIndex[_lay]
                    self.channelDataByName[_lay] = _channelDataByName[_lay]

                # setting volumes
                for chName in _channelDataByName[tmbase.busOutput].keys():

                    idx = _channelNamesByIndex[ti.output].index(chName)
                    if str(idx) in data['output volumes'].keys() and chName in data['output volumes'].keys():
                        outDic = data['output volumes'][chName]
                        self.outputVolumes[idx] = outDic
                        self.outputVolumes[chName] = outDic

                for _layer, _outChannels in _tmpOutputReceives.items():
                    for _outCh, _sendChannels in _outChannels.items():
                        for _sendCh, _data in _sendChannels.items():
                            self.setValueWithSubDicts(self.outputReceives, [_layer, _outCh, _sendCh], _data)
                            self.setValueWithSubDicts(self.channelSends, [_layer, _sendCh, _outCh], _data)

            dicF.close()

        except:
            print("Unexpected error:")
            print('CAUTION no data file found, or data corrupted')
            everythingsFine = False

        if everythingsFine:

            print('validate data...')

            numberChannelInLayer = [0,0,0]
            _i = 0
            for _lay in self.channelDataByName:
                # print('heereree ', _lay, len(self.channelDataByName[_lay].keys()), self.getNumberChannelOfLayer(_lay))

                if not len(self.channelDataByName[_lay].keys()) == self.getNumberChannelOfLayer(_lay):
                    everythingsFine = False
                else:
                    numberChannelInLayer[_i] = self.getNumberChannelOfLayer(_lay, False)

            # for _i in range(2):
            #     if not numberChannelInLayer[_i] == numberChannelInLayer[_i+1]:
            #         everythingsFine = False

            if everythingsFine:

                print('everything seems to be legit')

                # self.numberTmChannel = len(self.channelNamesByIndex[tmbase.busOutput])
                self.numberOfChannel[tmbase.total] = len(self.channelNamesByIndex[tmbase.busOutput])
                self.setNumberTmChannel()
                self.fetchState['layout'] = len(self.channelNamesByIndex[tmbase.busInput]) > 0
                self.fetchState['properties'] = len(self.getChannelDataByIndex(tmbase.busInput, 0).keys()) > 80
                self.fetchState['volumes'] = len(self.channelSends[tmbase.busInput].keys()) > 0

                self.fetchtime = data['fetchtime']


        return everythingsFine


    def setNumberTmChannel(self) -> bool:

        _tmpNumber= 0
        i = 0
        for _lay in self.channelDataByName:
            self.numberOfChannel[_lay] = self.getNumberChannelOfLayer(_lay)
            if not len(self.channelDataByName[_lay].keys()) == self.numberOfChannel[_lay]:
                return False

            _nChInLayer = self.getNumberChannelOfLayer(_lay, respectStereo=False)
            if i > 0 and not _tmpNumber == _nChInLayer:
                return False
            _tmpNumber = _nChInLayer
            i = i+1

        self.numberOfChannel[tmbase.total] = self.getNumberChannelOfLayer(respectStereo=False)
        print('tmdata number tmChannels', self.numberOfChannel[tmbase.total])

        if self.numberOfChannel[tmbase.total] > 0:
            return True
        else:
            return False


    def setLayoutFetched(self) -> bool:
        self.numberOfChannel[tmbase.total] = self.getNumberChannelOfLayer(respectStereo=False)
        self.channelLayoutFetched = self.numberOfChannel[tmbase.total] > 0
        return self.channelLayoutFetched


