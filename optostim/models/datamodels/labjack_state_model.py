class LabJackStateModel:

    def __init__(self, fio4state=False, fio5state=False, fio6state=False, fio7state=False, dac0=0.0,
                 dac1=0.0, duration=0.0):

        self.FIO4State = fio4state
        self.FIO5State = fio5state
        self.FIO6State = fio6state
        self.FIO7State = fio7state
        self.DAC0 = float(dac0)
        self.DAC1 = float(dac1)
        self.duration = float(duration)

    def __getitem__(self, item):
        return list(self.__dict__.values())[item]

    def __setitem__(self, key, value):
        keys = list(self.__dict__.keys())
        self.__dict__[keys[key]] = value

    def __repr__(self):
        return "LabJack State: {}".format(self.__dict__)
