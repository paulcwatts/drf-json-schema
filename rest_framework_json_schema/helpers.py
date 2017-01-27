from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList


class JSONReturnList(ReturnList):
    def __init__(self, *args, **kwargs):
        self.meta = kwargs.pop('meta', None)
        self.links = kwargs.pop('links', None)
        super(JSONReturnList, self).__init__(*args, **kwargs)


class JSONReturnDict(ReturnDict):
    def __init__(self, *args, **kwargs):
        self.meta = kwargs.pop('meta', None)
        self.links = kwargs.pop('links', None)
        super(JSONReturnDict, self).__init__(*args, **kwargs)
